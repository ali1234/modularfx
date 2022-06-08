import inspect
from collections import OrderedDict

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
        print(self._parameters)
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

    def serialize(self):
        data = super().serialize()
        data['type_name'] = self.__class__.__name__
        data['parameters'] = self._parameters
        return data

    def deserialize(self, data: dict, hashmap: dict={}, restore_id: bool=True, *args, **kwargs) -> bool:
        if super().deserialize(data, hashmap, restore_id):
            for k, v in data['parameters'].items():
                attr = getattr(self, k)
                attr.value = attr.deserialize(v)
            return True
        else:
            return False

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
    def _introspect_helper(cls, f, kwargs):
        namespace = OrderedDict()
        for x in ['group', 'node_colour']:
            if x in kwargs:
                namespace[x] = kwargs.pop(x)
        fargs = []
        fkwargs = []
        for k, v in inspect.signature(f).parameters.items():
            if v.kind is v.POSITIONAL_ONLY:
                fargs.append(k)
            else:
                fkwargs.append(k)
            namespace[k] = Parameter(default=v.default, annotation=v.annotation)
        return namespace, fargs, fkwargs

    @classmethod
    def introspect(cls, nodename=None, output='result', **kwargs):
        def _introspect(f):
            namespace, fargs, fkwargs = cls._introspect_helper(f, kwargs)
            namespace[output] = Output(**kwargs)
            namespace[output].evaluator(
                lambda self: f(*[getattr(self, arg).eval() for arg in fargs], **{arg: getattr(self, arg).eval() for arg in fkwargs})
            )
            namespace[output].codegen(
                lambda self: f'{f.__module__}.{f.__name__}({", ".join([f"{getattr(self, arg).code()}" for arg in fargs] + [f"{arg}={getattr(self, arg).code()}" for arg in fkwargs])})'
            )
            return type(nodename or f.__name__, (cls,), namespace)

        return _introspect

    @classmethod
    def introspect_many(cls, nodename, choice='type', output='result', **kwargs):
        def _introspect(fs):
            namespace, fargs, fkwargs = cls._introspect_helper(fs[0][1], kwargs)
            namespace[choice] = ChoiceParameter(fs, default=fs[0][0], socket_type=None)
            namespace.move_to_end(choice, False)
            namespace[output] = Output(**kwargs)
            namespace[output].evaluator(
                lambda self: getattr(self, choice).eval()(*[getattr(self, arg).eval() for arg in fargs], **{arg: getattr(self, arg).eval() for arg in fkwargs})
            )
            namespace[output].codegen(
                lambda self: f'{getattr(self, choice).eval().__module__}.{getattr(self, choice).eval().__name__}({", ".join([f"{getattr(self, arg).code()}" for arg in fargs] + [f"{arg}={getattr(self, arg).code()}" for arg in fkwargs])})'
            )
            return type(nodename, (cls,), namespace)

        return _introspect
