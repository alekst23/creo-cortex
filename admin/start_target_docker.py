import os
from docker_utils.docker_launcher import DockerEnvironmentManager

from dotenv import load_dotenv
load_dotenv()

data_folder = os.path.join(os.path.dirname(__file__), "..", "data-map")

launcher = DockerEnvironmentManager()
launcher.build_image(
    dockerfile_path=os.path.join(os.path.dirname(__file__), "Dockerfile"),
    requirements_path=os.path.join(os.path.dirname(__file__), "requirements.txt")
)
container = launcher.launch_container(
    container_name=os.getenv("EXECUTION_CONTAINER_NAME", "my_container"),
    environment={"MYVAR": "value"},
    ports={"80": "8080"},
    volumes={data_folder: {"bind": "/container/data", "mode": "rw"}},
    use_aws_credentials=True,
    use_github_credentials=True
)