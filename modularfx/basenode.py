import ast
import inspect

from qtpy.QtGui import QImage
from qtpy.QtCore import Qt, QRectF
from qtpy.QtWidgets import QPushButton, QFormLayout, QLineEdit, QComboBox, QLabel, QLayout

from nodeeditor.node_node import Node
from nodeeditor.node_content_widget import QDMNodeContentWidget
from nodeeditor.node_graphics_node import QDMGraphicsNode
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
        self.layout = QFormLayout(self)
        self.layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.fields = {}
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
            self.layout.addRow('Apply', None)
        if isinstance(self.node, ChainableNode):
            l = QLabel('Output', self)
            l.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.layout.addRow('Concat', l)

    def extract(self):
        return {k: self.readField(k) for k in self.node.sig.parameters.keys()}

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

    def addSelect(self, label, values):
        select = QComboBox(self)
        for k, v in values.items():
            select.addItem(k, v)
        select.currentIndexChanged.connect(self.onContentChanged)
        self.layout.addRow(label.title(), select)
        self.fields[label] = select

    def readField(self, field):
        x = self.fields[field].text()
        if x == '':
            x = self.fields[field].placeholderText()
        return ast.literal_eval(x)

    def hideField(self, field, hide):
        self.fields[field].setVisible(not hide)

    def readSelect(self, select):
        return self.fields[select].currentData()

    def onContentChanged(self):
        self.node.markDirty()
        self.node.markDescendantsDirty()


class BaseNode(Node):
    icon = None

    GraphicsNode_class = BaseGraphicsNode
    NodeContent_class = BaseContent

    def __init__(self, scene, name, inputs, outputs):
        self.inputmap = {}
        if hasattr(self, 'sig'):
            for n,(k,v) in enumerate(reversed(self.sig.parameters.items()), start=len(inputs)):
                self.inputmap[n] = k
                self.inputmap[k] = n
                inputs.append(2)
                print(n, k)
        super().__init__(scene, name, inputs, outputs)
        self.markDirty(True)

    def initSettings(self):
        super().initSettings()
        self.input_socket_position = LEFT_BOTTOM
        self.output_socket_position = RIGHT_BOTTOM

    def onInputChanged(self, socket=None):
        self.markDirty()
        self.markDescendantsDirty()
        self.content.hideField(self.inputmap[socket.index], socket.hasAnyEdge())

    def onOutputChanged(self, socket=None):
        self.markDirty()
        self.markDescendantsDirty()

    def evalImplementation(self):
        if hasattr(self, 'clsgrp'):
            return self.content.readSelect('type')(**self.content.extract())
        else:
            return self.cls(**self.content.extract())

    def eval(self, index=0):
        if self.isDirty():
            self.value = self.evalImplementation(index)
            self.markDirty(False)
        return self.value


class ChainableNode(BaseNode):
    inputtypes = []
    chaintype = 0

    def __init__(self, scene):
        super().__init__(scene, self.__class__.__name__, [self.chaintype] + self.inputtypes, [self.chaintype])

    def chain(self, s):
        chain = super().getInput(0)
        if chain is not None:
            prior = chain.eval()
            s = chain.eval() | s
        return s

    def eval(self, index=0):
        if self.isDirty():
            self.value = self.chain(self.evalImplementation())
            self.markDirty(False)
        return self.value

    def getInput(self, index=0):
        return super().getInput(index+1)


class CurveNode(ChainableNode):
    chaintype = 1


class SignalNode(ChainableNode):
    chaintype = 0

    def __init__(self, scene):
        super().__init__(scene)
        self.content.button.pressed.connect(self.onPlay)

    def onPlay(self):
        try:
            self.eval().play()
        except Exception as e:
            self.markDescendantsDirty()
            self.grNode.setToolTip(str(e))
            dumpException(e)


class TransformNode(SignalNode):
    inputtypes = [0]

    def evalImplementation(self):
        return self.getInput(0).eval() * super().evalImplementation()
