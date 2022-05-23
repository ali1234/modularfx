from functools import reduce
import operator
from traceback import print_exc

from nodeeditor.node_node import Node
from nodeeditor.node_socket import LEFT_TOP, LEFT_CENTER, LEFT_BOTTOM, RIGHT_BOTTOM


class BaseNode(Node):
    icon = None

    def __init__(self, scene, name, inputs, outputs):
        self.inputmap = {}
        if hasattr(self, 'sig'):
            auto_inputs = []
            for n,(k,v) in enumerate(self.sig.parameters.items()):
                self.inputmap[n] = k
                self.inputmap[k] = n
                auto_inputs.append(2)
                print(n, k)
            inputs = auto_inputs + inputs
        super().__init__(scene, name, inputs, outputs)
        self.markDirty(True)

    def initSettings(self):
        super().initSettings()
        self.input_socket_position = LEFT_BOTTOM
        self.output_socket_position = RIGHT_BOTTOM

    def getSocketPosition(self, index: int, position: int, num_out_of: int=1) -> '(x, y)':
        x, y = super().getSocketPosition(index, position, num_out_of)
        if position == LEFT_BOTTOM:
            field = self.content.inputs[index]
            y = 0.5 + self.grNode.title_height + (field.geometry().height()/2) + field.geometry().topLeft().y() - self.content.layout.geometry().topLeft().y()
        elif position == RIGHT_BOTTOM:
            field = self.content.outputs[index]
            y = 0.5 + self.grNode.title_height + (field.geometry().height()/2) + field.geometry().topLeft().y() - self.content.layout.geometry().topLeft().y()
        return [x, y]

    def onInputChanged(self, socket=None):
        self.markDirty()
        self.markDescendantsDirty()
        if socket.index in self.inputmap:
            self.content.hideField(self.inputmap[socket.index], socket.hasAnyEdge())

    def onOutputChanged(self, socket=None):
        self.markDirty()
        self.markDescendantsDirty()

    def extract(self):
        args = {}
        for n, k in enumerate(self.sig.parameters.keys()):
            conn = self.getInput(n)
            if conn is None:
                args[k] = self.content.readField(k)
            else:
                args[k] = conn.eval()
        return args

    def evalImplementation(self):
        if hasattr(self, 'clsgrp'):
            return self.content.readSelect('type')(**self.extract())
        else:
            return self.cls(**self.extract())

    def eval(self, index=0):
        if self.isDirty():
            self.value = self.evalImplementation(index)
            self.markDirty(False)
        return self.value

    def serialize(self):
        data = super().serialize()
        data['type_name'] = self.__class__.__name__
        print(self.content.fields.keys())
        print(self.sig.parameters.keys())
        data['content_data'] = {
            field: self.content.serializeField(field) for field in self.content.fields.keys()
        }
        return data

    def deserialize(self, data, hashmap, restore_id):
        if super().deserialize(data, hashmap, restore_id):
            for k, v in data.get('content_data', {}).items():
                self.content.deserializeField(k, v)
            return True
        else:
            return False


class ChainableNode(BaseNode):
    inputtypes = []
    chaintype = 0

    def __init__(self, scene):
        super().__init__(scene, self.__class__.__name__, self.inputtypes + [self.chaintype], [self.chaintype])

    def chain(self, s):
        i = self.getInputs(-1)
        if i:
            s = reduce(operator.add, (x.eval() for x in i)) | s
        return s

    def eval(self, index=0):
        if self.isDirty():
            self.value = self.chain(self.evalImplementation())
            self.markDirty(False)
        return self.value


class CurveNode(ChainableNode):
    chaintype = 1
    node_colour = 1

class SignalNode(ChainableNode):
    chaintype = 0
    node_colour = 0

    def __init__(self, scene):
        super().__init__(scene)
        self.content.button.pressed.connect(self.onPlay)
        self.inputs[-1].is_multi_edges = True

    def onPlay(self):
        try:
            self.eval().play()
        except Exception as e:
            self.markDescendantsDirty()
            self.grNode.setToolTip(str(e))
            print_exc()


class TransformNode(SignalNode):
    inputtypes = [0]
    node_colour = 3

    def __init__(self, scene):
        super().__init__(scene)
        self.inputs[-2].is_multi_edges = True

    def evalImplementation(self):
        return reduce(operator.add, (x.eval() for x in self.getInputs(-2))) * super().evalImplementation()
