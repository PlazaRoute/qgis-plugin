# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PlazaRouteDockWidget
                                 A QGIS plugin
 Pedestrian and Public Transport Routing
                             -------------------
        begin                : 2017-11-14
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Jonas Matter / Robin Suter
        email                : robin@robinsuter.ch
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
from ast import literal_eval

from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal, Qt, QTime

from qgis.core import QGis, QgsPoint, QgsCoordinateTransform, QgsCoordinateReferenceSystem
from qgis.gui import QgsRubberBand, QgsVertexMarker, QgsMessageBar

from util import log_helper as logger
from util import validator as validator
from util.point_transformer import PointTransformer
from observer import Observer
from plaza_route_context_menu import PlazaRouteContextMenu
from plaza_route_routing_generator import PlazaRouteRoutingGenerator
from plaza_route_route_drawer import PlazaRouteRouteDrawer
from plaza_route_service import PlazaRouteService

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'plaza_route_dockwidget_base.ui'))

PLAZA_ROUTING_URL = 'http://localhost:5000/api/route'

LIGHT_RED = QtGui.QColor(255, 0, 0, 128)
LIGHT_GREEN = QtGui.QColor(34, 139, 34, 128)
GREEN = QtGui.QColor(0, 255, 0)
RED = QtGui.QColor(255, 0, 0)
RUBBER_BAND_WIDTH = 4


class PlazaRouteDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()
    coordinate_source = 'start'  # start or destination
    start_marker = None
    destination_marker = None

    def __init__(self, iface, parent=None):
        super(PlazaRouteDockWidget, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.canvas = self.iface.mapCanvas()

        self.context_menu = PlazaRouteContextMenu(self.canvas)
        self.context_menu.attach(self)
        self.canvas.setMapTool(self.context_menu)

        self.register_events()

        self.plaza_route_service = PlazaRouteService(PLAZA_ROUTING_URL, self.handle_route, self.handle_error)
        self.routing_generator = PlazaRouteRoutingGenerator()
        self.point_transformer = PointTransformer(self.iface)
        self.route_drawer = PlazaRouteRouteDrawer(self.point_transformer)

        self.start_walking_rubber_band = self.setup_rubber_band(QGis.Line, LIGHT_RED, RUBBER_BAND_WIDTH)
        self.end_walking_rubber_band = self.setup_rubber_band(QGis.Line, LIGHT_RED, RUBBER_BAND_WIDTH)
        self.public_transport_rubber_band = self.setup_rubber_band(QGis.Line, LIGHT_GREEN, RUBBER_BAND_WIDTH)

        self.reset()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        self.reset()
        event.accept()

    def register_events(self):
        self.start_select_btn.clicked.connect(self.select_start)
        self.destination_select_btn.clicked.connect(self.select_destination)
        self.departure_refresh_btn.clicked.connect(self.refresh_departure)
        self.reset_btn.clicked.connect(self.reset)
        self.show_route_btn.clicked.connect(self.show_route)

    def update(self, arg):
        self.coordinate_source = arg['coordinate_source'] if 'coordinate_source' in arg else self.coordinate_source
        self.set_coordinate(arg['coordinate'], self.coordinate_source)

    def set_coordinate(self, point, source):
        coordinate = "{}, {}".format(point.x(), point.y())
        if source == 'start':
            self.start_value.setText(coordinate)
            self.canvas.scene().removeItem(self.start_marker)
            self.start_marker = self.set_vertex_marker(point, GREEN)
        elif source == 'destination':
            self.destination_value.setText(coordinate)
            self.canvas.scene().removeItem(self.destination_marker)
            self.destination_marker = self.set_vertex_marker(point, RED)

    def select_start(self):
        self.coordinate_source = 'start'
        self.canvas.setMapTool(self.context_menu)

    def select_destination(self):
        self.coordinate_source = 'destination'
        self.canvas.setMapTool(self.context_menu)

    def refresh_departure(self):
        current_time = QTime()
        current_time.start()
        self.departure_value.setTime(current_time)

    def show_route(self):
        QtGui.QApplication.setOverrideCursor(Qt.WaitCursor)

        if not self.validate_routing_params():
            QtGui.QApplication.restoreOverrideCursor()
            return

        if validator.is_address(self.start_value.text()):
            start = self.start_value.text()
        else:
            start = self.point_transformer.transform_project_to_base_crs_str(
                self.point_transformer.str_to_point(self.start_value.text()))

        if validator.is_address(self.destination_value.text()):
            destination = self.destination_value.text()
        else:
            destination = self.point_transformer.transform_project_to_base_crs_str(
                self.point_transformer.str_to_point(self.destination_value.text()))

        departure = self.departure_value.text()
        precise_public_transport_stops = self.precise_public_transport_stops_cb.isChecked()

        self.plaza_route_service.get_route(start, destination, departure, precise_public_transport_stops)

    def validate_routing_params(self):
        if validator.has_empty_fields(self.start_value.text(),
                                      self.destination_value.text(),
                                      self.departure_value.text()):
            self._add_qgis_msg(validator.ERROR_MSGS['empty_field'])
            return False

        if not self.validate_project_coordinate(self.start_value.text()) or \
                not self.validate_project_coordinate(self.destination_value.text()):
            self._add_qgis_msg(validator.ERROR_MSGS['invalid_coordinate'])
            return False

        if not validator.is_valid_departure(self.departure_value.text()):
            self._add_qgis_msg(validator.ERROR_MSGS['invalid_departure'])
            return False

        return True

    def validate_project_coordinate(self, coordinate):
        if validator.is_address(coordinate):
            return True
        else:
            transformed_coordinate = self.point_transformer.transform_project_to_base_crs_str(
                self.point_transformer.str_to_point(coordinate))
            if not validator.is_valid_coordinate(transformed_coordinate):
                return False
        return True

    def handle_route(self, route):
        try:
            self.draw_route(route)
            self.add_routing(route)
            self.update_route_markers(route)
        finally:
            QtGui.QApplication.restoreOverrideCursor()

    def handle_error(self, msg):
        try:
            logger.warn(msg)
            self._add_qgis_msg(msg)
        finally:
            QtGui.QApplication.restoreOverrideCursor()

    def draw_route(self, route):
        self.reset_rubber_bands()

        self.route_drawer.draw_walking_route(route['start_walking_route'], self.start_walking_rubber_band)
        self.route_drawer.draw_public_transport_connection(route['public_transport_connection'],
                                                           self.public_transport_rubber_band)
        self.route_drawer.draw_walking_route(route['end_walking_route'], self.end_walking_rubber_band)

    def add_routing(self, route):
        self.routing_value.clear()
        self.routing_value.append(''.join(self.routing_generator.generate_routing(route)))

    def update_route_markers(self, route):
        """ sets the start and destination marker based on the returned route """
        first_route = 'start_walking_route'
        last_route = 'end_walking_route'
        if not route[last_route]:
            # just a start walking route was provided
            last_route = first_route
        first_point = route[first_route]['path'][0]
        last_point = route[last_route]['path'][-1]
        self.reset_vertex_marker()
        self.start_marker = self.set_vertex_marker(
            self.point_transformer.transform_base_to_project_crs(QgsPoint(first_point[0], first_point[1])), GREEN)
        self.destination_marker = self.set_vertex_marker(
            self.point_transformer.transform_base_to_project_crs(QgsPoint(last_point[0], last_point[1])), RED)

    def reset(self):
        self.reset_rubber_bands()
        self.refresh_departure()
        self.reset_vertex_marker()
        self.start_value.clear()
        self.destination_value.clear()
        self.routing_value.clear()

    def set_vertex_marker(self, point, color):
        marker = QgsVertexMarker(self.canvas)
        marker.setColor(color)
        marker.setIconSize(7)
        marker.setPenWidth(2)
        marker.setIconType(QgsVertexMarker.ICON_X)
        marker.setCenter(point)
        return marker

    def reset_vertex_marker(self):
        self.canvas.scene().removeItem(self.start_marker)
        self.canvas.scene().removeItem(self.destination_marker)

    def setup_rubber_band(self, geometry_type, color, width):
        rubber_band = QgsRubberBand(self.canvas, geometry_type)
        rubber_band.setColor(color)
        rubber_band.setWidth(width)
        return rubber_band

    def reset_rubber_bands(self):
        self.start_walking_rubber_band.reset(QGis.Line)
        self.public_transport_rubber_band.reset(QGis.Line)
        self.end_walking_rubber_band.reset(QGis.Line)

    def _add_qgis_msg(self, msg, level=QgsMessageBar.CRITICAL):
        self.iface.messageBar().pushMessage('Error', msg, level=level)


Observer.register(PlazaRouteDockWidget)
