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

this is done by adding the following to [launch.json](/.vscode/launch.json):

```json

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

## DevContainer
