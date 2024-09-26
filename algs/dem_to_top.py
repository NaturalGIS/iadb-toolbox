# -*- coding: utf-8 -*-

"""
***************************************************************************
    dem_to_top.py
    ---------------------
    Date                 : July 2024
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
    QgsProcessingException,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFileDestination,
)

from iadb_toolbox.algorithm import IadbAlgorithm
from iadb_toolbox.utils import dem_to_top


class DemToTop(IadbAlgorithm):

    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

    def name(self):
        return "dem2top"

    def displayName(self):
        return self.tr("DEM to TOP")

    def group(self):
        return self.tr("Tools")

    def groupId(self):
        return "tools"

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT, self.tr("DEM")))
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT, self.tr("Output"), self.tr("TOP files (*.top *.TOP)")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        dem = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        if dem is None:
            raise QgsProcessingException(
                self.invalidRasterError(parameters, self.INPUT)
            )

        output = self.parameterAsFileOutput(parameters, self.OUTPUT, context)

        dem_to_top(dem, output)

        results = {self.OUTPUT: output}
        return results
