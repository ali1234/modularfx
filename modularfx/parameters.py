import inspect
from typing import Union


class ParamAttr:
    def __init__(self, store, param):
        self._param = param
        self._store = store

    @property
    def name(self):
        return self._param._name

    @property
    def type(self):
        return self._param._type

    @property
    def is_set(self):
        return self._param._name in self._store._values

    @property
    def is_socket(self):
        return self._param._socket

    @property
    def default(self):
        return self._param._default

    @property
    def value(self):
        try:
            return self._store._values[self._param._name]
        except KeyError:
            return self.default

    def set(self, value):
        self._store._values[self._param._name] = value
        if self._store._node.content is not None:
            self._store._node.content.fields[self._param._name].setText(repr(value))

    def clear(self):
        if self._param._name in self._store._values:
            del self._store._values[self._param._name]

    def deserialize(self, value):
        self.set(value)


class ChoiceParamAttr(ParamAttr):
    def set(self, value):
        self._store._values[self._param._name] = self._param._reverse_choices[value]
        if self._store._node.content is not None:
            select = self._store._node.content.fields[self._param._name]
            select.setCurrentIndex(select.findData(value))

    def deserialize(self, value):
        self.set(self._param._choices[value])

    @property
    def value(self):
        try:
            return self._param._choices[self._store._values[self._param._name]]
        except KeyError:
            return self.default

    @property
    def choices(self):
        return self._param._choices


class Parameter:
    AttrType = ParamAttr
    def __init__(self, default, type, socket=True):
        self._default = default
        self._type = type
        self._socket = socket

    def __set_name__(self, node_type, name):
        self._name = name

    def __get__(self, node, objtype):
        return self.AttrType(node, self)


class ChoiceParameter(Parameter):
    AttrType = ChoiceParamAttr
    def __init__(self, default, choices, socket=False):
        super().__init__(default, object, socket)
        self._choices = choices
        self._reverse_choices = {v: k for k, v in choices.items()}


class ParameterStore:
    _f = None
    _keys = []
    _socket_keys = []

    def __init__(self, node):
        self._values = {}
        self._node = node

    def deserialize(self, data):
        self._values = {}
        for k, v in data.items():
            getattr(self, k).deserialize(v)

    def serialize(self):
        return {k: v for k, v in self._values.items()}

    def __call__(self):
        return self.__class__._f(**self.args())

    def __iter__(self):
        return self.keys()

    def __len__(self):
        return len(self._socket_keys)

    def __getitem__(self, n):
        return getattr(self, self._socket_keys[n])

    def keys(self):
        yield from self._keys

    def items(self):
        for k in self._keys:
            yield (k, getattr(self, k))

    def socket_keys(self):
        yield from self._socket_keys

    def socket_items(self):
        for k in self._socket_keys:
            yield (k, getattr(self, k))

    def args(self):
        return {k: v.value for k, v in self.items()}

    @classmethod
    def extend(cls, params, name='Parameters'):
        socket_keys = [k for k, v in params.items() if v._socket]
        return type(name, (cls,), {
                '_keys': params.keys(),
                '_socket_keys': socket_keys,
                **params
        })

    @classmethod
    def install(cls, node_type, **kwargs):
        def _factory(f):
            params = {}
            for k, v in inspect.signature(f).parameters.items():
                if k in kwargs:
                    params[k] = ChoiceParameter(next(iter(kwargs[k])), kwargs[k])
                else:
                    params[k] = Parameter(v.default, v.annotation)

            return type(f.__name__, (node_type,), {
                '_f': f, 'Parameters': cls.extend(params)
            })

        return _factory

    @classmethod
    def install_combo(cls, name, node_type, callables, **kwargs):
        n, f = next(iter(callables.items()))
        params = {
            'type': ChoiceParameter(f, callables)
        }
        for k, v in inspect.signature(f).parameters.items():
            if k in kwargs:
                params[k] = ChoiceParameter(next(iter(kwargs[k])), kwargs[k])
            else:
                params[k] = Parameter(v.default, v.annotation)

        return type(name, (node_type,), {
            '_f': property(lambda self: lambda type, **kwargs: self.parameters.type.value(**kwargs)),
            'Parameters': cls.extend(params)
        })


class ParameterBase:
    Parameters = ParameterStore

    @property
    def parameters(self) -> ParameterStore:
        if not hasattr(self, '_parameters'):
            self._parameters = self.Parameters(self)
        return self._parameters
