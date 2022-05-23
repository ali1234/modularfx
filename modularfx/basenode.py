import ast
import inspect
from functools import reduce
import operator

from qtpy.QtGui import QImage, QBrush, QColor, QPalette, QFont
from qtpy.QtCore import Qt, QRectF
from qtpy.QtWidgets import QWidget, QPushButton, QFormLayout, QLineEdit, QComboBox, QLabel, QLayout, QHBoxLayout

from nodeeditor.node_node import Node
from nodeeditor.node_content_widget import QDMNodeContentWidget
from nodeeditor.node_graphics_node import QDMGraphicsNode
from nodeeditor.node_graphics_socket import SOCKET_COLORS
from nodeeditor.node_socket import LEFT_TOP, LEFT_CENTER, LEFT_BOTTOM, RIGHT_BOTTOM
from nodeeditor.utils import dumpException


class BaseGraphicsNode(QDMGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.edge_roundness = 6
        self.edge_padding = 0
        self.title_horizontal_padding = 8
        self.title_vertical_padding = 10

    def initUI(self):
        super().initUI()
        self.width = self.content.width()
        self.height = self.content.height() + self.title_height

    def initAssets(self):
        super().initAssets()
        self.icons = QImage("icons/status_icons.png")
        self._brush_title = QBrush(SOCKET_COLORS[self.node.node_colour])
        self._brush_background = QBrush(SOCKET_COLORS[self.node.node_colour].lighter(190))
        self._title_font.setWeight(QFont.Weight.Black)

    def paint(self, painter, QStyleOptionGraphicsItem, widget=None):
        super().paint(painter, QStyleOptionGraphicsItem, widget)

        offset = 24.0
        if self.node.isDirty(): offset = 0.0
        if self.node.isInvalid(): offset = 48.0

        painter.drawImage(
            QRectF(-10, -10, 24.0, 24.0),
            self.icons,
            QRectF(offset, 0, 24.0, 24.0)
        )


class BaseContent(QDMNodeContentWidget):

    def initUI(self):
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.layout = QFormLayout()
        self.setLayout(self.layout)
        self.layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.fields = {}
        self.inputs = []
        self.outputs = []
        if isinstance(self.node, SignalNode):
            self.button = QPushButton("Play", self)
            self.layout.addRow(self.button)
        if hasattr(self.node, 'clsgrp'):
            self.addSelect('type', self.node.clsgrp)
        if hasattr(self.node, 'sig'):
            for k,v in self.node.sig.parameters.items():
                default = repr(v.default) if v.default != inspect._empty else ""
                self.addField(k, default)
        if isinstance(self.node, TransformNode):
            self.addField('apply', None)
            self.hideField('apply', True)
        if isinstance(self.node, ChainableNode):
            # add an invisible line edit to make this row the right height
            spacer = QLineEdit(self)
            sp = spacer.sizePolicy()
            sp.setRetainSizeWhenHidden(True)
            spacer.setSizePolicy(sp)
            spacer.setVisible(False)
            spacer.setMinimumWidth(1)
            spacer.setFixedWidth(1)
            o = QLabel('Output', self)
            o.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            #o.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            l = QHBoxLayout(self)
            l.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            l.addWidget(spacer)
            l.addWidget(o)
            self.layout.addRow('Concat', l)
            self.inputs.append(l)
            self.outputs.append(l)

    def addField(self, label, val):
        field = QLineEdit(self)
        field.setPlaceholderText(val)
        field.setAlignment(Qt.AlignRight)
        sp = field.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        field.setSizePolicy(sp)
        field.textChanged.connect(self.onContentChanged)
        self.layout.addRow(label.title(), field)
        self.fields[label] = field
        self.inputs.append(field)

    def addSelect(self, label, values):
        select = QComboBox(self)
        for k, v in values.items():
            select.addItem(k, k)
        select.currentIndexChanged.connect(self.onContentChanged)
        self.layout.addRow(label.title(), select)
        self.fields[label] = select

    def readField(self, field):
        x = self.fields[field].text()
        if x == '':
            x = self.fields[field].placeholderText()
            if x == '':
                return None
        return ast.literal_eval(x)

    def serializeField(self, field):
        if isinstance(self.fields[field], QComboBox):
            return self.fields[field].currentData()
        else:
            return self.fields[field].text()

    def deserializeField(self, field, value):
        if isinstance(self.fields[field], QComboBox):
            self.fields[field].setCurrentIndex(self.fields[field].findData(value))
        else:
            if value != self.fields[field].placeholderText():
                self.fields[field].setText(value)

    def hideField(self, field, hide):
        self.fields[field].setVisible(not hide)

    def readSelect(self, select):
        return self.node.clsgrp[self.fields[select].currentData()]

    def onContentChanged(self):
        self.node.markDirty()
        self.node.markDescendantsDirty()


class BaseNode(Node):
    icon = None

    def __init__(self, scene, name, inputs, outputs):
        self.inputmap = {}
        if hasattr(self, 'sig'):
            auto_inputs = []
            for n,(k,v) in enumerate(self.sig.parameters.items()):
                self.inputmap[n] = k
                self.inputmap[k] = n
                auto_inputs.append(2)
                print(n, k)
            inputs = auto_inputs + inputs
        super().__init__(scene, name, inputs, outputs)
        self.markDirty(True)

    def initSettings(self):
        super().initSettings()
        self.input_socket_position = LEFT_BOTTOM
        self.output_socket_position = RIGHT_BOTTOM

    def getSocketPosition(self, index: int, position: int, num_out_of: int=1) -> '(x, y)':
        x, y = super().getSocketPosition(index, position, num_out_of)
        if position == LEFT_BOTTOM:
            field = self.content.inputs[index]
            y = 0.5 + self.grNode.title_height + (field.geometry().height()/2) + field.geometry().topLeft().y() - self.content.layout.geometry().topLeft().y()
        elif position == RIGHT_BOTTOM:
            field = self.content.outputs[index]
            y = 0.5 + self.grNode.title_height + (field.geometry().height()/2) + field.geometry().topLeft().y() - self.content.layout.geometry().topLeft().y()
        return [x, y]

    def onInputChanged(self, socket=None):
        self.markDirty()
        self.markDescendantsDirty()
        if socket.index in self.inputmap:
            self.content.hideField(self.inputmap[socket.index], socket.hasAnyEdge())

    def onOutputChanged(self, socket=None):
        self.markDirty()
        self.markDescendantsDirty()

    def extract(self):
        args = {}
        for n, k in enumerate(self.sig.parameters.keys()):
            conn = self.getInput(n)
            if conn is None:
                args[k] = self.content.readField(k)
            else:
                args[k] = conn.eval()
        return args

    def evalImplementation(self):
        if hasattr(self, 'clsgrp'):
            return self.content.readSelect('type')(**self.extract())
        else:
            return self.cls(**self.extract())

    def eval(self, index=0):
        if self.isDirty():
            self.value = self.evalImplementation(index)
            self.markDirty(False)
        return self.value

    def serialize(self):
        data = super().serialize()
        data['type_name'] = self.__class__.__name__
        print(self.content.fields.keys())
        print(self.sig.parameters.keys())
        data['content_data'] = {
            field: self.content.serializeField(field) for field in self.content.fields.keys()
        }
        return data

    def deserialize(self, data, hashmap, restore_id):
        if super().deserialize(data, hashmap, restore_id):
            for k, v in data.get('content_data', {}).items():
                self.content.deserializeField(k, v)
            return True
        else:
            return False


class ChainableNode(BaseNode):
    inputtypes = []
    chaintype = 0

    def __init__(self, scene):
        super().__init__(scene, self.__class__.__name__, self.inputtypes + [self.chaintype], [self.chaintype])

    def chain(self, s):
        i = self.getInputs(-1)
        if i:
            s = reduce(operator.add, (x.eval() for x in i)) | s
        return s

    def eval(self, index=0):
        if self.isDirty():
            self.value = self.chain(self.evalImplementation())
            self.markDirty(False)
        return self.value


class CurveNode(ChainableNode):
    chaintype = 1
    node_colour = 1

class SignalNode(ChainableNode):
    chaintype = 0
    node_colour = 0

    def __init__(self, scene):
        super().__init__(scene)
        self.content.button.pressed.connect(self.onPlay)
        self.inputs[-1].is_multi_edges = True

    def onPlay(self):
        try:
            self.eval().play()
        except Exception as e:
            self.markDescendantsDirty()
            self.grNode.setToolTip(str(e))
            dumpException(e)


class TransformNode(SignalNode):
    inputtypes = [0]
    node_colour = 3

    def __init__(self, scene):
        super().__init__(scene)
        self.inputs[-2].is_multi_edges = True

    def initAssets(self):
        super().initAssets()
        self._brush_title = QBrush(QColor("#FF713131"))

    def evalImplementation(self):
        return reduce(operator.add, (x.eval() for x in self.getInputs(-2))) * super().evalImplementation()
