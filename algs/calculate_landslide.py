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
    generate_data_file,
)


class CalculateLandslide(IadbAlgorithm):

    PROBLEM_NAME = "PROBLEM_NAME"

    DT = "DT"
    TIME_END = "TIME_END"
    PRINT_STEP = "PRINT_STEP"

    LAW_TYPE = "LAW_TYPE"
    CGRA = "CGRA"
    DENS = "DENS"
    CMANNING = "CMANNING"
    EROS_COEF = "EROS_COEF"
    NFRICT = "NFRICT"
    TAUY0 = "TAUY0"
    VISCO = "VISCO"
    TANFI8 = "TANFI8"

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
                self.tr("Analysis time step"),
                Qgis.ProcessingNumberParameterType.Double,
                0.1,
                minValue=1e-3,
                maxValue=1,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TIME_END,
                self.tr("Total analysis time"),
                Qgis.ProcessingNumberParameterType.Integer,
                1000,
                minValue=1,
                maxValue=10000,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PRINT_STEP,
                self.tr("Number of steps to print"),
                Qgis.ProcessingNumberParameterType.Integer,
                5,
                minValue=1,
                maxValue=100,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.LAW_TYPE,
                self.tr("law type"),
                Qgis.ProcessingNumberParameterType.Integer,
                7,
                minValue=1,
                maxValue=10,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.CGRA,
                self.tr("Gravity acceleration"),
                Qgis.ProcessingNumberParameterType.Double,
                9.81,
                minValue=1e-3,
                maxValue=10,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.DENS,
                self.tr("Density of the mixture"),
                Qgis.ProcessingNumberParameterType.Integer,
                2000,
                minValue=1000,
                maxValue=3000,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.CMANNING,
                self.tr("Voellmy’s coefficient of turbulent viscosity "),
                Qgis.ProcessingNumberParameterType.Integer,
                0,
                minValue=0,
                maxValue=100,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.EROS_COEF,
                self.tr("Erosion coefficient"),
                Qgis.ProcessingNumberParameterType.Integer,
                0,
                minValue=0,
                maxValue=100,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.NFRICT,
                self.tr("Rheological type to calculate basal friction"),
                Qgis.ProcessingNumberParameterType.Integer,
                7,
                minValue=0,
                maxValue=100,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TAUY0,
                self.tr("Bingham fluids cohesion"),
                Qgis.ProcessingNumberParameterType.Double,
                0,
                minValue=0,
                maxValue=100,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.VISCO,
                self.tr("Bingham fluids viscosity"),
                Qgis.ProcessingNumberParameterType.Double,
                0,
                minValue=0,
                maxValue=100,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TANFI8,
                self.tr("Tangents of the final friction angles"),
                Qgis.ProcessingNumberParameterType.Double,
                0.218,
                minValue=1e-3,
                maxValue=3.1415926,
            )
        )

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

        law_type = self.parameterAsInt(parameters, self.LAW_TYPE, context)
        cgra = self.parameterAsInt(parameters, self.CGRA, context)
        dens = self.parameterAsInt(parameters, self.DENS, context)
        cmanning = self.parameterAsInt(parameters, self.CMANNING, context)
        eros_coef = self.parameterAsInt(parameters, self.EROS_COEF, context)
        nfrict = self.parameterAsInt(parameters, self.NFRICT, context)
        tauy0 = self.parameterAsInt(parameters, self.TAUY0, context)
        visco = self.parameterAsInt(parameters, self.VISCO, context)
        tanfi8 = self.parameterAsInt(parameters, self.TANFI8, context)

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
            "law_type": law_type,
            "cgra": cgra,
            "dens": dens,
            "cmanning": cmanning,
            "eros_coef": eros_coef,
            "nfrict": nfrict,
            "tauy0": tauy0,
            "visco": visco,
            "tanfi8": tanfi8,
        }

        feedback.pushInfo(self.tr("Preparing inputs…"))
        work_dir = copy_inputs(points_file, dem, problem_name)
        generate_master_file(
            os.path.join(work_dir, f"{problem_name}.MASTER.DAT"), params
        )
        generate_data_file(os.path.join(work_dir, f"{problem_name}.DAT"), params)
        batch_file = generate_batch_file(work_dir, problem_name)

        feedback.pushInfo(self.tr("Running SPH model…"))
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
        #shutil.rmtree(work_dir)

        results = {self.OUTPUT: output}
        return results
