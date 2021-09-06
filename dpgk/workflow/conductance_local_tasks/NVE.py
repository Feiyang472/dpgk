import os, shutil
from pathlib import Path

from dpgk.workflow.conductance_local_tasks import NVE_in_ipi_template, bead_init_line

def make_task_from_NVT(NVE_INFO, NVE_params):
    
    NVT_abspath = NVE_INFO['NVT_abspath']
    n_beads = NVE_INFO['n_beads']
    dp_graph = NVE_INFO['dp_graph']
    
    root = Path(NVT_abspath).parent.absolute()

    NVT_addr = os.path.relpath(NVT_abspath, root)

    NVE_addr = 'NVE_from_'+NVT_addr

    NVE_abspath = os.path.join(root, NVE_addr)

    os.mkdir(NVE_abspath)
    
    shutil.copyfile(os.path.join(NVT_abspath, dp_graph), os.path.join(NVE_abspath, dp_graph))

    with open(os.path.join(NVT_abspath, f"simulation.pos_00.xyz"), "r") as posfile:
        poslines = posfile.readlines()
    N_atoms = int(poslines[0])
    if 'CELL' in poslines[1]:
        cell_info = poslines[1].split()
        cell_dims = cell_info[2:5]
    else:
        raise RuntimeWarning('Cell information not found on second line.')
    n_samples = len(poslines) // (N_atoms+2) - 1
    
    assert n_samples == NVE_INFO['n_samples'], f"{n_samples}, {NVE_INFO['n_samples']}"
    
    NVE_INFO['cell_dims'] = cell_dims
    
    for i_sample in range(n_samples):
        os.mkdir(os.path.join(NVE_abspath, f'sample_{i_sample:02}'))
        
        with open(os.path.join(NVE_abspath, f"sample_{i_sample:02}", "input.xml"), "x") as in_ipi:
            in_ipi.write(
                NVE_in_ipi_template.format(
                    **NVE_params,
                    MD_addr = f"sample_{i_sample:02}",
                    n_beads = n_beads,
                    bead_init = "".join([bead_init_line.format(i_bead = i_bead) for i_bead in range(n_beads)])
                )
            )

    for i_bead in range(n_beads):
        with open(os.path.join(NVT_abspath, f"simulation.pos_{i_bead:02}.xyz"), "r") as posfile:
            poslines = posfile.readlines()

        with open(os.path.join(NVT_abspath, f"simulation.vel_{i_bead:02}.xyz"), "r") as velfile:
            vellines = velfile.readlines()

        for i_sample in range(n_samples):
            with open(os.path.join(NVE_abspath, f"sample_{i_sample:02}/pos_bead_{i_bead:02}.xyz"), "x") as posframe:
                posframe.writelines(poslines[(i_sample+1)*(N_atoms+2): (i_sample+2)*(N_atoms+2)])
            
            with open(os.path.join(NVE_abspath, f"sample_{i_sample:02}/vel_bead_{i_bead:02}.xyz"), "x") as velframe:
                velframe.writelines(vellines[(i_sample+1)*(N_atoms+2): (i_sample+2)*(N_atoms+2)])
    

    NVE_INFO['N_atoms'] = N_atoms
    return NVE_addr