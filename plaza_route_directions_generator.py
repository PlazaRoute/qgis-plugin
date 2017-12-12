# -*- coding: utf-8 -*-
from collections import defaultdict
import string
from datetime import datetime


class PlazaRouteDirectionsGenerator:

    def __init__(self):
        pass

    def generate_directions(self, route):
        directions = list()
        directions.extend(self._generate_start_pedestrian_directions(route))
        directions.extend(self._generate_public_transport_directions(route))
        directions.extend(self._generate_end_pedestrian_directions(route))
        directions.extend(self._generate_creation_date())
        return ''.join(directions)

    def _generate_start_pedestrian_directions(self, route):
        directions = list()
        if not route['public_transport_connection']:
            directions.append("Walk from start to destination")
        else:
            directions.append(u"Walk from start to {0}".format(
                route['public_transport_connection']['path'][0]['start']))
        directions.append(self._generate_line_break())
        return directions

    def _generate_public_transport_directions(self, route):
        directions = list()
        if not route['public_transport_connection']:
            return directions
        for leg in route['public_transport_connection']['path']:
            values = defaultdict(str,
                                 line=leg['line'],
                                 platform=' on platform {0}'.format(leg['track']) if leg['track'] else '',
                                 start=leg['start'],
                                 destination=leg['destination'],
                                 departure=leg['departure'],
                                 arrival=leg['arrival'])
            leg_str = string.Formatter().vformat("Public transport with line {line}{platform} from {start} "
                                                 "to {destination} at {departure}, arriving at {arrival}", (), values)
            directions.append(leg_str)
            directions.append(self._generate_line_break())
        return directions

    def _generate_end_pedestrian_directions(self, route):
        directions = list()
        if not route['public_transport_connection']:
            return directions
        directions.append(u"Walk from {0} to destination".format(
            route['public_transport_connection']['path'][-1]['destination']))
        directions.append(self._generate_line_break())
        return directions

    def _generate_creation_date(self):
        return u"directions generated on {:%Y-%m-%d %H:%M:%S}".format(datetime.now())

    def _generate_line_break(self):
        return u"\n\n"
