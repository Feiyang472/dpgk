import os, json

from airflow.decorators import dag, task
from airflow.operators.python import get_current_context
from airflow.sensors.filesystem import FileSensor
from dpdispatcher import Submission, Task, Resources, Machine
from fryflow.workflow import conductance_ipi, conduct_ipi_flow
from airflow.utils.task_group import TaskGroup

from fryflow.workflow.conductance_ipi import NVT, NVE, calc_kappa

ENVIRONMENT = "/home/ubuntu/anaconda3/envs/thermo/deepmd-kit-2.0b3-gpu/bin/"

default_args = {
    'owner': 'team23',
    'start_date': '2021-07-01'
}

@task()
def equi():
    return 0

@task()
def 

@dag(default_args=default_args, schedule_interval = None)
def fryflow():
    # kappa_params = FileSensor(
    #     task_id = 'wait_for_kappa_params',
    #     mode = 'reschedule',
    #     filepath = f"{get_current_context()['params']['work_base_abspath']}/kappa.json"
    # )
    
    a = equi()
    
    for g_id in range(3):
        with TaskGroup(group_id=f'temperature_{g_id}') as tg1:
            NVT_INFO = conduct_ipi_flow.NVT_start(START_INFO)
            NVE_INFO = conduct_ipi_flow.NVT_sampling(NVT_INFO)
            conduct_ipi_flow.kappa_post_process(conduct_ipi_flow.NVE_runs(conduct_ipi_flow.NVE_start(NVE_INFO)))
            a >> tg1

    return 0

fryflow_dag = fryflow()