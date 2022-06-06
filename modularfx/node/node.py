import inspect

from nodeeditor.node_node import Node as _Node
from nodeeditor.node_socket import LEFT_BOTTOM, RIGHT_BOTTOM

from modularfx.node.meta import Attributes
from modularfx.node.attributes import *


class Node(_Node, metaclass=Attributes):
    icon = None
    group = 'General'
    node_colour = 2

    debug = Slot(socket_type=None)

    @debug.evaluator
    def debug(self):
        """Dump node description and code() for the last output."""
        print(self.describe())
        if len(self.outputs) > 0:
            print(getattr(self, type(self).name_for_index(-1, False)).code())

    def __init__(self, scene=None):
        inputs = [v.socket_type for k, v in type(self).input_sockets()]
        outputs = [v.socket_type for k, v in type(self).output_sockets()]
        self._parameters = {}
        if scene is not None:
            super().__init__(scene, type(self).__name__, inputs, outputs)

    @classmethod
    def describe(cls):
        result = [repr(cls)]
        inputs = cls.input_attrs()
        outputs = cls.output_attrs()
        length = 4 + max((len(k) for k, v in inputs + outputs), default=0)
        fmt = f'{{:>{length}s}} = {{}}'
        if inputs:
            result.append('  Inputs:')
            for k, v in inputs:
                result.append(fmt.format(k, v))
        if outputs:
            result.append('  Outputs:')
            for k, v in outputs:
                result.append(fmt.format(k, v))
        return '\n'.join(result)

    def initSettings(self):
        super().initSettings()
        self.input_socket_position = LEFT_BOTTOM
        self.output_socket_position = RIGHT_BOTTOM

    def getSocketPosition(self, index: int, position: int, num_out_of: int = 1) -> '(x, y)':
        x, y = super().getSocketPosition(index, position, num_out_of)
        if position == LEFT_BOTTOM:
            name = type(self).name_for_index(index, input=True)
            field = self.content.fields[name]
            y = 0.5 + self.grNode.title_height + (
                        field.geometry().height() / 2) + field.geometry().topLeft().y() - self.content.layout.geometry().topLeft().y()
        elif position == RIGHT_BOTTOM:
            name = type(self).name_for_index(index, input=False)
            field = self.content.fields[name]
            y = 0.5 + self.grNode.title_height + (
                        field.geometry().height() / 2) + field.geometry().topLeft().y() - self.content.layout.geometry().topLeft().y()
        return [x, y]

    def onInputChanged(self, socket):
        self.markDirty()
        self.markDescendantsDirty()
        name = type(self).name_for_index(socket.index, input=True)
        if isinstance(getattr(type(self), name), Parameter):
            self.content.hideField(name, socket.hasAnyEdge())

    def socket_for_name(self, name):
        index, input = type(self).index_for_name(name)
        if input:
            return self.inputs[index]
        else:
            return self.outputs[index]

    def output_for_index(self, index):
        return type(self).name_for_index(index, input=False)

    def eval(self, index=0):
        return getattr(self, self.output_for_index(index)).eval()

    def code(self, index=0):
        return getattr(self, self.output_for_index(index)).code()

    @classmethod
    def introspect(cls, nodename=None, output='result', **kwargs):
        def _introspect(f):
            namespace = {}
            for x in ['group', 'node_colour']:
                if x in kwargs:
                    namespace[x] = kwargs.pop(x)
            args = []
            for k, v in inspect.signature(f).parameters.items():
                args.append(k)
                namespace[k] = Parameter(default=v.default, annotation=v.annotation)
            namespace[output] = Output(**kwargs)
            namespace[output].evaluator(
                lambda self: f(**{arg: getattr(self, arg).eval() for arg in args})
            )
            namespace[output].codegen(
                lambda self: f'{f.__module__}.{f.__name__}({", ".join(f"{arg}={getattr(self, arg).code()}" for arg in args)})'
            )
            return type(nodename or f.__name__, (cls,), namespace)

        return _introspect

    @classmethod
    def introspect_many(cls, nodename, choice='type', output='result', **kwargs):
        def _introspect(fs):
            namespace = {}
            for x in ['group', 'node_colour']:
                if x in kwargs:
                    namespace[x] = kwargs.pop(x)
            namespace[choice] = Parameter(default=fs[0][1], socket_type=None)
            args = []
            for k, v in inspect.signature(fs[0][1]).parameters.items():
                args.append(k)
                namespace[k] = Parameter(default=v.default, annotation=v.annotation)
            namespace[output] = Output(**kwargs)
            namespace[output].evaluator(
                lambda self: getattr(self, choice).eval()(**{arg: getattr(self, arg).eval() for arg in args})
            )
            namespace[output].codegen(
                lambda self: f'{getattr(self, choice).eval().__module__}.{getattr(self, choice).eval().__name__}({", ".join(f"{arg}={getattr(self, arg).code()}" for arg in args)})'
            )
            return type(nodename, (cls,), namespace)

        return _introspect