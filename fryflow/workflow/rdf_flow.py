import shutil, os, ast, logging

import numpy as np
import matplotlib.pyplot as plt

from airflow.decorators import dag, task
from airflow.operators.python import get_current_context

from dpdispatcher import Submission, Task, Resources, Machine

in_lammps_template = """
variable ibead uloop 32 pad
units metal
atom_modify map yes
read_data data.${ibead}
pair_style deepmd {dp_graph}
pair_coeff * *
timestep {time_step}

fix 1 all nve
fix 2 all langevin {temperature} {temperature} {damp} {seed}

thermo_style custom step temp ke pe etotal 
thermo {thermo_steps}
thermo_modify norm no
dump dcd all custom {dump_steps} ${ibead}.xyz id x y z vx vy vz
dump_modify dcd sort id 
compute myrdf all rdf {N_bins} {rdf_combs}
fix 3 all ave/time {rdf_steps} 1 {rdf_steps} c_myrdf[*] file {out_rdf} mode vector

run {md_steps}
"""

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
def load_test_params():
    context = get_current_context()['params']

    inputs = context['inputs']
    atoms = context['atoms']
    params = context['params']
    outputs = context['outputs']

    for key in params.keys():
        params[key] = ast.literal_eval(params[key])

    work_base_abspath = inputs['work_base_abspath']

    md_rdf_dir = os.path.join(inputs['work_base_abspath'], 'md_rdf_')
    
    i = 0
    while os.path.isdir(md_rdf_dir+f'{i:02}'):
        i+=1
    md_rdf_dir+=f'{i:02}'
    os.mkdir(md_rdf_dir)

    MD_INFO = dict(work_base_abspath = work_base_abspath, md_rdf_dir= md_rdf_dir, inputs = ['in.lammps'], params = params, outputs = outputs, atoms = atoms)

    for file_type in ['dp_graph', 'data']:
        file_name = inputs[file_type]
        file_abspath = os.path.join(work_base_abspath, file_name)
        assert(os.path.isfile(file_abspath)), f'input file {file_name} required by lammps not found at {work_base_abspath}.'
        shutil.copyfile(file_abspath, os.path.join(md_rdf_dir, file_name))
        MD_INFO['inputs'].append(file_name)

    rdf_combs = ""
    for i in range(len(atoms)):
        for j in range(i+1):
            rdf_combs += f"{i+1} {j+1} "

    with open(os.path.join(md_rdf_dir, 'in.lammps'),  "x") as in_lammps:
        in_lammps_content = in_lammps_template.format(
            ibead = '{ibead}',
            seed = '323432',
            dp_graph = inputs['dp_graph'],
            time_step = params['time_step'],
            md_steps = params['md_steps'],
            temperature = params['temperature'],
            damp = params['damp'],
            dump_steps = params['dump_steps'],
            thermo_steps = params['thermo_steps'],
            rdf_steps = params['rdf_steps'],
            N_bins = params['N_bins'],
            out_rdf = outputs['out_rdf'],
            rdf_combs = rdf_combs
        )
        in_lammps.write(in_lammps_content)

    return MD_INFO

@task(trigger_rule = 'none_failed_or_skipped')
def md_sampling(MD_INFO):

    md_rdf_task = Task(
        command = 'mpirun -np 1 /home/ubuntu/anaconda3/envs/dp-dev/bin/lmp -in in.lammps -p 1x1 -log log -screen screen', 
        task_work_path = './',
        forward_files = MD_INFO['inputs'],
        backward_files = [
            'log',
            MD_INFO['outputs']['out_rdf']
        ])
    
    submission = get_empty_submission(MD_INFO['md_rdf_dir'])
    submission.register_task(md_rdf_task)
    submission.run_submission(clean=True)
    return MD_INFO

@task()
def md_end(MD_INFO):
    
    params = MD_INFO['params']
    atoms = MD_INFO['atoms']
    outputs = MD_INFO['outputs']

    n_elements = len(atoms)

    SAVEPATH = os.path.join(MD_INFO['work_base_abspath'], outputs['out_rdf_plot'])

    RDF_SAMPLES = params['md_steps']//params['rdf_steps'] + 1

    data=[]
    with open(os.path.join(MD_INFO['md_rdf_dir'], outputs['out_rdf']), "r") as f:
        for i in range(3):
            f.readline()
        for i in range(RDF_SAMPLES):
            f.readline()
            for j in range(params['N_bins']):
                data.append(f.readline().split())

    data=np.array(data, dtype="float").reshape(-1, params['N_bins'], 2 + n_elements*(n_elements+1) )

    fig, ax = plt.subplots(figsize=(10, 7.5), facecolor="white")

    ax.set_title("Radial Distribution Functions", fontsize=16)

    ax.set_xlabel("Distance / Angstrom", fontsize=16)
    ax.set_ylabel("$g(r)$", fontsize=16)

    ax.tick_params(axis='both', which='major', labelsize=16)
    
    for i in range(n_elements):
        for j in range(i+1):
            ax.plot(data[0, :, 1], data[:, :, (i+j+1)*2].mean(axis=0), label=f"{atoms[i]}-{atoms[j]}")

    ax.legend(fontsize=16)

    plt.savefig(SAVEPATH)

    return SAVEPATH


default_args = {
    'owner': 'team23',
    'start_date': '2021-07-01'
}

@dag(default_args=default_args, schedule_interval = None)
def rdf_workflow():   

    return md_end(md_sampling(load_test_params()))

r_dag = rdf_workflow()