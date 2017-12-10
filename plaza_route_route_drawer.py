# -*- coding: utf-8 -*-
from qgis.core import QgsPoint


class PlazaRouteRouteDrawer:

    def __init__(self, point_transformer):
        self.point_transformer = point_transformer

    def draw_walking_route(self, route, rubber_band):
        if not route:
            return  # end walking route is optional
        for point in route['path']:
            self._add_point(QgsPoint(point[0], point[1]), rubber_band)

    def draw_public_transport_connection(self, route, rubber_band):
        if not route:  # public transport connection is optional
            return  # public transport connection is optional

        for leg in route['path']:
            self._add_point(QgsPoint(leg['start_position'][0], leg['start_position'][1]), rubber_band)

            for stopover in leg['stopovers']:
                self._add_point(QgsPoint(stopover[0], stopover[1]), rubber_band)

            self._add_point(QgsPoint(leg['exit_position'][0], leg['exit_position'][1]), rubber_band)

    def _add_point(self, point, rubber_band):
        """ transforms the point to the projects coordinate system and adds it to the rubber band"""
        rubber_band.addPoint(self.point_transformer.transform_base_to_project_crs(point))
