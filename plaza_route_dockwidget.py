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
from ast import literal_eval

from PyQt4 import QtGui, uic, QtNetwork
from PyQt4.QtCore import pyqtSignal, Qt, QUrl

from qgis.core import QGis, QgsPoint
from qgis.gui import QgsRubberBand

import util.log_helper as logger

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'plaza_route_dockwidget_base.ui'))

PLAZA_ROUTING_URL = 'http://localhost:5000/api/route'


class PlazaRouteDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, iface, parent=None):
        super(PlazaRouteDockWidget, self).__init__(parent)
        self.setupUi(self)

        self.iface = iface
        self.network_access_manager = QtNetwork.QNetworkAccessManager()
        self.network_access_manager.finished.connect(self.handle_response)

        self.show_route_btn.clicked.connect(self.show_route)

        self.start_walking_rubber_band = QgsRubberBand(self.iface.mapCanvas(), QGis.Line)
        self.start_walking_rubber_band.setColor(QtGui.QColor(255, 0, 0, 128))
        self.start_walking_rubber_band.setWidth(4)

        self.end_walking_rubber_band = QgsRubberBand(self.iface.mapCanvas(), QGis.Line)
        self.end_walking_rubber_band.setColor(QtGui.QColor(255, 0, 0, 128))
        self.end_walking_rubber_band.setWidth(4)

        self.public_transport_rubber_band = QgsRubberBand(self.iface.mapCanvas(), QGis.Line)
        self.public_transport_rubber_band.setColor(QtGui.QColor(34, 139, 34, 128))
        self.public_transport_rubber_band.setWidth(4)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def show_route(self):
        QtGui.QApplication.setOverrideCursor(Qt.WaitCursor)
        self.get_route()

    def get_route(self):
        url = QUrl(PLAZA_ROUTING_URL)

        url.addQueryItem("start", literal_eval(self.star_value.text()))
        url.addQueryItem("destination", self.destination_value.text())
        url.addQueryItem("departure", "14:11")

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
        self.start_walking_rubber_band.reset(QGis.Line)
        self.public_transport_rubber_band.reset(QGis.Line)
        self.end_walking_rubber_band.reset(QGis.Line)

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
