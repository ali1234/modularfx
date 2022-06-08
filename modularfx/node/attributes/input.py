from functools import reduce
from traceback import print_exc

from ._nodeattribute import NodeAttribute, BoundNodeAttribute


class BoundInput(BoundNodeAttribute):
    def eval(self):
        result = [node.eval(index=index) for node, index in self.connected]
        if self._is_multi:
            print(result)
            if self._reduce:
                if len(result) > 0:
                    return reduce(self._reduce, result)
                else:
                    return None
            else:
                return result
        elif len(result) == 1:
            return result[0]
        elif len(result) == 0:
            return None

    def code(self):
        try:
            result = [node.code(index=index) for node, index in self.connected]
            if self._is_multi:
                result = f'[{", ".join(result)}]'
                if self._reduce:
                    return f'functools.reduce({self._reduce.__module__}.{self._reduce.__name__}, {result})'
                else:
                    return result
            elif len(result) == 1:
                return result[0]
            elif len(result) == 0:
                return None
        except AttributeError:
            print_exc()
            return None


class Input(NodeAttribute):
    _repr_attrs = ['label', 'reduce', 'is_multi', 'socket_type', 'order']
    _bound_type = BoundInput
    def __init__(self, /, label=None, socket_type=0, order=20, is_multi=False, reduce=None):
        super().__init__(label=label, socket_type=socket_type, order=order, is_input=True, is_multi=is_multi, hidden=False)
        self._reduce = reduce

    @property
    def reduce(self):
        return self._reduce
