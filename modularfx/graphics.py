import ast
import inspect

from qtpy.QtGui import QImage, QBrush, QFont
from qtpy.QtCore import Qt, QRectF
from qtpy.QtWidgets import QPushButton, QFormLayout, QLineEdit, QComboBox, QLabel, QLayout, QHBoxLayout

from nodeeditor.node_content_widget import QDMNodeContentWidget
from nodeeditor.node_graphics_node import QDMGraphicsNode
from nodeeditor.node_graphics_socket import SOCKET_COLORS

from modularfx.nodetypes import *


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
