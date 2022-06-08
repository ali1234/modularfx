import solid
import solid.objects

import atexit
import operator
import os
import subprocess
import tempfile

from modularfx.node.node import Node
from modularfx.node.attributes import *
from modularfx.node.registry import register_node


openscad_subprocess = None
openscad_temp_file = None


def cleanup_subprocess():
    global openscad_subprocess
    if openscad_subprocess is not None:
        openscad_subprocess.kill()
        openscad_subprocess.wait()


def ensure_subprocess():
    global openscad_subprocess, openscad_temp_file
    if openscad_temp_file is None:
        openscad_temp_file = tempfile.NamedTemporaryFile(suffix='.scad', dir='/home/al/', delete=True)
        atexit.register(cleanup_subprocess)
    if openscad_subprocess is None or openscad_subprocess.poll() is not None: # or if it exited
        openscad_subprocess = subprocess.Popen(' '.join(['exec', 'openscad', openscad_temp_file.name]), shell=True)
    return openscad_temp_file





class SolidNode(Node):
    group = 'Solid Python'
    node_color = 0
    preview = Slot()

    @preview.evaluator
    def preview(self):
        tmp = ensure_subprocess()
        if len(self.outputs) > 0:
            result = getattr(self, type(self).name_for_index(-1, False)).eval()
            print(result)
            scad = solid.scad_render(result)
            print(scad)
            tmp.truncate(0)
            tmp.seek(0, os.SEEK_SET)
            tmp.write(scad.encode('utf8'))
            tmp.flush()


def dir_module(module, base, filter=None):
    return {
        name: cls for name, cls in module.__dict__.items()
        if (filter is None or name not in filter) and isinstance(cls, type) and issubclass(cls, base)
    }


for name, cls in [
    ('Cube', solid.objects.cube),
    ('Sphere', solid.objects.sphere),
]:
    register_node(SolidNode.introspect(name)(cls))


@register_node
class Difference(SolidNode):
    a = Input(is_multi=True, reduce=operator.add)
    b = Input(is_multi=True, reduce=operator.add)
    result = Output()

    @result.evaluator
    def result(self):
        return solid.difference()(self.a.eval(), self.b.eval())


@register_node
class Intersection(SolidNode):
    objects = Input(is_multi=True)
    result = Output()

    @result.evaluator
    def result(self):
        return solid.intersection()(*self.objects.eval())


@register_node
class Translate(SolidNode):
    x = Parameter(default=0, annotation=float)
    y = Parameter(default=0, annotation=float)
    z = Parameter(default=0, annotation=float)
    objects = Input(is_multi=True, reduce=operator.add)

    result = Output()

    @result.evaluator
    def result(self):
        return solid.translate((self.x.eval(), self.y.eval(), self.z.eval()))(self.objects.eval())
