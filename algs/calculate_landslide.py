# -*- coding: utf-8 -*-

"""
***************************************************************************
    calculate_landslide.py
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
    QgsProcessingParameterFile,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFolderDestination,
)

from processing.core.ProcessingConfig import ProcessingConfig

from processing_iadb.algorithm import IadbAlgorithm
from processing_iadb.utils import sph_executable, generate_batch_file, execute, copy_inputs


class CalculateLandslide(IadbAlgorithm):

    INPUT = "INPUT"
    DATA = "DATA"
    POINTS = "POINTS"
    DEM = "DEM"
    OUTPUT = "OUTPUT"

    def name(self):
        return "calculatelandslide"

    def displayName(self):
        return self.tr("Calculate landslide")

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFile(self.INPUT, self.tr("Global problem file")))
        self.addParameter(QgsProcessingParameterFile(self.DATA, self.tr("Data file")))
        self.addParameter(QgsProcessingParameterFile(self.POINTS, self.tr("Points file")))
        self.addParameter(QgsProcessingParameterRasterLayer(self.DEM, self.tr("DEM file")))
        self.addParameter(QgsProcessingParameterFolderDestination(self.OUTPUT, self.tr("Output folder")))

    def processAlgorithm(self, parameters, context, feedback):
        problem_file = self.parameterAsFile(parameters, self.INPUT, context)
        data_file = self.parameterAsFile(parameters, self.DATA, context)
        points_file = self.parameterAsFile(parameters, self.POINTS, context)

        dem = self.parameterAsRasterLayer(parameters, self.DEM, context)
        if dem is None:
            raise QgsProcessingException(self.invalidRasterError(parameters, self.DEM))

        output = self.parameterAsString(parameters, self.OUTPUT, context)

        feedback.pushInfo(self.tr("Copying files…"))
        work_dir = copy_inputs(problem_file, data_file, points_file, dem)
        batch_file = generate_batch_file(work_dir, "Frank")

        feedback.pushInfo(self.tr("Running SPH24…"))
        commands = ["wine", "cmd.exe", "/c", batch_file]
        execute(commands, feedback)

        feedback.pushInfo(self.tr("Copying output files…"))
        if not os.path.exists(output):
            os.mkdir(output)

        for name in ("post.msh", "post.res"):
            output_name = os.path.join(work_dir, f"Frank.{name}")
            if os.path.exists(output_name):
                shutil.copy(output_name, output)

        feedback.pushInfo(self.tr("Cleanup…"))
        shutil.rmtree(work_dir)

        results = {self.OUTPUT: output}
        return results
