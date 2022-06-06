from ._nodeattribute import NodeAttribute, BoundNodeAttribute


class Output(NodeAttribute):
    def __init__(self, /, label=None, socket_type=0, order=20, hidden=False):
        super().__init__(label=label, socket_type=socket_type, order=order, is_input=False, is_multi=True, hidden=hidden)
