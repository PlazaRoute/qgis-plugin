from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from qgis.gui import QgsMapTool


class PlazaRouteContextMenu(QgsMapTool):
    context_menu = None
    coordinate_source = 'start'  # start or destination
    coordinate = None

    def __init__(self, canvas):
        self.canvas = canvas
        QgsMapTool.__init__(self, self.canvas)

        self.observers = set()

        self.setup_context_menu()

    def attach(self, observer):
        self.observers.add(observer)

    def notify_context_menu_selection(self):
        arg = {
            'coordinate_source': self.coordinate_source,
            'coordinate': self.coordinate
        }
        self.notify(arg)

    def notify_canvas_click(self):
        arg = {
            'coordinate': self.coordinate
        }
        self.notify(arg)

    def notify(self, arg):
        for observer in self.observers:
            observer.update(arg)

    def setup_context_menu(self):
        self.context_menu = QtGui.QMenu()
        set_start_coordinate_menu_item = self.context_menu.addAction("Directions from here")
        set_start_coordinate_menu_item.triggered.connect(self.set_start_coordinate_action)
        set_destination_coordinate_menu_item = self.context_menu.addAction("Directions to here")
        set_destination_coordinate_menu_item.triggered.connect(self.set_destination_coordinate_action)

    def canvasPressEvent(self, e):
        self.coordinate = e.mapPoint()
        if e.button() == Qt.RightButton:
            self.context_menu.exec_(self.canvas.mapToGlobal(e.pos()))
        elif e.button() == Qt.LeftButton:
            self.notify_canvas_click()

    def set_start_coordinate_action(self):
        self.coordinate_source = 'start'
        self.notify_context_menu_selection()

    def set_destination_coordinate_action(self):
        self.coordinate_source = 'destination'
        self.notify_context_menu_selection()



