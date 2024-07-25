# -*- coding: utf-8 -*-

"""
***************************************************************************
    test_utils.py
    ---------------------
    Date                 : July 2024
    Copyright            : (C) 2024 by Alexander Bruy
    Email                : alexander dot bruy at gmail dot com
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
import difflib
import tempfile

from qgis.core import (
    QgsRasterLayer,
)
from qgis.testing import start_app, QgisTestCase

from processing_iadb.utils import (
    dem2top,
    generate_master_file,
    generate_data_file,
    generate_batch_file,
)


TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), "data")


class TestUtils(QgisTestCase):

    def test_dem2top(self):
        dem = os.path.join(TEST_DATA_PATH, "dem.tif")
        layer = QgsRasterLayer(dem, "dem", "gdal")

        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file.close()

        dem2top(layer, tmp_file.name)

        self.assertFilesEqual(
            os.path.join(TEST_DATA_PATH, "expected", "dem.top"), tmp_file.name
        )
        os.unlink(tmp_file.name)

    def test_generate_master_file(self):
        params = {
            "problem_name": "frank",
            "dt": 0.1,
            "time_end": 80,
            "print_step": 25,
            # "law_type": 7,
            "cgra": 9.8,
            "dens": 2000.0,
            "cmanning": 0,
            "eros_coef": 0,
            "nfrict": 7,
            "tauy0": 0.0,
            "visco": 0.0,
            "tanfi8": 0.218,
        }

        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file.close()

        generate_master_file(tmp_file.name, params)

        self.assertFilesEqual(
            os.path.join(TEST_DATA_PATH, "expected", "frank.master.dat"), tmp_file.name
        )
        os.unlink(tmp_file.name)

    def test_generate_data_file(self):
        params = {
            "problem_name": "frank",
            "dt": 0.1,
            "time_end": 80,
            "print_step": 25,
            # "law_type": 7,
            "cgra": 9.8,
            "dens": 2000.0,
            "cmanning": 0,
            "eros_coef": 0,
            "nfrict": 7,
            "tauy0": 0.0,
            "visco": 0.0,
            "tanfi8": 0.218,
        }

        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file.close()

        generate_data_file(tmp_file.name, params)

        self.assertFilesEqual(
            os.path.join(TEST_DATA_PATH, "expected", "frank.dat"), tmp_file.name
        )
        os.unlink(tmp_file.name)

    def test_generate_batch_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            generate_batch_file("frank", tmp_dir)

            file_path = os.path.join(tmp_dir, "files.txt")
            self.assertTrue(os.path.exists(file_path))
            self.assertFilesEqual(
                os.path.join(TEST_DATA_PATH, "expected", "files.txt"), file_path
            )

            file_path = os.path.join(tmp_dir, "frank.bat")
            self.assertTrue(os.path.exists(file_path))
            lines = None
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            self.assertEqual(lines[0], "set CWDIR=%~dp0\n")
            self.assertEqual(lines[1], f"cd {tmp_dir}\n")
            self.assertEqual(lines[2], "SPH24.exe < files.txt\n")
            self.assertEqual(lines[3], "cd %WDIR%\n")


if __name__ == "__main__":
    nose2.main()
