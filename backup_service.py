"""
Database Backup & Version History Service for TeamTasks.

Provides:
- Fully automatic daily database backups at 23:00 to the instance mountpoint.
- Retention policy keeping the latest 14 versions.
- 'Backup Now' on-demand snapshot creation directly to the server folder.
- Fast direct database restore with SQLite integrity validation.
- Secure direct downloading of backup snapshots.
- Multi-worker / Gunicorn safe execution via atomic filesystem locks.
"""
import os
import sys
import time
import glob
import shutil
import sqlite3
import threading
import logging
from datetime import datetime

logger = logging.getLogger('teamtasks.backup')
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] [BackupService] %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Default settings
DEFAULT_RETENTION_COUNT = 14
DEFAULT_BACKUP_HOUR = 23
DEFAULT_BACKUP_MINUTE = 0

_scheduler_started = False
_scheduler_lock = threading.Lock()


def get_db_path(app_instance_path=None):
    """
    Resolves the canonical path of the active SQLite tasks.db file.
    """
    if app_instance_path:
        db_path = os.path.join(app_instance_path, 'tasks.db')
        if os.path.exists(db_path):
            return os.path.abspath(db_path)
    
    # Try relative to project root
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(base_dir, 'instance', 'tasks.db')
    if os.path.exists(candidate):
        return os.path.abspath(candidate)
        
    if app_instance_path:
        return os.path.abspath(os.path.join(app_instance_path, 'tasks.db'))
        
    return os.path.abspath(candidate)


def get_backups_dir(app_instance_path=None):
    """
    Resolves and ensures the backups folder on the exact same mountpoint
    as the active database file (inside instance/backups).
    Migrates any legacy loose backup files found in instance/.
    """
    db_path = get_db_path(app_instance_path)
    instance_dir = os.path.dirname(db_path)
    backups_dir = os.path.join(instance_dir, 'backups')
    os.makedirs(backups_dir, exist_ok=True)

    # Migrate any legacy loose tasks_backup_*.db from instance root into instance/backups
    try:
        legacy_files = glob.glob(os.path.join(instance_dir, 'tasks_backup_*.db'))
        for leg in legacy_files:
            fname = os.path.basename(leg)
            dest = os.path.join(backups_dir, fname)
            if not os.path.exists(dest):
                shutil.move(leg, dest)
                logger.info(f"Migrated legacy backup {fname} into backups folder")
    except Exception as e:
        logger.warning(f"Error migrating legacy backups: {e}")

    return backups_dir


