# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PlazaRoute
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
import os.path

from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt4.QtGui import QAction, QIcon

# Initialize Qt resources from file resources.py
import resources

from plaza_route_dockwidget import PlazaRouteDockWidget

# setup debugging
# pth = '/opt/dev/ide/pycharm-2017.2.4/debug-eggs/pycharm-debug.egg'
# import sys
# if pth not in sys.path:
#     sys.path.append(pth)
# import pydevd
# pydevd.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True)


class PlazaRoute:

    def __init__(self, iface):
        self.iface = iface

        self.plugin_dir = os.path.dirname(__file__)

        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'PlazaRoute_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr(u'&PlazaRoute')
        self.toolbar = self.iface.addToolBar(u'PlazaRoute')
        self.toolbar.setObjectName(u'PlazaRoute')

        self.pluginIsActive = False
        self.dockwidget = None

    def tr(self, message):
        """
        Get the translation for a string using Qt translation API.
        We implement this ourselves since we do not inherit QObject.
        """
        return QCoreApplication.translate('PlazaRoute', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """ Add a toolbar icon to the toolbar. """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """ Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = ':/plugins/PlazaRoute/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Plaza Routing'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def onClosePlugin(self):
        """ Cleanup necessary items here when plugin dockwidget is closed"""

        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)
        self.pluginIsActive = False

    def unload(self):
        """ Removes the plugin menu item and icon from QGIS GUI."""

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&PlazaRoute'),
                action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def run(self):
        """ Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True
            if not self.dockwidget:
                self.dockwidget = PlazaRouteDockWidget(self.iface)

            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

