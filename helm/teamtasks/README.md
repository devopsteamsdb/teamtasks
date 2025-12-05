# TeamTasks Helm Chart

Helm chart for deploying TeamTasks application on OpenShift.

## Prerequisites

- OpenShift cluster 4.x or higher
- Helm 3.x installed
- `oc` CLI configured and logged in to your cluster

## Quick Start

### Install the chart

```bash
# Create a new project
oc new-project teamtasks

# Install the chart
helm install teamtasks ./helm/teamtasks

# Or with custom values
helm install teamtasks ./helm/teamtasks -f custom-values.yaml
```

### Access the application

```bash
# Get the route URL
oc get route teamtasks -o jsonpath='{.spec.host}'

# Open in browser
export ROUTE_HOST=$(oc get route teamtasks -o jsonpath='{.spec.host}')
echo "https://$ROUTE_HOST"
```

## Configuration

The following table lists the configurable parameters and their default values.

### Image Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Image repository | `devopsteamsdb/devopsteamsdb` |
| `image.tag` | Image tag | `teamtasks_latest` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |

### Deployment Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `1` |
| `resources.limits.cpu` | CPU limit | `500m` |
| `resources.limits.memory` | Memory limit | `512Mi` |
| `resources.requests.cpu` | CPU request | `250m` |
| `resources.requests.memory` | Memory request | `256Mi` |

### Persistence Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `persistence.database.enabled` | Enable database persistence | `true` |
| `persistence.database.size` | Database PVC size | `1Gi` |
| `persistence.database.storageClass` | Storage class | `""` (default) |
| `persistence.uploads.enabled` | Enable uploads persistence | `true` |
| `persistence.uploads.size` | Uploads PVC size | `5Gi` |
| `persistence.uploads.storageClass` | Storage class | `""` (default) |

### Route Configuration (OpenShift)

| Parameter | Description | Default |
|-----------|-------------|---------|
| `route.enabled` | Enable OpenShift Route | `true` |
| `route.host` | Custom hostname | `""` (auto-generated) |
| `route.tls.enabled` | Enable TLS | `true` |
| `route.tls.termination` | TLS termination type | `edge` |

### Health Checks

| Parameter | Description | Default |
|-----------|-------------|---------|
| `livenessProbe.initialDelaySeconds` | Liveness probe initial delay | `30` |
| `readinessProbe.initialDelaySeconds` | Readiness probe initial delay | `10` |

## Examples

### Custom hostname

```bash
helm install teamtasks ./helm/teamtasks \
  --set route.host=teamtasks.apps.mycluster.com
```

### Increase storage

```bash
helm install teamtasks ./helm/teamtasks \
  --set persistence.database.size=5Gi \
  --set persistence.uploads.size=20Gi
```

### Use specific storage class

```bash
helm install teamtasks ./helm/teamtasks \
  --set persistence.database.storageClass=fast-ssd \
  --set persistence.uploads.storageClass=standard
```

### Scale replicas

```bash
helm install teamtasks ./helm/teamtasks \
  --set replicaCount=3
```

### Custom resource limits

```bash
helm install teamtasks ./helm/teamtasks \
  --set resources.limits.cpu=1000m \
  --set resources.limits.memory=1Gi
```

## Upgrading

```bash
# Upgrade to new version
helm upgrade teamtasks ./helm/teamtasks

# Upgrade with new values
helm upgrade teamtasks ./helm/teamtasks -f new-values.yaml
```

## Uninstalling

```bash
# Uninstall the release
helm uninstall teamtasks

# Note: PVCs are not deleted automatically
# To delete PVCs:
oc delete pvc teamtasks-database teamtasks-uploads
```

## Backup and Restore

### Backup

```bash
# Backup database
oc exec deployment/teamtasks -- tar czf - /app/instance > db-backup.tar.gz

# Backup uploads
oc exec deployment/teamtasks -- tar czf - /app/uploads > uploads-backup.tar.gz
```

### Restore

```bash
# Restore database
cat db-backup.tar.gz | oc exec -i deployment/teamtasks -- tar xzf - -C /

# Restore uploads
cat uploads-backup.tar.gz | oc exec -i deployment/teamtasks -- tar xzf - -C /
```

## Troubleshooting

### Check pod status

```bash
oc get pods -l app.kubernetes.io/name=teamtasks
```

### View logs

```bash
oc logs -f deployment/teamtasks
```

### Check PVC status

```bash
oc get pvc
```

### Describe pod for events

```bash
oc describe pod -l app.kubernetes.io/name=teamtasks
```

### Access pod shell

```bash
oc exec -it deployment/teamtasks -- /bin/bash
```

## Security Considerations

- The chart is configured to work with OpenShift's security context constraints (SCC)
- Runs as non-root user
- Uses arbitrary UIDs as required by OpenShift
- TLS enabled by default on routes

## Support

For issues or questions:
1. Check the logs: `oc logs -f deployment/teamtasks`
2. Check pod events: `oc describe pod -l app.kubernetes.io/name=teamtasks`
3. Verify PVCs are bound: `oc get pvc`
