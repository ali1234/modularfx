import ast
import inspect

from qtpy.QtGui import QImage, QBrush, QFont, QPalette, QColor
from qtpy.QtCore import Qt, QRectF
from qtpy.QtWidgets import QWidget, QPushButton, QFormLayout, QLineEdit, QComboBox, QLabel, QLayout, QHBoxLayout

from nodeeditor.node_content_widget import QDMNodeContentWidget
from nodeeditor.node_graphics_node import QDMGraphicsNode
from nodeeditor.node_graphics_socket import SOCKET_COLORS

from modularfx.nodetypes import *
from modularfx.parameters import ChoiceParamAttr


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
        for k, v in self.node.buttons.items():
            button = QPushButton(k, self)
            button.pressed.connect(getattr(self.node, v))
            self.layout.addRow(button)
            self.inputs.append(button)
        for k, v in self.node.parameters.items():
            if isinstance(v, ChoiceParamAttr):
                self.addSelect(k, v)
            else:
                self.addField(k, v)
        if isinstance(self.node, TransformNode):
            self.addLabelRow('Apply', None)
        if isinstance(self.node, ChainableNode):
            self.addLabelRow('Concat', 'Output')
        if isinstance(self.node, TriggerNode):
            self.addLabelRow(None, 'Trigger')
            for o in self.node.outputs:
                self.addLabelRow(None, o)

    def addLabelRow(self, inlabel=None, outlabel=None):
        # add an invisible line edit to make this row the right height
        spacer = QLineEdit(self)
        sp = spacer.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        spacer.setSizePolicy(sp)
        spacer.setVisible(False)
        spacer.setMinimumWidth(1)
        spacer.setFixedWidth(1)
        l = QHBoxLayout(self)
        l.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        l.addWidget(spacer)
        if outlabel is not None:
            o = QLabel(outlabel, self)
            o.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            l.addWidget(o)
            self.outputs.append(l)
        self.layout.addRow(inlabel, l)
        if inlabel is not None:
            self.inputs.append(l)

    def addField(self, label, attr):
        field = QLineEdit(self)
        field.setAlignment(Qt.AlignRight)
        sp = field.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        field.setSizePolicy(sp)
        if attr is not None:
            if attr.default is not inspect._empty:
                field.setPlaceholderText(repr(attr.default))
            field.textChanged.connect(lambda: self.onFieldChanged(field, attr))
        self.layout.addRow(label.title(), field)
        self.fields[label] = field
        if attr is None or attr.is_socket:
            self.inputs.append(field)

    def onFieldChanged(self, field, attr):
        try:
            t = field.text()
            if t == "":
                attr.clear()
            else:
                attr.set(ast.literal_eval(field.text()))
        except (ValueError, SyntaxError) as e:
            field.setStyleSheet("background-color:#ffaaaa;")
        else:
            field.setStyleSheet("")
        finally:
            self.node.markDirty()
            self.node.markDescendantsDirty()

    def addSelect(self, label, attr):
        select = QComboBox(self)
        sp = select.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        select.setSizePolicy(sp)
        for k, v in attr.choices.items():
            select.addItem(k.title(), v)
        select.currentIndexChanged.connect(lambda: self.onSelectChanged(select, attr))
        self.layout.addRow(label.title(), select)
        self.fields[label] = select
        if attr.is_socket:
            self.inputs.append(select)

    def onSelectChanged(self, select, attr):
        attr.set(select.currentData())
        self.node.markDirty()
        self.node.markDescendantsDirty()

    def hideField(self, field, hide):
        self.fields[field].setVisible(not hide)

BaseNode.GraphicsNode_class = BaseGraphicsNode
BaseNode.NodeContent_class = BaseContent
