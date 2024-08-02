# -*- coding: utf-8 -*-

"""
***************************************************************************
    sph_simple_mode.py
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
    QgsProcessingParameterString,
    QgsProcessingParameterFolderDestination,
    QgsProcessingOutputFile,
)

from processing.core.ProcessingConfig import ProcessingConfig

from iadb_toolbox.algorithm import IadbAlgorithm
from iadb_toolbox.utils import (
    generate_batch_file,
    execute,
    copy_inputs,
    copy_outputs,
)


class SphSimpleMode(IadbAlgorithm):

    PROBLEM_NAME = "PROBLEM_NAME"
    MASTER_FILE = "MASTER_FILE"
    CONFIG_FILE = "CONFIG_FILE"
    PTS_FILE = "PTS_FILE"
    DEM = "DEM"
    OUTPUT = "OUTPUT"
    OUTPUT_FILE = "OUTPUT_FILE"

    def name(self):
        return "sphsimplemode"

    def displayName(self):
        return self.tr("SPH model (simple mode)")

    def group(self):
        return self.tr("Modeling")

    def groupId(self):
        return "modeling"

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterString(self.PROBLEM_NAME, self.tr("Problem name"))
        )
        self.addParameter(
            QgsProcessingParameterFile(self.MASTER_FILE, self.tr("Global problem file"), fileFilter=self.tr("DAT files (*.dat *.DAT)"))
        )
        self.addParameter(
            QgsProcessingParameterFile(self.CONFIG_FILE, self.tr("Configuration file"), fileFilter=self.tr("DAT files (*.dat *.DAT)"))
        )
        self.addParameter(
            QgsProcessingParameterFile(self.PTS_FILE, self.tr("Points file"), fileFilter=self.tr("PTS files (*.pts *.PTS)"))
        )
        self.addParameter(QgsProcessingParameterFile(self.DEM, self.tr("DEM"), fileFilter=self.tr("TOP files (*.top *.TOP)")))
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT, self.tr("Output folder")
            )
        )
        self.addOutput(QgsProcessingOutputFile(self.OUTPUT_FILE, self.tr("RES file")))

    def processAlgorithm(self, parameters, context, feedback):
        problem_name = self.parameterAsString(parameters, self.PROBLEM_NAME, context)

        master_file = self.parameterAsFile(parameters, self.MASTER_FILE, context)
        config_file = self.parameterAsFile(parameters, self.CONFIG_FILE, context)
        pts_file = self.parameterAsFile(parameters, self.PTS_FILE, context)
        dem = self.parameterAsFile(parameters, self.DEM, context)
        output = self.parameterAsString(parameters, self.OUTPUT, context)

        feedback.pushInfo(self.tr("Preparing inputs…"))
        work_dir = copy_inputs(problem_name, dem, pts_file, master_file, config_file)
        batch_file = generate_batch_file(problem_name, work_dir)

        feedback.pushInfo(self.tr("Running SPH model…"))
        commands = ["cmd.exe", "/c", batch_file]
        execute(commands, feedback)

        feedback.pushInfo(self.tr("Copying output files…"))
        copy_outputs(work_dir, problem_name, output)

        feedback.pushInfo(self.tr("Cleanup…"))
        shutil.rmtree(work_dir)

        return {
            self.OUTPUT: output,
            self.OUTPUT_FILE: os.path.join(output, f"{problem_name}.QGIS_res"),
        }
