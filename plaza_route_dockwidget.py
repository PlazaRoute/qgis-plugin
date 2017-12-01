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
import json
from collections import defaultdict
import string

from PyQt4 import QtGui, uic, QtNetwork
from PyQt4.QtCore import pyqtSignal, Qt, QUrl, QTime

from qgis.core import QGis, QgsPoint
from qgis.gui import QgsRubberBand, QgsMapToolEmitPoint, QgsVertexMarker, QgsMessageBar

from util import log_helper as logger
from util import validator as validator

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'plaza_route_dockwidget_base.ui'))

PLAZA_ROUTING_URL = 'http://localhost:5000/api/route'

RED = QtGui.QColor(255, 0, 0, 128)
GREEN = QtGui.QColor(34, 139, 34, 128)
RUBBER_BAND_WIDTH = 4


class PlazaRouteDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()
    active_crosshairs = 'start'
    start_marker = None
    destination_marker = None

    def __init__(self, iface, parent=None):
        super(PlazaRouteDockWidget, self).__init__(parent)
        self.setupUi(self)
        self.init_gui_values()

        self.iface = iface
        self.network_access_manager = QtNetwork.QNetworkAccessManager()

        self.canvas = self.iface.mapCanvas()
        self.point_tool = QgsMapToolEmitPoint(self.canvas)
        self.show_crosshairs()

        self.register_events()

        self.start_walking_rubber_band = self.setup_rubber_band(QGis.Line, RED, RUBBER_BAND_WIDTH)
        self.end_walking_rubber_band = self.setup_rubber_band(QGis.Line, RED, RUBBER_BAND_WIDTH)
        self.public_transport_rubber_band = self.setup_rubber_band(QGis.Line, GREEN, RUBBER_BAND_WIDTH)

    def init_gui_values(self):
        current_time = QTime()
        current_time.start()
        self.departure_value.setTime(current_time)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def register_events(self):
        self.network_access_manager.finished.connect(self.handle_response)
        self.reset_btn.clicked.connect(self.reset)
        self.start_select_btn.clicked.connect(self.select_start)
        self.destination_select_btn.clicked.connect(self.select_destination)
        self.point_tool.canvasClicked.connect(self.display_point)
        self.show_route_btn.clicked.connect(self.show_route)

    def setup_rubber_band(self, geometry_type, color, width):
        rubber_band = QgsRubberBand(self.canvas, geometry_type)
        rubber_band.setColor(color)
        rubber_band.setWidth(width)
        return rubber_band

    def set_vertex_marker(self, point):
        marker = QgsVertexMarker(self.canvas)
        marker.setColor(QtGui.QColor(0, 255, 0))
        marker.setIconSize(7)
        marker.setPenWidth(2)
        marker.setIconType(QgsVertexMarker.ICON_X)
        marker.setCenter(point)
        return marker

    def reset(self):
        self.reset_rubberbands()
        self.canvas.scene().removeItem(self.start_marker)
        self.canvas.scene().removeItem(self.destination_marker)
        self.routing_value.clear()

    def select_start(self):
        self.active_crosshairs = 'start'
        self.show_crosshairs()

    def select_destination(self):
        self.active_crosshairs = 'destination'
        self.show_crosshairs()

    def show_crosshairs(self):
        self.canvas.setMapTool(self.point_tool)

    def display_point(self, point, button):
        coordinate = "{}, {}".format(point.x(), point.y())
        if self.active_crosshairs == 'start' and button == Qt.LeftButton:
            self.start_value.setText(coordinate)
            self.canvas.scene().removeItem(self.start_marker)
            self.start_marker = self.set_vertex_marker(QgsPoint(point.x(), point.y()))
        elif self.active_crosshairs == 'destination' or button == Qt.RightButton:
            self.destination_value.setText(coordinate)
            self.canvas.scene().removeItem(self.destination_marker)
            self.destination_marker = self.set_vertex_marker(QgsPoint(point.x(), point.y()))

    def show_route(self):
        QtGui.QApplication.setOverrideCursor(Qt.WaitCursor)

        if not self.validate_routing_params():
            QtGui.QApplication.restoreOverrideCursor()
            return

        url = QUrl(PLAZA_ROUTING_URL)
        url.addQueryItem("start", self.start_value.text())
        url.addQueryItem("destination", self.destination_value.text())
        url.addQueryItem("departure", self.departure_value.text())

        logger.info(str(url.encodedQuery()))
        req = QtNetwork.QNetworkRequest(url)

        self.network_access_manager.get(req)

    def validate_routing_params(self):
        if validator.has_empty_fields(self.start_value.text(),
                                      self.destination_value.text(),
                                      self.departure_value.text()):
            self._add_qgis_msg(validator.ERROR_MSGS['empty_field'])
            return False

        if not validator.is_valid_location(self.start_value.text()) and \
                not not validator.is_valid_location(self.destination_value.text()):
            self._add_qgis_msg(validator.ERROR_MSGS['invalid_coordinate'])
            return False

        if not validator.is_valid_departure(self.departure_value.text()):
            self._add_qgis_msg(validator.ERROR_MSGS['invalid_departure'])
            return False

        return True

    def handle_response(self, reply):
        er = reply.error()

        try:
            if er == QtNetwork.QNetworkReply.NoError:
                bytes_string = reply.readAll()
                route = json.loads(str(bytes_string))
                if not self.validate_response(route):
                    return
                self.set_destination_marker(route)
                self.draw_route(route)
                self.add_routing(route)
            else:
                logger.warn("Error occured: ", er)
                logger.warn(reply.errorString())
                self._add_qgis_msg('route could not be retrieved')
        finally:
            QtGui.QApplication.restoreOverrideCursor()

    def validate_response(self, route):
        if not validator.is_valid_route(route):
            self._add_qgis_msg(validator.ERROR_MSGS['invalid_route'])
            return False
        return True

    def draw_route(self, route):
        self.reset_rubberbands()

        self.draw_walking_route(route['start_walking_route'], self.start_walking_rubber_band)
        self.draw_public_transport_connection(route['public_transport_connection'], self.public_transport_rubber_band)
        self.draw_walking_route(route['end_walking_route'], self.end_walking_rubber_band)

    def draw_walking_route(self, route, rubber_band):
        if not route:
            return  # end walking route is optional

        for point in route['path']:
            rubber_band.addPoint(QgsPoint(point[0], point[1]))

    def draw_public_transport_connection(self, route, rubber_band):
        if not route:  # public transport route is optional
            return  # public transport route is optional

        for leg in route['path']:
            rubber_band.addPoint(QgsPoint(leg['start_position'][0], leg['start_position'][1]))
            for stopover in leg['stopovers']:
                rubber_band.addPoint(QgsPoint(stopover[0], stopover[1]))
            rubber_band.addPoint(QgsPoint(leg['exit_position'][0], leg['exit_position'][1]))

    def add_routing(self, route):
        self.routing_value.clear()
        self.add_start_pedestrian_routing(route)
        self.add_public_transport_routing(route)
        self.add_end_pedestrian_routing(route)

    def add_start_pedestrian_routing(self, route):
        if not route['public_transport_connection']:
            self.routing_value.append('By foot from start to destination')
        else:
            self.routing_value.append(u'By foot from start to {0}\n'.format(
                route['public_transport_connection']['path'][0]['name']))

    def add_public_transport_routing(self, route):
        if not route['public_transport_connection']:
            return
        for leg in route['public_transport_connection']['path']:
            values = defaultdict(str,
                                 line=leg['line'],
                                 platform=' on platform {0}'.format(leg['track']) if leg['track'] else '',
                                 start=leg['name'],
                                 destination=leg['destination'],
                                 departure=leg['departure'],
                                 arrival=leg['arrival'])
            leg_str = string.Formatter().vformat('Public transport with line {line}{platform} from {start} '
                                                 'to {destination} at {departure} arriving at {arrival}\n', (), values)
            self.routing_value.append(leg_str)

    def add_end_pedestrian_routing(self, route):
        if not route['public_transport_connection']:
            return
        self.routing_value.append(u'By foot from  {0} to destination\n'.format(
            route['public_transport_connection']['path'][-1]['destination']))

    def set_destination_marker(self, route):
        """
        Sets the destination marker.
        It's still necessary to set it, if the users provides an address as a destination.
        """
        last_route = 'end_walking_route'
        if not route[last_route]:
            # just a start walking route was provided
            last_route = 'start_walking_route'
        last_point = route[last_route]['path'][-1]
        self.canvas.scene().removeItem(self.destination_marker)
        self.destination_marker = self.set_vertex_marker(QgsPoint(last_point[0], last_point[1]))

    def reset_rubberbands(self):
        self.start_walking_rubber_band.reset(QGis.Line)
        self.public_transport_rubber_band.reset(QGis.Line)
        self.end_walking_rubber_band.reset(QGis.Line)

    def _add_qgis_msg(self, msg, level=QgsMessageBar.CRITICAL):
        self.iface.messageBar().pushMessage('Error', msg, level=level)
