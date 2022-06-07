from ._nodeattribute import NodeAttribute, BoundNodeAttribute


class BoundSignal(BoundNodeAttribute):
    def eval(self):
        for node, index in self.connected:
            getattr(node, type(node).name_for_index(index, True)).eval()



class Signal(NodeAttribute):
    _bound_type = BoundSignal
    def __init__(self, /, label=None, socket_type=5, order=0):
        super().__init__(label=label, socket_type=socket_type, order=order, is_input=False, is_multi=True)
