import logging
import os
import sys
import pkgutil
import importlib
import tempfile
import re

_KEY_REGEX = re.compile(r"(\?|&)(api_)?key=[^\s?&]*")

_DEBUG = "debug"
_INFO = "info"
_WARN = "warn"
_CRITICAL = "critical"


def remove_key(text):
    return _KEY_REGEX.sub("", text)


def get_temp_log_dir(path_extension=None):
    temp_log_dir = os.path.join(tempfile.gettempdir(), "plaza_routing")
    if not os.path.isdir(temp_log_dir):
        os.makedirs(temp_log_dir)
    if path_extension:
        temp_log_dir = os.path.join(temp_log_dir, path_extension)
    return temp_log_dir


def info(msg, *args):
    _log_message(msg, _INFO, *args)


def warn(msg, *args):
    _log_message(msg, _WARN, *args)


def critical(msg, *args):
    _log_message(msg, _CRITICAL, *args)


def debug(msg, *args):
    _log_message(msg, _DEBUG, *args)


def _log_message(msg, level, *args):
    try:
        msg = remove_key(msg.format(*args))

        if level == _INFO:
            _logger.info(msg)
        elif level == _WARN:
            _logger.warning(msg, *args)
        elif level == _CRITICAL:
            _logger.exception(msg)
        elif level == _DEBUG:
            _logger.debug(msg)

        _log_to_qgis(msg, level)
    except:
        _logger.info("Unexpected error during logging: {}", sys.exc_info()[1])
        _logger.info("Original message: '{}', params: '{}'", args)


def _import_qgis():
    if pkgutil.find_loader("qgis.core") is not None:
        return importlib.import_module("qgis.core")
    return None


def _log_to_qgis(msg, level):
    qgis = _import_qgis()
    if not qgis:
        return

    qgis_level = None
    if level == _DEBUG:
        pass
    elif level == _INFO:
        qgis_level = qgis.QgsMessageLog.INFO
    elif level == _WARN:
        qgis_level = qgis.QgsMessageLog.WARNING
    elif level == _CRITICAL:
        qgis_level = qgis.QgsMessageLog.CRITICAL

    if qgis_level is not None:
        qgis.QgsMessageLog.logMessage(msg, 'PlazaRouting', qgis_level)


try:
    log_path = get_temp_log_dir("plaza_routing_log.txt")
    temp_dir = os.path.dirname(log_path)
    if not os.path.isfile(log_path):
        open(log_path, 'a').close()
    logging.basicConfig(
        filename=log_path,
        format="[%(asctime)s] [%(threadName)-12s] [%(levelname)-8s]  %(message)s")
except IOError:
    _log_to_qgis("Creating logging config failed: {}".format(sys.exc_info(), _WARN))


_logger = logging.getLogger("PlazaRouting")
