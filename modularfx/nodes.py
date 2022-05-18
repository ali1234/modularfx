from modularfx.basenode import *
from modularfx.registry import register_node, register_many, register_combined, introspect

import gensound.curve
import gensound.signals
import gensound.filters
import gensound.effects


register_many(
    CurveNode, IntrospectedContent, 'Curves',
    introspect(gensound.curve, gensound.curve.Curve, ['CompoundCurve', 'MultiCurve'])
)

register_combined(
    SignalNode, PlayableIntrospectedContent, 'Signals', 'Oscillator',
    introspect(gensound.signals, gensound.signals.Oscillator, ['Oscillator'])
)

register_many(
    SignalNode, PlayableIntrospectedContent, 'Signals',
    {
        'Pink Noise': gensound.signals.PinkNoise,
        'White Noise': gensound.signals.WhiteNoise,
    }
)

register_many(
    TransformNode, PlayableIntrospectedContent, 'Effects',
    introspect(gensound.effects, gensound.effects.Transform, ['Transform'])
)

register_many(
    TransformNode, PlayableIntrospectedContent, 'Filters',
    introspect(gensound.filters, gensound.filters.Filter, ['Filter'])
)

register_many(
    TransformNode, PlayableIntrospectedContent, 'Transforms',
    introspect(gensound.transforms, gensound.transforms.Transform, ['Transform'])
)


@register_node
class Mix(SignalNode):
    group = 'Utilities'
    NodeContent_class = PlayableContent
    inputtypes = [0, 0]

    def evalImplementation(self, index):
        s = self.getInput(0).eval() + self.getInput(1).eval()
        return self.chain(s)


