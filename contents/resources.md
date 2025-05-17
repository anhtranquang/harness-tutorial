
# Kubernetes Resources & Helm Charts

## 1-Hour Session
**Date & Time:** 08:59 AM +07, Saturday, May 17, 2025

## Session Goals
- Understand Kubernetes resources (Pods, Deployments, Services, DaemonSets, StatefulSets, ConfigMaps, Secrets, Volumes, Ingress).
- Learn how Helm charts simplify application deployment.
- See a live demo of deploying an app with Helm.

## Agenda

| Time       | Topic                    | Duration |
|------------|--------------------------|----------|
| 0:00–0:05  | Introduction             | 5 min    |
| 0:05–0:25  | Kubernetes Resources     | 20 min   |
| 0:25–0:45  | Helm Charts              | 20 min   |
| 0:45–0:55  | Live Demo                | 10 min   |
| 0:55–1:00  | Q&A and Wrap-Up          | 5 min    |

## 1. Introduction (0:00–0:05)

### What is Kubernetes?
A platform to orchestrate containerized applications.

### Today’s Focus:
- Core and advanced Kubernetes resources.
- Helm charts for easy app deployment.

### Question:
What do you want to learn about Kubernetes or Helm?

## 2. Kubernetes Resources (0:05–0:25)

### What Are Resources?
- API objects (YAML/JSON) defining cluster behavior.
- Declarative: You set the desired state, Kubernetes maintains it.

### Key Resources

| Resource      | Purpose                                      | Example Use                         |
|---------------|----------------------------------------------|-------------------------------------|
| Pod           | Runs one or more containers (ephemeral).     | Host a single app instance.         |
| Deployment    | Manages pod replicas and updates.            | Scale a web app.                    |
| Service       | Stable networking for pods.                  | Expose app to users.                |
| DaemonSet     | Runs one pod per node (e.g., for networking).| Deploy NGINX Ingress Controller.    |
| StatefulSet   | Manages stateful apps with stable identity.  | Run apps like Confluence.           |
| ConfigMap     | Stores non-sensitive configuration data.     | Set app env variables.              |
| Secret        | Stores sensitive data (encrypted).           | Store API keys, passwords.          |
| Volume        | Provides persistent storage for pods.        | Store Confluence data.              |
| Ingress       | Manages external HTTP/HTTPS traffic.         | Route traffic to Confluence.        |

### Examples

#### Deployment + Service
For a scalable web app (e.g., nginx).

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  selector:
    app: nginx
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

#### DaemonSet
For NGINX Ingress Controller on every node.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: nginx-ingress-controller
spec:
  selector:
    matchLabels:
      app: nginx-ingress
  template:
    metadata:
      labels:
        app: nginx-ingress
    spec:
      containers:
      - name: nginx-ingress
        image: nginxinc/nginx-ingress:3.4.2
        args:
        - /nginx-ingress-controller
        - --ingress-class=nginx
        ports:
        - containerPort: 80
          name: http
        - containerPort: 443
          name: https
        securityContext:
          runAsUser: 101 # nginx user
      hostNetwork: true
```

#### StatefulSet + ConfigMap + Secret + Volume + PV/PVC + Ingress
For Atlassian Confluence, a stateful wiki platform.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: confluence
spec:
  serviceName: confluence
  replicas: 1
  selector:
    matchLabels:
      app: confluence
  template:
    metadata:
      labels:
        app: confluence
    spec:
      containers:
      - name: confluence
        image: atlassian/confluence:8.5.3
        env:
        - name: JVM_MAXIMUM_MEMORY
          valueFrom:
            configMapKeyRef:
              name: confluence-config
              key: jvm-max-memory
        - name: ATL_DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: confluence-secret
              key: db-password
        ports:
        - containerPort: 8090
        volumeMounts:
        - name: confluence-data
          mountPath: /var/atlassian/application-data/confluence
      volumes:
      - name: confluence-data
        persistentVolumeClaim:
          claimName: confluence-pvc
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: confluence-config
data:
  jvm-max-memory: "1024m"
---
apiVersion: v1
kind: Secret
metadata:
  name: confluence-secret
type: Opaque
data:
  db-password: cGFzc3dvcmQ= # base64-encoded "password"
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: confluence-pv
spec:
  capacity:
    storage: 10Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: standard
  hostPath:
    path: /mnt/confluence-data
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: confluence-pvc
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard
---
apiVersion: v1
kind: Service
metadata:
  name: confluence
spec:
  selector:
    app: confluence
  ports:
  - port: 8090
    targetPort: 8090
  clusterIP: None
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: confluence-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: confluence.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: confluence
            port:
              number: 8090
```

