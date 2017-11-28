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

from PyQt4 import QtGui, uic, QtNetwork
from PyQt4.QtCore import pyqtSignal, Qt, QUrl, QTime

from qgis.core import QGis, QgsPoint
from qgis.gui import QgsRubberBand, QgsMapToolEmitPoint

import util.log_helper as logger

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'plaza_route_dockwidget_base.ui'))

PLAZA_ROUTING_URL = 'http://localhost:5000/api/route'

RED = QtGui.QColor(255, 0, 0, 128)
GREEN = QtGui.QColor(34, 139, 34, 128)
RUBBER_BAND_WIDTH = 4


class PlazaRouteDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

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
        rubber_band = QgsRubberBand(self.iface.mapCanvas(), geometry_type)
        rubber_band.setColor(color)
        rubber_band.setWidth(width)
        return rubber_band

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def reset(self):
        self.reset_bubberbands()

    def show_crosshairs(self):
        self.canvas.setMapTool(self.point_tool)

    def display_point(self, point, button):
        coordinates = "{}, {}".format(point.x(), point.y())
        self.start_value.setText(str(coordinates))

    def show_route(self):
        QtGui.QApplication.setOverrideCursor(Qt.WaitCursor)

        url = QUrl(PLAZA_ROUTING_URL)
        url.addQueryItem("start", self.start_value.text())
        url.addQueryItem("destination", self.destination_value.text())
        url.addQueryItem("departure", self.departure_value.text())

        logger.info(str(url.encodedQuery()))
        req = QtNetwork.QNetworkRequest(url)

        self.network_access_manager.get(req)

    def handle_response(self, reply):
        logger.info("handle_response")
        er = reply.error()

        try:
            if er == QtNetwork.QNetworkReply.NoError:
                bytes_string = reply.readAll()
                route = json.loads(str(bytes_string))
                self.draw_route(route)
            else:
                logger.warn("Error occured: ", er)
                logger.warn(reply.errorString())
        finally:
            QtGui.QApplication.restoreOverrideCursor()

    def draw_route(self, route):
        self.reset_bubberbands()

        self.draw_walking_route(route['start_walking_route']['path'], self.start_walking_rubber_band)
        self.draw_public_transport_connection(route['public_transport_connection']['path'],
                                              self.public_transport_rubber_band)
        self.draw_walking_route(route['end_walking_route']['path'], self.end_walking_rubber_band)

    def draw_walking_route(self, points, rubber_band):
        for point in points:
            rubber_band.addPoint(QgsPoint(point[0], point[1]))

    def draw_public_transport_connection(self, legs, rubber_band):
        for leg in legs:
            rubber_band.addPoint(QgsPoint(leg['start_position'][0], leg['start_position'][1]))
            for stopover in leg['stopovers']:
                rubber_band.addPoint(QgsPoint(stopover[0], stopover[1]))
            rubber_band.addPoint(QgsPoint(leg['exit_position'][0], leg['exit_position'][1]))

    def reset_bubberbands(self):
        self.start_walking_rubber_band.reset(QGis.Line)
        self.public_transport_rubber_band.reset(QGis.Line)
        self.end_walking_rubber_band.reset(QGis.Line)
