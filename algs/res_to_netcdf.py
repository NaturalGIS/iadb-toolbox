# -*- coding: utf-8 -*-

"""
***************************************************************************
    res_to_netcdf.py
    ---------------------
    Date                 : August 2024
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
    QgsProcessingParameterFile,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterRasterDestination,
)

from iadb_toolbox.algorithm import IadbAlgorithm
from iadb_toolbox.utils import res2netcdf


class ResToNetcdf(IadbAlgorithm):

    INPUT = "INPUT"
    DEM = "DEM"
    OUTPUT = "OUTPUT"

    def name(self):
        return "res2netcdf"

    def displayName(self):
        return self.tr("RES to netCDF")

    def group(self):
        return self.tr("Tools")

    def groupId(self):
        return "tools"

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT,
                self.tr("RES file"),
                fileFilter=self.tr("RES files (*.QGIS_res *.qgis_res)"),
            )
        )
        self.addParameter(QgsProcessingParameterRasterLayer(self.DEM, self.tr("DEM")))
        self.addParameter(
            QgsProcessingParameterRasterDestination(self.OUTPUT, self.tr("Output"))
        )

    def processAlgorithm(self, parameters, context, feedback):
        res_file = self.parameterAsFile(parameters, self.INPUT, context)
        dem = self.parameterAsRasterLayer(parameters, self.DEM, context)
        if dem is None:
            raise QgsProcessingException(self.invalidRasterError(parameters, self.DEM))

        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        res2netcdf(res_file, dem, output)

        return {self.OUTPUT: output}
