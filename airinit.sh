#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# airflow will be created at ~/airflow
airflow -h
cd ~/airflow
mkdir ~/airflow/dags
# airflow will initialize datebase with sqlite
airflow db init

ln $SCRIPT_DIR/fryflow/workflow/*flow.py ~/airflow/dags/

# create a user
airflow users create \
    --username haxon \
    --firstname twentythree \
    --lastname haxon \
    --role Admin \
    --email fc472@cam.ac.uk