# -*- coding: utf-8 -*-

"""
***************************************************************************
    provider.py
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

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication

from qgis.core import QgsProcessingProvider

from processing.core.ProcessingConfig import ProcessingConfig, Setting

from iadb_toolbox.algs.dem_to_top import DemToTop
from iadb_toolbox.algs.sph_simple_mode import SphSimpleMode
from iadb_toolbox.algs.sph_advanced_mode import SphAdvancedMode
from iadb_toolbox.utils import PLUGIN_ROOT, SPH_EXECUTABLE, sph_executable


class IadbProvider(QgsProcessingProvider):
    def __init__(self):
        super().__init__()
        self.algs = list()

    def id(self):
        return "iadb"

    def name(self):
        return "IADB"

    def longName(self):
        return "IADB"

    def icon(self):
        return QIcon(os.path.join(PLUGIN_ROOT, "icons", "iadb.svg"))

    def load(self):
        ProcessingConfig.settingIcons[self.name()] = self.icon()
        ProcessingConfig.addSetting(
            Setting(
                self.name(),
                SPH_EXECUTABLE,
                self.tr("SPH executable"),
                sph_executable(),
                valuetype=Setting.FILE,
            )
        )
        ProcessingConfig.readSettings()
        self.refreshAlgorithms()
        return True

    def unload(self):
        ProcessingConfig.removeSetting(SPH_EXECUTABLE)

    def loadAlgorithms(self):
        self.algs = [DemToTop(), SphAdvancedMode(), SphSimpleMode()]
        for a in self.algs:
            self.addAlgorithm(a)

    def supportsNonFileBasedOutput(self):
        return False

    def tr(self, string):
        return QCoreApplication.translate(self.__class__.__name__, string)
