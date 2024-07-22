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
    Qgis,
    QgsProcessingException,
    QgsProcessingParameterFile,
    QgsProcessingParameterString,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFolderDestination,
)

from processing.core.ProcessingConfig import ProcessingConfig

from processing_iadb.algorithm import IadbAlgorithm
from processing_iadb.utils import (
    generate_batch_file,
    execute,
    copy_inputs,
    generate_master_file,
)


class CalculateLandslide(IadbAlgorithm):

    PROBLEM_NAME = "PROBLEM_NAME"
    DT = "DT"
    TIME_END = "TIME_END"
    PRINT_STEP = "PRINT_STEP"

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
        self.addParameter(
            QgsProcessingParameterString(self.PROBLEM_NAME, self.tr("Problem name"))
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.DT,
                self.tr("dt"),
                Qgis.ProcessingNumberParameterType.Double,
                0.1,
                minValue=1e-3,
                maxValue=1,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TIME_END,
                self.tr("time_end"),
                Qgis.ProcessingNumberParameterType.Integer,
                120,
                minValue=1,
                maxValue=1000,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PRINT_STEP,
                self.tr("print_step"),
                Qgis.ProcessingNumberParameterType.Integer,
                10,
                minValue=1,
                maxValue=100,
            )
        )

        self.addParameter(QgsProcessingParameterFile(self.DATA, self.tr("Data file")))
        self.addParameter(
            QgsProcessingParameterFile(self.POINTS, self.tr("Points file"))
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(self.DEM, self.tr("DEM file"))
        )
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT, self.tr("Output folder")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        problem_name = self.parameterAsString(parameters, self.PROBLEM_NAME, context)
        dt = self.parameterAsDouble(parameters, self.DT, context)
        time_end = self.parameterAsInt(parameters, self.TIME_END, context)
        print_step = self.parameterAsInt(parameters, self.PRINT_STEP, context)

        data_file = self.parameterAsFile(parameters, self.DATA, context)
        points_file = self.parameterAsFile(parameters, self.POINTS, context)

        dem = self.parameterAsRasterLayer(parameters, self.DEM, context)
        if dem is None:
            raise QgsProcessingException(self.invalidRasterError(parameters, self.DEM))

        output = self.parameterAsString(parameters, self.OUTPUT, context)

        params = {
            "problem_name": problem_name,
            "dt": dt,
            "time_end": time_end,
            "print_step": print_step,
        }

        feedback.pushInfo(self.tr("Copying files…"))
        work_dir = copy_inputs(data_file, points_file, dem)
        generate_master_file(
            os.path.join(work_dir, f"{problem_name}.MASTER.DAT"), params
        )
        batch_file = generate_batch_file(work_dir, problem_name)

        feedback.pushInfo(self.tr("Running SPH24…"))
        commands = ["wine", "cmd.exe", "/c", batch_file]
        execute(commands, feedback)

        feedback.pushInfo(self.tr("Copying output files…"))
        if not os.path.exists(output):
            os.mkdir(output)

        for suffix in ("post.msh", "post.res"):
            output_name = os.path.join(work_dir, f"{problem_name}.{suffix}")
            if os.path.exists(output_name):
                shutil.copy(output_name, output)

        feedback.pushInfo(self.tr("Cleanup…"))
        shutil.rmtree(work_dir)

        results = {self.OUTPUT: output}
        return results
