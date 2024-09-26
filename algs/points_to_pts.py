# -*- coding: utf-8 -*-

"""
***************************************************************************
    points_to_pts.py
    ---------------------
    Date                 : September 2024
    Copyright            : (C) 2024 by NaturalGIS
    Email                : info at naturalgis dot pt
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

import os
import shutil

from qgis.core import (
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFileDestination,
)

from iadb_toolbox.algorithm import IadbAlgorithm
from iadb_toolbox.utils import points_to_pts


class PointsToPts(IadbAlgorithm):

    INPUT = "INPUT"
    FIELD = "FIELD"
    USE_Z = "USE_Z"
    OUTPUT = "OUTPUT"

    def name(self):
        return "points2pts"

    def displayName(self):
        return self.tr("Points to PTS")

    def group(self):
        return self.tr("Tools")

    def groupId(self):
        return "tools"

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT, self.tr("Points"), [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterField(self.FIELD, self.tr("Height field"), parentLayerParameterName=self.INPUT, type=QgsProcessingParameterField.Numeric, optional=True))
        self.addParameter(QgsProcessingParameterBoolean(self.USE_Z, self.tr("Use Z value as a height")))
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT, self.tr("Output"), self.tr("PTS files (*.pts *.PTS)")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(
                self.invalidSourceError(parameters, self.INPUT)
            )

        field = None
        if self.FIELD in parameters and parameters[self.FIELD] is not None:
            field = self.parameterAsString(parameters, self.FIELD, context)
        use_z = self.parameterAsBoolean(parameters, self.USE_Z, context)
        output = self.parameterAsFileOutput(parameters, self.OUTPUT, context)

        points_to_pts(source, field, use_z, output)

        results = {self.OUTPUT: output}
        return results
