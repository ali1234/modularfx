from modularfx.basenode import *
from modularfx.registry import register_node, register_many, register_combined, introspect

import gensound.curve
import gensound.signals
import gensound.filters
import gensound.effects


def register_all_nodes(graphic, content, socket):

    register_many(
        CurveNode, graphic, content, socket, 'Curves',
        introspect(gensound.curve, gensound.curve.Curve, ['Curve', 'Line', 'Logistic', 'CompoundCurve', 'MultiCurve'])
    )

    register_combined(
        CurveNode, graphic, content, socket, 'Curves', 'Curve',
        {
            'Line': gensound.curve.Line,
            'Logistic': gensound.curve.Logistic,
        }
    )

    register_combined(
        SignalNode, graphic, content, socket, 'Signals', 'Oscillator',
        introspect(gensound.signals, gensound.signals.Oscillator, ['Oscillator'])
    )

    register_combined(
        SignalNode, graphic, content, socket, 'Signals', 'Noise',
        {
            'Pink': gensound.signals.PinkNoise,
            'White': gensound.signals.WhiteNoise,
        }
    )

    register_many(
        TransformNode, graphic, content, socket, 'Effects',
        introspect(gensound.effects, gensound.effects.Transform, ['Transform'])
    )

    register_many(
        TransformNode, graphic, content, socket, 'Filters',
        introspect(gensound.filters, gensound.filters.Filter, ['Filter'])
    )

    register_many(
        TransformNode, graphic, content, socket, 'Transforms',
        introspect(gensound.transforms, gensound.transforms.Transform, ['Transform'])
    )
