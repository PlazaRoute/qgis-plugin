# -*- coding: utf-8 -*-
import json
from PyQt4 import QtNetwork
from PyQt4.QtCore import QUrl


from util import log_helper as logger
from util import validator as validator


class PlazaRouteRoutingService:

    def __init__(self, route_handler, error_handler, config):
        self.route_handler = route_handler
        self.error_handler = error_handler
        self.config = config
        self.network_access_manager = QtNetwork.QNetworkAccessManager()
        self.network_access_manager.finished.connect(self.handle_response)

    def get_route(self, start, destination, departure, precise_public_transport_stops):
        url = QUrl(self._get_plaza_routing_url())
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
                    self.error_handler(validator.ERROR_MSGS["invalid_route"])
                    return
                self.route_handler(route)
            else:
                self._handle_response_error(reply)
        except Exception as ex:
            logger.warn(str(ex))
            self.error_handler("unknown error occurred during retrieving the route, see log for more details")

    def _handle_response_error(self, reply):
        error_code = reply.error()
        log_msg = None
        if error_code == QtNetwork.QNetworkReply.ConnectionRefusedError:
            error_msg = 'server at {} is unavailable, make sure that the right server url was configured' \
                .format(self._get_plaza_routing_url())
        elif error_code == QtNetwork.QNetworkReply.UnknownContentError:
            error_msg = "third party service is temporarily unavailable " \
                        "or the server rejected the provided parameters"
        else:
            log_msg = "unknown error with code {0} occurred: {1}".format(error_code, reply.errorString())
            error_msg = "route could not be retrieved, see log for more details"
        if error_msg:
            logger.warn(error_msg if not log_msg else log_msg)
            self.error_handler(error_msg)

    def update_config(self, config):
        self.config = config

    def _get_plaza_routing_url(self):
        return self.config.get('plazaroute', 'plaza_routing_url')
