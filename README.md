![Blender](blender-version.svg) ![Python](python.svg) [![Test Status](https://github.com/varkenvarken/blenderaddons-ng/actions/workflows/test_all.yml/badge.svg)](https://github.com/varkenvarken/blenderaddons-ng/actions/workflows/test_all.yml) ![Coverage](coverage.svg)

# blenderaddons-ng

A Visual Studio Code project to develop, test and profile Blender add-ons

## background

I would like to focus a bit more on automated testing of Blender add-ons.
And I am not talking about interactively testing an add-on to see if it does what it should do,
that has its place, but creating and automatically executing unit tests for core functionality in add-ons.

This requires a clean setup and some thinking, and this repository should reflect this setup.

The name of the repo reflects that this is (sort of) intended as the `next generation` of the add-ons in the [blenderaddons repo](https://github.com/varkenvarken/blenderaddons), although I do not intend to port everything over.

## goals

- [x] create a repository / Visual Studio Code project for Blender add-ons

  with a folder structure that allows us to maintain multiple add-ons in the same repo

- [x] suitable for DevContainer development

  so that we can easily change Blender and Python versions.

  Note that we do *not* install the Blender application, but that the goal is to use the stand-alone `bpy` module, so that we can automate testing and profiling. Also, although DevContainer sounds vscode specific, it isn´t as we actually work
  based on a Dockerfile that can be used to build and deploy independently of vscode.

- [x] suitable for automated testing

  Both with pytest and coverage in a way we can automate with GitHub actions as well. The configuration that is currently
  implemented works both with vscode test discovery as well as in [the automated test workflow](.github/workflows/test_all.yml) in GitHub actions.

- [ ] suitable for profiling

  With the line_profiler package

## folder structure

- all add-on code lives in `/add-ons`
- if the add-on is a package (i.e. contains an __init__.py file), it should be in its own subfolder
  
  (a .zip file will be created in the toplevel directory `/packages` **not yet implemented**)

- tests are located in the `/tests` folder

  they should have a name starting with `test_` and should contain `pytest` discoverable tests

## installation

```bash
git clone https://github.com/varkenvarken/blenderaddons-ng.git
cd ./blenderaddons-ng
```

The just open the folder in vscode. It will probably prompt you, but you can also explicitely call Rebuild Container from 
the command palette and then start developing inside it. 

## requirements

The [Dockerfile](Dockerfile) creates a Ubuntu 24.04 image with all binary dependencies for Blender installed.
It also install downloads and compiles the exact Python version that the current version of Blender comes bundled with
(this may take some time because compiling is cpu intensive).

It does *not* install Blender, but installs the `bpy` module from Pypi. This allows us to run the add-ons headless.
It also install/upgrades the packages mentioned in [requirements.txt](requirements.txt), or, as is the case with `numpy`, *downgrades* it to the version bundled with Blender. Other notable packages it installs are:
- fake-bpy-module (so that we get nice type checking in vscode)
- pytest-cov (for creating test coverage reports; pytest itself is installed by vscode when creating the container)


## workflow

1. copy add_ons/example_simple.py to add_ons/<new_name>.py

  it provides a good starting point for simple add-ons

2. change the code to your liking

  don´t forget to update the `bl_info` dictionary and to define the `OPERATOR_NAME` variable (that is used in the test script)

3. copy tests/test_example_simple.py to tests/test_<new_name>.py

  and make sure to create good tests which ensure good coverage as well.

## contributing

I am happy to review pull requests with improvements or even complete new add-ons. Just make sure:
- the code is yours,
- is licensed GPL v3 or later,
- runs on the current Blender version (see label at top of this file),
- and comes with extensive test coverage


