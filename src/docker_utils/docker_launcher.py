import docker
import argparse
import os
import shutil
import tempfile
from typing import Optional, Dict, List

class DockerEnvironmentManager:
    def __init__(self):
        self.client = docker.from_env()
        self.image_name = "custom-python-env"
        self.image_tag = "latest"

    def build_image(self, dockerfile_path: str, requirements_path: str) -> str:
        """
        Build a Docker image from the Dockerfile
        
        Args:
            dockerfile_path: Path to the Dockerfile
            requirements_path: Path to requirements.txt
        
        Returns:
            str: Image ID
        """
        try:
            # Create a temporary build context
            with tempfile.TemporaryDirectory() as build_context:
                # Copy Dockerfile and requirements.txt to build context
                shutil.copy2(dockerfile_path, build_context)
                shutil.copy2(requirements_path, os.path.join(build_context, 'requirements.txt'))
                
                print(f"Building image {self.image_name}...")
                image, logs = self.client.images.build(
                    path=build_context,
                    dockerfile=os.path.basename(dockerfile_path),
                    tag=f"{self.image_name}:{self.image_tag}",
                    rm=True
                )
                
                # Print build logs
                for log in logs:
                    if 'stream' in log:
                        print(log['stream'].strip())
                        
                return image.id
            
        except Exception as e:
            print(f"Error building image: {str(e)}")
            raise

    def launch_container(
        self,
        container_name: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        ports: Optional[Dict[str, str]] = None,
        volumes: Optional[Dict[str, Dict[str, str]]] = None,
        aws_credentials: bool = True,
        additional_mounts: Optional[List[str]] = None
    ):
        """
        Launch a container with the custom environment
        
        Args:
            container_name: Optional name for the container
            environment: Dictionary of environment variables
            ports: Dictionary of port mappings
            volumes: Dictionary of volume mappings
            aws_credentials: Whether to mount AWS credentials
            additional_mounts: List of additional host:container path pairs to mount
        """
        try:
            # Prepare volumes
            volumes = volumes or {}
            
            # Add AWS credentials if requested
            if aws_credentials:
                aws_path = os.path.expanduser("~/.aws")
                if os.path.exists(aws_path):
                    print(f"Found AWS credentials at {aws_path}")
                    # List the files to verify they exist
                    if os.path.exists(os.path.join(aws_path, 'credentials')):
                        print("Found AWS credentials file")
                    if os.path.exists(os.path.join(aws_path, 'config')):
                        print("Found AWS config file")
                    
                    # Mount with read-write permission temporarily to debug
                    volumes[aws_path] = {'bind': '/root/.aws', 'mode': 'rw'}
                else:
                    print("Warning: AWS credentials directory not found at " + aws_path)
            
            # Add additional mounts
            if additional_mounts:
                for mount in additional_mounts:
                    host_path, container_path = mount.split(':')
                    volumes[host_path] = {'bind': container_path, 'mode': 'rw'}
            
            # Launch container
            container = self.client.containers.run(
                f"{self.image_name}:{self.image_tag}",
                name=container_name,
                environment=environment or {},
                ports=ports or {},
                volumes=volumes,
                detach=True,
                tty=True,
                stdin_open=True,
                working_dir="/workspace"
            )
            
            print(f"Container {container.name} launched successfully!")
            print(f"To attach to the container, run: docker exec -it {container.name} /bin/bash")
            
            return container
            
        except Exception as e:
            print(f"Error launching container: {str(e)}")
            raise

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
        aws_credentials=not args.no_aws_credentials,
        additional_mounts=args.volumes
    )

if __name__ == "__main__":
    main()