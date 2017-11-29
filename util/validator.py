# -*- coding: utf-8 -*-

import re

COORDINATE_RX = re.compile(r'^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$')
TIME_RX = re.compile(r'^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$')

ERROR_MSGS = {
    'empty_field':          'missing values',
    'invalid_coordinate':   'invalid coordinate format',
    'invalid_departure':    'invalid time format: {H:M}',
    'invalid_route':        'no route was returned'
}


def has_empty_fields(*fields):
    for field in fields:
        if not field:
            return True
    return False


def is_valid_coordinate(coordinate):
    return bool(COORDINATE_RX.match(coordinate))


def is_valid_departure(departure):
    return bool(TIME_RX.match(departure))


def is_valid_route(route):
    return bool(route['start_walking_route'])
