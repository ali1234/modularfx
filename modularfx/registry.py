import inspect
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


def introspect(module, base, filter=None):
    return {
        name: cls for name, cls in module.__dict__.items()
        if (filter is None or name not in filter) and isinstance(cls, type) and issubclass(cls, base)
    }


def register_many(node, content, group, items):
    for name, cls in items.items():
        try:
            register_node(type(name, (node,), {
                'group': group,
                'cls': cls,
                'sig': inspect.signature(cls),
                'NodeContent_class': content
            }))
        except InvalidNodeRegistration:
            pass


def get_node_by_id(id):
    if id not in node_registry: raise OpCodeNotRegistered(f"Node {id} is not registered.")
    return node_registry[id]


from modularfx import nodes

