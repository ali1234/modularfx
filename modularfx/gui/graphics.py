import ast
import inspect

from qtpy.QtGui import QImage, QBrush, QFont
from qtpy.QtCore import Qt, QRectF
from qtpy.QtWidgets import QPushButton, QFormLayout, QLineEdit, QComboBox, QLabel, QLayout, QHBoxLayout

from nodeeditor.node_content_widget import QDMNodeContentWidget
from nodeeditor.node_graphics_node import QDMGraphicsNode
from nodeeditor.node_graphics_socket import SOCKET_COLORS

from modularfx.node.attributes import *


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
        self.icons = QImage("../data/icons/status_icons.png")
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
        left_tmp = []
        right_tmp = []
        for k, v in type(self.node).all_attrs():
            if isinstance(v, Slot):
                self.doLeftRight(left_tmp, right_tmp)
                self.fields[k] = self.addButton(k, v)
            elif isinstance(v, Parameter):
                self.doLeftRight(left_tmp, right_tmp)
                self.fields[k] = self.addField(v.label, v)
            elif isinstance(v, Input):
                if not v.hidden:
                    left_tmp.append((k, v))
            elif isinstance(v, (Signal, Output)):
                if not v.hidden:
                    right_tmp.append((k, v))
        self.doLeftRight(left_tmp, right_tmp)

    def doLeftRight(self, l, r):
        while(len(l) > len(r)):
            k, v = l.pop(0)
            self.fields[k] = self.addLabelRow(v.label, None)
        while(len(r) > len(l)):
            k, v = r.pop(0)
            self.fields[k] = self.addLabelRow(None, v.label)
        while(len(l)):
            lk, lv = l.pop(0)
            rk, rv = r.pop(0)
            row = self.addLabelRow(lv.label, rv.label)
            self.fields[lk] = row
            self.fields[rk] = row

    def addButton(self, k, v):
        button = QPushButton(v.label, self)
        button.setToolTip(v.doc)
        self.layout.addRow(button)
        self.fields[k] = button
        button.pressed.connect(getattr(self.node, k).eval)
        return button

    def addLabelRow(self, inlabel, outlabel):
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
            o = QLabel(outlabel.title(), self)
            o.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            l.addWidget(o)
            self.fields[outlabel] = o
        self.layout.addRow(inlabel, l)
        return l

    def addField(self, label, attr):
        field = QLineEdit(self)
        field.setAlignment(Qt.AlignRight)
        sp = field.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        field.setSizePolicy(sp)
        if isinstance(attr, Parameter):
            if attr.default is not inspect._empty:
                field.setPlaceholderText(repr(attr.default))
            field.textChanged.connect(lambda: self.onFieldChanged(field, attr))
        self.layout.addRow(label.title(), field)
        return field

    def onFieldChanged(self, field, attr):
        try:
            t = field.text()
            if t == "":
                attr.clear()
            else:
                attr = ast.literal_eval(field.text())
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
