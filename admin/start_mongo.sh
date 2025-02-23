#!/bin/bash

export MONGODB_VERSION=6.0-ubi8

# Check if the container exists and is stopped
if docker ps -a --filter "name=mongodb" --filter "status=exited" | grep -q "mongodb"; then
    echo "Container exists but is stopped. Starting container..."
    docker start mongodb
# Check if the container exists and is running
elif docker ps --filter "name=mongodb" | grep -q "mongodb"; then
    echo "Container is already running."
else
    echo "Container does not exist. Creating and starting new container..."
    docker run --name mongodb -d -p 27017:27017 mongodb/mongodb-community-server:$MONGODB_VERSION
fi