def verify_db_file_integrity(file_path):
    """
    Validates SQLite file integrity using PRAGMA integrity_check.
    Returns (is_valid: bool, error_message: str).
    """
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        return False, "File is missing or empty"
        
    conn = None
    try:
        conn = sqlite3.connect(file_path, timeout=10.0)
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check")
        row = cur.fetchone()
        if row and row[0] == "ok":
            return True, "ok"
        return False, str(row[0]) if row else "Unknown integrity check failure"
    except Exception as e:
        return False, str(e)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def format_file_size(size_bytes):
    """Formats file size into human-readable string (KB/MB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def parse_backup_filename(filename):
    """
    Parses metadata from backup filename.
    Recognized patterns:
      - tasks_daily_YYYY-MM-DD_HHMMSS.db
      - tasks_manual_YYYY-MM-DD_HHMMSS.db
      - tasks_backup_YYYYMMDD_HHMMSS.db
    """
    backup_type = "system"
    type_label = "גיבוי מערכת"
    dt = None

    base = filename
    if base.endswith('.db'):
        base = base[:-3]

    parts = base.split('_')
    if len(parts) >= 2:
        tag = parts[1].lower()
        if tag == "daily":
            backup_type = "daily"
            type_label = "אוטומטי (יומי 23:00)"
        elif tag == "manual":
            backup_type = "manual"
            type_label = "ידני (לפי דרישה)"

    # Try parsing date from parts
    try:
        # Pattern tasks_daily_YYYY-MM-DD_HHMMSS
        if len(parts) >= 4 and '-' in parts[2]:
            date_str = f"{parts[2]} {parts[3]}"
            dt = datetime.strptime(date_str, "%Y-%m-%d %H%M%S")
        elif len(parts) >= 3 and len(parts[2]) == 8 and parts[2].isdigit():
            # Pattern tasks_backup_YYYYMMDD_HHMMSS
            time_part = parts[3] if len(parts) >= 4 and len(parts[3]) >= 6 else "000000"
            dt = datetime.strptime(f"{parts[2]} {time_part[:6]}", "%Y%m%d %H%M%S")
    except Exception:
        dt = None

    return {
        'type': backup_type,
        'type_label': type_label,
        'datetime': dt
    }


def list_backups(app_instance_path=None):
    """
    Returns sorted list of available database backup files with full metadata.
    Sorted from newest to oldest.
    """
    backups_dir = get_backups_dir(app_instance_path)
    pattern = os.path.join(backups_dir, "*.db")
    files = glob.glob(pattern)

    result = []
    for fpath in files:
        fname = os.path.basename(fpath)
        # Skip temporary files
        if fname.endswith('.tmp') or fname.startswith('.'):
            continue

        try:
            stat = os.stat(fpath)
            size_bytes = stat.st_size
            mtime = stat.st_mtime
            
            parsed = parse_backup_filename(fname)
            created_dt = parsed['datetime'] or datetime.fromtimestamp(mtime)
            created_timestamp = created_dt.timestamp()

            result.append({
                'filename': fname,
                'filepath': fpath,
                'type': parsed['type'],
                'type_label': parsed['type_label'],
                'size_bytes': size_bytes,
                'size_formatted': format_file_size(size_bytes),
                'created_at': created_timestamp,
                'created_at_formatted': created_dt.strftime('%d/%m/%Y %H:%M:%S'),
                'is_valid': True
            })
        except Exception as e:
            logger.warning(f"Error reading backup file {fname}: {e}")

    # Sort newest first
    result.sort(key=lambda x: x['created_at'], reverse=True)
    return result


def prune_backups(keep_count=DEFAULT_RETENTION_COUNT, app_instance_path=None):
    """
    Deletes older backup files exceeding the keep_count limit.
    Also cleans up expired daily lock files older than 7 days.
    """
    backups = list_backups(app_instance_path)
    removed_files = []
    
    if len(backups) > keep_count:
        excess = backups[keep_count:]
        for item in excess:
            try:
                if os.path.exists(item['filepath']):
                    os.remove(item['filepath'])
                    removed_files.append(item['filename'])
                    logger.info(f"Pruned older backup: {item['filename']}")
            except Exception as e:
                logger.error(f"Failed to prune backup {item['filename']}: {e}")

    # Clean old .lock_daily_* files older than 7 days
    try:
        backups_dir = get_backups_dir(app_instance_path)
        now_ts = time.time()
        for lock_file in glob.glob(os.path.join(backups_dir, ".lock_daily_*")):
            try:
                if now_ts - os.path.getmtime(lock_file) > 7 * 86400:
                    os.remove(lock_file)
            except Exception:
                pass
    except Exception:
        pass

    return removed_files


def create_backup(backup_type="manual", keep_count=DEFAULT_RETENTION_COUNT, app_instance_path=None):
    """
    Creates an online, transactionally-safe SQLite snapshot of tasks.db
    into the backups directory on the database mountpoint.
    Enforces retention policy (default 14 versions).
    """
    db_path = get_db_path(app_instance_path)
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found at {db_path}")

    backups_dir = get_backups_dir(app_instance_path)
    now = datetime.now()
    ts_str = now.strftime('%Y-%m-%d_%H%M%S')
    filename = f"tasks_{backup_type}_{ts_str}.db"
    counter = 1
    while os.path.exists(os.path.join(backups_dir, filename)):
        filename = f"tasks_{backup_type}_{ts_str}_{counter}.db"
        counter += 1
    target_path = os.path.join(backups_dir, filename)
    temp_path = target_path + ".tmp"

    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except Exception:
            pass

    # Safe SQLite Online Backup API
    src_conn = None
    dest_conn = None
    try:
        src_conn = sqlite3.connect(db_path, timeout=30.0)
        # Attempt WAL checkpoint to flush pending changes to main db file
        try:
            src_conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except Exception:
            pass

        dest_conn = sqlite3.connect(temp_path)
        src_conn.backup(dest_conn, pages=100)
    finally:
        if dest_conn:
            try:
                dest_conn.close()
            except Exception:
                pass
        if src_conn:
            try:
                src_conn.close()
            except Exception:
                pass

    # Verify integrity of the created snapshot
    is_valid, err = verify_db_file_integrity(temp_path)
    if not is_valid:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        raise ValueError(f"Created backup failed integrity check: {err}")

    # Atomic move to final destination
    if os.path.exists(target_path):
        os.remove(target_path)
    os.replace(temp_path, target_path)

    logger.info(f"Database backup created: {filename} ({format_file_size(os.path.getsize(target_path))})")

    # Prune older backups
    pruned = prune_backups(keep_count=keep_count, app_instance_path=app_instance_path)

    # Return new backup info
    stat = os.stat(target_path)
    parsed = parse_backup_filename(filename)
    return {
        'filename': filename,
        'filepath': target_path,
        'type': parsed['type'],
        'type_label': parsed['type_label'],
        'size_bytes': stat.st_size,
        'size_formatted': format_file_size(stat.st_size),
        'created_at': now.timestamp(),
        'created_at_formatted': now.strftime('%d/%m/%Y %H:%M:%S'),
        'is_valid': True,
        'pruned_count': len(pruned)
    }


def restore_backup(filename, app=None, db=None, on_version_bump=None):
    """
    Performs a fast, verified restore from a chosen backup file in the backups folder.
    Steps:
      1. Validates safe filename and existence.
      2. Validates SQLite integrity of the backup file.
      3. Disposes SQLAlchemy engine and active connections.
      4. Restores via SQLite online backup API to tasks.db.
      5. Re-checks restored database integrity.
      6. Triggers data version bump so all clients refresh.
    """
    safe_name = os.path.basename(filename)
    if not safe_name.endswith('.db') or '/' in filename or '\\' in filename or '..' in filename:
        raise ValueError("Invalid backup filename")

    app_instance = app.instance_path if app else None
    backups_dir = get_backups_dir(app_instance)
    backup_path = os.path.join(backups_dir, safe_name)

    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file '{safe_name}' does not exist in backups directory")

    # Step 1: Verify integrity before restoring
    is_valid, err = verify_db_file_integrity(backup_path)
    if not is_valid:
        raise ValueError(f"Backup file failed integrity verification: {err}")

    target_db = get_db_path(app_instance)

    # Step 2: Safety snapshot of current database
    safety_backup = target_db + ".pre_restore"
    try:
        if os.path.exists(target_db):
            shutil.copyfile(target_db, safety_backup)
    except Exception as e:
        logger.warning(f"Could not create pre-restore safety copy: {e}")

    # Step 3: Dispose active SQLAlchemy connections
    if db:
        try:
            db.session.remove()
            db.engine.dispose()
        except Exception as e:
            logger.warning(f"Disposing SQLAlchemy engine before restore: {e}")

    # Step 4: Perform online restore from backup file to active db
    src_conn = None
    dest_conn = None
    try:
        src_conn = sqlite3.connect(backup_path, timeout=30.0)
        dest_conn = sqlite3.connect(target_db, timeout=30.0)
        src_conn.backup(dest_conn, pages=100)
    finally:
        if dest_conn:
            try:
                dest_conn.close()
            except Exception:
                pass
        if src_conn:
            try:
                src_conn.close()
            except Exception:
                pass

    # Step 5: Verify restored database integrity
    is_restored_valid, rest_err = verify_db_file_integrity(target_db)
    if not is_restored_valid:
        # Revert to safety copy
        if os.path.exists(safety_backup):
            try:
                shutil.copyfile(safety_backup, target_db)
            except Exception:
                pass
        raise ValueError(f"Database restore failed integrity check: {rest_err}")

    # Clean up safety copy on success
    if os.path.exists(safety_backup):
        try:
            os.remove(safety_backup)
        except Exception:
            pass

    # Step 6: Dispose connections again so next request connects cleanly to restored db
    if db:
        try:
            db.session.remove()
            db.engine.dispose()
        except Exception as e:
            logger.warning(f"Disposing SQLAlchemy engine after restore: {e}")

    # Step 7: Trigger version bump
    if callable(on_version_bump):
        try:
            on_version_bump()
        except Exception as e:
            logger.warning(f"Version bump listener error: {e}")

    logger.info(f"Database restored successfully from {safe_name}")
    return {
        'success': True,
        'filename': safe_name,
        'message': f"מסד הנתונים שוחזר בהצלחה מגרסת {safe_name}",
        'restored_at': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }


def delete_backup(filename, app_instance_path=None):
    """
    Deletes a specific backup snapshot file.
    """
    safe_name = os.path.basename(filename)
    if not safe_name.endswith('.db') or '/' in filename or '\\' in filename or '..' in filename:
        raise ValueError("Invalid backup filename")

    backups_dir = get_backups_dir(app_instance_path)
    target_path = os.path.join(backups_dir, safe_name)

    if not os.path.exists(target_path):
        raise FileNotFoundError(f"Backup file '{safe_name}' not found")

    os.remove(target_path)
    logger.info(f"Deleted backup snapshot: {safe_name}")
    return True


# =====================================================================
# AUTOMATIC DAILY SCHEDULER (23:00) WITH MULTI-WORKER ATOMIC LOCKS
# =====================================================================

def _scheduler_worker_loop(app_instance_path, target_hour=DEFAULT_BACKUP_HOUR, target_minute=DEFAULT_BACKUP_MINUTE, keep_count=DEFAULT_RETENTION_COUNT):
    """
    Background worker loop. Checks every 30 seconds if it is time to perform
    the daily backup (hour >= 23 and not yet completed today).
    Uses atomic filesystem lock to guarantee single execution across multiple Gunicorn workers.
    """
    logger.info(f"Daily backup scheduler worker started (target: {target_hour:02d}:{target_minute:02d}, retention: {keep_count} versions)")

    while True:
        try:
            time.sleep(30)
            now = datetime.now()
            today_str = now.strftime('%Y-%m-%d')

            # We trigger when current hour is >= target_hour (e.g., 23:00 to 23:59 or past)
            if now.hour >= target_hour:
                backups_dir = get_backups_dir(app_instance_path)
                
                # Check if a daily backup already exists for today
                daily_today_matches = glob.glob(os.path.join(backups_dir, f"tasks_daily_{today_str}_*.db"))
                if daily_today_matches:
                    # Already backed up today
                    continue

                # Acquire atomic lock using O_CREAT | O_EXCL
                lock_file = os.path.join(backups_dir, f".lock_daily_{today_str}")
                try:
                    fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    try:
                        with os.fdopen(fd, 'w') as f:
                            f.write(f"daily_backup_started_at={now.isoformat()}\npid={os.getpid()}\n")
                    except Exception:
                        pass
                except FileExistsError:
                    # Another worker is already taking or has locked today's daily backup
                    continue

                # We acquired the lock! Create today's daily backup
                try:
                    logger.info(f"Executing automatic daily backup for {today_str} at 23:00...")
                    res = create_backup(backup_type="daily", keep_count=keep_count, app_instance_path=app_instance_path)
                    logger.info(f"Automatic daily backup finished successfully: {res['filename']}")
                except Exception as ex:
                    logger.error(f"Failed to create automatic daily backup: {ex}")
                    # If failed, remove lock file so it can retry
                    try:
                        if os.path.exists(lock_file):
                            os.remove(lock_file)
                    except Exception:
                        pass

        except Exception as e:
            logger.error(f"Error in backup scheduler loop: {e}")
            time.sleep(60)


def start_daily_backup_scheduler(app=None, target_hour=DEFAULT_BACKUP_HOUR, target_minute=DEFAULT_BACKUP_MINUTE, keep_count=DEFAULT_RETENTION_COUNT):
    """
    Starts the daemon background thread for automatic daily backups.
    Idempotent: starts only once per process.
    """
    global _scheduler_started
    with _scheduler_lock:
        if _scheduler_started:
            return

        # Read environment overrides if available
        try:
            env_hour = os.environ.get('DB_BACKUP_HOUR')
            if env_hour is not None and env_hour.isdigit():
                target_hour = int(env_hour)
            env_retention = os.environ.get('DB_BACKUP_RETENTION_COUNT')
            if env_retention is not None and env_retention.isdigit():
                keep_count = int(env_retention)
        except Exception:
            pass

        app_instance = app.instance_path if app else None
        t = threading.Thread(
            target=_scheduler_worker_loop,
            args=(app_instance, target_hour, target_minute, keep_count),
            daemon=True,
            name="DailyDbBackupScheduler"
        )
        t.start()
        _scheduler_started = True
        logger.info(f"Daily DB Backup Scheduler initialized (Daily at {target_hour:02d}:00, keep {keep_count} versions)")
