import ast
import inspect

from qtpy.QtGui import QImage
from qtpy.QtCore import Qt, QRectF
from qtpy.QtWidgets import QPushButton, QFormLayout, QLineEdit, QComboBox

from nodeeditor.node_node import Node
from nodeeditor.node_content_widget import QDMNodeContentWidget
from nodeeditor.node_graphics_node import QDMGraphicsNode
from nodeeditor.node_socket import LEFT_BOTTOM, RIGHT_BOTTOM
from nodeeditor.utils import dumpException

from modularfx.registry import register_node, InvalidNodeRegistration


class BaseGraphicsNode(QDMGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.width = 240
        self.height = 240
        self.edge_roundness = 6
        self.edge_padding = 0
        self.title_horizontal_padding = 8
        self.title_vertical_padding = 10

    def initUI(self):
        super().initUI()
        r = self.content.childrenRect()

        print(r)
        #self.width = r.width()
        #self.height = r.height()


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
        self.fields = {}

    def addField(self, label, val):
        field = QLineEdit(val, self)
        field.setAlignment(Qt.AlignRight)
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
        return ast.literal_eval(self.fields[field].text())

    def readSelect(self, select):
        return self.fields[select].currentData()

    def onContentChanged(self):
        self.node.markDirty()
        self.node.markDescendantsDirty()


class BaseNode(Node):
    icon = None

    GraphicsNode_class = BaseGraphicsNode
    NodeContent_class = BaseContent

    def __init__(self, *args, **kwargs):
        print(args, kwargs)
        super().__init__(*args, **kwargs)
        self.markDirty(True)

    def initSettings(self):
        super().initSettings()
        self.input_socket_position = LEFT_BOTTOM
        self.output_socket_position = RIGHT_BOTTOM

    def onInputChanged(self, socket=None):
        self.markDirty()
        self.markDescendantsDirty()

    def onOutputChanged(self, socket=None):
        self.markDirty()
        self.markDescendantsDirty()

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
            self.value = self.chain(self.evalImplementation(index))
            self.markDirty(False)
        return self.value

    def getInput(self, index=0):
        return super().getInput(index+1)


class IntrospectedContent(BaseContent):

    def initUI(self):
        super().initUI()
        if isinstance(self.node, SignalNode):
            self.button = QPushButton("Play", self)
            self.layout.addRow(self.button)
        for k,v in self.node.sig.parameters.items():
            default = repr(v.default) if v.default != inspect._empty else ""
            self.addField(k, default)

    def extract(self):
        return {k: self.readField(k) for k in self.node.sig.parameters.keys()}


class PlayableContent(BaseContent):

    def initUI(self):
        super().initUI()



class PlayableIntrospectedContent(PlayableContent, IntrospectedContent):
    pass


class CurveNode(ChainableNode):
    chaintype = 1

    def evalImplementation(self, index):
        return self.cls(**self.content.extract())


class SignalNode(ChainableNode):
    chaintype = 0

    def __init__(self, scene):
        super().__init__(scene)
        self.content.button.pressed.connect(self.onPlay)

    def evalImplementation(self, index):
        return self.cls(**self.content.extract())

    def onPlay(self):
        try:
            self.eval().play()
        except Exception as e:
            self.markDescendantsDirty()
            self.grNode.setToolTip(str(e))
            dumpException(e)


class TransformNode(SignalNode):
    inputtypes = [0]

    def evalImplementation(self, index):
        return self.getInput(0).eval() * self.cls(**self.content.extract())
