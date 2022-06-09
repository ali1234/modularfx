import operator
import math

from modularfx.node.node import Node
from modularfx.node.attributes import *
from modularfx.node.registry import register_node


@register_node
@Node.introspect()
def Value(value):
    return value


register_node(Node.introspect_many('Math', choice='operation', socket_type=2)([
    ('Add', operator.add),
    ('Subtract', operator.sub),
    ('Multiply', operator.mul),
    ('Divide', operator.truediv),
    ('Integer Divide', operator.floordiv),
    ('Power', operator.pow),
    ('Log', math.log),
]))


@register_node
class Button(Node):
    group = 'Triggers'
    node_colour = 5
    button = Slot(label='Trigger', socket_type=None)
    trigger = Signal()

    @button.evaluator
    def button(self):
        self.trigger.eval()


@register_node
class Inspector(Node):
    group = 'Sinks'
    node_colour = 6
    input = Input(socket_type=6)
    inspect = Slot()

    def print_ast(self, code):
        import ast
        print(ast.unparse(ast.parse(code)))

    def print_black(self, code):
        import black
        print(black.format_str(code, mode=black.mode.Mode()))

    @inspect.evaluator
    def inspect(self):
        print(self.input.eval())
        print(self.input.code())


@register_node
@Node.introspect('Range')
def _range(start, stop, step=1):
    return range(start, stop, step)


@register_node
class ForEach(Node):
    group = 'General'
    node_colour = 2
    iterable = Input()
    operation = Input(order=0)
    len = Output(socket_type=2, order=0)
    item = Output(socket_type=2)
    index = Output(socket_type=2)
    result = Output()

    def __init__(self, scene):
        super().__init__(scene)
        self._current_item = None
        self._current_index = None

    @len.evaluator
    def len(self):
        return len(self.iterable.eval())

    @item.evaluator
    def item(self):
        return self._current_item

    @index.evaluator
    def index(self):
        return self._current_index

    @result.evaluator
    def result(self):
        results = []
        for n, i in enumerate(self.iterable.eval()):
            self._current_index = n
            self._current_item = i
            results.append(self.operation.eval())
        return results
