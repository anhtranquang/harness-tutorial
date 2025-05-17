```mermaid
graph TD
    A[Deployment] -->|manages| B[Pod]
    B -->|exposed by| C[Service]
    C -->|routes to| D[Ingress]
    E[DaemonSet] -->|deploys| F[Pod]
    F -->|exposed by| G[Service]
    G -->|routes to| D
    H[StatefulSet] -->|manages| I[Pod]
    I -->|exposed by| J[Service]
    J -->|routes to| K[Ingress]
    L[ConfigMap] -->|provides config| I
    M[Secret] -->|provides sensitive data| I
    N[PersistentVolumeClaim] -->|mounts| I
    O[PersistentVolume] -->|backs| N
    N -->|uses| P[Volume]
    P -->|mounted in| I
```