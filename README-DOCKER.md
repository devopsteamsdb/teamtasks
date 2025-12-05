# Docker Deployment Guide

## Quick Start

### Using Docker Compose (Recommended)
```bash
docker-compose up -d
```

Access the application at: http://localhost:5000

### Manual Docker Run
```bash
docker run -d \
  -p 5000:5000 \
  -v teamtasks-db:/app/instance \
  -v teamtasks-uploads:/app/uploads \
  --name teamtasks \
  devopsteamsdb/devopsteamsdb:teamtasks_latest
```

---

## Persistent Data

### Volumes
- **teamtasks-db**: Database storage (`/app/instance`)
- **teamtasks-uploads**: User-uploaded avatars (`/app/uploads`)

### Default Avatar
The default avatar (`default.png`) is bundled with the Docker image in `/app/static/images/` and does not require a volume.

---

## Backup & Restore

### Backup Database
```bash
docker run --rm -v teamtasks-db:/data -v $(pwd):/backup \
  alpine tar czf /backup/db-backup.tar.gz -C /data .
```

### Backup Uploads
```bash
docker run --rm -v teamtasks-uploads:/data -v $(pwd):/backup \
  alpine tar czf /backup/uploads-backup.tar.gz -C /data .
```

### Restore Database
```bash
docker run --rm -v teamtasks-db:/data -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/db-backup.tar.gz"
```

### Restore Uploads
```bash
docker run --rm -v teamtasks-uploads:/data -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/uploads-backup.tar.gz"
```

---

## Environment Variables

- `FLASK_ENV`: Set to `production` for production deployment (default)
- `FLASK_APP`: Application entry point (default: `app.py`)

---

## Health Check

The container includes a health check that monitors the `/api/version` endpoint every 30 seconds.

Check container health status:
```bash
docker ps
# Look for "(healthy)" in the STATUS column
```

View health check logs:
```bash
docker inspect --format='{{json .State.Health}}' teamtasks-app | jq
```

---

## Logs

View real-time logs:
```bash
docker-compose logs -f
```

View last 100 lines:
```bash
docker-compose logs --tail=100
```

---

## Updating the Application

### Pull Latest Image
```bash
docker-compose pull
docker-compose up -d
```

### Rebuild from Source
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

---

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs

# Check if ports are in use
netstat -an | grep 5000
```

### Database Issues
```bash
# Restart container
docker-compose restart

# If database is corrupted, restore from backup
# (see Backup & Restore section)
```

### Avatar Upload Issues
```bash
# Check volume permissions
docker exec teamtasks-app ls -la /app/uploads/avatars

# Ensure directory exists
docker exec teamtasks-app mkdir -p /app/uploads/avatars
```

---

## Development vs Production

### Development (without Docker)
```bash
python app.py
```
- Uploads go to `uploads/avatars/`
- Database at `instance/tasks.db`

### Production (with Docker)
```bash
docker-compose up -d
```
- Uploads persist in `teamtasks-uploads` volume
- Database persists in `teamtasks-db` volume

---

## Migration from Old Setup

If you have existing avatars in `static/images/`:

1. **Start the new container:**
   ```bash
   docker-compose up -d
   ```

2. **Copy user avatars to the uploads volume:**
   ```bash
   # For each user avatar (exclude default.png)
   docker cp static/images/elad.png teamtasks-app:/app/uploads/avatars/
   docker cp static/images/guy.png teamtasks-app:/app/uploads/avatars/
   # ... repeat for all user avatars
   ```

3. **Verify avatars are accessible:**
   - Visit http://localhost:5000
   - Check that all user avatars display correctly
   - Default avatar should still work for new users

---

## Security Notes

- The application runs in production mode (`FLASK_ENV=production`)
- Debug mode is disabled in production
- Uploaded files are limited to 5MB
- Only image files are accepted (PNG, JPG, JPEG, GIF)

---

## Support

For issues or questions, check the logs first:
```bash
docker-compose logs -f
```

Common issues are usually related to:
- Port conflicts (5000 already in use)
- Volume permissions
- Missing environment variables
