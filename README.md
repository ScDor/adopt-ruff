# Adopt-Ruff

Adopt [Ruff](https://ruff.rs) in your repo faster 😎

A tool for finding Ruff rules that are not yet configured, and can be added to your repo easily: 

- Rules are already respected in your repository
- Rules that can be automatically fixed by Ruff (see below)
- All other Rules, sorted by the number of violations found in the repository

The output is a markdown report, easily viewed as a Github action summary, as well as CSV files with relevant Rule information per category. 


## Configurations
To decide whether to consider a rule, `adopt-ruff` uses arguments. See below on how to configure them. 

- Ruff considers some new or experimental rules `in preview`. These should be used with caution. You can choose whether `adopt-ruff` considers them or not. Read more about Ruff's preview [here](https://docs.astral.sh/ruff/preview/).
- Ruff supports many autofixable rules - some are always autofixable, and some can only be autofixed by Ruff in specific cases. It's up to you whether to consider "sometimes-autofixable" as autofixable. 

## Usage

### As a Github action (recommended)
Create a yaml file under `.github/workspaces` in your repo, with the following content:

```yaml
name: Adopt Ruff
on: workflow_dispatch

jobs:
  adopt-ruff:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository code
        uses: actions/checkout@v4
      
      - name: Set up python
        id: setup-python
        uses: actions/setup-python@v5
        with: 
          python-version: 3.x
  
      - name: Install ruff 
        run: pip install ruff

      - name: Run the adopt-ruff action
        uses: ScDor/adopt-ruff@master
         
```
Now, manually trigger the workflow from the `Actions` panel of your repository.\
 _Learn more about manually triggering a workflow [here](https://docs.github.com/en/actions/using-workflows/manually-running-a-workflow)._

When the action is done running, head to the [job summary](https://github.blog/wp-content/uploads/2022/05/newjobsummary.png) to watch the report. 

The output tables are also availalbe as CSV files, under `Artifacts`.

Re-run this action to get insights about applicable rules when Ruff updates with more exciting rules ⚡

#### Notes:
- This flow always installs Ruff's latest version. If your project already has Ruff as a dependency (i.e. in `pyproject.toml` or `requirements.txt`), replace the `Install ruff` step with an appropriate command. 

- adopt-ruff calls Ruff, assuming it's installed in the environment. adopt-ruff will fail if ruff is not found. 


#### Arguments
To pass arguments different than the default, use the `with` key. The values mentioned below are the default. Omit any argument to use the default.

```yaml
      - name: Run the adopt-ruff action
        uses: ScDor/adopt-ruff@master
        with:
            path: "."
            repo-name: "" # won't show in report if blank
            config-file-path: "" # will be searched in `path` if empty
            include-preview: True
            include-sometimes-fixable: False
```

### Locally
Install: `pip install git+https://github.com/ScDor/adopt-ruff@master`.\
All arguments can be used with environment variables. Run `adopt-ruff --help` for more information. 


#### Arguments
- `--path`: directory adopt-ruff will search for ruff violations.
- `--ruff-conf-path`: Path to the `pyproject.toml` ,`ruff.toml` or `.ruff.toml`. When not provided, `adopt-ruff` will attempt to seach one of those under `path`. 
- `--sometimes-fixable`: whether to consider sometimes-fixable rules as fixable.
- `--preview`/`--no-preview`: weather to include preview rules.
- `--repo-name`: Will be shown in the output. When not provided, won't be shown.


## Output Example: adopt-ruff report for ScDor/my-dummy-repo (ruff 0.1.13)

## Respected Ruff rules
  
374 Ruff rules are already respected in the repo - they can be added right away 🚀  
<details>
<summary>Details</summary>

| Code     | Name                                         | Fixable   | Preview   | Linter                     |
|----------|----------------------------------------------|-----------|-----------|----------------------------|
| A003     | builtin-attribute-shadowing                  | No        | False     | flake8-builtins            |
| AIR001   | airflow-variable-name-task-id-mismatch       | No        | False     | Airflow                    |
| ASYNC100 | blocking-http-call-in-async-function         | No        | False     | flake8-async               |
| ASYNC101 | open-sleep-or-subprocess-in-async-function   | No        | False     | Perflint                   |
| PERF403  | manual-dict-comprehension                    | No        | True      | Perflint                   |

(table truncated for example purposes)

</details>

## Autofixable Ruff rules
  
65 Ruff rules are violated in the repo, but can be auto-fixed 🪄  
<details>
<summary>Details</summary>

| Code    | Name                                              | Fixable   | Preview   | Linter                |
|---------|---------------------------------------------------|-----------|-----------|-----------------------|
| B010    | set-attr-with-constant                            | Always    | False     | flake8-bugbear        |
| B011    | assert-false                                      | Always    | False     | flake8-bugbear        |
| C401    | unnecessary-generator-set                         | Always    | False     | flake8-comprehensions |

(table truncated for example purposes)

</details>

## Applicable Rules
  
194 other Ruff rules are not yet configured in the repository  
<details>
<summary>Details</summary>

| Code    | Name                                             | Fixable   | Preview   | Linter                     |   Violations |
|---------|--------------------------------------------------|-----------|-----------|----------------------------|--------------|
| PLW0127 | self-assigning-variable                          | No        | False     | Pylint                     |            1 |
| RUF009  | function-call-in-dataclass-default-argument      | No        | False     | Ruff-specific rules        |            1 |
| S314    | suspicious-xml-element-tree-usage                | No        | False     | flake8-bandit              |            1 |
| B005    | strip-with-multi-characters                      | No        | False     | flake8-bugbear             |            1 |
| PTH116  | os-stat                                          | No        | False     | flake8-use-pathlib         |            6 |
| N803    | invalid-argument-name                            | No        | False     | pep8-naming                |            6 |
| UP032   | f-string                                         | Sometimes | False     | pyupgrade                  |            6 |
| B019    | cached-instance-method                           | No        | False     | flake8-bugbear             |            7 |
| B017    | assert-raises-exception                          | No        | False     | flake8-bugbear             |            8 |
| TCH002  | typing-only-third-party-import                   | Sometimes | False     | flake8-type-checking       |            8 |
| PLW1508 | invalid-envvar-default                           | No        | False     | Pylint                     |            9 |
| S607    | start-process-with-partial-path                  | No        | False     | flake8-bandit              |            9 |
| DTZ007  | call-datetime-strptime-without-zone              | No        | False     | flake8-datetimez           |           10 |
| D205    | blank-line-after-summary                         | Sometimes | False     | pydocstyle                 |         2860 |

(table truncated for example purposes)

</details>
  
| Configuration                   | Value   |
|---------------------------------|---------|
| Include sometimes-fixable rules | False   |
| Include preview rules           | True    |