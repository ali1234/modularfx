from ._attribute import Attribute, BoundAttribute


class BoundNodeAttribute(BoundAttribute):
    @property
    def eval(self):
        return self._attr._eval.__get__(self._instance)

    @property
    def code(self):
        return self._attr._code.__get__(self._instance)

    @property
    def socket(self):
        return self._instance.socket_for_name(self._attr._name)

    @property
    def connected(self):
        if hasattr(self, 'socket'):
            for e in self.socket.edges:
                other = e.getOtherSocket(self.socket)
                yield other.node, other.index


class NodeAttribute(Attribute):
    _repr_attrs = ['label', 'is_input', 'is_multi', 'socket_type', 'order', 'hidden']
    _bound_type = BoundNodeAttribute
    def __init__(self, /, label=None, socket_type=None, order=0, is_input=False, is_multi=False, hidden=False):
        super().__init__()
        self._label = label
        self._socket_type=socket_type
        self._order = order
        self._is_input=is_input
        self._is_multi=is_multi
        self._hidden=hidden

    @property
    def doc(self):
        return self._eval.__doc__

    @property
    def label(self):
        return self._label

    @property
    def socket_type(self):
        return self._socket_type

    @property
    def order(self):
        return self._order

    @property
    def is_input(self):
        return self._is_input

    @property
    def is_multi(self):
        return self._is_multi

    @property
    def hidden(self):
        return self._hidden

    def _code(self):
        print("Warning: using default _code")
        return '0'

    def _eval(self):
        print("Warning: using default _eval")
        return 0

    def evaluator(self, f):
        self._eval = f
        return self

    def codegen(self, f):
        self._code = f
        return self

    def __repr__(self):
        attrs = ', '.join(f'{a}={repr(getattr(self, a))}' for a in self._repr_attrs)
        return f'{type(self).__name__}({attrs})'

    def __set_name__(self, owner, name):
        super().__set_name__(owner, name)
        if self._label is None:
            self._label = name.title()
