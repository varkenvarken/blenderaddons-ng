There a several parts of this project that need Vscode specific configuration to work optimally.

All these can be found in the [.vscode](/.vscode) folder.

## testing

We use `pytest` and want autodiscovery of tests, so we set the `pytestEnabled` property to `true`.

We also want to measure coverage so we define `pytestArgs` to:
- look only in the `add_ons` directory
- generate a coverage report in xml format
- autosave any benchmarks we generate, which is not needed, because we...
- skip any benchmarks (see [below](#benchmarking) for where that is configured
 
[settings.json](/.vscode/settings.json)
```json
{
    "python.testing.pytestArgs": [
        "tests", "--cov=add_ons", "--cov-report=xml", "--benchmark-autosave", "--benchmark-skip"
    ],
    "python.testing.unittestEnabled": false,
    "python.testing.pytestEnabled": true
}
```

## debugging tests

With the current settings autodiscovery, coverage and performing the tests works, 
but if we also want be able to debug any tests interactively with the Python debugger
we need to disable coverage during debugging otherwise breakpoints simply won't trigger.

This is done by adding the following to [launch.json](/.vscode/launch.json):

```json
{
  "version": "0.2.0",
  
  "configurations": [{
  "name": "Python: Debug Tests",
  "type": "python",
  "request": "launch",
  "program": "${file}",
  "purpose": ["debug-test"],
  "console": "integratedTerminal",
  "justMyCode": true,
  "env": {"PYTEST_ADDOPTS": "--no-cov"} // coverage messes up breakpoints, see: https://code.visualstudio.com/docs/python/testing#_pytest-configuration-settings
 }]
}

```

## benchmarking

Benchmarking was excluded from the regular test discovery because they may take longer to run and we need them
only infrequently. So to run all benchmarks we created a [task](/.vscode/tasks.json). Every time we perform it
we only run the benchmarks and autosave them:


```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Run benchmarks",
            "type": "shell",
            "command": "pytest tests --benchmark-autosave --benchmark-only "
        }
    ]
}
```

## profiling

For profiling we don´t change anything in the Vscode config, as we simply run the add-on to profile from the command line. For example:

```bash
LINE_PROFILE=1 python3 add_ons/select_colinear_edges.py
python3 -m line_profiler -rtmz profile_output.lprof
```

## DevContainer

The DevContainer we work in is based on the [Dockerfile](/Dockerfile) we provide ourselves:

[devcontainer.json](/.devcontainer/devcontainer.json)

```json
{
	"name": "Existing Dockerfile",
	"build": {
		// Sets the run context to one level up instead of the .devcontainer folder.
		"context": "..",
		// Update the 'dockerFile' property if you aren't using the standard 'Dockerfile' filename.
		"dockerfile": "../Dockerfile"
	}
}
```

## dependencies

Any pytest / coverage / benchmark dependencies are listed in [requirements.txt](/requirements.txt)

