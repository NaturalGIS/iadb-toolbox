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
    C1_GRAW = "C1_GRAW"
    C2_DENS = "C2_DENS"
    C3_VOELMY = "C3_VOELMY"
    C4_HUNGR = "C4_HUNGR"
    C5_FRIC = "C5_FRIC"
    C6_TAUY = "C6_TAUY"
    C8_VISCO = "C8_VISCO"
    C9_TANFI = "C9_TANFI"

    #DATA = "DATA"
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

        self.addParameter(QgsProcessingParameterNumber(self.LAW_TYPE, self.tr("law type"), Qgis.ProcessingNumberParameterType.Integer, 7, minValue=1, maxValue=10))
        self.addParameter(QgsProcessingParameterNumber(self.C1_GRAW, self.tr("C1 graw"), Qgis.ProcessingNumberParameterType.Double, 9.81, minValue=1e-3, maxValue=10))
        self.addParameter(QgsProcessingParameterNumber(self.C2_DENS, self.tr("C2 dens"), Qgis.ProcessingNumberParameterType.Integer, 2000, minValue=1, maxValue=10000))
        self.addParameter(QgsProcessingParameterNumber(self.C3_VOELMY, self.tr("C3 voellmy"), Qgis.ProcessingNumberParameterType.Integer, 0, minValue=0, maxValue=100))
        self.addParameter(QgsProcessingParameterNumber(self.C4_HUNGR, self.tr("C4 hungr"), Qgis.ProcessingNumberParameterType.Integer, 0, minValue=0, maxValue=100))
        self.addParameter(QgsProcessingParameterNumber(self.C5_FRIC, self.tr("C5 fric"), Qgis.ProcessingNumberParameterType.Integer, 7, minValue=0, maxValue=100))
        self.addParameter(QgsProcessingParameterNumber(self.C6_TAUY, self.tr("C6 tauy"), Qgis.ProcessingNumberParameterType.Double, 0, minValue=0, maxValue=100))
        self.addParameter(QgsProcessingParameterNumber(self.C8_VISCO, self.tr("C8 visco"), Qgis.ProcessingNumberParameterType.Double, 0, minValue=0, maxValue=100))
        self.addParameter(QgsProcessingParameterNumber(self.C9_TANFI, self.tr("C9 tanfi"), Qgis.ProcessingNumberParameterType.Double, 0.218, minValue=0, maxValue=1))

        #self.addParameter(QgsProcessingParameterFile(self.DATA, self.tr("Data file")))
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
        c1_graw = self.parameterAsInt(parameters, self.C1_GRAW, context)
        c2_dens = self.parameterAsInt(parameters, self.C2_DENS, context)
        c3_voelmy = self.parameterAsInt(parameters, self.C3_VOELMY, context)
        c4_hungr = self.parameterAsInt(parameters, self.C4_HUNGR, context)
        c5_fric = self.parameterAsInt(parameters, self.C5_FRIC, context)
        c6_tauy = self.parameterAsInt(parameters, self.C6_TAUY, context)
        c8_visco = self.parameterAsInt(parameters, self.C8_VISCO, context)
        c9_tanfi = self.parameterAsInt(parameters, self.C9_TANFI, context)

        #data_file = self.parameterAsFile(parameters, self.DATA, context)
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
            "c1_graw": c1_graw,
            "c2_dens": c2_dens,
            "c3_voelmy": c3_voelmy,
            "c4_hungr": c4_hungr,
            "c5_fric": c5_fric,
            "c6_tauy": c6_tauy,
            "c8_visco": c8_visco,
            "c9_tanfi": c9_tanfi,
        }

        feedback.pushInfo(self.tr("Copying files…"))
        work_dir = copy_inputs(points_file, dem)
        generate_master_file(
            os.path.join(work_dir, f"{problem_name}.MASTER.DAT"), params
        )
        generate_data_file(os.path.join(work_dir, f"{problem_name}.DAT"), params)
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
