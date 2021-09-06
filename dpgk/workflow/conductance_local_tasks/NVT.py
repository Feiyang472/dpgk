import os, shutil

from dpgk.workflow.conductance_local_tasks import NVT_in_ipi_template

def make_task(work_base_abspath, NVT_params, inputs):
    """
    Creates subdirectory for NVT job
    inputs:
        work_base_abspath
        NVT_params
        inputs
    returns: 
        NVT_addr
    """

    NVT_addr = f"NVT_{NVT_params['temperature']}K_"

    i = 0
    while os.path.isdir(os.path.join(work_base_abspath, NVT_addr+f'{i:02}')):
        i+=1
    NVT_addr+=f'{i:02}'
    NVT_dir = os.path.join(work_base_abspath, NVT_addr)
    os.mkdir(NVT_dir)

    NVT_params['md_steps'] = (NVT_params['NVE_samples']) * NVT_params['xv_stride']
    del NVT_params['NVE_samples']
    with open(os.path.join(NVT_dir, 'input.xml'),  "x") as in_ipi:
        in_ipi.write(
            NVT_in_ipi_template.format(
                DYNAMICS = 'nvt',
                **NVT_params,
                MD_addr = NVT_addr,
                initial_state = inputs['initial_state']
            )
        )

    for file_name in list(inputs.values()):
        file_abspath = os.path.join(work_base_abspath, file_name)
        assert(os.path.isfile(file_abspath)), f'input file {file_name} required by ipi not found at {work_base_abspath}.'
        shutil.copyfile(file_abspath, os.path.join(work_base_abspath, NVT_addr, file_name))

    return NVT_addr
