import pygame as pg

from traceback import print_exc

from modularfx.node.node import Node
from modularfx.node.attributes import *
from modularfx.node.registry import register_node


@register_node
class Polyphonic(Node):
    group = 'Sinks'
    node_colour = 6
    volume = Parameter(default=0.5, annotation=float)
    sink = Input()
    play = Slot()

    def __init__(self, scene):
        super().__init__(scene)
        self.freq = 44100
        self.size = -16
        self.init_mixer()

    def init_mixer(self):
        pg.mixer.quit()
        pg.mixer.init(self.freq, self.size, 1)

    @play.evaluator
    def play(self):
        try:
            src = self.sink.eval()
            snd = pg.mixer.Sound(src.to_bytes(sample_rate=self.freq, byte_width=2, max_amplitude=self.volume.eval()))
            snd.play()
        except Exception as e:
            print_exc()
