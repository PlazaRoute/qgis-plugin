import re

COORDINATE_RX = re.compile(r'^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$')
TIME_RX = re.compile(r'^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$')


def validate_not_empty(*fields):
    for field in fields:
        if not field:
            return 'missing values'
    return ''


def validate_coordinate(coordinate):
    if not COORDINATE_RX.match(coordinate):
        return 'invalid coordinate format'
    return ''


def validate_time(time):
    if not TIME_RX.match(time):
        return 'invalid time format'
    return ''


def validate_route(route):
    if not route['start_walking_route']:
        return 'no route was returned'
    return ''
