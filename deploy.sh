#!/bin/sh

# Deploys the current code as a docker container to a configured heroku instance in the current directory
docker build -t flask-heroku:latest .
heroku container:push web
heroku container:release web 