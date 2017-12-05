from qgis.core import QgsPoint


class PlazaRouteRouteDrawer:

    def __init__(self):
        pass

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
