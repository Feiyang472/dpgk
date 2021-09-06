# DPGK (Deep potential Green-Kubo transport property workflows)

## Requirements
DPGK performs simple, short calculations locally (or on the login node), and puts molecular dynamics simulations on the remote machine (or the compute node) via `dpdispatcher`. 

## Installation
Clone this repository and do
```sh
pip install -e dpgk
```
Then, run `airinit.sh` to initialise airflow and import all the workflows to `~/airflow/dags/`. 

Include the files in `remote_xcutables` in your remote bin, and make them executable.

## Quick start
To calculate the thermal conductivity and the phonon density of states for your system, first fill in a json file which contains 
1. list of temperatures
2. number of beads in ring-polymer
3. time step sizes to test integrator divergence rates
4. file names of a **trained** Deep Potential graph, and a initial structure.
```json
{
    "work_base_abspath": "/your/work/path/",
    "temperature_list": [78],
    "n_beads": 32,
    "test_ts": [0.2],
    "inputs":{
        "dp_graph": "graph10_c.pb",
        "initial_state": "init.xyz"
    },
    "machine": {
        "batch_type": "Shell",
        "context_type": "SSHContext",
        "local_root": "/your/work/path/",
        "remote_root": "/tour/remote/root/",
        "remote_profile": {
            "hostname": "xx.xx.xx",
            "username": "user",
            "password": "password"
        }
    },    
    "resources":{
        "number_node": 1,
        "cpu_per_node": 1,
        "gpu_per_node": 1,
        "queue_name": "dpgk_test_0",
        "group_size": 1
    }
}
```
See [dpdispatcher documentation](https://github.com/deepmodeling/dpdispatcher) for details of `machine` and `resources` specification. You may need `source_list` to activate the appropriate environment. On machines where this doesn't work, edit the `ENVIRONMENT` variable at the top of your workflow file.

Start an airflow scheduler
```sh
airflow scheduler
```
and 'trigger' the dpgk_workflow with your parameters.
```sh
airflow dags trigger dpgk_workflow --conf $(printf "%s" $(cat YOURJSON.json))
```

To view your workflow progress on the graphical webserver, try ssh tunnel it on local machine, and then open `localhost:8080` in your browser.
```sh
airflow webserver --port <PORT>
ssh -L 8080:localhost:<PORT> <REMOTE_USER>@<REMOTE_HOST>
```