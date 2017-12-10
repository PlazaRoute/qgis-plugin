# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PlazaRoute
                                 A QGIS plugin
 Pedestrian and Public Transport Routing
                             -------------------
        begin                : 2017-11-14
        copyright            : (C) 2017 by Jonas Matter / Robin Suter
        email                : robin@robinsuter.ch
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


def classFactory(iface):
    """Load PlazaRoute class from file PlazaRoute.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """

    from .plaza_route import PlazaRoute
    return PlazaRoute(iface)
