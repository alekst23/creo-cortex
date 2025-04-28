import os
import sys
import logging
import argparse

from dotenv import load_dotenv

from docker_utils.docker_launcher import DockerEnvironmentManager


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    load_dotenv()

    parser = argparse.ArgumentParser(description="Start the DevOps Docker Manager")
    parser.add_argument('--shared-folder', action='append', help='Folders to mount into the container', default=[])
    parser.add_argument('--ports', type=str, nargs='*', help='Port mappings in the format host:container')
    args = parser.parse_args()

    src_path = os.path.join(os.path.dirname(__file__), "..", "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    data_folder = os.path.join(os.path.dirname(__file__), "..", "data-map")

    volume_paths = [data_folder] + args.shared_folder

    volumes = {}
    for path in volume_paths:
        if os.path.exists(path):
            volumes[path] = {"bind": f"/container/{os.path.basename(path)}", "mode": "rw"}
        else:
            logger.warning(f"Path {path} does not exist and will not be mounted.")

    if not volumes:
        logger.error("No valid volumes to mount. Exiting.")
        sys.exit(6)

    logger.info("\n\n>>> Making mount volumes list...")
    for k, v in volumes.items():
        logger.info(f"{k} -> {v['bind']}")

    ports = {}
    if args.ports:
        for p in args.ports:
            try:
                host, container = p.split(":")
                ports[container] = host
            except ValueError:
                logger.error(f"Invalid port mapping format: {p}. Expected host:container.")
                sys.exit(7)
    logger.info("\n\n>>> Port mappings:")
    for k, v in ports.items():
        logger.info(f"{k} -> {v}")

    logger.info("\n\n>>> Starting Docker environment manager...")
    launcher = DockerEnvironmentManager()
    launcher.build_image(
        dockerfile_path=os.path.join(os.path.dirname(__file__), "Dockerfile"),
        requirements_path=os.path.join(os.path.dirname(__file__), "requirements.txt")
    )

    env_vars = {
        "AWS_PROFILE": os.getenv("AWS_PROFILE"),
        "AWS_REGION": os.getenv("AWS_REGION"),
    }
    container = launcher.launch_container(
        container_name=os.getenv("EXECUTION_CONTAINER_NAME", "my_container"),
        environment=env_vars,
        ports=ports,
        volumes=volumes,
        use_aws_credentials=True,
        use_github_credentials=True
    )