# TeamTasks - Infrastructure Task Management System

A modern, bilingual (Hebrew/English) task management application built with Flask, designed for Infrastructure teams. Features team-based organization, real-time updates, and easy deployment to Docker and Kubernetes/OpenShift.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)

---

## 📋 Table of Contents

- [Features](#-features)
- [Screenshots](#-screenshots)
- [Quick Start](#-quick-start)
- [Deployment](#-deployment)
  - [Docker](#docker)
  - [Docker Compose](#docker-compose)
  - [Kubernetes/OpenShift](#kubernetesopenshift)
- [Configuration](#-configuration)
- [Development](#-development)
- [API Documentation](#-api-documentation)
- [Backup & Restore](#-backup--restore)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### Core Functionality
- ✅ **Task Management** - Create, edit, delete, and track tasks
- ✅ **Team Organization** - Organize tasks by teams and projects
- ✅ **Member Management** - Assign tasks to team members
- ✅ **Priority Levels** - High, Medium, Low, None
- ✅ **Status Tracking** - Not Started, In Progress, Done, Delayed
- ✅ **Notes Support** - Add detailed notes to tasks
- ✅ **Task Archiving** - Archive completed tasks and view them in a dedicated mode

### User Experience
- 🌐 **Bilingual Interface** - Full Hebrew and English support
- 🔍 **Real-time Search** - Instant search across all tasks
- 🎨 **Modern UI** - Clean, responsive design
- 📱 **Mobile Friendly** - Works on all devices
- 🔄 **Auto-refresh** - Real-time updates without page reload
- 🖨️ **Advanced Print View** - Filterable printable reports with project scoping

### Technical Features
- 🐳 **Docker Ready** - Containerized deployment
- ☸️ **Kubernetes/OpenShift** - Helm chart included
- 💾 **Persistent Storage** - Database and uploads persist
- 🔒 **Secure** - Production-ready security settings
- 📊 **RESTful API** - Full API for automation
- ✅ **Advanced Calendar** - Weekly view and Workload view for team capacity planning
- ✅ **Advanced Filtering** - Filter by Team, Member, Status, and Priority across all views (Dashboard, Calendar, Print)
- 🏥 **Health Checks** - Built-in health monitoring

---

## 🖼️ Screenshots

### Main Dashboard
The main task board with team filtering and search capabilities.
<img width="1912" height="907" alt="image" src="https://github.com/user-attachments/assets/baf73720-620d-44ad-9695-ab0be1abe49f" />


### Admin Panel
Manage teams and members, upload avatars, and configure settings.
<img width="1915" height="729" alt="image" src="https://github.com/user-attachments/assets/0f5d9854-24ad-4635-a6d0-45fd2706e054" />


---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/devopsteamsdb/teamtasks.git
   cd teamtasks
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the application**
   - Main dashboard: http://localhost:5000
   - Admin panel: http://localhost:5000/admin
   - Print view: http://localhost:5000/print

---

## 📦 Deployment

### Docker

#### Build and Run
```bash
# Build the image
docker build -t teamtasks:latest .

# Run the container
docker run -d \
  -p 5000:5000 \
  -v teamtasks-db:/app/instance \
  -v teamtasks-uploads:/app/uploads \
  --name teamtasks \
  teamtasks:latest
```

#### Using Pre-built Image
```bash
docker run -d \
  -p 5000:5000 \
  -v teamtasks-db:/app/instance \
  -v teamtasks-uploads:/app/uploads \
  --name teamtasks \
  devopsteamsdb/devopsteamsdb:teamtasks_latest
```

### Docker Compose

The easiest way to deploy with persistent storage:

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

**docker-compose.yml** includes:
- Persistent volumes for database and uploads
- Health checks
- Automatic restart policy
- Production environment variables

For detailed Docker documentation, see [README-DOCKER.md](README-DOCKER.md).

### Kubernetes/OpenShift

Deploy using the included Helm chart:

#### Quick Install
```bash
# Create namespace/project
kubectl create namespace teamtasks
# or for OpenShift
oc new-project teamtasks

# Install with Helm
helm install teamtasks ./helm/teamtasks
```

#### Custom Configuration
```bash
# Custom hostname and storage
helm install teamtasks ./helm/teamtasks \
  --set route.host=teamtasks.apps.mycluster.com \
  --set persistence.database.size=5Gi \
  --set persistence.uploads.size=20Gi
```

#### Production Deployment
```bash
helm install teamtasks-prod ./helm/teamtasks \
  --set replicaCount=3 \
  --set resources.limits.cpu=1000m \
  --set resources.limits.memory=1Gi \
  --set persistence.database.storageClass=fast-ssd
```

For detailed Helm chart documentation, see [helm/teamtasks/README.md](helm/teamtasks/README.md).

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment mode | `production` |
| `FLASK_APP` | Application entry point | `app.py` |

### Storage Configuration

**Database Location:** `/app/instance/tasks.db`
- SQLite database
- Stores all tasks, teams, and members

**Uploads Location:** `/app/uploads/avatars/`
- User-uploaded avatar images
- Default avatar bundled in `/app/static/images/default.png`

### Resource Limits (Kubernetes)

Default resource allocation:
- **CPU**: 250m request, 500m limit
- **Memory**: 256Mi request, 512Mi limit

Adjust in `values.yaml` or via `--set` flags.

---

## 🛠️ Development

### Project Structure
```
teamtasks/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker image definition
├── docker-compose.yml    # Docker Compose configuration
├── static/               # Static assets
│   ├── style.css        # Main styles
│   ├── script.js        # Frontend logic
│   ├── admin.css        # Admin panel styles
│   ├── admin.js         # Admin panel logic
│   └── images/          # Static images
├── templates/            # HTML templates
│   ├── index.html       # Main dashboard
│   ├── admin.html       # Admin panel
│   └── print.html       # Print view
├── scripts/             # Utility scripts
│   ├── seed_data.py     # Sample data generator
│   └── clear_data.py    # Database cleanup
└── helm/                # Helm chart
    └── teamtasks/       # Chart files
```

### Database Schema

**Teams**
- `id`: Primary key
- `name_en`: English name
- `name_he`: Hebrew name

**TeamMembers**
- `id`: Primary key
- `team_id`: Foreign key to Teams
- `name_en`: English name
- `name_he`: Hebrew name
- `avatar_path`: Avatar image filename

**Tasks**
- `id`: Primary key
- `project`: Project name
- `task`: Task description
- `members`: Comma-separated member names
- `status`: Task status
- `priority`: Priority level
- `notes`: Additional notes
- `team_id`: Foreign key to Teams

### Running Tests

```bash
# Install development dependencies
pip install -r requirements.txt

# Run the application in debug mode
FLASK_ENV=development python app.py
```

---

## 📡 API Documentation

### Tasks

**Get all tasks**
```bash
GET /api/tasks
```

**Create task**
```bash
POST /api/tasks
Content-Type: application/json

{
  "project": "Infrastructure",
  "task": "Setup monitoring",
  "members": "john,jane",
  "status": "status-inprogress",
  "priority": "high",
  "notes": "Use Prometheus",
  "team_id": 1
}
```

**Update task**
```bash
PUT /api/tasks/{id}
Content-Type: application/json

{
  "status": "status-done"
}
```

**Delete task**
```bash
DELETE /api/tasks/{id}
```

### Teams

**Get all teams**
```bash
GET /api/teams
```

**Create team**
```bash
POST /api/teams
Content-Type: application/json

{
  "name_en": "devops",
  "name_he": "צוות DevOps"
}
```

### Members

**Get all members**
```bash
GET /api/members
```

**Upload avatar**
```bash
POST /api/members/{id}/avatar
Content-Type: multipart/form-data

avatar: <file>
```

### Health Check

**Version endpoint**
```bash
GET /api/version
```

---

## 💾 Backup & Restore

### Via Admin Interface (Recommended)
You can easily backup and restore data via the Admin Panel (`/admin > Backup & Restore`):
- **Backup**: Select a table (or "All System") and download a JSON file.
- **Restore**: Select a target table (or "All System") and upload a JSON backup file.
  - **All System Restore**: WARNING! This will wipe existing data and replace it with the backup content to ensure consistency.

### Via API

**Backup Table**
```bash
GET /api/backup/{table_name}
# table_name can be: teams, members, tasks, special_days, or all
```

**Restore Table**
```bash
POST /api/restore/{table_name}
Content-Type: multipart/form-data
file: <backup_file.json>
```

### Manual (Docker/K8s)
Legacy method for full volume backup:

#### Docker

**Backup**
```bash
# Database
docker exec teamtasks tar czf - /app/instance > db-backup.tar.gz

# Uploads
docker exec teamtasks tar czf - /app/uploads > uploads-backup.tar.gz
```

**Restore**
```bash
# Database
cat db-backup.tar.gz | docker exec -i teamtasks tar xzf - -C /

# Uploads
cat uploads-backup.tar.gz | docker exec -i teamtasks tar xzf - -C /
```

#### Kubernetes/OpenShift

**Backup**
```bash
# Database
kubectl exec deployment/teamtasks -- tar czf - /app/instance > db-backup.tar.gz

# Uploads
kubectl exec deployment/teamtasks -- tar czf - /app/uploads > uploads-backup.tar.gz
```

**Restore**
```bash
# Database
cat db-backup.tar.gz | kubectl exec -i deployment/teamtasks -- tar xzf - -C /

# Uploads
cat uploads-backup.tar.gz | kubectl exec -i deployment/teamtasks -- tar xzf - -C /
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- Database: [SQLAlchemy](https://www.sqlalchemy.org/)
- Icons: Custom SVG icons
- Deployment: Docker, Kubernetes, OpenShift

---

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the [Docker documentation](README-DOCKER.md)
- Review the [Helm chart documentation](helm/teamtasks/README.md)

---

**Made with ❤️ by the DevOps Team**

