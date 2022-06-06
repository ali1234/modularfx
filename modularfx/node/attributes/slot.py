from ._nodeattribute import NodeAttribute


class Slot(NodeAttribute):
    _repr_attrs = ['label', 'socket_type', 'order', 'hidden']
    def __init__(self, /, label=None, socket_type=5, order=0, hidden=False):
        super().__init__(label=label, socket_type=socket_type, order=order, is_input=True, is_multi=True, hidden=hidden)
