import shutil, os, ast, logging

import numpy as np
from airflow.decorators import dag, task
from airflow.operators.python import get_current_context
from airflow.sensors.filesystem import FileSensor

from dpdispatcher import Submission, Task, Resources, Machine

def get_empty_submission(job_work_dir):
    context = get_current_context()
    dag_run = context['params']

    machine = Machine.load_from_dict(context['machine'])
    resources = Resources.load_from_dict(context['resources'])

    submission = Submission(
        work_base=job_work_dir, 
        resources=resources, 
        machine=machine, 
    )
    return submission

@task()
def load_test_params():
    context = get_current_context()
    return 0

@task()
def md_time_step_test(test_params):
    return 0

@task()
def box_size_test(test_params, time_steps):
    return 0

@task()
def accuracy_cost_tradeoff_eval(box_step):
    return 0

@task()
def NVT_sampling(NVT_param):
    return 0

@task()
def NVE_runs(NVE_initials):
    return 0

@task()
def NVE_post_process(NVE_param):
    return 0

default_args = {
    'owner': 'team23',
    'start_date': '2021-07-01'
}

@dag(default_args=default_args, schedule_interval = None)
def conductance_workflow():
    test_params = load_test_params()

    report = accuracy_cost_tradeoff_eval(box_size_test(test_params, md_time_step_test(test_params)))


    NVT_file = FileSensor(
        task_id = 'wait_for_NVT_params',
        mode = 'reschedule',
        filepath = '/home/feiyang/Documents/dptech/conduct/deep_hackathon/NVT/param.json'
        )    

    get_report = prompt_user_input(NVT_file.filepath)
    
    report >> NVT_file >> get_report

    return NVE_post_process(NVE_runs(NVT_sampling(get_report)))

conductance_dag = conductance_workflow()