import numpy as np
from qtpy.QtWidgets import QApplication
from nodeeditor.node_editor_widget import NodeEditorWidget
from nodeeditor.node_socket import Socket
from modularfx.nodes import register_all_nodes
from modularfx.registry import get_node_by_id
from modularfx.graphics import BaseGraphicsNode, BaseContent

sample_rate = 22050


def utos(b):
    return (np.frombuffer(b, dtype=np.uint8)-128).astype(np.int8)


def render(source, max_amplitude):
    return source.to_bytes(sample_rate, byte_width=1, max_amplitude=max_amplitude)


def cli(filename, output):
    app = QApplication([])
    register_all_nodes(BaseGraphicsNode, BaseContent, Socket)
    ed = NodeEditorWidget()
    ed.scene.setNodeClassSelector(lambda data: get_node_by_id(data['type_name']))
    ed.scene.loadFromFile(filename)
    source = ed.scene.nodes[0].eval()
    pcm = render(source, 0.9)
    output.write(utos(pcm).tobytes())
    # TODO: make none of the above require Qt
    import sys
    assert('PyQt5' not in sys.modules)
