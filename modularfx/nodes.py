from modularfx.basenode import *
from modularfx.registry import register_node, register_many, register_combined, introspect

import gensound.curve
import gensound.signals
import gensound.filters
import gensound.effects


register_many(
    CurveNode, BaseContent, 'Curves',
    introspect(gensound.curve, gensound.curve.Curve, ['Curve', 'Line', 'Logistic', 'CompoundCurve', 'MultiCurve'])
)

register_combined(
    CurveNode, BaseContent, 'Curves', 'Curve',
    {
        'Line': gensound.curve.Line,
        'Logistic': gensound.curve.Logistic,
    }
)

register_combined(
    SignalNode, BaseContent, 'Signals', 'Oscillator',
    introspect(gensound.signals, gensound.signals.Oscillator, ['Oscillator'])
)

register_combined(
    SignalNode, BaseContent, 'Signals', 'Noise',
    {
        'Pink': gensound.signals.PinkNoise,
        'White': gensound.signals.WhiteNoise,
    }
)

register_many(
    TransformNode, BaseContent, 'Effects',
    introspect(gensound.effects, gensound.effects.Transform, ['Transform'])
)

register_many(
    TransformNode, BaseContent, 'Filters',
    introspect(gensound.filters, gensound.filters.Filter, ['Filter'])
)

register_many(
    TransformNode, BaseContent, 'Transforms',
    introspect(gensound.transforms, gensound.transforms.Transform, ['Transform'])
)


@register_node
class Mix(SignalNode):
    group = 'Utilities'
    NodeContent_class = BaseContent
    inputtypes = [0, 0]

    def evalImplementation(self, index):
        s = self.getInput(0).eval() + self.getInput(1).eval()
        return self.chain(s)


