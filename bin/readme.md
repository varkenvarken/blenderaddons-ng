# bin Directory

This directory contains utility scripts and binaries used to support development, testing, and deployment of Blender add-ons in this repository.

## Usage

Place executable scripts and helper tools here.

Scripts in this folder are typically not part of the main add-ons, but are used for project automation or developer convenience.

Typical Contents
- Build scripts
- Deployment helpers
- Project setup scripts

## Scripts

- clone_addon.py

  A utility script that automates creating a new Blender add-on template.
  It works by copying add_ons/example_simple.py to a new file (named after your new add-on in snake_case)
  and updates all relevant names and identifiers inside the file to match your add-on name
  (both in the UI and in the code, handling names with spaces).
  It aint't perfect but does save a lot of typing!
  
  Usage:

  ```bash
  python3 bin/clone_addon.py "My New Addon"
  ```
  This will create add_ons/my_new_addon.py with all references updated for your chosen name.

