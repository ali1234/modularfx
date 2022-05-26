from modularfx.parameters import ParameterStore
from modularfx.nodetypes import *
from modularfx.registry import register_node

import gensound.curve
import gensound.signals
import gensound.filters
import gensound.effects


def introspect(module, base, filter=None):
    return {
        name: cls for name, cls in module.__dict__.items()
        if (filter is None or name not in filter) and isinstance(cls, type) and issubclass(cls, base)
    }


for name, cls in introspect(gensound.curve, gensound.curve.Curve, ['Curve', 'Line', 'Logistic', 'CompoundCurve', 'MultiCurve']).items():
    register_node(ParameterStore.install(CurveNode)(cls))

register_node(ParameterStore.install_combo('Curve', CurveNode, {
        'Line': gensound.curve.Line,
        'Logistic': gensound.curve.Logistic,
    }))

register_node(ParameterStore.install_combo('Oscillator', SignalNode, introspect(gensound.signals, gensound.signals.Oscillator, ['Oscillator'])))

register_node(ParameterStore.install_combo('Noise', SignalNode, {
        'Pink': gensound.signals.PinkNoise,
        'White': gensound.signals.WhiteNoise,
    }))

for name, cls in introspect(gensound.effects, gensound.effects.Transform, ['Transform']).items():
    register_node(ParameterStore.install(EffectNode)(cls))

for name, cls in introspect(gensound.filters, gensound.filters.Filter, ['Filter']).items():
    register_node(ParameterStore.install(FilterNode)(cls))

for name, cls in introspect(gensound.transforms, gensound.transforms.Transform, ['Transform', 'Convolution']).items():
    register_node(ParameterStore.install(TransformNode)(cls))
