// Admin Page JavaScript
document.addEventListener('DOMContentLoaded', () => {
    let teams = [];
    let currentTeam = null;
    let currentMember = null;
    let selectedFile = null;
    let selectedPredefinedAvatar = null;
    let predefinedAvatarsCache = null;

    // DOM Elements
    const teamsContainer = document.getElementById('teamsContainer');
    const addTeamBtn = document.getElementById('addTeamBtn');
    const addMemberBtn = document.getElementById('addMemberBtn');
    const teamModal = document.getElementById('teamModal');
    const memberModal = document.getElementById('memberModal');
    const specialDayModal = document.getElementById('specialDayModal');
    const closeModalBtns = document.querySelectorAll('.close-modal, .close-member-modal, .close-special-modal');
    const saveTeamBtn = document.getElementById('saveTeamBtn');
    const saveMemberBtn = document.getElementById('saveMemberBtn');
    const cancelTeamBtn = document.getElementById('cancelTeamBtn');
    const cancelMemberBtn = document.getElementById('cancelMemberBtn');
    const toast = document.getElementById('toast');

    // Special Days Elements
    let specialDays = [];
    const specialDaysContainer = document.getElementById('specialDaysContainer');
    const addSpecialDayBtn = document.getElementById('addSpecialDayBtn');
    const saveSpecialDayBtn = document.getElementById('saveSpecialDayBtn');
    const cancelSpecialDayBtn = document.getElementById('cancelSpecialDayBtn');
    const specialDayDateInput = document.getElementById('specialDayDateInput');
    const specialDayNameInput = document.getElementById('specialDayNameInput');
    const specialDayTypeSelect = document.getElementById('specialDayTypeSelect');
    const specialDayIdInput = document.getElementById('specialDayId');
    const specialDayColorPicker = document.getElementById('specialDayColorPicker');
    const specialDayColorInput = document.getElementById('specialDayColorInput');

    // Helper to notify other tabs/pages
    function broadcastAdminChange() {
        if (typeof window.teamtasksNotifyChange === 'function') {
            window.teamtasksNotifyChange();
        } else if (typeof BroadcastChannel !== 'undefined') {
            try {
                new BroadcastChannel('teamtasks_live_sync').postMessage({ type: 'teamtasks:data_changed', timestamp: Date.now() });
            } catch (e) {}
        }
    }

    function isAnyAdminModalOpen() {
        return (teamModal && teamModal.style.display === 'block') ||
               (memberModal && memberModal.style.display === 'block') ||
               (specialDayModal && specialDayModal.style.display === 'block');
    }

    let lastAdminVersion = null;
    let isAdminUpdating = false;

    async function checkAdminUpdates() {
        if (isAdminUpdating || isAnyAdminModalOpen()) return;
        try {
            const res = await fetch('/api/version?t=' + Date.now());
            const data = await res.json();
            if (data && typeof data.timestamp !== 'undefined') {
                if (lastAdminVersion === null) {
                    lastAdminVersion = data.timestamp;
                    return;
                }
                if (data.timestamp > lastAdminVersion) {
                    lastAdminVersion = data.timestamp;
                    isAdminUpdating = true;
                    await loadTeams();
                    const activeSection = document.querySelector('.settings-section.active');
                    if (activeSection && activeSection.id === 'section-special-days') {
                        await loadSpecialDays();
                    } else if (activeSection && activeSection.id === 'section-backup') {
                        await loadDbBackups();
                    }
                    isAdminUpdating = false;
                }
            }
        } catch (e) {
            isAdminUpdating = false;
        }
    }

    // Load teams on page load
    loadTeams();

    // Start fast polling (every 1.5 seconds)
    setInterval(checkAdminUpdates, 1500);

    // Cross-tab live sync listener
    if (typeof BroadcastChannel !== 'undefined') {
        try {
            const liveChannel = new BroadcastChannel('teamtasks_live_sync');
            liveChannel.onmessage = (event) => {
                if (event.data && event.data.type === 'teamtasks:data_changed') {
                    if (!isAnyAdminModalOpen()) {
                        loadTeams();
                        const activeSection = document.querySelector('.settings-section.active');
                        if (activeSection && activeSection.id === 'section-special-days') {
                            loadSpecialDays();
                        } else if (activeSection && activeSection.id === 'section-backup') {
                            loadDbBackups();
                        }
                    }
                }
            };
        } catch (e) {}
    }

    window.addEventListener('teamtasks:refresh', () => {
        if (!isAnyAdminModalOpen()) {
            loadTeams();
            const activeSection = document.querySelector('.settings-section.active');
            if (activeSection && activeSection.id === 'section-special-days') {
                loadSpecialDays();
            } else if (activeSection && activeSection.id === 'section-backup') {
                loadDbBackups();
            }
        }
    });

    // Sidebar Navigation
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.settings-section');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            // Update Nav
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            // Update Section
            const sectionId = 'section-' + item.dataset.section;
            sections.forEach(section => {
                if (section.id === sectionId) {
                    section.classList.add('active');
                } else {
                    section.classList.remove('active');
                }
            });

            if (item.dataset.section === 'special-days') {
                loadSpecialDays();
            } else if (item.dataset.section === 'backup') {
                loadDbBackups();
            } else if (item.dataset.section === 'system') {
                loadSystemSettings();
            } else if (item.dataset.section === 'mcp') {
                loadMcpInfo();
            }
        });
    });

    // Backup & Restore
    const downloadBackupBtn = document.getElementById('downloadBackupBtn');
    if (downloadBackupBtn) {
        downloadBackupBtn.addEventListener('click', () => {
            const table = document.getElementById('backupTableSelect').value;
            window.location.href = `/api/backup/${table}`;
        });
    }

    const restoreBtn = document.getElementById('restoreBtn');
    if (restoreBtn) {
        restoreBtn.addEventListener('click', async () => {
            const table = document.getElementById('restoreTableSelect').value;
            const fileInput = document.getElementById('restoreFileInput');
            const files = fileInput.files;

            if (files.length === 0) {
                showToast('נא לבחור קובץ אחד לפחות', 'error');
                return;
            }

            const confirmMsg = table === 'all'
                ? 'אזהרה חמורה: שחזור כל המערכת ימחק את כל הנתונים הקיימים ויחליף אותם בנתוני קובץ הגיבוי! האם להמשיך?'
                : `האם אתה בטוח שברצונך לשחזר נתונים לטבלה "${table}"? פעולה זו תעדכן או תוסיף נתונים מהגיבוי.`;

            if (!confirm(confirmMsg)) {
                return;
            }

            const origHtml = restoreBtn.innerHTML;
            restoreBtn.disabled = true;
            restoreBtn.innerHTML = 'משחזר נתונים...';

            let successCount = 0;
            let errorCount = 0;

            try {
                // Process files sequentially
                for (let i = 0; i < files.length; i++) {
                    const formData = new FormData();
                    formData.append('file', files[i]);

                    try {
                        const response = await fetch(`/api/restore/${table}`, {
                            method: 'POST',
                            body: formData
                        });
                        const result = await response.json();

                        if (result.success) {
                            successCount++;
                        } else {
                            console.error(`Error restoring file ${files[i].name}:`, result.error);
                            errorCount++;
                            showToast(`שגיאה בקובץ ${files[i].name}: ${result.error}`, 'error');
                        }
                    } catch (error) {
                        console.error(error);
                        errorCount++;
                        showToast(`שגיאה בקובץ ${files[i].name}`, 'error');
                    }
                }

                if (successCount > 0) {
                    showToast(`השחזור הושלם: ${successCount} קבצים עובדו בהצלחה`, 'success');
                    if (table === 'teams' || table === 'members' || table === 'projects' || table === 'all') {
                        if (typeof loadTeams === 'function') loadTeams();
                    }
                    if (typeof loadSystemMetrics === 'function') {
                        loadSystemMetrics();
                    }
                    broadcastAdminChange();
                }
            } finally {
                restoreBtn.disabled = false;
                restoreBtn.innerHTML = origHtml;
                fileInput.value = '';
            }
        });
    }

    // --- Database Version History & Fast Restore ---
    const btnRefreshDbBackups = document.getElementById('btnRefreshDbBackups');
    if (btnRefreshDbBackups) {
        btnRefreshDbBackups.addEventListener('click', () => {
            loadDbBackups();
            showToast('היסטוריית גרסאות רועננה', 'info');
        });
    }

    const btnBackupNow = document.getElementById('btnBackupNow');
    if (btnBackupNow) {
        btnBackupNow.addEventListener('click', () => triggerBackupNow());
    }

    async function loadDbBackups() {
        const tbody = document.getElementById('dbBackupsTableBody');
        if (!tbody) return;

        try {
            const response = await fetch('/api/backups');
            const data = await response.json();

            if (!data.success) {
                tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #ef4444; padding: 2rem;">שגיאה בטעינת גיבויים: ${escapeHtml(data.error || 'שגיאה לא ידועה')}</td></tr>`;
                return;
            }

            const backups = data.backups || [];
            const countBadge = document.getElementById('badgeBackupsCount');
            if (countBadge) {
                countBadge.textContent = `${backups.length} / ${data.retention_limit || 14} גרסאות`;
            }
            const retentionBadge = document.getElementById('badgeRetentionPolicy');
            if (retentionBadge && data.retention_limit) {
                retentionBadge.textContent = `שמירת ${data.retention_limit} גרסאות`;
            }

            if (backups.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="6" style="text-align: center; color: #6b7280; padding: 2.5rem 1rem;">
                            <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem; color: #374151;">אין עדיין גיבויים שמורים במערכת</div>
                            <p style="font-size: 0.875rem; margin: 0 0 1rem 0; color: #9ca3af;">הגיבוי האוטומטי מתבצע מדי יום ב-23:00, או שניתן לבצע גיבוי ידני כעת בלחיצה על הכפתור.</p>
                            <button type="button" class="btn btn-primary btn-sm" onclick="triggerBackupNow()">
                                גבה עכשיו לשרת
                            </button>
                        </td>
                    </tr>
                `;
                return;
            }

            let html = '';
            backups.forEach(item => {
                const typeClass = item.type === 'daily' ? 'backup-type-daily' : (item.type === 'manual' ? 'backup-type-manual' : 'backup-type-system');
                const typeIcon = item.type === 'daily' ? '🕒' : (item.type === 'manual' ? '⚡' : '💾');

                html += `
                    <tr data-filename="${escapeHtml(item.filename)}">
                        <td style="font-weight: 600; white-space: nowrap;">
                            ${escapeHtml(item.created_at_formatted || '')}
                        </td>
                        <td>
                            <span class="backup-type-pill ${typeClass}">
                                <span>${typeIcon}</span>
                                <span>${escapeHtml(item.type_label || item.type)}</span>
                            </span>
                        </td>
                        <td dir="ltr" style="font-family: monospace; font-size: 0.825rem; color: #4b5563; text-align: left;">
                            ${escapeHtml(item.filename)}
                        </td>
                        <td style="white-space: nowrap; color: #6b7280; font-weight: 500;">
                            ${escapeHtml(item.size_formatted || '')}
                        </td>
                        <td>
                            <span class="status-pill status-pill-success" style="font-size: 0.75rem; padding: 0.15rem 0.5rem;">
                                ✓ מאומת
                            </span>
                        </td>
                        <td style="text-align: center; white-space: nowrap;">
                            <div class="backup-actions-cell">
                                <button type="button" class="btn-restore-action" onclick="fastRestoreBackup('${escapeHtml(item.filename)}', '${escapeHtml(item.created_at_formatted || item.filename)}')">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <polyline points="1 4 1 10 7 10"></polyline>
                                        <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
                                    </svg>
                                    שחזור מהיר
                                </button>
                                <a href="/api/backups/${encodeURIComponent(item.filename)}/download" class="btn-download-action" download title="הורד קובץ מסד נתונים .db">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                        <polyline points="7 10 12 15 17 10"></polyline>
                                        <line x1="12" y1="15" x2="12" y2="3"></line>
                                    </svg>
                                    הורדה
                                </a>
                                <button type="button" class="btn-delete-backup-action" onclick="deleteDbBackup('${escapeHtml(item.filename)}')" title="מחק גרסת גיבוי זו">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <polyline points="3 6 5 6 21 6"></polyline>
                                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                    </svg>
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            });

            tbody.innerHTML = html;

        } catch (e) {
            console.error('Failed to load database backups:', e);
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #ef4444; padding: 2rem;">שגיאה בתקשורת עם השרת: ${escapeHtml(e.message)}</td></tr>`;
        }
    }

    async function triggerBackupNow() {
        const btn = document.getElementById('btnBackupNow');
        const origHtml = btn ? btn.innerHTML : '';
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = 'מגבה לשרת...';
        }

        try {
            const response = await fetch('/api/backups/now', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: 'manual' })
            });
            const result = await response.json();

            if (result.success) {
                showToast('גיבוי מסד הנתונים נוצר בהצלחה ונשמר בשרת!', 'success');
                await loadDbBackups();
                if (typeof loadSystemMetrics === 'function') loadSystemMetrics();
            } else {
                showToast(`שגיאה ביצירת גיבוי: ${result.error}`, 'error');
            }
        } catch (err) {
            console.error('Backup now failed:', err);
            showToast('שגיאה בתקשורת עם השרת ביצירת גיבוי', 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = origHtml;
            }
        }
    }

    async function fastRestoreBackup(filename, displayDate) {
        const confirmMsg = `אזהרה:\n\nהאם לשחזר את מסד הנתונים מהגרסה שנבחרה?\n\nקובץ: ${filename}\nמועד: ${displayDate}\n\nפעולה זו תחליף את מסד הנתונים הקיים בגרסת הגיבוי. האם להמשיך?`;
        if (!confirm(confirmMsg)) {
            return;
        }

        const row = document.querySelector(`tr[data-filename="${filename}"]`);
        const restoreBtn = row ? row.querySelector('.btn-restore-action') : null;
        let origText = '';
        if (restoreBtn) {
            origText = restoreBtn.innerHTML;
            restoreBtn.disabled = true;
            restoreBtn.innerHTML = 'משחזר...';
        }

        try {
            const response = await fetch(`/api/backups/${encodeURIComponent(filename)}/restore`, {
                method: 'POST'
            });
            const result = await response.json();

            if (result.success) {
                showToast(result.message || 'מסד הנתונים שוחזר בהצלחה מגרסת הגיבוי!', 'success');
                if (typeof loadTeams === 'function') loadTeams();
                if (typeof loadSpecialDays === 'function') loadSpecialDays();
                if (typeof loadSystemMetrics === 'function') loadSystemMetrics();
                if (typeof broadcastAdminChange === 'function') broadcastAdminChange();
                await loadDbBackups();
            } else {
                showToast(`שגיאה בשחזור: ${result.error}`, 'error');
                if (restoreBtn) {
                    restoreBtn.disabled = false;
                    restoreBtn.innerHTML = origText;
                }
            }
        } catch (err) {
            console.error('Fast restore error:', err);
            showToast('שגיאת תקשורת בעת ביצוע שחזור מהיר', 'error');
            if (restoreBtn) {
                restoreBtn.disabled = false;
                restoreBtn.innerHTML = origText;
            }
        }
    }

    async function deleteDbBackup(filename) {
        if (!confirm(`האם אתה בטוח שברצונך למחוק לצמיתות את גרסת הגיבוי "${filename}"?`)) {
            return;
        }

        try {
            const response = await fetch(`/api/backups/${encodeURIComponent(filename)}`, {
                method: 'DELETE'
            });
            const result = await response.json();
            if (result.success) {
                showToast('הגיבוי נמחק בהצלחה', 'success');
                await loadDbBackups();
            } else {
                showToast(`שגיאה במחיקת גיבוי: ${result.error}`, 'error');
            }
        } catch (err) {
            console.error('Delete backup error:', err);
            showToast('שגיאת תקשורת במחיקת גיבוי', 'error');
        }
    }

    // Expose helpers globally
    window.loadDbBackups = loadDbBackups;
    window.triggerBackupNow = triggerBackupNow;
    window.fastRestoreBackup = fastRestoreBackup;
    window.deleteDbBackup = deleteDbBackup;

    // Event Listeners
    addTeamBtn.addEventListener('click', () => openTeamModal());
    if (addMemberBtn) addMemberBtn.addEventListener('click', () => openMemberModal());
    saveTeamBtn.addEventListener('click', saveTeam);
    saveMemberBtn.addEventListener('click', saveMember);
    cancelTeamBtn.addEventListener('click', () => closeModal(teamModal));
    cancelMemberBtn.addEventListener('click', () => closeModal(memberModal));

    if (addSpecialDayBtn) addSpecialDayBtn.addEventListener('click', () => openSpecialDayModal());
    if (saveSpecialDayBtn) saveSpecialDayBtn.addEventListener('click', saveSpecialDay);
    if (cancelSpecialDayBtn) cancelSpecialDayBtn.addEventListener('click', closeSpecialDayModal);

    closeModalBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            closeModal(teamModal);
            closeModal(memberModal);
            if (specialDayModal) closeSpecialDayModal();
        });
    });

    // Avatar file input
    document.getElementById('memberAvatar').addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            selectedFile = file;
            selectedPredefinedAvatar = null;
            document.querySelectorAll('#predefinedAvatarsGrid .predefined-avatar-item').forEach(el => el.classList.remove('selected'));
            const reader = new FileReader();
            reader.onload = (e) => {
                document.getElementById('avatarPreview').src = e.target.result;
            };
            reader.readAsDataURL(file);
        }
    });

    async function loadPredefinedAvatars() {
        if (!predefinedAvatarsCache) {
            try {
                const res = await fetch('/api/avatars');
                const data = await res.json();
                if (data.success && Array.isArray(data.avatars) && data.avatars.length > 0) {
                    predefinedAvatarsCache = data.avatars;
                }
            } catch (e) {
                console.error('Failed to fetch predefined avatars:', e);
            }
            if (!predefinedAvatarsCache) {
                predefinedAvatarsCache = Array.from({ length: 12 }, (_, i) => ({
                    id: `avatar_${i + 1}.png`,
                    filename: `avatar_${i + 1}.png`,
                    url: `/static/avatars/avatar_${i + 1}.png`
                }));
            }
        }
        return predefinedAvatarsCache;
    }

    async function renderPredefinedAvatars() {
        const grid = document.getElementById('predefinedAvatarsGrid');
        if (!grid) return;
        const avatars = await loadPredefinedAvatars();
        grid.innerHTML = avatars.map(av => {
            const isSelected = selectedPredefinedAvatar === av.filename;
            return `
                <div class="predefined-avatar-item ${isSelected ? 'selected' : ''}" data-filename="${av.filename}" data-url="${av.url}" title="בחר אווטאר">
                    <img src="${av.url}" alt="${av.filename}">
                    <span class="avatar-check-badge"><i class="fas fa-check"></i></span>
                </div>
            `;
        }).join('');

        grid.querySelectorAll('.predefined-avatar-item').forEach(item => {
            item.addEventListener('click', () => {
                const filename = item.dataset.filename;
                const url = item.dataset.url;
                selectedPredefinedAvatar = filename;
                selectedFile = null;
                document.getElementById('memberAvatar').value = '';
                document.getElementById('avatarPreview').src = url;

                grid.querySelectorAll('.predefined-avatar-item').forEach(el => el.classList.remove('selected'));
                item.classList.add('selected');
            });
        });
    }

    // Close modals on outside click
    window.addEventListener('click', (e) => {
        if (e.target === teamModal) closeModal(teamModal);
        if (e.target === memberModal) closeModal(memberModal);
        if (e.target === specialDayModal) closeSpecialDayModal();
    });

    // Functions
    async function loadTeams() {
        try {
            const response = await fetch('/api/teams');
            teams = await response.json();
            renderTeams();
        } catch (error) {
            showToast('שגיאה בטעינת צוותים', 'error');
            console.error(error);
        }
    }

    function renderTeams() {
        if (teams.length === 0) {
            teamsContainer.innerHTML = `
                <div class="empty-state">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                        <circle cx="9" cy="7" r="4"></circle>
                        <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                        <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                    </svg>
                    <h3>אין צוותים במערכת</h3>
                    <p>לחץ על "הוסף צוות חדש" כדי להתחיל</p>
                </div>
            `;
            return;
        }

        teamsContainer.innerHTML = teams.map(team => `
            <div class="team-card" data-team-id="${team.id}">
                <div class="team-card-header">
                    <div>
                        <span class="team-name">${team.name_he}</span>
                        <span class="team-name-en">(${team.name_en})</span>
                    </div>
                    <div class="team-actions">
                        <button class="btn-icon-small edit-team" data-team-id="${team.id}" title="ערוך צוות">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                            </svg>
                        </button>
                        <button class="btn-icon-small delete delete-team" data-team-id="${team.id}" title="מחק צוות">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3 6 5 6 21 6"></polyline>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                            </svg>
                        </button>
                    </div>
                </div>
                <div class="members-list">
                    <div class="members-list-header">
                        <span class="members-list-title">חברי צוות (${team.members.length})</span>
                        <button class="btn btn-small btn-primary add-member" data-team-id="${team.id}">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                            </svg>
                            הוסף חבר
                        </button>
                    </div>
                    ${team.members.length === 0 ? '<p style="color: #9ca3af; font-size: 0.875rem;">אין חברי צוות</p>' : ''}
                    ${team.members.map(member => {
                        const otherTeams = (member.teams || []).filter(t => t.id !== team.id);
                        const otherTeamsHtml = otherTeams.length > 0 ? `
                            <div class="member-other-teams">
                                ${otherTeams.map(t => `<span class="team-badge-pill" title="משויך גם לצוות ${t.name_he}">${t.name_he}</span>`).join('')}
                            </div>
                        ` : '';
                        return `
                        <div class="member-item">
                            <div class="member-info">
                            <img src="/uploads/avatars/${member.avatar_path}" class="member-avatar" alt="${member.name_he}"
                                 onerror="this.src='/static/images/default.png'">
                                <div class="member-names">
                                    <span class="member-name-he">${member.name_he}</span>
                                    <span class="member-name-en">${member.name_en}</span>
                                    ${otherTeamsHtml}
                                </div>
                            </div>
                            <div class="member-actions">
                                <button class="btn-icon-small edit-member" data-team-id="${team.id}" data-member-id="${member.id}" title="ערוך חבר צוות ושיוך לצוותים">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                                    </svg>
                                </button>
                                <button class="btn-icon-small delete delete-member" data-team-id="${team.id}" data-member-id="${member.id}" title="${otherTeams.length > 0 ? 'הסר מצוות זה' : 'מחק חבר צוות'}">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <polyline points="3 6 5 6 21 6"></polyline>
                                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                    </svg>
                                </button>
                            </div>
                        </div>
                    `;}).join('')}
                </div>
            </div>
        `).join('');

        // Attach event listeners to dynamically created elements
        attachEventListeners();
    }

    function attachEventListeners() {
        // Edit team buttons
        document.querySelectorAll('.edit-team').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const teamId = parseInt(btn.dataset.teamId);
                openTeamModal(teamId);
            });
        });

        // Delete team buttons
        document.querySelectorAll('.delete-team').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const teamId = parseInt(btn.dataset.teamId);
                deleteTeam(teamId);
            });
        });

        // Add member buttons
        document.querySelectorAll('.add-member').forEach(btn => {
            btn.addEventListener('click', () => {
                const teamId = parseInt(btn.dataset.teamId);
                openMemberModal(teamId);
            });
        });

        // Edit member buttons
        document.querySelectorAll('.edit-member').forEach(btn => {
            btn.addEventListener('click', () => {
                const teamId = parseInt(btn.dataset.teamId);
                const memberId = parseInt(btn.dataset.memberId);
                openMemberModal(teamId, memberId);
            });
        });

        // Delete member buttons
        document.querySelectorAll('.delete-member').forEach(btn => {
            btn.addEventListener('click', () => {
                const teamId = parseInt(btn.dataset.teamId);
                const memberId = parseInt(btn.dataset.memberId);
                deleteMember(teamId, memberId);
            });
        });
    }

    function openTeamModal(teamId = null) {
        currentTeam = teamId ? teams.find(t => t.id === teamId) : null;

        document.getElementById('teamModalTitle').textContent = currentTeam ? 'ערוך צוות' : 'הוסף צוות חדש';
        document.getElementById('teamNameEn').value = currentTeam ? currentTeam.name_en : '';
        document.getElementById('teamNameHe').value = currentTeam ? currentTeam.name_he : '';

        teamModal.style.display = 'block';
    }

    function openMemberModal(teamId = null, memberId = null) {
        let member = null;
        if (memberId) {
            for (const t of teams) {
                const found = (t.members || []).find(m => m.id === memberId);
                if (found) {
                    member = found;
                    break;
                }
            }
        }
        currentTeam = teamId ? teams.find(t => t.id === teamId) : null;
        currentMember = member;
        selectedFile = null;
        selectedPredefinedAvatar = null;

        document.getElementById('memberModalTitle').textContent = currentMember ? 'ערוך חבר צוות' : 'הוסף חבר צוות';
        document.getElementById('memberNameEn').value = currentMember ? currentMember.name_en : '';
        document.getElementById('memberNameHe').value = currentMember ? currentMember.name_he : '';

        if (currentMember && currentMember.avatar_path && currentMember.avatar_path.startsWith('avatar_')) {
            selectedPredefinedAvatar = currentMember.avatar_path;
        }

        const avatarPath = currentMember ? `/uploads/avatars/${currentMember.avatar_path}` : '/static/images/default.png';
        document.getElementById('avatarPreview').src = avatarPath;
        document.getElementById('memberAvatar').value = '';

        renderPredefinedAvatars();

        // Populate team checkboxes
        const memberTeamsContainer = document.getElementById('memberTeamsContainer');
        if (memberTeamsContainer) {
            const memberTeamIds = new Set();
            if (currentMember) {
                if (Array.isArray(currentMember.team_ids)) {
                    currentMember.team_ids.forEach(id => memberTeamIds.add(id));
                } else if (Array.isArray(currentMember.teams)) {
                    currentMember.teams.forEach(t => memberTeamIds.add(t.id));
                } else if (currentMember.team_id) {
                    memberTeamIds.add(currentMember.team_id);
                }
            } else if (teamId) {
                memberTeamIds.add(teamId);
            } else if (teams.length === 1) {
                memberTeamIds.add(teams[0].id);
            }

            memberTeamsContainer.innerHTML = teams.map(t => {
                const isChecked = memberTeamIds.has(t.id);
                return `
                    <label class="team-checkbox-card ${isChecked ? 'checked' : ''}">
                        <input type="checkbox" name="memberTeams" value="${t.id}" ${isChecked ? 'checked' : ''}>
                        <span class="team-checkbox-label" title="${t.name_he}">${t.name_he} <span class="team-checkbox-en">(${t.name_en})</span></span>
                    </label>
                `;
            }).join('');

            memberTeamsContainer.querySelectorAll('input[name="memberTeams"]').forEach(input => {
                input.addEventListener('change', (e) => {
                    const card = e.target.closest('.team-checkbox-card');
                    if (card) {
                        if (e.target.checked) card.classList.add('checked');
                        else card.classList.remove('checked');
                    }
                });
            });
        }

        memberModal.style.display = 'block';
    }

    function closeModal(modal) {
        modal.style.display = 'none';
        currentTeam = null;
        currentMember = null;
        selectedFile = null;
    }

    // ==========================================
    // SPECIAL DAYS MANAGEMENT
    // ==========================================
    let specialDayPicker = null;
    if (specialDayDateInput && typeof flatpickr !== 'undefined') {
        const fpConfig = {
            dateFormat: 'd/m/Y',
            allowInput: false
        };
        if (flatpickr.l10ns && flatpickr.l10ns.he) {
            fpConfig.locale = flatpickr.l10ns.he;
        }
        specialDayPicker = flatpickr(specialDayDateInput, fpConfig);
    }

    // Color preset listeners
    document.querySelectorAll('#specialDayColorPresets .color-preset-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const color = btn.dataset.color;
            if (specialDayColorPicker) specialDayColorPicker.value = color;
            if (specialDayColorInput) specialDayColorInput.value = color;
            document.querySelectorAll('#specialDayColorPresets .color-preset-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });

    if (specialDayColorPicker) {
        specialDayColorPicker.addEventListener('input', (e) => {
            const val = e.target.value.toUpperCase();
            if (specialDayColorInput) specialDayColorInput.value = val;
            updatePresetActiveColor(val);
        });
    }

    if (specialDayColorInput) {
        specialDayColorInput.addEventListener('input', (e) => {
            let val = e.target.value.trim();
            if (!val.startsWith('#') && val.length > 0) val = '#' + val;
            if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
                if (specialDayColorPicker) specialDayColorPicker.value = val;
                updatePresetActiveColor(val);
            }
        });
    }

    function updatePresetActiveColor(hex) {
        if (!hex) return;
        document.querySelectorAll('#specialDayColorPresets .color-preset-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.color.toUpperCase() === hex.toUpperCase());
        });
    }

    const HEBREW_DAYS_NAMES = ['א\'', 'ב\'', 'ג\'', 'ד\'', 'ה\'', 'ו\'', 'ש\''];
    const SPECIAL_DAY_TYPE_LABELS = {
        'holiday': 'חג / שבתון',
        'company_event': 'אירוע חברה',
        'other': 'מועד מיוחד'
    };

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function formatSpecialDayDate(dateStr) {
        if (!dateStr) return '';
        const parts = dateStr.slice(0, 10).split('-');
        if (parts.length !== 3) return dateStr;
        const y = parseInt(parts[0], 10);
        const m = parseInt(parts[1], 10) - 1;
        const d = parseInt(parts[2], 10);
        const dt = new Date(y, m, d);
        const dayLetter = HEBREW_DAYS_NAMES[dt.getDay()] || '';
        return `יום ${dayLetter}, ${parts[2]}/${parts[1]}/${parts[0]}`;
    }

    function parseDateToISO(dmyStr) {
        if (!dmyStr) return '';
        if (dmyStr.includes('-')) return dmyStr.slice(0, 10);
        const parts = dmyStr.split('/');
        if (parts.length === 3) {
            return `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
        }
        return dmyStr;
    }

    function formatISOToDMY(isoStr) {
        if (!isoStr) return '';
        const clean = isoStr.slice(0, 10);
        const parts = clean.split('-');
        if (parts.length === 3) {
            return `${parts[2]}/${parts[1]}/${parts[0]}`;
        }
        return isoStr;
    }

    async function loadSpecialDays() {
        try {
            const res = await fetch('/api/special-days');
            specialDays = await res.json();
            renderSpecialDays();
        } catch (err) {
            console.error('Failed to load special days:', err);
            showToast('שגיאה בטעינת ימים מיוחדים', 'error');
        }
    }

    function renderSpecialDays() {
        if (!specialDaysContainer) return;

        if (!specialDays || specialDays.length === 0) {
            specialDaysContainer.innerHTML = `
                <div class="empty-state">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                        <line x1="16" y1="2" x2="16" y2="6"></line>
                        <line x1="8" y1="2" x2="8" y2="6"></line>
                        <line x1="3" y1="10" x2="21" y2="10"></line>
                    </svg>
                    <h3>אין ימים מיוחדים או חגים מוגדרים במערכת</h3>
                    <p>לחץ על "הוסף יום מיוחד" כדי להגדיר ימי חג, שבתון או אירועי חברה שיוצגו בתרשים הגאנט.</p>
                </div>
            `;
            return;
        }

        const sorted = [...specialDays].sort((a, b) => (a.date || '').localeCompare(b.date || ''));

        specialDaysContainer.innerHTML = `
            <div class="special-days-table-wrapper">
                <table class="special-days-table">
                    <thead>
                        <tr>
                            <th style="width: 48px;">צבע</th>
                            <th style="width: 170px;">תאריך</th>
                            <th>שם המועד / אירוע</th>
                            <th style="width: 150px;">סוג</th>
                            <th style="width: 110px; text-align: left; white-space: nowrap;">פעולות</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${sorted.map(day => {
                            const typeLabel = SPECIAL_DAY_TYPE_LABELS[day.type] || 'מועד מיוחד';
                            const color = day.color || '#E91E63';
                            const dateDisp = formatSpecialDayDate(day.date);
                            return `
                                <tr class="special-day-row" data-id="${day.id}">
                                    <td>
                                        <span class="special-day-color-dot" style="background-color: ${color};" title="${color}"></span>
                                    </td>
                                    <td>
                                        <span class="special-day-date-badge">${escapeHtml(dateDisp)}</span>
                                    </td>
                                    <td>
                                        <strong class="special-day-name">${escapeHtml(day.name)}</strong>
                                    </td>
                                    <td>
                                        <span class="special-day-type-badge ${day.type || 'other'}">${typeLabel}</span>
                                    </td>
                                    <td style="text-align: left; white-space: nowrap;">
                                        <div class="table-actions">
                                            <button type="button" class="btn-icon-small edit-special-day" data-id="${day.id}" title="ערוך מועד">
                                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                                                </svg>
                                            </button>
                                            <button type="button" class="btn-icon-small delete delete-special-day" data-id="${day.id}" data-name="${escapeHtml(day.name)}" title="מחק מועד">
                                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                    <polyline points="3 6 5 6 21 6"></polyline>
                                                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                                </svg>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        `;

        attachSpecialDaysListeners();
    }

    function attachSpecialDaysListeners() {
        if (!specialDaysContainer) return;

        specialDaysContainer.querySelectorAll('.edit-special-day').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = parseInt(btn.dataset.id, 10);
                openSpecialDayModal(id);
            });
        });

        specialDaysContainer.querySelectorAll('.delete-special-day').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = parseInt(btn.dataset.id, 10);
                const name = btn.dataset.name || '';
                deleteSpecialDay(id, name);
            });
        });
    }

    function openSpecialDayModal(dayId = null) {
        if (dayId) {
            const day = specialDays.find(d => d.id === dayId);
            if (!day) return;
            document.getElementById('specialDayModalTitle').textContent = 'ערוך יום מיוחד';
            specialDayIdInput.value = day.id;
            const cleanDate = (day.date || '').slice(0, 10);
            if (specialDayPicker) {
                specialDayPicker.setDate(cleanDate, true);
            } else {
                specialDayDateInput.value = formatISOToDMY(cleanDate);
            }
            specialDayNameInput.value = day.name || '';
            specialDayTypeSelect.value = day.type || 'holiday';
            const col = day.color || '#E91E63';
            specialDayColorPicker.value = col;
            specialDayColorInput.value = col;
            updatePresetActiveColor(col);
        } else {
            document.getElementById('specialDayModalTitle').textContent = 'הוסף יום מיוחד';
            specialDayIdInput.value = '';
            if (specialDayPicker) {
                specialDayPicker.clear();
            } else {
                specialDayDateInput.value = '';
            }
            specialDayNameInput.value = '';
            specialDayTypeSelect.value = 'holiday';
            specialDayColorPicker.value = '#E91E63';
            specialDayColorInput.value = '#E91E63';
            updatePresetActiveColor('#E91E63');
        }
        specialDayModal.style.display = 'block';
    }

    function closeSpecialDayModal() {
        if (specialDayModal) {
            specialDayModal.style.display = 'none';
        }
    }

    async function saveSpecialDay() {
        const rawDate = specialDayDateInput ? specialDayDateInput.value.trim() : '';
        const name = specialDayNameInput ? specialDayNameInput.value.trim() : '';
        const type = specialDayTypeSelect ? specialDayTypeSelect.value : 'holiday';
        const color = specialDayColorInput ? specialDayColorInput.value.trim() : (specialDayColorPicker ? specialDayColorPicker.value : '#E91E63');
        const dayId = (specialDayIdInput && specialDayIdInput.value) ? parseInt(specialDayIdInput.value, 10) : null;

        if (!rawDate) {
            showToast('נא לבחור תאריך', 'error');
            return;
        }
        if (!name) {
            showToast('נא להזין שם עבור המועד', 'error');
            return;
        }

        const isoDate = parseDateToISO(rawDate);
        const payload = {
            date: isoDate,
            name: name,
            type: type,
            color: color
        };

        try {
            const url = dayId ? `/api/special-days/${dayId}` : '/api/special-days';
            const method = dayId ? 'PUT' : 'POST';
            const res = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (res.ok && data.success) {
                showToast(dayId ? 'המועד עודכן בהצלחה' : 'המועד נוסף בהצלחה', 'success');
                closeSpecialDayModal();
                await loadSpecialDays();
                broadcastAdminChange();
            } else {
                showToast(data.error || 'שגיאה בשמירת המועד', 'error');
            }
        } catch (err) {
            console.error(err);
            showToast('שגיאה בשמירת המועד', 'error');
        }
    }

    async function deleteSpecialDay(id, name) {
        if (!confirm(`האם אתה בטוח שברצונך למחוק את המועד "${name}"?`)) {
            return;
        }

        try {
            const res = await fetch(`/api/special-days/${id}`, { method: 'DELETE' });
            const data = await res.json();
            if (res.ok && data.success) {
                showToast('המועד נמחק בהצלחה', 'success');
                await loadSpecialDays();
                broadcastAdminChange();
            } else {
                showToast(data.error || 'שגיאה במחיקת המועד', 'error');
            }
        } catch (err) {
            console.error(err);
            showToast('שגיאה במחיקת המועד', 'error');
        }
    }

    async function saveTeam() {
        const nameEn = document.getElementById('teamNameEn').value.trim().toLowerCase();
        const nameHe = document.getElementById('teamNameHe').value.trim();

        if (!nameEn || !nameHe) {
            showToast('נא למלא את כל השדות', 'error');
            return;
        }

        try {
            const url = currentTeam ? `/api/teams/${currentTeam.id}` : '/api/teams';
            const method = currentTeam ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name_en: nameEn, name_he: nameHe })
            });

            const data = await response.json();

            if (data.success) {
                showToast(currentTeam ? 'הצוות עודכן בהצלחה' : 'הצוות נוצר בהצלחה', 'success');
                closeModal(teamModal);
                await loadTeams();
                broadcastAdminChange();
            } else {
                showToast(data.error || 'שגיאה בשמירת הצוות', 'error');
            }
        } catch (error) {
            showToast('שגיאה בשמירת הצוות', 'error');
            console.error(error);
        }
    }

    async function deleteTeam(teamId) {
        if (!confirm('האם אתה בטוח שברצונך למחוק צוות זה? פעולה זו תמחק גם את כל חברי הצוות.')) {
            return;
        }

        try {
            const response = await fetch(`/api/teams/${teamId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                showToast('הצוות נמחק בהצלחה', 'success');
                await loadTeams();
                broadcastAdminChange();
            } else {
                showToast('שגיאה במחיקת הצוות', 'error');
            }
        } catch (error) {
            showToast('שגיאה במחיקת הצוות', 'error');
            console.error(error);
        }
    }

    async function saveMember() {
        const nameEn = document.getElementById('memberNameEn').value.trim().toLowerCase();
        const nameHe = document.getElementById('memberNameHe').value.trim();

        if (!nameEn || !nameHe) {
            showToast('נא למלא את כל השדות', 'error');
            return;
        }

        const checkedBoxes = Array.from(document.querySelectorAll('input[name="memberTeams"]:checked'));
        const selectedTeamIds = checkedBoxes.map(cb => parseInt(cb.value)).filter(id => !isNaN(id));

        if (selectedTeamIds.length === 0) {
            showToast('יש לבחור לפחות צוות אחד', 'error');
            return;
        }

        try {
            const url = currentMember
                ? `/api/members/${currentMember.id}`
                : `/api/members`;
            const method = currentMember ? 'PUT' : 'POST';

            const payload = { 
                name_en: nameEn, 
                name_he: nameHe,
                team_ids: selectedTeamIds
            };
            if (selectedPredefinedAvatar && !selectedFile) {
                payload.avatar_path = selectedPredefinedAvatar;
            }

            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (data.success) {
                const memberId = currentMember ? currentMember.id : data.member.id;

                // If there's a file selected, upload it
                if (selectedFile) {
                    await uploadAvatar(memberId, selectedFile);
                }

                showToast(currentMember ? 'חבר הצוות עודכן בהצלחה' : 'חבר הצוות נוסף בהצלחה', 'success');
                closeModal(memberModal);
                await loadTeams();
                broadcastAdminChange();
            } else {
                showToast(data.error || 'שגיאה בשמירת חבר הצוות', 'error');
            }
        } catch (error) {
            showToast('שגיאה בשמירת חבר הצוות', 'error');
            console.error(error);
        }
    }

    async function uploadAvatar(memberId, file) {
        const formData = new FormData();
        formData.append('avatar', file);

        try {
            const response = await fetch(`/api/members/${memberId}/avatar`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!data.success) {
                showToast('שגיאה בהעלאת התמונה', 'error');
            }
        } catch (error) {
            showToast('שגיאה בהעלאת התמונה', 'error');
            console.error(error);
        }
    }

    async function deleteMember(teamId, memberId) {
        let member = null;
        const team = teams.find(t => t.id === teamId);
        if (team) {
            member = (team.members || []).find(m => m.id === memberId);
        }

        const isMultiTeam = member && member.teams && member.teams.length > 1;
        const confirmMsg = isMultiTeam
            ? `האם להסיר את "${member.name_he}" מצוות "${team.name_he}"? (חבר הצוות משויך לצוותים נוספים ויישאר בהם)`
            : `האם אתה בטוח שברצונך למחוק את חבר הצוות "${member ? member.name_he : ''}"?`;

        if (!confirm(confirmMsg)) {
            return;
        }

        try {
            const response = await fetch(`/api/teams/${teamId}/members/${memberId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                showToast(isMultiTeam ? 'חבר הצוות הוסר מהצוות בהצלחה' : 'חבר הצוות נמחק בהצלחה', 'success');
                await loadTeams();
                broadcastAdminChange();
            } else {
                showToast('שגיאה במחיקת חבר הצוות', 'error');
            }
        } catch (error) {
            showToast('שגיאה במחיקת חבר הצוות', 'error');
            console.error(error);
        }
    }

    function showToast(message, type = 'success') {
        toast.textContent = message;
        toast.className = `toast show ${type}`;

        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    // --- General System & Environment Settings ---
    let systemSettingsLoaded = false;

    async function loadSystemSettings() {
        try {
            const res = await fetch('/api/system/settings?t=' + Date.now());
            const data = await res.json();
            if (!data.success) {
                showToast(data.error || 'שגיאה בטעינת הגדרות המערכת', 'error');
                return;
            }

            const { settings, ai_status, system_info } = data;

            // 1. AI Provider Radios
            const currentProvider = settings.ai_provider || ai_status.provider || 'cloudflare';
            const radioLocal = document.getElementById('radioProviderLocal');
            const radioCloudflare = document.getElementById('radioProviderCloudflare');

            if (currentProvider === 'local_openai') {
                if (radioLocal) radioLocal.checked = true;
                updateProviderCardSelection('local_openai');
            } else {
                if (radioCloudflare) radioCloudflare.checked = true;
                updateProviderCardSelection('cloudflare');
            }

            // 2. Populate Local Fields
            const inputOpenAiBaseUrl = document.getElementById('inputOpenAiBaseUrl');
            const inputOpenAiModel = document.getElementById('inputOpenAiModel');
            const inputOpenAiApiKey = document.getElementById('inputOpenAiApiKey');
            if (inputOpenAiBaseUrl) inputOpenAiBaseUrl.value = settings.openai_base_url || '';
            if (inputOpenAiModel) inputOpenAiModel.value = settings.openai_model || 'llama3.3';
            if (inputOpenAiApiKey) {
                inputOpenAiApiKey.value = settings.has_openai_key ? (settings.openai_api_key_masked || '••••••••••••••••') : '';
            }

            // 3. Populate Cloudflare Fields
            const inputCfAccountId = document.getElementById('inputCfAccountId');
            const inputCfModel = document.getElementById('inputCfModel');
            const inputCfApiToken = document.getElementById('inputCfApiToken');
            const hintCfTokenStatus = document.getElementById('hintCfTokenStatus');
            if (inputCfAccountId) inputCfAccountId.value = settings.cloudflare_account_id || '';
            if (inputCfModel) inputCfModel.value = settings.cloudflare_model || '@cf/meta/llama-3.1-8b-instruct';
            if (inputCfApiToken) {
                if (settings.has_cloudflare_token) {
                    inputCfApiToken.value = settings.cloudflare_api_token_masked || '••••••••••••••••';
                    if (hintCfTokenStatus) hintCfTokenStatus.textContent = 'מפתח API קיים ושמור במערכת. הזן מפתח חדש רק במידה שברצונך להחליפו.';
                } else {
                    inputCfApiToken.value = '';
                    if (hintCfTokenStatus) hintCfTokenStatus.textContent = 'לא הוגדר מפתח API עבור Cloudflare. אנא הזן מפתח.';
                }
            }

            // 4. Update AI Status Badges
            updateAiBadges(ai_status);

            // 5. Populate System Metrics
            if (system_info && system_info.metrics) {
                const m = system_info.metrics;
                const statTasksCount = document.getElementById('statTasksCount');
                const statTasksSub = document.getElementById('statTasksSub');
                const statProjectsCount = document.getElementById('statProjectsCount');
                const statProjectsSub = document.getElementById('statProjectsSub');
                const statTeamsCount = document.getElementById('statTeamsCount');
                const statMembersCount = document.getElementById('statMembersCount');
                const statDbSize = document.getElementById('statDbSize');

                if (statTasksCount) statTasksCount.textContent = m.total_tasks || 0;
                if (statTasksSub) statTasksSub.textContent = `${m.done_tasks || 0} הושלמו · ${m.inprogress_tasks || 0} בתהליך`;
                if (statProjectsCount) statProjectsCount.textContent = m.total_projects || 0;
                if (statProjectsSub) statProjectsSub.textContent = `${m.active_projects || 0} פעילים · ${m.archived_projects || 0} בארכיון`;
                if (statTeamsCount) statTeamsCount.textContent = m.total_teams || 0;
                if (statMembersCount) statMembersCount.textContent = `${m.total_members || 0} חברי צוות`;
                if (statDbSize) statDbSize.textContent = system_info.db_size || '--';
            }

            // 6. Storage & Runtime info
            if (system_info) {
                const infoDbPath = document.getElementById('infoDbPath');
                const infoUploadsSummary = document.getElementById('infoUploadsSummary');
                const infoPlatform = document.getElementById('infoPlatform');
                const infoPythonVersion = document.getElementById('infoPythonVersion');

                if (infoDbPath) infoDbPath.textContent = system_info.db_path || 'tasks.db';
                if (infoUploadsSummary && system_info.uploads) {
                    infoUploadsSummary.textContent = `${system_info.uploads.count || 0} תמונות (${system_info.uploads.size || '0 KB'})`;
                }
                if (infoPlatform && system_info.runtime) {
                    infoPlatform.textContent = `${system_info.runtime.platform || 'Unknown'} (Debug: ${system_info.runtime.debug ? 'פעיל' : 'כבוי'})`;
                }
                if (infoPythonVersion && system_info.runtime) {
                    infoPythonVersion.textContent = system_info.runtime.python_version || '--';
                }
            }

            systemSettingsLoaded = true;
        } catch (e) {
            console.error('Error loading system settings:', e);
            showToast('שגיאה בתקשורת עם השרת בעת טעינת הגדרות', 'error');
        }
    }

    function updateAiBadges(ai_status) {
        const badgeStatus = document.getElementById('badgeAiStatus');
        const badgeProvider = document.getElementById('badgeAiProvider');
        const badgeAirgap = document.getElementById('badgeAirgap');

        if (!badgeStatus) return;

        if (ai_status && ai_status.configured) {
            badgeStatus.textContent = '● פעיל ומחובר';
            badgeStatus.className = 'status-pill status-pill-success';
        } else {
            badgeStatus.textContent = '● אינו מוגדר';
            badgeStatus.className = 'status-pill status-pill-warning';
        }

        if (badgeProvider) {
            badgeProvider.textContent = (ai_status && ai_status.name) ? ai_status.name : ((ai_status && ai_status.provider === 'local_openai') ? 'Local OpenAI Gateway' : 'Cloudflare Workers AI');
        }

        if (badgeAirgap) {
            if (ai_status && ai_status.is_airgapped) {
                badgeAirgap.textContent = '🛡️ שער מקומי מבודד (Airgapped)';
                badgeAirgap.className = 'status-pill status-pill-airgap';
            } else {
                badgeAirgap.textContent = '☁️ ענן (Cloudflare)';
                badgeAirgap.className = 'status-pill status-pill-cloud';
            }
        }
    }

    function updateProviderCardSelection(provider) {
        const cardLocal = document.getElementById('cardProviderLocal');
        const cardCloudflare = document.getElementById('cardProviderCloudflare');
        const boxLocal = document.getElementById('boxLocalAiFields');
        const boxCloudflare = document.getElementById('boxCloudflareFields');

        if (provider === 'local_openai') {
            if (cardLocal) cardLocal.classList.add('selected');
            if (cardCloudflare) cardCloudflare.classList.remove('selected');
            if (boxLocal) boxLocal.style.display = 'block';
            if (boxCloudflare) boxCloudflare.style.display = 'none';
        } else {
            if (cardCloudflare) cardCloudflare.classList.add('selected');
            if (cardLocal) cardLocal.classList.remove('selected');
            if (boxLocal) boxLocal.style.display = 'none';
            if (boxCloudflare) boxCloudflare.style.display = 'block';
        }
    }

    // Provider radio switch event listeners
    document.querySelectorAll('input[name="ai_provider_radio"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            updateProviderCardSelection(e.target.value);
        });
    });

    // Password visibility toggle buttons
    document.querySelectorAll('.btn-toggle-visibility').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.dataset.target;
            const input = document.getElementById(targetId);
            if (!input) return;
            if (input.type === 'password') {
                input.type = 'text';
                btn.textContent = '🔒';
            } else {
                input.type = 'password';
                btn.textContent = '👁️';
            }
        });
    });

    // Save System Settings
    const btnSaveSystemSettings = document.getElementById('btnSaveSystemSettings');
    if (btnSaveSystemSettings) {
        btnSaveSystemSettings.addEventListener('click', async () => {
            const selectedRadio = document.querySelector('input[name="ai_provider_radio"]:checked');
            const provider = selectedRadio ? selectedRadio.value : 'cloudflare';

            const payload = {
                ai_provider: provider,
                openai_base_url: document.getElementById('inputOpenAiBaseUrl')?.value.trim() || '',
                openai_model: document.getElementById('inputOpenAiModel')?.value.trim() || 'llama3.3',
                openai_api_key: document.getElementById('inputOpenAiApiKey')?.value.trim() || '',
                cloudflare_account_id: document.getElementById('inputCfAccountId')?.value.trim() || '',
                cloudflare_model: document.getElementById('inputCfModel')?.value.trim() || '@cf/meta/llama-3.1-8b-instruct',
                cloudflare_api_token: document.getElementById('inputCfApiToken')?.value.trim() || ''
            };

            btnSaveSystemSettings.disabled = true;
            btnSaveSystemSettings.textContent = 'שומר...';

            try {
                const res = await fetch('/api/system/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await res.json();
                if (result.success) {
                    showToast('ההגדרות נשמרו בהצלחה בקובץ .env ומנוע ה-AI עודכן!', 'success');
                    if (result.ai_status) {
                        updateAiBadges(result.ai_status);
                    }
                    await loadSystemSettings();
                } else {
                    showToast(result.error || 'שגיאה בשמירת ההגדרות', 'error');
                }
            } catch (err) {
                console.error(err);
                showToast('שגיאת תקשורת עם השרת', 'error');
            } finally {
                btnSaveSystemSettings.disabled = false;
                btnSaveSystemSettings.innerHTML = `<img src="/static/icons/save.svg" width="18" height="18" style="vertical-align:middle; filter: brightness(0) invert(1);"> שמור הגדרות`;
            }
        });
    }

    // Test AI Connection
    const btnTestAiConnection = document.getElementById('btnTestAiConnection');
    const testAiSpinner = document.getElementById('testAiSpinner');
    const testAiBtnText = document.getElementById('testAiBtnText');
    const aiTestResultBox = document.getElementById('aiTestResultBox');
    const testResultTitle = document.getElementById('testResultTitle');
    const testResultDetails = document.getElementById('testResultDetails');
    const testResultIcon = document.getElementById('testResultIcon');

    if (btnTestAiConnection) {
        btnTestAiConnection.addEventListener('click', async () => {
            const selectedRadio = document.querySelector('input[name="ai_provider_radio"]:checked');
            const provider = selectedRadio ? selectedRadio.value : 'cloudflare';

            const payload = {
                ai_provider: provider,
                openai_base_url: document.getElementById('inputOpenAiBaseUrl')?.value.trim() || '',
                openai_model: document.getElementById('inputOpenAiModel')?.value.trim() || '',
                openai_api_key: document.getElementById('inputOpenAiApiKey')?.value.trim() || '',
                cloudflare_account_id: document.getElementById('inputCfAccountId')?.value.trim() || '',
                cloudflare_model: document.getElementById('inputCfModel')?.value.trim() || '',
                cloudflare_api_token: document.getElementById('inputCfApiToken')?.value.trim() || ''
            };

            btnTestAiConnection.disabled = true;
            if (testAiSpinner) testAiSpinner.style.display = 'inline-block';
            if (testAiBtnText) testAiBtnText.textContent = 'בודק חיבור...';
            if (aiTestResultBox) aiTestResultBox.style.display = 'none';

            try {
                const res = await fetch('/api/system/test-ai', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await res.json();

                if (aiTestResultBox) {
                    aiTestResultBox.style.display = 'flex';
                    if (result.success) {
                        aiTestResultBox.className = 'test-result-box success';
                        if (testResultIcon) testResultIcon.textContent = '✓';
                        if (testResultTitle) testResultTitle.textContent = `חיבור תקין בהצלחה! (זמן תגובה: ${result.latency_ms}ms)`;
                        if (testResultDetails) {
                            const provText = result.is_airgapped ? 'שער מקומי מבודד (Airgapped)' : 'Cloudflare Workers AI';
                            testResultDetails.innerHTML = `<strong>ספק:</strong> ${provText} | <strong>מודל:</strong> <code>${result.model}</code> | <strong>תשובה:</strong> <em>${result.reply || 'OK'}</em>`;
                        }
                    } else {
                        aiTestResultBox.className = 'test-result-box error';
                        if (testResultIcon) testResultIcon.textContent = '✕';
                        if (testResultTitle) testResultTitle.textContent = `בדיקת החיבור נכשלה! (${result.latency_ms || 0}ms)`;
                        if (testResultDetails) testResultDetails.textContent = result.error || 'שגיאה לא מזוהה בעת יצירת קשר עם המודל.';
                    }
                }
            } catch (err) {
                console.error(err);
                if (aiTestResultBox) {
                    aiTestResultBox.style.display = 'flex';
                    aiTestResultBox.className = 'test-result-box error';
                    if (testResultIcon) testResultIcon.textContent = '✕';
                    if (testResultTitle) testResultTitle.textContent = 'שגיאת רשת בבדיקת החיבור';
                    if (testResultDetails) testResultDetails.textContent = err.message || 'לא ניתן לתקשר עם שרת האפליקציה.';
                }
            } finally {
                btnTestAiConnection.disabled = false;
                if (testAiSpinner) testAiSpinner.style.display = 'none';
                if (testAiBtnText) testAiBtnText.textContent = 'בדיקת חיבור מודל';
            }
        });
    }

    const btnDismissTestResult = document.getElementById('btnDismissTestResult');
    if (btnDismissTestResult && aiTestResultBox) {
        btnDismissTestResult.addEventListener('click', () => {
            aiTestResultBox.style.display = 'none';
        });
    }

    // Refresh System button
    const btnRefreshSystem = document.getElementById('btnRefreshSystem');
    if (btnRefreshSystem) {
        btnRefreshSystem.addEventListener('click', async () => {
            btnRefreshSystem.disabled = true;
            await loadSystemSettings();
            showToast('נתוני המערכת רועננו בהצלחה', 'info');
            btnRefreshSystem.disabled = false;
        });
    }

    // Check DB Integrity
    const btnCheckDbIntegrity = document.getElementById('btnCheckDbIntegrity');
    const dbIntegrityResult = document.getElementById('dbIntegrityResult');
    if (btnCheckDbIntegrity) {
        btnCheckDbIntegrity.addEventListener('click', async () => {
            btnCheckDbIntegrity.disabled = true;
            btnCheckDbIntegrity.textContent = 'בודק...';
            if (dbIntegrityResult) dbIntegrityResult.textContent = '';
            try {
                const res = await fetch('/api/system/check-db', { method: 'POST' });
                const data = await res.json();
                if (dbIntegrityResult) {
                    if (data.success && data.integrity === 'ok') {
                        dbIntegrityResult.textContent = '✓ מסד הנתונים תקין לחלוטין (ok)';
                        dbIntegrityResult.style.color = '#10b981';
                    } else {
                        dbIntegrityResult.textContent = `סטטוס: ${data.integrity || data.error}`;
                        dbIntegrityResult.style.color = '#ef4444';
                    }
                }
            } catch (e) {
                if (dbIntegrityResult) {
                    dbIntegrityResult.textContent = 'שגיאה בבדיקה';
                    dbIntegrityResult.style.color = '#ef4444';
                }
            } finally {
                btnCheckDbIntegrity.disabled = false;
                btnCheckDbIntegrity.textContent = 'בדוק שלמות מסד נתונים (Integrity Check)';
            }
        });
    }

    const navTasks = document.getElementById('navTasksLink');
    if (navTasks) {
        navTasks.addEventListener('click', (e) => {
            const storedTeam = localStorage.getItem('activeTeamFilter');
            if (storedTeam === 'archive') {
                e.preventDefault();
                window.location.href = '/?mode=archive';
            } else if (storedTeam) {
                e.preventDefault();
                window.location.href = `/?team=${encodeURIComponent(storedTeam)}`;
            }
        });
    }

    // --- MCP Server Management & Playground ---
    let mcpInfoData = null;
    let activeMcpConfigTab = 'stdio';
    let activeMcpCategory = 'all';

    const defaultMcpToolExamples = {
        list_tasks: { status: "not-done", limit: 10 },
        get_task: { id: 1 },
        create_task: { project: "שדרוג ליבה", task: "בדיקת אוטומציית MCP", priority: "high", status: "status-inprogress", members: ["elad"] },
        update_task: { id: 1, status: "status-inprogress", priority: "high" },
        update_task_schedule: { id: 1, shift_days: 2, estimated_hours: 4 },
        archive_task: { id: 1 },
        unarchive_task: { id: 1 },
        delete_task: { id: 999 },
        bulk_update_tasks: { task_ids: [1, 2], status: "status-inprogress" },
        search_tasks: { query: "שדרוג", include_archived: false },
        list_projects: { mode: "active" },
        get_project: { name: "שדרוג ליבה" },
        create_project: { name: "פרויקט AI חדש", teams: ["devops"] },
        update_project: { name: "פרויקט AI חדש", add_teams: ["devops"] },
        archive_project: { name: "פרויקט AI חדש", is_archived: true },
        delete_project: { name: "פרויקט AI חדש" },
        list_teams: {},
        create_team: { name_en: "secops", name_he: "צוות SecOps" },
        update_team: { name: "secops", new_name_he: "צוות אבטחה ו-SecOps" },
        delete_team: { name: "secops" },
        list_members: {},
        create_member: { name_en: "daniel", name_he: "דניאל", teams: ["devops"], avatar_path: "avatar_5.png" },
        update_member: { name: "daniel", avatar_path: "avatar_10.png" },
        delete_member: { name: "daniel" },
        list_avatars: {},
        get_calendar_week: {},
        get_calendar_month: {},
        get_member_workload: {},
        list_special_days: {},
        create_special_day: { date: "2026-11-15", name: "יום גיבוש חברה", type: "company_event", color: "#8b5cf6" },
        delete_special_day: { name: "יום גיבוש חברה" },
        get_executive_summary: {},
        get_deadlines_analysis: {},
        get_stale_and_suggestions: {},
        get_system_diagnostics: {},
        export_system_backup: { table_name: "teams" },
        restore_system_backup: { table_name: "teams", records: [] }
    };

    const categoryNamesHe = {
        tasks: 'משימות',
        projects: 'פרויקטים',
        teams: 'צוותים',
        members: 'חברי צוות',
        calendar: 'יומן ועומסים',
        analytics: 'דוחות וגיבוי'
    };

    async function loadMcpInfo() {
        try {
            const res = await fetch('/api/mcp/info?t=' + Date.now());
            const data = await res.json();
            if (!data.success) {
                showToast(data.error || 'שגיאה בטעינת נתוני שרת MCP', 'error');
                return;
            }
            mcpInfoData = data;

            const { server, counts, tools } = data;
            const badgeTools = document.getElementById('badgeMcpToolsCount');
            const badgeRes = document.getElementById('badgeMcpResourcesCount');
            const badgePrompts = document.getElementById('badgeMcpPromptsCount');
            if (badgeTools) badgeTools.textContent = `${counts.tools} כלים (Tools)`;
            if (badgeRes) badgeRes.textContent = `${counts.resources} משאבים (Resources)`;
            if (badgePrompts) badgePrompts.textContent = `${counts.prompts} תבניות (Prompts)`;

            const httpCode = document.getElementById('mcpHttpEndpointCode');
            const sseCode = document.getElementById('mcpSseEndpointCode');
            if (httpCode) httpCode.textContent = server.http_endpoint;
            if (sseCode) sseCode.textContent = server.sse_endpoint;

            const inputMcpKey = document.getElementById('inputMcpApiKey');
            const hintMcpKey = document.getElementById('hintMcpKeyStatus');
            if (inputMcpKey) {
                inputMcpKey.value = server.has_api_key ? (server.api_key_masked || '••••••••') : '';
            }
            if (hintMcpKey) {
                hintMcpKey.innerHTML = server.has_api_key
                    ? '🔒 מפתח אבטחה פעיל. בקשות ל-<code>/mcp</code> מחייבות הזדהות.'
                    : '🔓 גישה פתוחה ברשת המקומית (ללא מפתח). ניתן להגדיר מפתח לאבטחת חיבורים מרוחקים.';
            }

            renderMcpConfigSnippet(activeMcpConfigTab);
            populateMcpPlaygroundSelect(tools);
            renderMcpToolsCatalog(tools, activeMcpCategory);
        } catch (e) {
            console.error('Error loading MCP info:', e);
            showToast('שגיאת תקשורת בטעינת נתוני MCP', 'error');
        }
    }

    function renderMcpConfigSnippet(tab) {
        activeMcpConfigTab = tab;
        const pre = document.getElementById('mcpConfigCodeBlock');
        const hint = document.getElementById('mcpConfigHint');
        if (!pre || !mcpInfoData) return;

        const scriptPath = mcpInfoData.server.script_path || '/app/mcp_server.py';
        const httpUrl = mcpInfoData.server.http_endpoint || (window.location.origin + '/mcp');
        let snippet = {};

        if (tab === 'stdio') {
            snippet = {
                mcpServers: {
                    teamtasks: {
                        command: "python",
                        args: [scriptPath]
                    }
                }
            };
            if (hint) hint.innerHTML = 'הוסף לקובץ <code>mcp_config.json</code> ב-Antigravity או <code>.cursor/mcp.json</code> ב-Cursor.';
        } else if (tab === 'claude') {
            snippet = {
                mcpServers: {
                    teamtasks: {
                        command: "python",
                        args: [scriptPath],
                        env: {
                            PYTHONIOENCODING: "utf-8"
                        }
                    }
                }
            };
            if (hint) hint.innerHTML = 'הוסף לקובץ <code>claude_desktop_config.json</code> תחת הגדרות Developer ב-Claude Desktop.';
        } else if (tab === 'http') {
            snippet = {
                mcpServers: {
                    "teamtasks-remote": {
                        url: httpUrl,
                        transport: "streamable-http"
                    }
                }
            };
            if (hint) hint.innerHTML = 'חיבור ישיר ב-HTTP (ללא צורך ב-Python מקומי) אל שרת ה-TeamTasks הפעיל.';
        } else if (tab === 'docker') {
            snippet = {
                mcpServers: {
                    teamtasks: {
                        command: "docker",
                        args: ["exec", "-i", "teamtasks-app", "python", "/app/mcp_server.py"]
                    }
                }
            };
            if (hint) hint.innerHTML = 'הרצת שרת ה-MCP בתוך קונטיינר ה-Docker הפעיל של TeamTasks.';
        }

        pre.textContent = JSON.stringify(snippet, null, 2);
    }

    document.querySelectorAll('.mcp-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.mcp-tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            renderMcpConfigSnippet(btn.dataset.configTab);
        });
    });

    const btnCopyMcpConfig = document.getElementById('btnCopyMcpConfig');
    if (btnCopyMcpConfig) {
        btnCopyMcpConfig.addEventListener('click', () => {
            const pre = document.getElementById('mcpConfigCodeBlock');
            if (pre && pre.textContent) {
                navigator.clipboard.writeText(pre.textContent);
                showToast('הגדרות ה-MCP הועתקו ללוח!', 'success');
            }
        });
    }

    document.querySelectorAll('.btn-copy-inline').forEach(btn => {
        btn.addEventListener('click', () => {
            const target = document.getElementById(btn.dataset.copyTarget);
            if (target && target.textContent) {
                navigator.clipboard.writeText(target.textContent);
                showToast('הכתובת הועתקה ללוח!', 'success');
            }
        });
    });

    function populateMcpPlaygroundSelect(tools) {
        const select = document.getElementById('mcpPlaygroundToolSelect');
        if (!select || select.options.length > 0) return;

        const grouped = {};
        tools.forEach(t => {
            const cat = t.category || 'other';
            if (!grouped[cat]) grouped[cat] = [];
            grouped[cat].push(t);
        });

        select.innerHTML = Object.entries(grouped).map(([cat, list]) => {
            const label = categoryNamesHe[cat] || cat;
            const opts = list.map(t => `<option value="${t.name}">${t.name} — ${t.title || ''}</option>`).join('');
            return `<optgroup label="${label}">${opts}</optgroup>`;
        }).join('');

        updateMcpPlaygroundSelection('get_executive_summary');
        select.value = 'get_executive_summary';

        select.addEventListener('change', () => {
            updateMcpPlaygroundSelection(select.value);
        });
    }

    function updateMcpPlaygroundSelection(toolName) {
        if (!mcpInfoData || !mcpInfoData.tools) return;
        const tool = mcpInfoData.tools.find(t => t.name === toolName);
        const descEl = document.getElementById('mcpPlaygroundToolDesc');
        const argsEl = document.getElementById('mcpPlaygroundArgs');
        if (tool && descEl) {
            descEl.textContent = `${tool.title ? tool.title + ': ' : ''}${tool.description}`;
        }
        if (argsEl) {
            const example = defaultMcpToolExamples[toolName] || {};
            argsEl.value = JSON.stringify(example, null, 2);
        }
    }

    const btnRunMcpTool = document.getElementById('btnRunMcpTool');
    if (btnRunMcpTool) {
        btnRunMcpTool.addEventListener('click', async () => {
            const select = document.getElementById('mcpPlaygroundToolSelect');
            const argsEl = document.getElementById('mcpPlaygroundArgs');
            const resultBox = document.getElementById('mcpPlaygroundResultContainer');
            const resultPre = document.getElementById('mcpPlaygroundResultPre');
            const latencyEl = document.getElementById('mcpPlaygroundLatency');

            const toolName = select ? select.value : '';
            let parsedArgs = {};
            try {
                parsedArgs = argsEl && argsEl.value.trim() ? JSON.parse(argsEl.value.trim()) : {};
            } catch (err) {
                showToast('שגיאת תחביר ב-JSON של הפרמטרים', 'error');
                return;
            }

            btnRunMcpTool.disabled = true;
            btnRunMcpTool.textContent = 'מריץ כלי...';
            if (latencyEl) latencyEl.textContent = '';

            try {
                const res = await fetch('/api/mcp/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: toolName, arguments: parsedArgs })
                });
                const data = await res.json();
                if (resultBox && resultPre) {
                    resultBox.style.display = 'block';
                    resultPre.textContent = JSON.stringify(data.result || data, null, 2);
                }
                if (latencyEl && typeof data.latency_ms !== 'undefined') {
                    latencyEl.textContent = `✓ בוצע תוך ${data.latency_ms}ms`;
                }
                if (data.success && data.result && data.result.success) {
                    if (/^(create_|update_|delete_|archive_|unarchive_|bulk_|restore_)/.test(toolName)) {
                        broadcastAdminChange();
                        loadTeams();
                    }
                }
            } catch (e) {
                showToast('שגיאה בהרצת כלי MCP', 'error');
            } finally {
                btnRunMcpTool.disabled = false;
                btnRunMcpTool.textContent = '▶ הרץ כלי MCP כעת';
            }
        });
    }

    function renderMcpToolsCatalog(tools, category = 'all') {
        const grid = document.getElementById('mcpToolsCatalogGrid');
        if (!grid || !tools) return;

        const filtered = category === 'all' ? tools : tools.filter(t => t.category === category);
        grid.innerHTML = filtered.map(t => {
            const props = (t.inputSchema && t.inputSchema.properties) ? Object.keys(t.inputSchema.properties) : [];
            const reqs = new Set((t.inputSchema && t.inputSchema.required) || []);
            const paramsHtml = props.length > 0
                ? props.map(p => `<span class="mcp-param-badge ${reqs.has(p) ? 'required' : ''}" title="${reqs.has(p) ? 'שדה חובה' : 'אופציונלי'}">${p}${reqs.has(p) ? '*' : ''}</span>`).join('')
                : '<span class="mcp-param-none">ללא פרמטרים</span>';

            return `
                <div class="mcp-tool-card">
                    <div class="mcp-tool-card-top">
                        <div>
                            <code class="mcp-tool-name" dir="ltr">${t.name}</code>
                            <div class="mcp-tool-title-he">${t.title || ''}</div>
                        </div>
                        <button type="button" class="btn btn-secondary btn-sm btn-try-mcp-tool" data-tool="${t.name}">
                            בדוק כלי
                        </button>
                    </div>
                    <p class="mcp-tool-desc" dir="ltr">${t.description}</p>
                    <div class="mcp-tool-params" dir="ltr">${paramsHtml}</div>
                </div>
            `;
        }).join('');

        grid.querySelectorAll('.btn-try-mcp-tool').forEach(btn => {
            btn.addEventListener('click', () => {
                const tName = btn.dataset.tool;
                const select = document.getElementById('mcpPlaygroundToolSelect');
                if (select) {
                    select.value = tName;
                    updateMcpPlaygroundSelection(tName);
                    select.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            });
        });
    }

    document.querySelectorAll('#mcpCategoryFilters .mcp-cat-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            document.querySelectorAll('#mcpCategoryFilters .mcp-cat-pill').forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            activeMcpCategory = pill.dataset.cat;
            if (mcpInfoData && mcpInfoData.tools) {
                renderMcpToolsCatalog(mcpInfoData.tools, activeMcpCategory);
            }
        });
    });

    const btnSaveMcpKey = document.getElementById('btnSaveMcpKey');
    if (btnSaveMcpKey) {
        btnSaveMcpKey.addEventListener('click', async () => {
            const keyVal = document.getElementById('inputMcpApiKey')?.value.trim() || '';
            btnSaveMcpKey.disabled = true;
            try {
                const res = await fetch('/api/system/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mcp_api_key: keyVal })
                });
                const data = await res.json();
                if (data.success) {
                    showToast('הגדרות האבטחה של שרת ה-MCP נשמרו!', 'success');
                    await loadMcpInfo();
                } else {
                    showToast(data.error || 'שגיאה בשמירת המפתח', 'error');
                }
            } catch (e) {
                showToast('שגיאת תקשורת עם השרת', 'error');
            } finally {
                btnSaveMcpKey.disabled = false;
            }
        });
    }

    const btnRefreshMcp = document.getElementById('btnRefreshMcp');
    if (btnRefreshMcp) {
        btnRefreshMcp.addEventListener('click', async () => {
            await loadMcpInfo();
            showToast('נתוני שרת ה-MCP רועננו', 'success');
        });
    }
});
