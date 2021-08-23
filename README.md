# DeepFRY workflows
Clone this repository and
```sh
conda develop .
```
dependencies should be installed automatically by conda.

Run `airinit.sh` should initialise airflow and import all the workflows to `~/airflow/dags/` 
```sh
airflow webserver --port <PORT>
```
```sh
airflow scheduler
```
to view the webserver, try ssh tunnel it on local machine, and then open `localhost:8080` on browser.
```sh
ssh -L 8080:localhost:<PORT> <REMOTE_USER>@<REMOTE_HOST>
```

Edit the context `.json` files to match local and remote working paths, and the tests can be run by
```sh
airflow dags trigger conductance_ipi_workflow --conf $(printf "%s" $(cat ice_vii_ipi.json))
```