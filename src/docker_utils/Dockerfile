FROM python:3.11-slim

# Install necessary CLI tools (AWS CLI, Git, Docker CLI)
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    groff \
    less \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# AWS CLI v2 install
RUN arch=$(uname -m) && \
    if [ "$arch" = "x86_64" ]; then \
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"; \
    elif [ "$arch" = "aarch64" ]; then \
        curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"; \
    else \
        echo "Unsupported architecture: $arch" && exit 1; \
    fi && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf aws awscliv2.zip

# Docker CLI (client only)
RUN curl -fsSL https://get.docker.com -o get-docker.sh && \
    sh get-docker.sh && \
    rm get-docker.sh

# Install Python packages
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Set working directory
WORKDIR /workspace

# Create .aws directory with proper permissions
RUN mkdir -p /root/.aws && chmod 700 /root/.aws

# Optional: Add a nice shell experience
RUN apt-get update && apt-get install -y zsh vim && \
    chsh -s $(which zsh)

CMD ["/bin/zsh"]
