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
from processing_iadb.utils import sph_executable, generate_batch_file, execute, dem2top


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

        sph_path = os.path.split(sph_executable())[0]

        feedback.pushInfo(self.tr("Copying input files…"))

        file_name = os.path.split(problem_file)[1]
        problem_file_name = os.path.join(sph_path, file_name)
        shutil.copyfile(problem_file, problem_file_name)

        file_name = os.path.split(data_file)[1]
        data_file_name = os.path.join(sph_path, file_name)
        shutil.copyfile(data_file, data_file_name)

        file_name = os.path.split(points_file)[1]
        points_file_name = os.path.join(sph_path, file_name)
        shutil.copyfile(points_file, points_file_name)

        file_name = os.path.split(dem.source())[1]
        dem_file_name = os.path.join(sph_path, f"{os.path.splitext(file_name)[0]}.top")
        #shutil.copyfile(dem, dem_file_name)
        dem2top(dem, dem_file_name)

        batch_file, input_file = generate_batch_file(os.path.splitext(file_name)[0])

        feedback.pushInfo(self.tr("Running SPH24…"))
        commands = ["wine", "cmd.exe", "/c", batch_file]
        execute(commands, feedback)

        feedback.pushInfo(self.tr("Copying output files…"))
        if not os.path.exists(output):
            os.mkdir(output)

        file_name = os.path.splitext(file_name)[0]
        for name in ("post.msh", "post.res"):
            output_name = os.path.join(sph_path, f"{file_name}.{name}")
            if os.path.exists(output_name):
                shutil.copy(output_name, output)

        feedback.pushInfo(self.tr("Cleanup…"))
        with os.scandir(sph_path) as it:
            for i in it:
                if i.is_file() and not i.name.lower() == "sph24.exe":
                    os.remove(os.path.join(sph_path, i.name))

        results = {self.OUTPUT: output}
        return results
