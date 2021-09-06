# airflow 基本用法

```bash
airflow dags trigger <WORFLOW> --conf $(printf "%s" $(cat <CONTEXT_FILE>))
```

for example, to calculate rdf, go to the directory where ice_vii_md.json is in
```
airflow dags trigger rdf_workflow --conf $(printf "%s" $(cat ice_vii_md.json))
```