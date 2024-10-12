 # DVC

Currently tracking dvc remotes per data source (commits, repos)
Possibly using raw, staging, prod in the future
 -> Not using data source specific remotes can get tricky with data validation


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

### Set up cache
```sh
sudo mkdir -p /home/shared/dvc-cache
sudo chown -R $USER:$USER /home/shared/dvc-cache/
```

### Migrate existing cache
```sh
sudo mkdir -p /home/shared/dvc-cache
mv .dvc/cache/* /home/shared/dvc-cache

sudo find /home/shared/dvc-cache -type d -exec chmod 0775 {} \;
sudo find /home/shared/dvc-cache -type f -exec chmod 0444 {} \;
sudo chown -R myuser:ourgroup /home/shared/dvc-cache/
```

### Github Actions runner set-up checklist
- Install Github CLI
- Open firewall for storages
- Set up cache
- Install jq

