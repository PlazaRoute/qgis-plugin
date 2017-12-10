# -*- coding: utf-8 -*-
from collections import defaultdict
import string
from datetime import datetime


class PlazaRouteRoutingGenerator:

    def __init__(self):
        pass

    def generate_routing(self, route):
        routing = list()
        routing.extend(self._generate_start_pedestrian_routing(route))
        routing.extend(self._generate_public_transport_routing(route))
        routing.extend(self._generate_end_pedestrian_routing(route))
        routing.extend(self._generate_routing_date())
        return ''.join(routing)

    def _generate_start_pedestrian_routing(self, route):
        routing = list()
        if not route['public_transport_connection']:
            routing.append("Walk from start to destination")
        else:
            routing.append(u"Walk from start to {0}".format(
                route['public_transport_connection']['path'][0]['name']))
        routing.append(self._generate_line_break())
        return routing

    def _generate_public_transport_routing(self, route):
        routing = list()
        if not route['public_transport_connection']:
            return routing
        for leg in route['public_transport_connection']['path']:
            values = defaultdict(str,
                                 line=leg['line'],
                                 platform=' on platform {0}'.format(leg['track']) if leg['track'] else '',
                                 start=leg['name'],
                                 destination=leg['destination'],
                                 departure=leg['departure'],
                                 arrival=leg['arrival'])
            leg_str = string.Formatter().vformat("Public transport with line {line}{platform} from {start} "
                                                 "to {destination} at {departure}, arriving at {arrival}", (), values)
            routing.append(leg_str)
            routing.append(self._generate_line_break())
        return routing

    def _generate_end_pedestrian_routing(self, route):
        routing = list()
        if not route['public_transport_connection']:
            return routing
        routing.append(u"Walk from {0} to destination".format(
            route['public_transport_connection']['path'][-1]['destination']))
        routing.append(self._generate_line_break())
        return routing

    def _generate_routing_date(self):
        return u"Routing generated on {:%Y-%m-%d %H:%M:%S}".format(datetime.now())

    def _generate_line_break(self):
        return u"\n\n"
