#!/bin/bash
cd ..
docker build --no-cache -t cicd:synopsisd .
docker tag cicd:synopsisd registry:5000/synopsisd:$VERSION
docker push registry:5000/synopsisd:$VERSION
docker rmi cicd:synopsisd

