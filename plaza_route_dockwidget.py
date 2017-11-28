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
import re

from PyQt4 import QtGui, uic, QtNetwork
from PyQt4.QtCore import pyqtSignal, Qt, QUrl, QTime

from qgis.core import QGis, QgsPoint
from qgis.gui import QgsRubberBand, QgsMapToolEmitPoint, QgsVertexMarker, QgsMessageBar

import util.log_helper as logger

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'plaza_route_dockwidget_base.ui'))

PLAZA_ROUTING_URL = 'http://localhost:5000/api/route'

RED = QtGui.QColor(255, 0, 0, 128)
GREEN = QtGui.QColor(34, 139, 34, 128)
RUBBER_BAND_WIDTH = 4

COORDINATE_RX = re.compile(r'^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$')
TIME_RX = re.compile(r'^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$')

class PlazaRouteDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()
    start_vertex = None

    def __init__(self, iface, parent=None):
        super(PlazaRouteDockWidget, self).__init__(parent)
        self.setupUi(self)
        self.init_gui_values()

        self.iface = iface
        self.network_access_manager = QtNetwork.QNetworkAccessManager()
        self.network_access_manager.finished.connect(self.handle_response)

        # create the map tool to handle clicks on a map in QGIS
        self.canvas = self.iface.mapCanvas()
        self.point_tool = QgsMapToolEmitPoint(self.canvas)
        self.show_crosshairs()

        # register events
        self.reset_btn.clicked.connect(self.reset)
        self.start_select_btn.clicked.connect(self.show_crosshairs)
        self.point_tool.canvasClicked.connect(self.display_point)
        self.show_route_btn.clicked.connect(self.show_route)

        self.start_walking_rubber_band = self.setup_rubber_band(QGis.Line, RED, RUBBER_BAND_WIDTH)
        self.end_walking_rubber_band = self.setup_rubber_band(QGis.Line, RED, RUBBER_BAND_WIDTH)
        self.public_transport_rubber_band = self.setup_rubber_band(QGis.Line, GREEN, RUBBER_BAND_WIDTH)

    def init_gui_values(self):
        current_time = QTime()
        current_time.start()
        self.departure_value.setTime(current_time)

    def setup_rubber_band(self, geometry_type, color, width):
        rubber_band = QgsRubberBand(self.canvas, geometry_type)
        rubber_band.setColor(color)
        rubber_band.setWidth(width)
        return rubber_band

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def set_vertex_marker(self, point):
        marker = QgsVertexMarker(self.canvas)
        marker.setColor(QtGui.QColor(0, 255, 0))
        marker.setIconSize(5)
        marker.setIconType(QgsVertexMarker.ICON_X)  # or ICON_CROSS, ICON_X
        marker.setPenWidth(3)
        marker.setCenter(point)
        return marker

    def reset(self):
        self.reset_bubberbands()

    def show_crosshairs(self):
        self.canvas.setMapTool(self.point_tool)

    def display_point(self, point, button):
        coordinates = "{}, {}".format(point.x(), point.y())
        self.start_value.setText(str(coordinates))
        if self.start_vertex:
            self.canvas.scene().removeItem(self.start_vertex)
        self.start_vertex = self.set_vertex_marker(QgsPoint(point.x(), point.y()))

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
        if not self.start_value.text() or not self.destination_value.text() or not self.departure_value.text():
            self.add_qgis_msg('missing values')
            return False

        if not COORDINATE_RX.match(self.start_value.text()):
            self.add_qgis_msg('invalid coordinate format')
            return False

        if not TIME_RX.match(self.departure_value.text()):
            self.add_qgis_msg('invalid time format')
            return False
        return True

    def handle_response(self, reply):
        er = reply.error()

        try:
            if er == QtNetwork.QNetworkReply.NoError:
                bytes_string = reply.readAll()
                route = json.loads(str(bytes_string))
                self.draw_route(route)
            else:
                logger.warn("Error occured: ", er)
                logger.warn(reply.errorString())
                self.add_qgis_msg(reply.errorString())
        finally:
            QtGui.QApplication.restoreOverrideCursor()

    def draw_route(self, route):
        self.reset_bubberbands()

        self.draw_walking_route(route['start_walking_route'], self.start_walking_rubber_band)
        self.draw_public_transport_connection(route['public_transport_connection'], self.public_transport_rubber_band)
        self.draw_walking_route(route['end_walking_route'], self.end_walking_rubber_band)

    def draw_walking_route(self, route, rubber_band):
        if not route:
            # error should be thrown
            return

        for point in route['path']:
            rubber_band.addPoint(QgsPoint(point[0], point[1]))

    def draw_public_transport_connection(self, route, rubber_band):
        if not route:
            return

        for leg in route['path']:
            rubber_band.addPoint(QgsPoint(leg['start_position'][0], leg['start_position'][1]))
            for stopover in leg['stopovers']:
                rubber_band.addPoint(QgsPoint(stopover[0], stopover[1]))
            rubber_band.addPoint(QgsPoint(leg['exit_position'][0], leg['exit_position'][1]))

    def set_destination_marker(self):
        pass

    def reset_bubberbands(self):
        self.start_walking_rubber_band.reset(QGis.Line)
        self.public_transport_rubber_band.reset(QGis.Line)
        self.end_walking_rubber_band.reset(QGis.Line)

    def add_qgis_msg(self, msg, level=QgsMessageBar.CRITICAL):
        self.iface.messageBar().pushMessage('Error', msg, level=level)