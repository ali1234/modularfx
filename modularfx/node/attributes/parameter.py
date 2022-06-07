import inspect

from ._nodeattribute import NodeAttribute, BoundNodeAttribute


class BoundParameter(BoundNodeAttribute):
    @property
    def value(self):
        try:
            return self._instance._parameters[self._attr._name]
        except KeyError:
            if self._attr._default is not inspect._empty:
                return self._attr._default
            else:
                return ValueError(f"Parameter '{self._attr._name}' is not set and has no default.")

    @value.setter
    def value(self, value):
        self._instance._parameters[self._attr._name] = value

    @value.deleter
    def value(self):
        try:
            del self._instance._parameters[self._attr._name]
        except KeyError:
            pass

    @property
    def is_set(self):
        return self._attr._name in self._instance._parameters

    def eval(self):
        if self.socket_type is not None:
            try:
                node, index = next(self.connected)
                return node.eval(index)
            except StopIteration:
                return self.value
        else:
            return self.value

    def code(self):
        if self.socket_type is not None:
            try:
                node, index = next(self.connected)
                return node.code(index)
            except StopIteration:
                return repr(self.value)
        else:
            return repr(self.value)


class Parameter(NodeAttribute):
    _repr_attrs = ['label', 'default', 'annotation', 'socket_type', 'order']
    _bound_type = BoundParameter

    def __init__(self, /, label=None, default=inspect._empty, annotation=inspect._empty, socket_type=2, order=10):
        super().__init__(label=label, socket_type=socket_type, order=order, is_multi=False, is_input=True)
        self._default = default
        self._annotation = annotation

    @property
    def default(self):
        return self._default

    @property
    def annotation(self):
        return self._annotation


class BoundChoiceParameter(BoundParameter):
    @property
    def value(self):
        return self._forward[BoundParameter.value.__get__(self)]

    @value.setter
    def value(self, value):
        BoundParameter.value.__set__(self, self._reverse[value])

    @value.deleter
    def value(self):
        BoundParameter.value.__delete__(self)

class ChoiceParameter(Parameter):
    _bound_type = BoundChoiceParameter

    def __init__(self, choices, /, label=None, default=inspect._empty, annotation=inspect._empty, socket_type=2, order=10):
        super().__init__(label=label, default=default, annotation=annotation, socket_type=socket_type, order=order)
        self._forward = {k: v for k, v in choices}
        self._reverse = {v: k for k, v in choices}

