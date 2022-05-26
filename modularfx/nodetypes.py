from functools import reduce
import operator
from traceback import print_exc

from nodeeditor.node_node import Node
from nodeeditor.node_socket import LEFT_BOTTOM, RIGHT_BOTTOM

from modularfx.parameters import ParameterBase


class BaseNode(ParameterBase, Node):
    icon = None
    _f = None

    def __init__(self, scene, name, inputs, outputs):
        super().__init__(scene, name, [2] * len(self.parameters) + inputs, outputs)
        self.markDirty()

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

    def onInputChanged(self, socket):
        self.markDirty()
        self.markDescendantsDirty()
        if socket.index < len(self.parameters):
            self.content.hideField(self.parameters[socket.index].name, socket.hasAnyEdge())

    def args(self):
        args = self.parameters.args()
        for n, (k, v) in enumerate(self.parameters.socket_items()):
            conn = self.getInput(n)
            if conn is not None:
                args[k] = conn.eval()
        return args

    def evalImplementation(self):
        return self._f(**self.args())

    def eval(self, index=0):
        if self.isDirty():
            self.value = self.evalImplementation()
            self.markDirty(False)
        return self.value

    def serialize(self):
        data = super().serialize()
        data['type_name'] = self.__class__.__name__
        data['parameters'] = self.parameters.serialize()
        return data

    def deserialize(self, data, hashmap, restore_id):
        if super().deserialize(data, hashmap, restore_id):
            self.parameters.deserialize(data['parameters'])
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
    group = 'Curves'


class SignalNode(ChainableNode):
    chaintype = 0
    node_colour = 0
    group = 'Signals'

    def __init__(self, scene):
        super().__init__(scene)
        if hasattr(self.content, 'button'):
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
    group = 'Transforms'

    def __init__(self, scene):
        super().__init__(scene)
        self.inputs[-2].is_multi_edges = True

    def evalImplementation(self):
        return reduce(operator.add, (x.eval() for x in self.getInputs(-2))) * super().evalImplementation()


class EffectNode(TransformNode):
    group = 'Effects'


class FilterNode(TransformNode):
    group = 'Filters'
