import rtmidi

from modularfx.node.node import Node
from modularfx.node.attributes import *
from modularfx.node.registry import register_node


@register_node
class MIDI(Node):
    group = 'Triggers'
    node_colour = 5

    def __init__(self, scene):
        super().__init__(scene)
        self.midiin = rtmidi.MidiIn()
        self.midiin.open_port(0, "ModularFX")
        self.midiin.set_callback(self.onMidi)
        self.markDirty()
        self._note = 69

    def onMidi(self, event, data):
        message, time = event
        if message[0] == 144 and message[2] > 0:
            self._note = message[1]
            self.markDirty()
            self.markDescendantsDirty()
            self.trigger.eval()

    trigger = Signal()

    note = Output(socket_type=2)

    @note.evaluator
    def note(self):
        return self._note

    @note.codegen
    def note(self):
        return repr(self._note)

    frequency = Output(socket_type=2)

    @frequency.evaluator
    def frequency(self):
        return 440 * (2**((self._note-69)/12))

    @frequency.codegen
    def frequency(self):
        return repr(440 * (2**((self._note-69)/12)))
