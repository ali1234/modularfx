import gensound.curve
import gensound.signals
import gensound.filters
import gensound.effects

import operator

from modularfx.node.node import Node
from modularfx.node.attributes import *
from modularfx.node.registry import register_node


class CurveNode(Node):
    group = 'Curves'
    node_colour = 1
    concat = Input(socket_type=1, is_multi=True, reduce=operator.add)
    result = Output(hidden=True)
    output = Output(socket_type=1)

    @output.evaluator
    def output(self):
        concat = self.concat.eval()
        result = self.result.eval()
        if concat is None:
            return result
        else:
            return concat | result

    @output.codegen
    def output(self):
        concat = self.concat.code()
        result = self.result.code()
        if concat is None:
            return result
        else:
            return f'{concat} | {result}'


class SignalNode(Node):
    group = 'Signals'
    node_colour = 0
    play = Slot()
    concat = Input(socket_type=0, is_multi=True, reduce=operator.add)
    result = Output(hidden=True)
    output = Output(socket_type=0)

    @play.evaluator
    def play(self):
        """Preview the sound up to this node."""
        self.output.eval().play()

    @output.evaluator
    def output(self):
        concat = self.concat.eval()
        result = self.result.eval()
        if concat is None:
            return result
        else:
            return concat | result

    @output.codegen
    def output(self):
        concat = self.concat.code()
        result = self.result.code()
        if concat is None:
            return result
        else:
            return f'{concat} | {result}'


class TransformNode(Node):
    group = 'Transforms'
    node_colour = 3
    play = Slot()
    apply = Input(socket_type=0, is_multi=True, reduce=operator.add)
    concat = Input(socket_type=0, is_multi=True, reduce=operator.add)
    output = Output(socket_type=0)

    @play.evaluator
    def play(self):
        """Preview the sound up to this node."""
        self.output.eval().play()

    @output.evaluator
    def output(self):
        concat = self.concat.eval()
        result = self.result.eval()
        apply = self.apply.eval()
        if concat is None:
            return apply * result
        else:
            return concat | (apply * result)

    @output.codegen
    def output(self):
        concat = self.concat.code()
        result = self.result.code()
        apply = self.apply.code()
        if concat is None:
            return f'({apply} * {result})'
        else:
            return f'{concat} | ({apply} * {result})'


class EffectNode(TransformNode):
    group = 'Effects'


class FilterNode(TransformNode):
    group = 'Filters'


class SinkNode(Node):
    group = 'Sinks'
    node_colour = 6


class TriggerNode(Node):
    group = 'Triggers'
    node_colour = 5


def dir_module(module, base, filter=None):
    return {
        name: cls for name, cls in module.__dict__.items()
        if (filter is None or name not in filter) and isinstance(cls, type) and issubclass(cls, base)
    }


for cls in dir_module(gensound.curve, gensound.curve.Curve, ['Line', 'Logistic', 'Curve', 'CompoundCurve', 'MultiCurve']).values():
    register_node(CurveNode.introspect(hidden=True)(cls))

register_node(CurveNode.introspect_many('Curve', hidden=True)([
    ('Line', gensound.curve.Line),
    ('Logistic', gensound.curve.Logistic),
]))


register_node(SignalNode.introspect_many('Oscillator', hidden=True)(
    list(dir_module(gensound.signals, gensound.signals.Oscillator, ['Oscillator']).items())
))


register_node(SignalNode.introspect_many('Noise', hidden=True)([
    ('Pink', gensound.signals.PinkNoise),
    ('White', gensound.signals.WhiteNoise),
]))


for cls in dir_module(gensound.effects, gensound.effects.Transform, ['Transform']).values():
    register_node(EffectNode.introspect(hidden=True)(cls))


for cls in dir_module(gensound.filters, gensound.filters.Filter, ['Filter']).values():
    register_node(FilterNode.introspect(hidden=True)(cls))


for cls in dir_module(gensound.transforms, gensound.transforms.Transform, ['Transform', 'Convolution']).values():
    register_node(TransformNode.introspect(hidden=True)(cls))
