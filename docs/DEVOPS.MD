# DevOps Container Workspace Setup

## Overview
This guide outlines how to create an isolated DevOps container environment for development, container management, and version control. This setup allows you to:

- Run shell commands like `aws`, `git`, and `docker` inside a container
- Build and launch other Docker containers from within the DevOps container
- Edit code locally with immediate reflection inside the container
- Maintain Git version control inside the container

---

## Architecture

```
Host Machine (Laptop/Server)
├── Docker Daemon
├── DevOps Container (Workspace)
│   ├── aws cli, git, docker-cli installed
│   ├── Docker socket mounted
│   └── Mounted code volume from host
│
└── Application Containers
    ├── App Container A (launched by DevOps container)
    └── App Container B (launched by DevOps container)
```

---

## DevOps Container Setup

### 1. Create a DevOps Dockerfile

```Dockerfile
FROM python:3.11-slim

# Install CLI tools
RUN apt-get update && apt-get install -y \
    curl \
    git \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI v2
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && ./aws/install && \
    rm -rf awscliv2.zip aws

# Install Docker CLI
RUN curl -fsSL https://get.docker.com -o get-docker.sh && \
    sh get-docker.sh && \
    rm get-docker.sh

# Optional Git configuration
RUN git config --global user.name "Your Name" && \
    git config --global user.email "you@example.com"

# Set working directory
WORKDIR /workspace

# Install additional tools
RUN apt-get update && apt-get install -y zsh vim && \
    chsh -s $(which zsh)

CMD ["/bin/zsh"]
```

---

### 2. Launch DevOps Container

```bash
docker run -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd):/workspace \
  --name devops-workspace \
  devops-container-image
```

- `/var/run/docker.sock` mount provides access to Docker daemon
- `$(pwd):/workspace` mount provides live code editing and git integration

---

## Typical Workflow Inside DevOps Container

### Build and Launch Containers

```bash
# Build your app image
cd /workspace
docker build -t my-app-image .

# Run the app container
docker run -d -p 8000:8000 my-app-image
```

### Git Version Control

```bash
git add .
git commit -m "Update code"
git push origin main
```

---

## Advanced: Persistent AWS Credentials

To persist AWS credentials inside the DevOps container:

```bash
docker run -it \
  -v ~/.aws:/root/.aws \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd):/workspace \
  devops-container-image
```

---

## Optional: Kubernetes Tooling

Extend your DevOps container with Kubernetes tools:

```Dockerfile
# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/v1.30.0/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
RUN curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

---

## Security Considerations

- Mounting the Docker socket gives the container full control of the host Docker daemon.
- Only use trusted containers and restrict access to the host.

---

## Final Benefits

| Requirement                      | Implementation                             | Benefit                        |
|----------------------------------|-------------------------------------------|--------------------------------|
| Shell Commands (`git`, `aws`)     | DevOps container                          | Clean, isolated environment    |
| Container Launch/Build           | Docker socket mount                       | Full Docker control            |
| Live Editing with Git            | Volume-mounted workspace                  | Instant editing and commits    |
| Kubernetes & Cloud Tools (Optional) | kubectl, helm, awscli inside DevOps container | Production readiness           |

---

## Conclusion

This method provides a portable, secure, and highly efficient development environment where you can manage your full lifecycle: coding, version control, container management, and eventual deployment preparation.

