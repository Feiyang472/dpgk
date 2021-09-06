import os
from dpgk.workflow.conductance_local_tasks import NVE
import numpy as np

def make_task(NVE_INFO):
    temperature = NVE_INFO['temperature']
    n_samples = NVE_INFO['n_samples']
    work_base_abspath = NVE_INFO['work_base_abspath']
    NVE_addr = NVE_INFO['NVE_addr']

    zflux_all = None
    
    for i_sample in range(n_samples):
        J_array = np.load(
            os.path.join(work_base_abspath, NVE_addr, f'sample_{i_sample:02}', 'J_array.npy')
        )
        if zflux_all is None:
            zflux_all = np.empty((J_array.shape[0], n_samples))
        zflux_all[:, i_sample] = J_array[:, 2]
    
    os.mkdir(os.path.join(work_base_abspath, f'kappa_{temperature}K'))    
    np.save(os.path.join(work_base_abspath, f'kappa_{temperature}K', 'flux_data.npy'), {'zflux': zflux_all}, allow_pickle=True)
    
    return temperature