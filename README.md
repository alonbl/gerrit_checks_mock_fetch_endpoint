# gerrit-check-mocks Fetch Endpoint

A fetch endpoint to be integrated with [gerrit-checks-mock](https://github.com/alonbl/gerrit-checks-mock) plugin.
The endpoint supports sandbox for testing and GitHub workflow status.

## Usage

```
$ python3 -m gerrit_checks_mock_fetch_endpoint --help
usage: gerrit-checks-mock-fetch-endpoint [-h] [--version] [--log-level LEVEL] [--log-file FILE] [--bind-address ADDR] [--bind-port PORT] --config FILE

Gerrit checks-mock plugin fetch endpoint

options:
  -h, --help           show this help message and exit
  --version            show program's version number and exit
  --log-level LEVEL    Log level CRITICAL, ERROR, WARNING, INFO, DEBUG
  --log-file FILE      Log file to use, default is stdout
  --bind-address ADDR  Bind address
  --bind-port PORT     Bind port
  --config FILE        Configuration file, may be specified multiple times
```

## Configuration File

```ini
[main]
drivers = sandbox, github, bitbucket
log_file =
log_level = INFO
bind_address =
bind_port = 8080
```

### Sandbox Driver

A sandbox is a standalone demo which can be used for debug. No additional
configuration is required.

#### Fetch Endpoint Configuration

```ini
[sandbox]
```

### GitHub Driver


#### Fetch Endpoint Configuration

```ini
[github]
base_url = https://api.github.com/repos/@SPACE@
branch_prefix = @GERRIT_ID@/changes/
repo_format = {project}-ci
timeout = 2
token = @APP_TOKEN@
```

Do not use anonymous access, GitHub blocks requests after a threshold.

The GitHub password must be application password.
* Select your user.
* Select settings.
* Select developer settings
* Select Personal access tokens
  * Generate a new token
  * For replication select Workflow which in turn will also select repo.
  * For query select repository read

#### Gerrit Replication

##### `etc/replication.config`

```ini
[gerrit]
replicateOnStartup = true
autoReload = true
```

##### `etc/replication/github.config`

Replicate the Gerrit changesets as branches in GitHub, this way we
automatically trigger the workflow at replication.

```ini
[remote]
	url = https://github.com/@SPACE@/${name}-ci.git
	push = +refs/heads/*:refs/heads/@GERRIT_ID@/heads/*
	push = +refs/tags/*:refs/tags/@GERRIT_ID@/*
	push = +refs/changes/*:refs/heads/@GERRIT_ID@/changes/*
	projects = @PROJECT1@
	projects = @PROJECT2@
	replicationDelay = 2
```

### BitBucket Driver


#### Fetch Endpoint Configuration

```ini
[bitbucket]
base_url = https://api.bitbucket.org/2.0/repositories/@WORKSPACE@
branch_prefix = @GERRIT_ID@/changes/
repo_format = {project}-ci
timeout = 2
user = @USER@
password = @APP PASSWORD@
```

The BitBucket password must be app password.
* Select your user.
* Select personal settings.
* Select app passwords.
  * Select create app password
  * For replication select repository write
  * For query select pipelines read

#### Gerrit Replication

##### `etc/replication.config`

```ini
[gerrit]
replicateOnStartup = true
autoReload = true
```

##### `etc/replication/bitbucket.config`

Replicate the Gerrit changesets as branches in GitHub, this way we
automatically trigger the workflow at replication.

```ini
[remote]
        url = https://bitbucket.org/@WORKSPACE@/${name}-ci.git
        push = +refs/heads/*:refs/heads/@GERRIT_ID@/heads/*
        push = +refs/tags/*:refs/tags/@GERRIT_ID@/*
        push = +refs/changes/*:refs/heads/@GERRIT_ID@/changes/*
	projects = @PROJECT1@
	projects = @PROJECT2@
        replicationDelay = 2
```

## Build

```sh
$ tox
```

## Generate checks.py

The `checks.py` is generated out of `./polygerrit-ui/app/api/checks.ts` in
Gerrit tree.

The generation is done using `ts2python` but it requires some manual changes.

* Generate the file using:

```sh
sed -e 's/declare //' -e '/^import/d' ../checks.ts > checks-in.ts
./ts2pythonParser.py checks-in.ts
sed -e 's/(Enum)/(str, Enum)/' checks-in.py > checks.py
```

* Add the following the header:

```
# flake8: noqa
# mypy: ignore-errors
# pylint: disable=unused-import, invalid-name, unused-argument, too-few-public-methods
```

* Rework the imports to make it sane, remove requirements of external
  dependencies and duplication due to older python versions.
* Remove unneeded code.
* Replace NotRequired with Optional until python-3.11.

# Debug

```
$ curl -X POST -H "Accept: application/json" -H "Content-Type: application/json" http://localhost:8080/fetch -d '{"project": "test1", "changeId": 122, "revision": 9}'
```