### Question:
Which resource seems most useful for your projects?

## 3. Helm Charts (0:25–0:45)

### What is Helm?
- Kubernetes’ package manager (like npm or apt).
- **Chart**: A package of Kubernetes manifests.
- **Release**: A deployed chart instance.
- **Benefits**: Simplifies deployment, supports versioning.

### Anatomy of a Helm Chart

```
my-chart/
├── Chart.yaml      # Metadata (name, version)
├── values.yaml     # Customizable settings
├── templates/      # Kubernetes YAMLs
│   ├── deployment.yaml
│   ├── service.yaml
```

#### Example: my-chart

**Chart.yaml**
Metadata for the chart.

```yaml
apiVersion: v2
name: my-app
version: 0.1.0
description: Sample web application
```

**values.yaml**
Customizable settings for the chart.

```yaml
replicaCount: 2
image:
  repository: nginx
  tag: latest
service:
  type: ClusterIP
  port: 80
```

**templates/deployment.yaml**
Templated Deployment manifest.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-app
  labels:
    app: {{ .Release.Name }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Release.Name }}
  template:
    metadata:
      labels:
        app: {{ .Release.Name }}
    spec:
      containers:
      - name: {{ .Release.Name }}
        image: {{ .Values.image.repository }}:{{ .Values.image.tag }}
        ports:
        - containerPort: 80
```

**templates/service.yaml**
Templated Service manifest.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ .Release.Name }}-service
  labels:
    app: {{ .Release.Name }}
spec:
  selector:
    app: {{ .Release.Name }}
  ports:
  - port: {{ .Values.service.port }}
    targetPort: 80
  type: {{ .Values.service.type }}
```

**Note on {{ .Release.Name }}**: This is a Helm built-in variable set during installation (e.g., `helm install my-release my-app`). It uniquely names resources for each release, not defined in `Chart.yaml`.

### Use Cases
- Deploy complex apps (e.g., WordPress + MySQL).
- Standardize microservices configurations.

### Poll:
Have you used Helm or a similar tool?

## 4. Live Demo (0:45–0:55)

### Deploying an App with Helm
- Add a repository:
  ```bash
  helm repo add bitnami https://charts.bitnami.com/bitnami
  helm repo update
  ```
- Install nginx chart:
  ```bash
  helm install my-nginx bitnami/nginx
  ```
- Check resources:
  ```bash
  kubectl get pods,svc
  ```
- Customize (`values.yaml`):
  ```yaml
  replicaCount: 3
  service:
    port: 8080
  ```
- Upgrade release:
  ```bash
  helm upgrade my-nginx bitnami/nginx -f values.yaml
  ```

### Question:
What would you customize in this chart?

## 5. Q&A and Wrap-Up (0:55–1:00)

### Key Takeaways
- **Kubernetes Resources**: Build apps with Pods, Deployments, DaemonSets, StatefulSets, Ingress, and more.
- **Helm Charts**: Streamline deployment and management.

### Resources
- [Kubernetes Docs](https://kubernetes.io/docs/)
- [Helm Docs](https://helm.sh/docs/)
- [Bitnami Charts](https://bitnami.com/stacks/helm)

### Contact
Questions? [Insert email/Slack].
