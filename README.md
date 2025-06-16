![Blenderaddons ng logo](docs/Blenderaddons%20ng%20logo%20small.png)
![Blender](blender-version.svg) ![Python](python.svg) [![Test Status](https://github.com/varkenvarken/blenderaddons-ng/actions/workflows/test_all.yml/badge.svg)](https://github.com/varkenvarken/blenderaddons-ng/actions/workflows/test_all.yml) ![Coverage](coverage.svg)

# blenderaddons-ng

A Visual Studio Code project to develop, test, and profile Blender add-ons

## background

I would like to focus a bit more on automated testing of Blender add-ons.
And I am not talking about interactively testing an add-on to see if it does what it should do,
that has its place, but creating and automatically executing unit tests for core functionality in add-ons.

This requires a clean setup and some thinking, and this repository should reflect this setup.

The name of the repo reflects that this is (sort of) intended as the `next generation` of the add-ons in the [blenderaddons repo](https://github.com/varkenvarken/blenderaddons), although I do not intend to port everything over.

## goals

- [x] Create a repository / Visual Studio Code project for Blender add-ons

  With a folder structure that allows us to maintain multiple add-ons in the same repo

- [x] suitable for DevContainer development

  so that we can easily change Blender and Python versions.

  Note that we do not install the Blender application; the goal is to use the stand-alone `bpy` module to automate testing and profiling. Also, although DevContainer sounds VS Code-specific, it isn´t, as we actually work based on a Dockerfile that can be used to build and deploy independently of VS Code.

- [x] suitable for automated testing

  Both with `pytest` and `pytest-coverage` in a way we can automate with GitHub actions as well. The configuration that is currently implemented works both with VSCode test discovery as well as in [the automated test workflow](.github/workflows/test_all.yml) in GitHub actions.

- [x] suitable for profiling

  With the `line_profiler` package. See [below](#profiling) for details.

- [x] suitable for benchmarking

  With the `pytest-benchmark` package. See [below](#benchmarking) for details.

- [ ] Move some addons over from the [blenderaddons repo](https://github.com/varkenvarken/blenderaddons)

  - first one done: [select_colinear_edges.py](add_ons/select_colinear_edges.py)   (but tests are not complete yet)

## folder structure

- All add-on code lives in `/add-ons`
- If the add-on is a package (i.e., contains an __init__.py file), it should be in its own subfolder
  
  (A .zip file will be created in the toplevel directory `/packages` **not yet implemented**)

- tests are located in the `/tests` folder

  They should have a name starting with `test_` and should contain `pytest` discoverable tests

## installation

```bash
git clone https://github.com/varkenvarken/blenderaddons-ng.git
cd ./blenderaddons-ng
```

Just open the folder in VS Code. It will probably prompt you, but you can also explicitly call Rebuild Container from 
the command palette and then start developing inside it. 

## requirements

The [Dockerfile](Dockerfile) creates a Ubuntu 24.04 image with all binary dependencies for Blender installed.
It also installs downloads and compiles the exact Python version that the current version of Blender comes bundled with
(This may take some time because compiling is CPU-intensive.)

It does *not* install Blender, but installs the `bpy` module from Pypi. This allows us to run the add-ons headless.
It also installs/upgrades the packages mentioned in [requirements.txt](requirements.txt), or, as is the case with `numpy`,
*downgrades* it to the version bundled with Blender. Other notable packages it installs are:

- **fake-bpy-module** so that we get nice type checking in vscode, but see pyproject.toml file because we needed to
  disable the invalid type form warning. This is because the pylance/pyright people insist that the Blender implementation
  of properties is wrong, which it isn´t: They seem to forget that annotations are for more than type hinting.
  See [here for more info](https://github.com/microsoft/pylance-release/issues/5457#issuecomment-1937101627).
  If you are annoyed by this, you can disable typechecking altogether by adding `typeCheckingMode = "off"` to your pyproject.toml file

- **pytest-cov** for creating test coverage reports; pytest itself is installed by VS Code when creating the container

- **pytest-benchmark** for creating benchmarks (See: [benchmarking](#benchmarking))

- **line_profiler** to provide line-by-line profiling (See: [profiling](#profiling))

## workflow

1. Copy add_ons/example_simple.py to add_ons/<new_name>.py

  It provides a good starting point for simple add-ons

2. Change the code to your liking

  Don´t forget to update the `bl_info` dictionary and to define the `OPERATOR_NAME` variable (that is used in the test script)

3. copy tests/test_example_simple.py to tests/test_<new_name>.py

  And make sure to create good tests that ensure good coverage as well.

## profiling

The file [example_simple.py](add_ons/example_simple.py) contains code showing how to profile (parts of) an operator using the 
[line-profiler package](https://pypi.org/project/line-profiler/).

No profiling is done if the package isn´t available or if the LINE_PROFILE environment variable is not set to "1". 
To create a profile, simply run:

```bash
LINE_PROFILE=1 python3 add_ons/example_simple.py
```

It will produce output like:

```
Timer unit: 1e-09 s

Total time: 8.615e-06 s
File: /workspaces/blenderaddons-ng/add_ons/example_simple.py
Function: do_execute at line 44

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    44                                               @profile  # type: ignore (if line_profiler is available)
    45                                               def do_execute(self, context: Context) -> None:
    46                                                   """Expensive part is moved out of the execute method to allow profiling.
    47                                           
    48                                                   Note that no profiling is done if line_profiler is not available or
    49                                                   if the environment variable `LINE_PROFILE` is not set to "1".
    50                                                   """
    51         1       1031.0   1031.0     12.0          obj: Object | None = context.active_object
    52         1       7584.0   7584.0     88.0          obj.location.x += self.amount  # type: ignore (because of the poll() method that ensures obj is not None)
```

Note: you cannot profile the `execute()` method directly, so you would typically factor out expensive code and profile just that. If you don´t, i.e. apply the `@profile` decorator directly to the `execute()` method, the `register_class()` function will complain:

```
ValueError: expected Operator, MESH_OT_select_colinear_edges class "execute" function to have 2 args, found 0
```

## benchmarking

Profiling is not the same as benchmarking, of course, so support for the [pytest-benchmark package](https://pytest-benchmark.readthedocs.io/en/latest/) was added.

The file [test_example_simple.py](tests/test_example_simple.py) provides an example benchmark, and all benchmarks are stored in the `.benchmarks` directory.

I have opted to put them in .gitignore because you wouldn't usually need to save them.

Benchmarks are excluded from the normal runs and are also not part of the [automated workflow](.github/workflows/test_all.yml) because they sometimes cause VS Code to hang. So, a VS Code task `Run benchmarks` is configured to run all benchmarks.

Comparing two runs is done on the command line:

```bash
pytest-benchmark compare 0001 0002
```

## contributing

I am happy to review pull requests with improvements or even complete new add-ons. Just make sure:
- The code is yours,
- is licensed under GPL v3 or later,
- runs on the current Blender version (see label at top of this file),
- and comes with extensive test coverage

## what about AI?
<img src="https://raw.githubusercontent.com/varkenvarken/blenderaddons-ng/refs/heads/main/docs/brainrot.svg" alt="Brainrot warning" width="150">

I have mixed feelings about AI. On the one hand, it can save time if you quickly want to cobble up some code, but on the other hand, if you don't have experience writing the code yourself, it is difficult to create a good prompt or review the generated code. Also, LLMs are quick in creating a unit test for a function, but in test-driven development, that is the wrong way around! And unit tests are not just about code that works; they also should test functionality, exceptions, or edge cases. But since it cannot guess the functional requirements (or 'intentions'), it tends to generate poor tests.

However, they can be used quite effectively to write a quick starter that you can then expand on. After all, it's often easier when you don't have to start from a blank slate. This is true for unit tests as well as new functions. Asking to write a function that does something specific is often quicker than looking it up and implementing the code from scratch. I documented my try at this in [this blog article](https://blog.michelanders.nl/2025/05/httpsblog.michelanders.nl202505select-colinear-edges-vibe-coding-a-blender-addon.html).

Another thing LLMs are good at is summarizing: you can quickly create docstrings or even a webpage [the webpage for this repo](https://varkenvarken.github.io/blenderaddons-ng/) was created with the help of GitHub CoPilot based on the readme. I still had to check the text, but it came formatted with HTML and CSS, saving a huge amount of time (the logo was added later). 

So, use AI or not? Yes, but sparingly, and verify the results! And please have a good look at the coding style: the LLM probably has seen tons of example code that illustrates a specific bit of functionality, but wasn't particularly focused on code quality. And yes, that is a friendly way to say it often produces beginner code that will be hard to maintain. It also tends to be liberal with comments that describe what the code is doing (which can already be known by looking at the code) instead of describing its intent or providing references (which can be useful when you encounter logic bugs). So yeah, call its code unpythonic if you like 😃
