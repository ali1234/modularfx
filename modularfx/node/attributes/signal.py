from ._nodeattribute import NodeAttribute


class Signal(NodeAttribute):
    def __init__(self, /, label=None, socket_type=5, order=0):
        super().__init__(label=label, socket_type=socket_type, order=order, is_input=False, is_multi=True)
