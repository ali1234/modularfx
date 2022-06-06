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
    input = Input(socket_type=2)
    inspect = Slot()

    def print_ast(self, code):
        import ast
        print(ast.unparse(ast.parse(code)))

    def print_black(self, code):
        import black
        print(black.format_str(code, mode=black.mode.Mode()))

    @inspect.evaluator
    def inspect(self):
        print(self.input.code())
