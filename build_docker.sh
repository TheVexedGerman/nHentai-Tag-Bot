#!/bin/bash
url="localhost:6880/reddit-bots/nhentaitagbot"
dockerfileName="dockerfile"

dateTag="$(date +%Y-%m-%d-%H%M)"

#build + tag docker image
docker build --pull --no-cache -t $url:latest -t $url:$dateTag -f $dockerfileName .
#Push all docker image
docker push --all-tags $url