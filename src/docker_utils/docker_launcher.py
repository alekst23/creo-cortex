import os
import sys
import time
import docker
import argparse
import os
from typing import Optional, Dict, List
from docker.errors import APIError, NotFound

from dotenv import load_dotenv
load_dotenv()


# Setup logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_WORKING_DIR = "/container/data"
AWS_PROFILE = os.getenv("DOCKER_AWS_PROFILE", "default")


class DockerEnvironmentManager:
    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            sys.exit(2)

    def build_image(self, dockerfile_path: str, requirements_path: str = None, tag: str = "devops-container"):
        try:
            logger.info(f"\n\n>>> Building Docker image from {dockerfile_path}")
            context_path = os.path.dirname(dockerfile_path)
            dockerfile_rel = os.path.basename(dockerfile_path)

            build_args = {}
            if requirements_path:
                build_args["REQUIREMENTS"] = requirements_path

            image, logs = self.client.images.build(
                path=context_path,
                dockerfile=dockerfile_rel,
                tag=tag,
                buildargs=build_args,
                rm=True
            )
            for chunk in logs:
                if 'stream' in chunk:
                    logger.info(chunk['stream'].strip())
            logger.info(f"Successfully built image: {tag}")
        except APIError as e:
            logger.error(f"Docker build failed: {e}")
            sys.exit(3)

    def launch_container(
            self,
            container_name: Optional[str] = None,
            environment: Optional[Dict[str, str]] = None,
            ports: Optional[Dict[str, str]] = None,
            volumes: Optional[Dict[str, Dict[str, str]]] = None,
            use_aws_credentials: bool = False, 
            use_github_credentials: bool = False, 
            image_tag: str = "devops-container"):
        try:
            logger.info("\n\n>>> Launching Docker container...")

            # Clean up any existing container with same name
            try:
                old_container = self.client.containers.get(container_name)
                logger.info(f"\n\n>>> Removing existing container: {container_name}")
                old_container.stop()
                old_container.remove()
            except NotFound:
                pass  # No existing container

            env_vars = environment or {}
            volumes = volumes or {}

            # Always mount Docker socket to control the daemon
            docker_socket_path = "/var/run/docker.sock"
            if os.path.exists(docker_socket_path):
                volumes[docker_socket_path] = {"bind": "/var/run/docker.sock", "mode": "rw"}
                logger.info("\n\n>>> Mounted Docker socket for daemon access.")
            else:
                logger.warning("\n\n>>> Docker socket not found. Container control will not be available.")

            if use_aws_credentials:
                aws_path = os.path.expanduser("~/.aws")
                if os.path.exists(aws_path):
                    volumes[aws_path] = {"bind": "/root/.aws", "mode": "rw"}
                    logger.info("Mounted AWS credentials.")

            if use_github_credentials:
                gitconfig = os.path.expanduser("~/.gitconfig")
                ssh_folder = os.path.expanduser("~/.ssh")
                if os.path.exists(gitconfig):
                    volumes[gitconfig] = {"bind": "/root/.gitconfig", "mode": "rw"}
                if os.path.exists(ssh_folder):
                    volumes[ssh_folder] = {"bind": "/root/.ssh", "mode": "rw"}
                logger.info("Mounted GitHub credentials.")

            logger.info(f"\n\n>>> Launching container {container_name}")
            container = self.client.containers.run(
                image_tag,
                name=container_name,
                environment=env_vars,
                ports=ports,
                volumes=volumes,
                stdin_open=True,
                tty=True,
                detach=True,
                privileged=True,
            )

            # Wait for container to be healthy or timeout
            timeout = 30  # seconds
            start_time = time.time()
            while time.time() - start_time < timeout:
                container.reload()
                if container.status == "running":
                    logger.info(f"Container {container_name} is running.")
                    return container
                time.sleep(1)
            logger.error(f"Container {container_name} did not become healthy within {timeout} seconds.")
            sys.exit(4)

        except APIError as e:
            logger.error(f"Failed to launch container: {e}")
            sys.exit(5)


def main():
    parser = argparse.ArgumentParser(description='Build and launch custom Docker environment')
    parser.add_argument('--build', action='store_true', help='Build the Docker image')
    parser.add_argument('--dockerfile', default='Dockerfile', help='Path to Dockerfile')
    parser.add_argument('--requirements', default='requirements.txt', help='Path to requirements.txt')
    parser.add_argument('--name', help='Container name')
    parser.add_argument('--env', nargs='*', help='Environment variables (KEY=VALUE)')
    parser.add_argument('--ports', nargs='*', help='Port mappings (HOST:CONTAINER)')
    parser.add_argument('--volumes', nargs='*', help='Volume mappings (HOST:CONTAINER)')
    parser.add_argument('--no-aws-credentials', action='store_true', help='Don\'t mount AWS credentials')
    parser.add_argument('--no-github-credentials', action='store_true', help='Don\'t mount GitHub credentials')
    
    args = parser.parse_args()
    
    manager = DockerEnvironmentManager()
    
    # Build image if requested
    if args.build:
        manager.build_image(args.dockerfile, args.requirements)
    
    # Process environment variables
    env = {}
    if args.env:
        for env_var in args.env:
            key, value = env_var.split('=')
            env[key] = value
    
    # Process port mappings
    ports = {}
    if args.ports:
        for port_mapping in args.ports:
            host_port, container_path = port_mapping.split(':')
            ports[container_path] = host_port
    
    # Launch container
    manager.launch_container(
        container_name=args.name,
        environment=env,
        ports=ports,
        volumes=None,  # Will be handled by additional_mounts
        use_aws_credentials=not args.no_use_aws_credentials,
        use_github_credentials=not args.no_use_github_credentials,
        additional_mounts=args.volumes
    )

if __name__ == "__main__":
    main()