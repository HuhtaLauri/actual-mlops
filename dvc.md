 # DVC

## Setup

```sh
dvc init
dvc remote add -d actual-mlops s3://my-bucket/
dvc remote modify --local actual-mlops access_key_id 'mysecret'
dvc remote modify --local actual-mlops secret_access_key 'mysecret'
# If using non-AWS S3 store
dvc remote modify actual-mlops endpointurl http://s3host
# Also to automatically keep dvc on track with git, i recommend setting autostage
dvc config core.autostage true
```

## Workflow

1. Create branch
2. Write code 
3. Execute code
4. dvc add /data/dir/
5. git add && git commit
6. dvc push
7. git push


## Operations

### Add
```sh
# File
dvc add data/data.json
# Directory
dvc add data/
```


