from functools import reduce
import inspect
import operator
from traceback import print_exc

from nodeeditor.node_node import Node
from nodeeditor.node_socket import LEFT_BOTTOM, RIGHT_BOTTOM

from modularfx.node.parameters import ParameterBase


class UI(type):
    def __init__(cls, name, bases, attrs):
        super().__init__(cls)
        cls.buttons = getattr(cls, 'buttons', {}).copy()
        for k, v in attrs.items():
            if callable(v) and hasattr(v, 'label'):
                cls.buttons[v.label] = k

    @classmethod
    def button(cls, label, socket=True):
        def _button(f):
            f.label = label
            f.socket = socket
            return f
        return _button


class BaseNode(ParameterBase, Node, metaclass=UI):
    icon = None
    _f = None
    buttons = {}

    def __init__(self, scene, inputs, outputs):
        n_buttons = len(list(filter(lambda b: getattr(self, b).socket, self.buttons.values())))
        super().__init__(scene, self.__class__.__name__, [5] * n_buttons + [2] * len(self.parameters) + inputs, outputs)
        # triggers are multi
        for socket in self.inputs + self.outputs:
            if socket.socket_type == 5:
                socket.is_multi_edges = True
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
        index = socket.index - len(self.buttons)
        if 0 <= index < len(self.parameters):
            self.content.hideField(self.parameters[index].name, socket.hasAnyEdge())

    def args(self):
        args = self.parameters.args()
        for n, (k, v) in enumerate(self.parameters.socket_items()):
            conn, index = self.getInputWithSocketIndex(n + len(self.buttons))
            if conn is not None:
                args[k] = conn.eval(index)
        return args

    def code_args(self, index=0):
        args = self.parameters.args()
        for n, (k, v) in enumerate(self.parameters.socket_items()):
            conn, index = self.getInputWithSocketIndex(n + len(self.buttons))
            if conn is not None:
                args[k] = conn.code(index)
        return {k: v for k, v in args.items() if v is not inspect._empty}

    def code_format(self, f, **kwargs):
        return '{}.{}({})'.format(
            f.__module__,
            f.__name__,
            ', '.join(f'{k} = {v}' for k, v in kwargs.items())
        )

    def code_impl(self, index=0):
        if callable(self._f):
            return self.code_format(self._f, **self.code_args(index))
        else:
            return ''

    def code(self, index=0):
        return self.code_impl(index)

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


class GeneralNode(BaseNode):
    group = 'General'
    node_colour = 2

    def __init__(self, scene):
        super().__init__(scene, [], [2])

    def code(self, index=0):
        return repr(self.eval(index))


class ChainableNode(BaseNode):
    inputtypes = []
    chaintype = 0

    def __init__(self, scene):
        super().__init__(scene, self.inputtypes + [self.chaintype], [self.chaintype])

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

    def code(self, index=0):
        i = [x.code() for x in self.getInputs(-1)]
        if len(i) > 1:
            chain = '(' + ' + '.join(i) + ') | '
        elif len(i) == 1:
            chain = i[0] + ' | '
        else:
            chain = ''
        return chain + self.code_impl(index)


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
        self.inputs[-1].is_multi_edges = True

    @UI.button('Play')
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

    def code_impl(self, index=0):
        chain = [x.code() for x in self.getInputs(-2)]
        if len(chain) > 0:
            chain = '(' + ' + '.join(chain) + ') * '
        else:
            chain = ''
        return chain + super().code_impl()


class EffectNode(TransformNode):
    group = 'Effects'


class FilterNode(TransformNode):
    group = 'Filters'


class SinkNode(BaseNode):
    inputtypes = [0]
    node_colour = 6
    group = 'Sinks'

    def __init__(self, scene):
        super().__init__(scene, self.inputtypes, [])
        self.inputs[-1].is_multi_edges = True

    def evalImplementation(self):
        return reduce(operator.add, (x.eval() for x in self.getInputs(-2)))


class TriggerNode(BaseNode):
    node_colour = 5
    group = 'Triggers'

    def __init__(self, scene, outputs=None):
        if outputs is None:
            outputs = []
        self.output_names = outputs
        super().__init__(scene, [], [5] + ([2]*len(self.output_names)))

    def trigger(self):
        for e in self.outputs[0].edges:
            node = e.end_socket.node
            index = e.end_socket.index
            cb = list(node.buttons.values())[index]
            getattr(node, cb)()