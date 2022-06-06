from collections import OrderedDict

from modularfx.node.attributes._nodeattribute import NodeAttribute


class Attributes(type):
    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        try:
            cls.__node_meta = cls.__node_meta.copy()
        except AttributeError:
            cls.__node_meta = OrderedDict()
        for k, v in attrs.items():
            if isinstance(v, NodeAttribute):
                cls.__node_meta[k] = v

    def all_attrs(cls):
        return sorted(((k, v) for k, v in cls.__node_meta.items()), key=lambda i: i[1].order)

    def input_attrs(cls):
        return sorted(((k, v) for k, v in cls.__node_meta.items() if v.is_input), key=lambda i: i[1].order)

    def output_attrs(cls):
        return sorted(((k, v) for k, v in cls.__node_meta.items() if not v.is_input), key=lambda i: i[1].order)

    def input_sockets(cls):
        for k, v in cls.input_attrs():
            if v.socket_type is not None and not v.hidden:
                yield k, v

    def output_sockets(cls):
        for k, v in cls.output_attrs():
            if v.socket_type is not None and not v.hidden:
                yield k, v

    def name_for_index(cls, index, input):
        if input:
            return list(cls.input_sockets())[index][0]
        else:
            return list(cls.output_sockets())[index][0]

    def index_for_name(cls, name):
        for n, (k, v) in enumerate(cls.input_sockets()):
            if k == name:
                return n, True
        for n, (k, v) in enumerate(cls.output_sockets()):
            if k == name:
                return n, False
        raise NameError(name)
