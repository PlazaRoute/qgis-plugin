from ast import literal_eval

from qgis.core import QgsPoint, QgsCoordinateTransform, QgsCoordinateReferenceSystem


class PointTransformer:

    def __init__(self, iface):
        self.iface = iface
        self.project_crs_id = self.iface.mapCanvas().mapRenderer().destinationCrs().postgisSrid()
        self.project_crs = QgsCoordinateReferenceSystem(self.project_crs_id)
        self.base_crs = QgsCoordinateReferenceSystem(4326)  # WGS 84
        self.transformer = QgsCoordinateTransform(self.project_crs, self.base_crs)

    def transform_project_to_base_crs(self, point):
        self._update_transformer()
        return self.transformer.transform(point)

    def transform_project_to_base_crs_str(self, point):
        transformed_point = self.transform_project_to_base_crs(point)
        return self.point_to_str(transformed_point)

    def transform_base_to_project_crs(self, point):
        self._update_transformer()
        return self.transformer.transform(point, QgsCoordinateTransform.ReverseTransform)

    def transform_base_to_project_crs_str(self, point):
        transformed_point = self.transform_base_to_project_crs(point)
        return self.point_to_str(transformed_point)

    def str_to_tuple(self, value):
        return literal_eval(value)

    def point_to_str(self, point):
        return '{0},{1}'.format(point.x(), point.y())

    def str_to_point(self, value):
        parsed_point = self.str_to_tuple(value)
        return QgsPoint(parsed_point[0], parsed_point[1])

    def _update_transformer(self):
        """ checks if the project crs has changed in the meantime and updates the project crs if it has """
        new_project_crs_id = self.iface.mapCanvas().mapRenderer().destinationCrs()
        if new_project_crs_id != self.project_crs_id:
            self.project_crs_id = new_project_crs_id
            self.project_crs = QgsCoordinateReferenceSystem(self.project_crs_id)
            self.transformer = QgsCoordinateTransform(self.project_crs_id, self.base_crs)
