import os
import numpy as np

def autocorr(x):
    """
    Calculates the physically meaningful autocorrelation of an one-dimensional array
    """
    N = len(x)
    result = np.correlate(x, x, mode='full')
    z = result[result.size // 2:] / - np.arange(-N, 0)
    return z[:N]

def vel_auto(velocities, alpha):
    """
    Calculates the velocity autocorrelation function of 
    """
    corrs = np.empty((velocities.shape[1], velocities.shape[0]))
    for iatom in range(NVE_INFO['N_atoms']):
        icorr = autocorr(velocities[:, iatom, alpha])
        icorr = icorr/icorr[0]
        corrs[iatom] = icorr
    corrs = np.array(corrs)
    return corrs

def test_ts_erranalysis(test_ts, work_base_abspath):
    J_cor = np.empty((len(test_ts), 30))
    i = 0
    for i_test in test_ts:
        J_array = np.load(os.path.join(work_base_abspath, f"test_{i_test}fs", 'J_array.npy'))
        J_cor[i] = autocorr(J_array[:2000, 2])[:30]
        i += 1
    
    factors = np.abs(J_cor - J_cor[0].reshape(1, -1))/J_cor[0].reshape(1, -1)**2
    ave = np.average(factors, axis=1)
    rmse = np.sqrt(np.average(np.square(factors - ave.reshape(-1, 1) ), axis = 1))
    
    return test_ts, ave, rmse