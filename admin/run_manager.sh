#!/bin/bash

source .env
python src/docker_utils/start_docker_manager.py --shared-folder $PROJECT_FOLDER