#!/home/ubuntu/anaconda3/envs/thermo/deepmd-kit-2.0b3-gpu/bin/python
import os
import sys
import driver
import numpy as np
from deepmd.infer import DeepPot as DP

eV2J = 1.60217662E-19
eV2H = 1.60217662E-19/4.35974417e-18
eV_p_A2J_p_m = eV2J * 1E10
def format_print_2dmat(A, n, tag='', fn=None, format='%15.6f'):
    if fn is None:
        ofile = sys.stdout
    else:
        ofile = open(fn, 'w')
    print('--- %s ---'%tag, file=ofile)
    for i in range(n):
        print((format+format+format)%(A[i,0],A[i,1],A[i,2]), file=ofile)
    if fn is not None:
        ofile.close()
    return

# make a complete molecule, in PBC, stupid openMM does not find the closest periodic image for bonding interactions
def make_mol_whole(positions, topology, box, box_inv, atom_mapping=None):
    positions_ref = np.zeros(positions.shape)
    for res in topology.residues():
        indices = np.array([a.index for a in res.atoms()])
        # shift reference
        positions_ref[indices] = positions[indices[0]]
    dr = positions - positions_ref
    ds = dr.dot(box_inv)
    ds = ds - np.floor(ds+0.5)
    dr = ds.dot(box)
    if atom_mapping is None:
        atom_mapping = np.arange(len(positions))
    positions[atom_mapping] = positions_ref[atom_mapping] + dr[atom_mapping]
    return positions


class DeepmdDriver(driver.BaseDriver):

    def __init__(self, port, addr, socktype, dpgraphfile, conf_filename = "init.xyz"):
        self.dp = DP(dpgraphfile)
        conf_file = open(conf_filename, "r")
        a_type = []
        for line in conf_file:
            words = line.split()
            if len(words) == 4:
                if words[0] == 'O' or words[0] == 'OW':
                    a_type.append(0)
                elif words[0] == 'H' or words[0] == 'HW1' or words[0] == 'HW2':
                    a_type.append(1)
        self.a_type = np.array(a_type)
        driver.BaseDriver.__init__(self, port, addr, socktype)
        return

    def grad(self, crd, cell):
        pos = np.array(crd*1e10) # convert to angstrom
        box = np.array(cell*1e10)      # convert to angstrom
        e, f, v = self.dp.eval(pos, box, self.a_type)
        e = e[0] * eV2J
        f = f[0] *  eV_p_A2J_p_m
        v = v[0].reshape([3,3]) * eV2H
        #print(v,  file=open('dump', 'a'))
        ### do the unit transfer
        return e, f, v

if __name__ == '__main__':
    addr = sys.argv[2]
    port = sys.argv[1]
    socktype = sys.argv[3]
    dpgraphfile = sys.argv[4]
    conf_filename = sys.argv[5]
    driver_deepmd = DeepmdDriver(port, addr, socktype, dpgraphfile, conf_filename)
    while True:
        driver_deepmd.parse()
