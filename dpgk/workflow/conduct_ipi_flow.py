import os, json

from airflow.decorators import dag, task
from airflow.operators.python import get_current_context
from dpdispatcher import Submission, Task, Resources, Machine

from dpgk.workflow.conductance_local_tasks import NVT, NVE, KAPPA

ENVIRONMENT = "/home/ubuntu/anaconda3/envs/thermo/deepmd-kit-2.0b3-gpu/bin/"

def get_kappa_params(params_path):
    with open(params_path) as f:
        return json.load(f)

def get_empty_submission(job_work_dir):
    context = get_current_context()['params']
    machine = Machine.load_from_dict(context['machine'])
    resources = Resources.load_from_dict(context['resources'])
    submission = Submission(
        work_base=job_work_dir, 
        resources=resources, 
        machine=machine, 
    )
    return submission

@task()
def NVT_start(START_INFO):
    work_base_abspath = START_INFO['work_base_abspath']
    inputs = START_INFO['inputs']

    NVT_params = get_kappa_params(os.path.join(work_base_abspath, 'kappa.json'))['NVT_params']
    NVT_addr = NVT.make_task(work_base_abspath, NVT_params, inputs)

    NVT_INFO = dict(
        work_base_abspath = work_base_abspath, 
        NVT_addr = NVT_addr,
        dp_graph = inputs['dp_graph'],
        initial_state = inputs['initial_state'],
        NVT_params = NVT_params
    )

    return NVT_INFO

@task()
def NVT_sampling(NVT_INFO):
    N_clients = 32

    NVT_addr = NVT_INFO['NVT_addr']

    ipi_md_task = Task(
        command = (
            f"{ENVIRONMENT}i-pi input.xml >& logfile & sleep 5; "
            f"iclient=1; while [ $iclient -le {N_clients} ]; "
            f"do {ENVIRONMENT}client_dp 1234 {NVT_addr} unix {NVT_INFO['dp_graph']} {NVT_INFO['initial_state']} & "
            "iclient=$((iclient+1)); "
            "done; "
            "wait; echo '********* finish time *********'; date; sleep 1; "
            ), 
        task_work_path = NVT_addr,
        forward_files = [NVT_INFO['dp_graph'], 
                         NVT_INFO['initial_state'], 
                         'input.xml'],
        backward_files = ['simulation.out',
                          'simulation.pos_*.xyz', 
                          'simulation.vel_*.xyz'])
    
    work_base_abspath = NVT_INFO['work_base_abspath']
    
    submission = get_empty_submission(work_base_abspath)
    submission.register_task(ipi_md_task)
    submission.run_submission(clean=True)

    NVT_params = NVT_INFO['NVT_params']
    NVE_INFO = dict(
        work_base_abspath = work_base_abspath,
        dp_graph = NVT_INFO['dp_graph'],
        NVT_abspath = os.path.join(work_base_abspath, NVT_addr),
        n_beads = NVT_params['n_beads'],
        n_samples = NVT_params['md_steps'] // NVT_params['xv_stride'],
        temperature = NVT_params['temperature']
    )

    return NVE_INFO

@task()
def NVE_start(NVE_INFO):
    
    work_base_abspath = NVE_INFO['work_base_abspath']

    NVE_params = get_kappa_params(os.path.join(work_base_abspath, 'kappa.json'))['NVE_params']
    NVE_addr = NVE.make_task_from_NVT(NVE_INFO, NVE_params)
    NVE_INFO['NVE_addr'] = NVE_addr

    return NVE_INFO


@task()
def NVE_runs(NVE_INFO):
    
    work_base_abspath = NVE_INFO['work_base_abspath']
    NVE_addr = NVE_INFO['NVE_addr']
    
    N_clients = 4
    
    ipi_md_task_list = [Task(
        command = (
            f"{ENVIRONMENT}i-pi input.xml >& logfile & sleep 5; "
            f"iclient=1; while [ $iclient -le {N_clients} ]; "
            f"do {ENVIRONMENT}client_dp 1234 sample_{i_sample:02} unix ../{NVE_INFO['dp_graph']} pos_bead_00.xyz & "
            "iclient=$((iclient+1)); "
            "done; "
            "wait; echo '********* finish time *********'; date; sleep 1; "
            f"{ENVIRONMENT}calc_J ../{NVE_INFO['dp_graph']} ;"
            ), 
        task_work_path = f'sample_{i_sample:02}',
        forward_files = ['*.xyz', 'input.xml'],
        backward_files = ['simulation.out',
                          'J_array.npy',
                          'x_array.npy',
                          'v_array.npy',
                          'a_array.npy'])
                        for i_sample in range(NVE_INFO['n_samples'])]
    
    submission = get_empty_submission(os.path.join(work_base_abspath, NVE_addr))
    submission.register_task_list(ipi_md_task_list)
    submission.forward_common_files = [NVE_INFO['dp_graph']]
    submission.run_submission(clean=True)
    return NVE_INFO

@task()
def kappa_post_process(NVE_INFO):
    KAPPA.make_task(NVE_INFO)
    work_base_abspath = NVE_INFO['work_base_abspath']

    NVE_params = get_kappa_params(os.path.join(work_base_abspath, 'kappa.json'))['NVE_params']
    time_step = NVE_params['time_step']*NVE_params['xv_stride']
    work_base_abspath = NVE_INFO['work_base_abspath']
    cell_dims = list(map(float, NVE_INFO['cell_dims']))
    cell_vol = cell_dims[0] * cell_dims[1] * cell_dims[2]
    
    temperature = NVE_INFO['temperature']
    kappa_task = Task(
        command = (
            f"{ENVIRONMENT}thermocepstrum-analysis flux_data.npy --input-format dict -V {cell_vol} -T {temperature} -t {time_step} -k zflux -u real -r --FSTAR 1.2 -w 0.5 -o kappa_{temperature}K"
            ), 
        task_work_path = f'kappa_{temperature}K',
        forward_files = ['flux_data.npy'],
        backward_files = [f"kappa_{temperature}K*", 'err', 'log']
    )
    
    submission = get_empty_submission(work_base_abspath)
    submission.register_task(kappa_task)
    submission.run_submission(clean=True)
    return 0

default_args = {
    'owner': 'DeepPotentialUser',
    'start_date': '2021-07-01'
}

@task()
def start_check():
    context = get_current_context()['params']
    START_INFO = dict(
        work_base_abspath=context['work_base_abspath'],
        inputs=context['inputs']
    )
    return START_INFO

@dag(default_args=default_args, schedule_interval = None)
def conductance_ipi_workflow():

    START_INFO = start_check()
    
    NVT_INFO = NVT_start(START_INFO)
    NVE_INFO = NVT_sampling(NVT_INFO)

    return kappa_post_process(NVE_runs(NVE_start(NVE_INFO)))

conductance_dag = conductance_ipi_workflow()
