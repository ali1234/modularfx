import ast
import numpy as np

from nodeeditor.node_scene import Scene

from modularfx.nodes import register_all_nodes
from modularfx.registry import get_node_by_id


class Content:
    def __init__(self, node):
        self.fields = {}
        self.node = node

    def deserializeField(self, field, value):
        self.fields[field] = value

    def readField(self, field):
        x = self.fields[field]
        if x == '':
            x = repr(self.node.sig.parameters[field].default)
            if x == '':
                return None
        return ast.literal_eval(x)

    def readSelect(self, select):
        return self.node.clsgrp[self.fields[select]]


def utos(b):
    return (np.frombuffer(b, dtype=np.uint8)-128).astype(np.int8)


def render(source, max_amplitude):
    return source.to_bytes(22050, byte_width=1, max_amplitude=max_amplitude)


def cli(filename, output):
    register_all_nodes(None, Content)
    scene = Scene()
    scene.setNodeClassSelector(lambda data: get_node_by_id(data['type_name']))
    scene.loadFromFile(filename)
    source = scene.nodes[0].eval()
    pcm = render(source, 0.9)
    output.write(utos(pcm).tobytes())
    import sys
    assert('PyQt5' not in sys.modules)
