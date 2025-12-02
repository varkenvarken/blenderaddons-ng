![Blenderaddons ng logo](docs/Blenderaddons%20ng%20logo%20small.png)
[![Blender](docs/blender-version.svg)](https://www.blender.org/download/releases/4-4/) ![Python](docs/python.svg) [![Test Status](https://github.com/varkenvarken/blenderaddons-ng/actions/workflows/test_all.yml/badge.svg)](https://github.com/varkenvarken/blenderaddons-ng/actions/workflows/test_all.yml) ![Coverage](docs/coverage.svg)

# blenderaddons-ng

A Visual Studio Code project to develop, test, and profile Blender add-ons.

## background

I would like to focus a bit more on automated testing of Blender add-ons.
And I am not talking about interactively testing an add-on to see if it does what it should do,
that has its place, but creating and automatically executing unit tests for core functionality in add-ons.

This requires a clean setup and some thinking, and this repository should reflect this setup.

The name of the repo reflects that this is (sort of) intended as the `next generation` of the add-ons in the [blenderaddons repo](https://github.com/varkenvarken/blenderaddons), although I do not intend to port everything over.


## additional information

More information can be found on the [website for this repo](https://varkenvarken.github.io/blenderaddons-ng/). Here you will find more on the goals, dependencies and the workflow to setup things for a new add-on.

I have also written some blog articles that provide some background information and show this repo in action:

- [New blenderaddons repo aimed at developers](https://blog.michelanders.nl/2025/06/new-blenderaddons-repository-aimed-at-developers.html)
- [Colinearity tests in Blender meshes using Numpy](https://blog.michelanders.nl/2025/06/Colinearity-tests-in-Blender-meshes-using-Numpy.html)
- [Automatic unit tests for Blender add-ons](https://blog.michelanders.nl/2025/06/automatic-unit-tests-for-blender-add-ons.html)
- [Stonework - A Blender add-on to create stone walls](https://blog.michelanders.nl/2025/06/stonework-blender-add-on-to-create-stone-walls.html)
- [Efficient Vertex Manipulation in Blender with NumPy](https://blog.michelanders.nl/2025/10/efficient-vertex-manipulation-inblender-with-numpy.html)
- [Performance of numpy operations in Blender](https://blog.michelanders.nl/2025/10/perfornce-of-umpy-operations-in-blender.html)
- [How to profile a Blender add-on](https://blog.michelanders.nl/2025/10/how-to-profile-blender-add-on.html)

## contributing

I am happy to review pull requests with improvements or even complete new add-ons. Just make sure:
- The code is yours,
- is licensed under GPL v3 or later,
- runs on the current Blender version (see label at top of this file),
- and comes with extensive test coverage
