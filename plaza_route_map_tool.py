# -*- coding: utf-8 -*-
from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from qgis.core import QGis, QgsPoint
from qgis.gui import QgsRubberBand, QgsVertexMarker, QgsMapTool

from plaza_route_route_drawer import PlazaRouteRouteDrawer


LIGHT_RED = QtGui.QColor(255, 0, 0, 128)
LIGHT_GREEN = QtGui.QColor(34, 139, 34, 128)
GREEN = QtGui.QColor(0, 255, 0)
RED = QtGui.QColor(255, 0, 0)
RUBBER_BAND_WIDTH = 4


class PlazaRouteMapTool(QgsMapTool):
    context_menu = None
    coordinate = None
    coordinate_source = 'start'  # start or destination
    start_marker = None
    destination_marker = None

    def __init__(self, iface, point_transformer):
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        QgsMapTool.__init__(self, self.canvas)

        self.observers = set()
        self.point_transformer = point_transformer
        self.route_drawer = PlazaRouteRouteDrawer(self.point_transformer)

        self._setup_context_menu()

        self.start_walking_rubber_band = self._setup_rubber_band(QGis.Line, LIGHT_RED, RUBBER_BAND_WIDTH)
        self.end_walking_rubber_band = self._setup_rubber_band(QGis.Line, LIGHT_RED, RUBBER_BAND_WIDTH)
        self.public_transport_rubber_band = self._setup_rubber_band(QGis.Line, LIGHT_GREEN, RUBBER_BAND_WIDTH)

    def attach(self, observer):
        self.observers.add(observer)

    def draw_route(self, route):
        self._reset_rubber_bands()

        self.route_drawer.draw_walking_route(route['start_walking_route'], self.start_walking_rubber_band)
        self.route_drawer.draw_public_transport_connection(route['public_transport_connection'],
                                                           self.public_transport_rubber_band)
        self.route_drawer.draw_walking_route(route['end_walking_route'], self.end_walking_rubber_band)
        self._update_route_markers(route)

    def set_coordinate(self, point, source):
        if source == 'start':
            self.canvas.scene().removeItem(self.start_marker)
            self.start_marker = self._set_vertex_marker(point, GREEN)
        elif source == 'destination':
            self.canvas.scene().removeItem(self.destination_marker)
            self.destination_marker = self._set_vertex_marker(point, RED)

    def reset_map(self):
        self._reset_vertex_marker()
        self._reset_rubber_bands()

    def canvasPressEvent(self, e):
        self.coordinate = e.mapPoint()
        if e.button() == Qt.RightButton:
            self.context_menu.exec_(self.canvas.mapToGlobal(e.pos()))
        elif e.button() == Qt.LeftButton:
            self._notify_canvas_click()

    def _setup_context_menu(self):
        self.context_menu = QtGui.QMenu()
        set_start_coordinate_menu_item = self.context_menu.addAction("Directions from here")
        set_start_coordinate_menu_item.triggered.connect(self._set_start_coordinate_action)
        set_destination_coordinate_menu_item = self.context_menu.addAction("Directions to here")
        set_destination_coordinate_menu_item.triggered.connect(self._set_destination_coordinate_action)

    def _update_route_markers(self, route):
        """ sets the start and destination marker based on the returned route """
        first_route = 'start_walking_route'
        last_route = 'end_walking_route'
        if not route[last_route]:
            # just a start walking route was provided
            last_route = first_route
        first_point = route[first_route]['path'][0]
        last_point = route[last_route]['path'][-1]
        self._reset_vertex_marker()
        self.start_marker = self._set_vertex_marker(
            self.point_transformer.transform_base_to_project_crs(QgsPoint(first_point[0], first_point[1])), GREEN)
        self.destination_marker = self._set_vertex_marker(
            self.point_transformer.transform_base_to_project_crs(QgsPoint(last_point[0], last_point[1])), RED)

    def _set_start_coordinate_action(self):
        self.coordinate_source = 'start'
        self._notify_context_menu_selection()

    def _set_destination_coordinate_action(self):
        self.coordinate_source = 'destination'
        self._notify_context_menu_selection()

    def _notify_context_menu_selection(self):
        arg = {
            'coordinate_source': self.coordinate_source,
            'coordinate': self.coordinate
        }
        self._notify(arg)

    def _notify_canvas_click(self):
        arg = {
            'coordinate': self.coordinate
        }
        self._notify(arg)

    def _notify(self, arg):
        for observer in self.observers:
            observer.update(arg)

    def _setup_rubber_band(self, geometry_type, color, width):
        rubber_band = QgsRubberBand(self.canvas, geometry_type)
        rubber_band.setColor(color)
        rubber_band.setWidth(width)
        return rubber_band

    def _reset_rubber_bands(self):
        self.start_walking_rubber_band.reset(QGis.Line)
        self.public_transport_rubber_band.reset(QGis.Line)
        self.end_walking_rubber_band.reset(QGis.Line)

    def _set_vertex_marker(self, point, color):
        marker = QgsVertexMarker(self.canvas)
        marker.setColor(color)
        marker.setIconSize(7)
        marker.setPenWidth(2)
        marker.setIconType(QgsVertexMarker.ICON_X)
        marker.setCenter(point)
        return marker

    def _reset_vertex_marker(self):
        self.canvas.scene().removeItem(self.start_marker)
        self.canvas.scene().removeItem(self.destination_marker)




