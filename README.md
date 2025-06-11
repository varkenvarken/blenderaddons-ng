[![Test Status](https://github.com/varkenvarken/blenderaddons-ng/actions/workflows/test_all.yml/badge.svg)](https://github.com/varkenvarken/blenderaddons-ng/actions/workflows/test_all.yml) ![Coverage](coverage.svg)

# blenderaddons-ng

A Visual Studio Code project to develop, test and profile Blender add-ons

## background

I would like to focus a bit more on automated testing of Blender add-ons.
And I am not talking about interactively testing an add-on to see if it does what it should do,
that has its place, but creating and automatically executing unit tests for core functionality in add-ons.

This requires a clean setup and some thinking, and this repository should reflect this setup.

## goals

- [ ] create a repository / Visual Studio Code project for Blender add-ons

  with a folder structure that allows us to maintain multiple add-ons in the same repo

- [ ] suitable for DevContainer development

  so that we can easily change Blender and Python versions.

  Note that we do *not* install the Blender application, but that the goal is to use the stand-alone `bpy` module, so that we can automate testing and profiling.

- [ ] suitable for automated testing

  Both with unittest and coverage in a way we can automate with GitHub actions

- [ ] suitable for profiling

  With the line_profiler package

## folder structure

** work in progress **

- each add-on has its own folder
- if the add-on is a package (i.e. contains an __init__.py file), a .zip file will be created in the toplevel directory packages
- tests are discoverable in the add-on file itself, or if it's package, inside separate files in the add-on folder (possibly in a subfolder)

