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

from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal, Qt, QTime

from qgis.gui import QgsMessageBar

from util import validator as validator
from util.point_transformer import PointTransformer
from observer import Observer
from plaza_route_map_tool import PlazaRouteMapTool
from plaza_route_directions_generator import PlazaRouteDirectionsGenerator
from plaza_route_routing_service import PlazaRouteRoutingService

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'plaza_route_dockwidget_base.ui'))


class PlazaRouteDockWidget(QtGui.QDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()
    coordinate_source = None  # start or destination

    def __init__(self, iface, parent=None):
        super(PlazaRouteDockWidget, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.cross_cursor = QtGui.QCursor(Qt.CrossCursor)

        self.plaza_route_routing_service = PlazaRouteRoutingService(self._handle_route, self._handle_error)
        self.routing_generator = PlazaRouteDirectionsGenerator()
        self.point_transformer = PointTransformer(self.iface)

        self.map_tool = PlazaRouteMapTool(self.iface, self.point_transformer)
        self.map_tool.attach(self)
        self.canvas.setMapTool(self.map_tool)

        self._register_events()
        self._reset()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        self._reset()
        event.accept()

    def update(self, arg):
        update_type = arg['type']
        value = arg['value']
        if update_type == 'coordinate_update':
            self.coordinate_source = \
                value['coordinate_source'] if 'coordinate_source' in value else self.coordinate_source
            self._set_coordinate(value['coordinate'], self.coordinate_source)
        elif update_type == 'map_tool_event':
            self.coordinate_source = None

    def _register_events(self):
        self.start_select_btn.clicked.connect(self._select_start)
        self.destination_select_btn.clicked.connect(self._select_destination)
        self.departure_refresh_btn.clicked.connect(self._refresh_departure)
        self.reset_btn.clicked.connect(self._reset)
        self.show_route_btn.clicked.connect(self._show_route)

    def _show_route(self):
        QtGui.QApplication.setOverrideCursor(Qt.WaitCursor)

        if not self._validate_routing_params():
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

        self.plaza_route_routing_service.get_route(start, destination, departure, precise_public_transport_stops)

    def _validate_routing_params(self):
        if validator.has_empty_fields(self.start_value.text(),
                                      self.destination_value.text(),
                                      self.departure_value.text()):
            self._add_qgis_msg(validator.ERROR_MSGS['empty_field'])
            return False

        if not validator.is_valid_project_coordinate(self.start_value.text(), self.point_transformer) or \
                not validator.is_valid_project_coordinate(self.destination_value.text(), self.point_transformer):
            self._add_qgis_msg(validator.ERROR_MSGS['invalid_coordinate'])
            return False

        if not validator.is_valid_departure(self.departure_value.text()):
            self._add_qgis_msg(validator.ERROR_MSGS['invalid_departure'])
            return False

        return True

    def _handle_route(self, route):
        try:
            self.map_tool.draw_route(route)
            self._add_routing(route)
        finally:
            QtGui.QApplication.restoreOverrideCursor()

    def _handle_error(self, msg):
        try:
            self._add_qgis_msg(msg)
        finally:
            QtGui.QApplication.restoreOverrideCursor()

    def _add_routing(self, route):
        self.direction_value.clear()
        self.direction_value.append(self.routing_generator.generate_directions(route))

    def _set_coordinate(self, point, source):
        if not source:
            return
        coordinate = "{}, {}".format(point.x(), point.y())
        if source == 'start':
            self.start_value.setText(coordinate)
        elif source == 'destination':
            self.destination_value.setText(coordinate)
        self.map_tool.set_coordinate(point, source)

    def _select_start(self):
        self.coordinate_source = 'start'
        self._handle_crosshairs_selection()

    def _select_destination(self):
        self.coordinate_source = 'destination'
        self._handle_crosshairs_selection()

    def _handle_crosshairs_selection(self):
        self.canvas.setMapTool(self.map_tool)
        self.canvas.setCursor(self.cross_cursor)

    def _refresh_departure(self):
        current_time = QTime()
        current_time.start()
        self.departure_value.setTime(current_time)

    def _reset(self):
        self.map_tool.reset_map()
        self._refresh_departure()
        self.start_value.clear()
        self.destination_value.clear()
        self.direction_value.clear()

    def _add_qgis_msg(self, msg, level=QgsMessageBar.CRITICAL):
        self.iface.messageBar().pushMessage('Error', msg, level=level)


Observer.register(PlazaRouteDockWidget)
