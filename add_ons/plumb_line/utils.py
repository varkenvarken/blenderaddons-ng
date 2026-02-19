# SPDX-FileCopyrightText: © 2016 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

# utilities useful for all kind of add-ons

from importlib import reload as _reload_module
from sys import modules

def get_package_name():
    return __name__.split(".")[0]

def reload(package: str) -> None:
    # print(f"{__name__=}")
    prefix = f"{package}."  # note the dot, we only want to reload modules, not the packageitself (i.e. not __init__.py)
    reload_needed = [
        mod for name, mod in modules.items() if name.startswith(prefix)
    ]  # can´t modify this dict in place, so we gather the mods first, then reload them later (which will alter modules)
    # print(f"{reload_needed=}")
    for mod in reload_needed:
        print(f"reloading {mod.__name__}")
        _reload_module(mod)
