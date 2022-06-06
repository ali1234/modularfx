import pkgutil
import importlib
from traceback import print_exc
from collections import defaultdict

node_registry = {}
node_groups = defaultdict(dict)

class ConfException(Exception): pass
class InvalidNodeRegistration(ConfException): pass
class OpCodeNotRegistered(ConfException): pass


def register_node(cls):
    if cls.__name__ in node_registry:
        raise InvalidNodeRegistration(f"Duplicate node registration of {cls.__name__}.")
    node_registry[cls.__name__] = cls
    node_groups[cls.group][cls.__name__] = cls
    return cls


def get_node_by_id(type_name):
    if type_name not in node_registry:
        raise OpCodeNotRegistered(f"Node {type_name} is not registered.")
    return node_registry[type_name]


import modularfx.lib

missing = []

# Load all the implementations dynamically.
for loader, module_name, is_pkg in pkgutil.walk_packages(modularfx.lib.__path__, modularfx.lib.__name__ + '.'):
    # We don't need to import anything from the modules. We just need to load them.
    try:
        importlib.import_module(module_name, modularfx.lib.__name__)
    except ImportError as e:
        missing.append(e)
        print_exc()

if missing:
    print('Some node types were not registered due to import errors:')
    for e in missing:
        print('   ', e.args[0])
