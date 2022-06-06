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
        del self._instance._parameters[self._attr._name]

    @property
    def is_set(self):
        return self._attr._name in self._instance._parameters

    def eval(self):
        return self.value

    def code(self):
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
