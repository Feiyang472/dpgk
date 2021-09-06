import os, json, time, datetime, shutil

import numpy as np

from airflow.decorators import dag, task
from airflow.operators.python import get_current_context
from airflow.utils.task_group import TaskGroup
from airflow.models import Variable

from dpdispatcher import Task

from dpgk.workflow import conduct_ipi_flow
from dpgk.workflow.conductance_local_tasks import calcs, test_in_ipi_template


ENVIRONMENT = "/home/ubuntu/anaconda3/envs/thermo/deepmd-kit-2.0b3-gpu/bin/"

default_args = {
    'owner': 'DeepPotentialUser',
    'start_date': '2021-07-01'
}

@task()
def test_ts():
    """
    Before the actual RPMD simulation begins, perform short classical md NVEs for several different time steps, to analyse the divergence rates. 
    """
    context = get_current_context()['params']
    work_base_abspath = context['work_base_abspath']
    
    N_clients = 4

    test_ts_tasks = []
    for i_test in context['test_ts']:
        test_addr = f"test_{i_test}fs"
        test_abspath = os.path.join(work_base_abspath, test_addr)
        if os.path.isdir(test_abspath):
            shutil.rmtree(test_abspath)
        os.mkdir(test_abspath)
        shutil.copyfile(os.path.join(work_base_abspath, context['inputs']['initial_state']), os.path.join(test_abspath, context['inputs']['initial_state']))
        with open(os.path.join(test_abspath, 'input.xml'),  "x") as in_ipi:
            in_ipi.write(
                test_in_ipi_template.format(
                    n_beads = 1,
                    seed = '3924',
                    temperature = context['temperature_list'][0],
                    time_step = i_test,
                    check_stride = 500,
                    xv_stride = int(1.0/i_test),
                    md_steps = int(2000/i_test),
                    MD_addr = test_addr,
                    initial_state = context['inputs']['initial_state']
                )
            )
        test_task = Task(
            command = (
                f"{ENVIRONMENT}i-pi input.xml >& logfile & sleep 5; "
                f"iclient=1; while [ $iclient -le {N_clients} ]; "
                f"do {ENVIRONMENT}client_dp 1234 {test_addr} unix ../{context['inputs']['dp_graph']} init.xyz & "
                "iclient=$((iclient+1)); "
                "done; "
                "wait; echo '***** finish time *****'; date; sleep 1; "
                f"{ENVIRONMENT}calc_J ../{context['inputs']['dp_graph']} ; "
                ), 
            task_work_path = f'{test_addr}',
            forward_files = ['*.xyz', 'input.xml'],
            backward_files = ['simulation.out',
                              'J_array.npy',
                              'x_array.npy',
                              'v_array.npy',
                              'a_array.npy'])
        test_ts_tasks.append(test_task)

    submission = conduct_ipi_flow.get_empty_submission(work_base_abspath)
    submission.register_task_list(test_ts_tasks)
    submission.forward_common_files = [context['inputs']['dp_graph']]
    submission.run_submission(clean = True)
    return context

@task()
def test_ts_analysis(context):
    """
    Analyse the errors of the tested time steps
    """
    work_base_abspath = context['work_base_abspath']
    PREPARE_INFO = dict(
        work_base_abspath=work_base_abspath,
        inputs=context['inputs'],
        temperature_list = context['temperature_list'],
        n_beads = context['n_beads']
    )
    
    test_ts, ave, rmse = calcs.test_ts_erranalysis(context['test_ts', work_base_abspath])
    
    print('tested time steps:                     ', test_ts, '\n',
          'average errors (percentage):           ', ave * 100, '\n',
          'root mean square errors (percentage):  ', rmse * 100)
    
    Variable.set("Number_of_T_points", len(context['temperature_list']))

    return PREPARE_INFO

@task(execution_timeout = datetime.timedelta(seconds=300))
def kappa_task_start(PREPARE_INFO, t_id):
    """
    Prepare a working directory for a specific temperature.
    """
    temperature = int(PREPARE_INFO['temperature_list'][int(t_id)])

    T_base_abspath = PREPARE_INFO['work_base_abspath'] + f'/temperature_{temperature:02}K'

    kappa_params = {
        "NVT_params" : {
            "NVE_samples": None,
            "xv_stride": 2000,
            "check_stride": 500,
            "seed": 3924,
            "n_beads": PREPARE_INFO['n_beads'],
            "temperature": temperature,
            "time_step": 0.2
        },
        "NVE_params": {
            "md_steps": None,
            "time_step": None,
            "check_stride": 500
        }
    }
    
    if not os.path.isdir(T_base_abspath):
        os.mkdir(T_base_abspath)
        with open(os.path.join(T_base_abspath, 'kappa_template.json'), 'x') as f:
            json.dump(kappa_params, f, indent=4, sort_keys=True)
        for infile in PREPARE_INFO['inputs'].values():
            shutil.copyfile(os.path.join(PREPARE_INFO['work_base_abspath'], infile), os.path.join(T_base_abspath, infile))
    
    # On login node or local machine, detect whether the user has provided parameter files for each of the temperature points
    while not os.path.isfile(os.path.join(T_base_abspath, 'kappa.json')):
        time.sleep(30)

    START_INFO = dict(
        work_base_abspath = T_base_abspath,
        inputs = PREPARE_INFO['inputs'],
        temperature = temperature
    )

    return START_INFO

@task()
def pdos_post_process(NVE_INFO):
    n_samples = int(NVE_INFO['n_samples'])
    pdos = None
    for i_sample in range(n_samples):
        vel = np.load(os.path.join(NVE_INFO['work_base_abspath'], NVE_INFO['NVE_addr'], f'sample_{i_sample:02}', 'v_array.npy'))
        if pdos is None:
            pdos = calcs.vel_auto(vel, 2).sum(axis=0)/n_samples
        else:
            pdos += calcs.vel_auto(vel, 2).sum(axis=0)/n_samples
    np.save(os.path.join(NVE_INFO['work_base_abspath'], 'pdos'), np.fft.rfft(pdos))
    return 0

@dag(default_args=default_args, schedule_interval = None)
def dpgk_workflow():
    """
    The main DPGK workflow: 
    Calculate thermal conductivities in a range of temperatures.
    """
    PREPARE_INFO = test_ts_analysis(test_ts())
    
    for t_id in range(int(Variable.get("Number_of_T_points"))):
        with TaskGroup(group_id=f'temperature_{t_id:02}') as tg:
            START_INFO = kappa_task_start(PREPARE_INFO, t_id)
            NVT_INFO = conduct_ipi_flow.NVT_start(START_INFO)
            NVE_INFO = conduct_ipi_flow.NVT_sampling(NVT_INFO)
            NVE_INFO = conduct_ipi_flow.NVE_runs(conduct_ipi_flow.NVE_start(NVE_INFO))
            conduct_ipi_flow.kappa_post_process(NVE_INFO)
            pdos_post_process(NVE_INFO)

    return 0

dpgk_workflow_dag = dpgk_workflow()