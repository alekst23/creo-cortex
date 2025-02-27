import os, sys

src_path = os.path.join(os.path.dirname(__file__), "..", "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)
    
from docker_utils.docker_launcher import DockerEnvironmentManager

from dotenv import load_dotenv
load_dotenv()

data_folder = os.path.join(os.path.dirname(__file__), "..", "data-map")

if len(sys.argv) > 1:
    shared_folders = sys.argv[1:]
else:
    shared_folders = []

volume_paths = [data_folder]
volume_paths.extend(shared_folders)
volumes = {path: {"bind": f"/container/{os.path.basename(path)}", "mode": "rw"} for path in volume_paths}

print(">>> Mounting volumes:")
for k, v in volumes.items():
    print(f"{k}: {v}")

launcher = DockerEnvironmentManager()
launcher.build_image(
    dockerfile_path=os.path.join(os.path.dirname(__file__), "Dockerfile"),
    requirements_path=os.path.join(os.path.dirname(__file__), "requirements.txt")
)
container = launcher.launch_container(
    container_name=os.getenv("EXECUTION_CONTAINER_NAME", "my_container"),
    environment={"MYVAR": "value"},
    ports={"80": "8080"},
    volumes=volumes,
    use_aws_credentials=True,
    use_github_credentials=True
)