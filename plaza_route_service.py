import json
from PyQt4 import QtNetwork
from PyQt4.QtCore import QUrl

from util import log_helper as logger
from util import validator as validator


class PlazaRouteService:

    def __init__(self, plaza_routing_url, route_handler, error_handler):
        self.plaza_routing_url = plaza_routing_url
        self.route_handler = route_handler
        self.error_handler = error_handler
        self.network_access_manager = QtNetwork.QNetworkAccessManager()
        self.network_access_manager.finished.connect(self.handle_response)

    def get_route(self, start, destination, departure, precise_public_transport_stops):
        url = QUrl(self.plaza_routing_url)
        url.addQueryItem("start", start)
        url.addQueryItem("destination", destination)
        url.addQueryItem("departure", departure)
        url.addQueryItem("precise_public_transport_stops", str(precise_public_transport_stops))

        logger.info(str(url.encodedQuery()))
        req = QtNetwork.QNetworkRequest(url)

        self.network_access_manager.get(req)

    def handle_response(self, reply):
        er = reply.error()

        try:
            if er == QtNetwork.QNetworkReply.NoError:
                bytes_string = reply.readAll()
                route = json.loads(str(bytes_string))
                if not validator.is_valid_route(route):
                    self.error_handler(validator.ERROR_MSGS['invalid_route'])
                    return
                self.route_handler(route)
            else:
                logger.warn("Error occured: ", er)
                logger.warn(reply.errorString())
                self.error_handler("route could not be retrieved")
        except Exception as ex:
            self.error_handler(ex)