#!/bin/bash -ex
docker exec -it $(docker ps -f publish=8000 -f name=django -q) bash
