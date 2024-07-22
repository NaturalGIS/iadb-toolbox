# -*- coding: utf-8 -*-

"""
***************************************************************************
    utils.py
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
from tempfile import NamedTemporaryFile, mkdtemp

from qgis.PyQt.QtCore import QProcess
from qgis.core import (
    Qgis,
    QgsRectangle,
    QgsMessageLog,
    QgsRunProcess,
    QgsBlockingProcess,
    QgsProcessingFeedback,
    QgsProcessingException,
)
from processing.core.ProcessingConfig import ProcessingConfig


PLUGIN_ROOT = os.path.dirname(__file__)
SPH_EXECUTABLE = "SPH_EXECUTABLE"


def sph_executable():
    filePath = ProcessingConfig.getSetting(SPH_EXECUTABLE)
    return filePath if filePath is not None else "sph24"


def execute(commands, feedback=None):
    if feedback is None:
        feedback = QgsProcessingFeedback()

    fused_command = " ".join([str(c) for c in commands])
    QgsMessageLog.logMessage(fused_command, "Processing", Qgis.Info)
    feedback.pushInfo("SPH command:")
    feedback.pushCommandInfo(fused_command)
    feedback.pushInfo("SPH output:")

    def onStdOut(ba):
        val = ba.data().decode("utf-8")
        if "%" in val:
            onStdOut.progress = int(progressRegex.search(val).group(0))
            feedback.setProgress(onStdOut.progress)
        else:
            onStdOut.buffer += val

        if onStdOut.buffer.endswith(("\n", "\r")):
            feedback.pushConsoleInfo(onStdOut.buffer.rstrip())
            onStdOut.buffer = ""
            onStdOut.progress += 1

    onStdOut.progress = 0
    onStdOut.buffer = ""

    def onStdErr(ba):
        val = ba.data().decode("utf-8")
        onStdErr.buffer += val

        if onStdErr.buffer.endswith(("\n", "\r")):
            feedback.reportError(onStdErr.buffer.rstrip())
            onStdErr.buffer = ""

    onStdErr.buffer = ""

    command, *arguments = QgsRunProcess.splitCommand(fused_command)
    proc = QgsBlockingProcess(command, arguments)
    proc.setStdOutHandler(onStdOut)
    proc.setStdErrHandler(onStdErr)

    res = proc.run(feedback)
    if feedback.isCanceled() and res != 0:
        feedback.pushInfo("Process was canceled and did not complete.")
    elif not feedback.isCanceled() and proc.exitStatus() == QProcess.CrashExit:
        raise QgsProcessingException("Process was unexpectedly terminated.")
    elif res == 0:
        feedback.pushInfo("Process completed successfully.")
    elif proc.processError() == QProcess.FailedToStart:
        raise QgsProcessingException(
            'Process "{}" failed to start. Either "{}" is missing, or you may have insufficient permissions to run the program.'.format(
                command, command
            )
        )
    else:
        feedback.reportError("Process returned error code {}".format(res))


def generate_batch_file(work_dir, name):
    input_file = os.path.join(work_dir, "files.txt")
    with open(input_file, "w", encoding="utf-8") as f:
        for i in range(2):
            f.write(f"{name}\n")

    batch_file = os.path.join(work_dir, f"{name}.bat")
    with open(batch_file, "w", encoding="utf-8") as f:
        f.write("set CWDIR=%~dp0\n")
        f.write(f"cd {work_dir}\n")
        f.write(f"{sph_executable()} < {input_file}\n")
        f.write("cd %WDIR%\n")

    return batch_file


def copy_inputs(points_file, dem):
    work_dir = mkdtemp(prefix="sph-")

    shutil.copy(sph_executable(), work_dir)

    file_name = os.path.split(points_file)[1]
    points_file_name = os.path.join(work_dir, file_name)
    shutil.copyfile(points_file, points_file_name)

    file_name = os.path.split(dem.source())[1]
    dem_file_name = os.path.join(work_dir, f"{os.path.splitext(file_name)[0]}.top")
    dem2top(dem, dem_file_name)

    return work_dir


def generate_master_file(file_name, params):
    with open(file_name, "w", encoding="utf-8") as f:
        f.write("1\n")
        f.write(f"{params['problem_name']}\n")
        f.write("if_sph if_gfl if_tgf\n")
        f.write("  1      0      0 \n")
        f.write("SPH_problem_type   SPH_t_integ_Alg\n")
        f.write("       1               4\n")
        f.write("sph problem name\n")
        f.write(f"{params['problem_name']}\n")
        f.write("dt      time_end   maxtimesteps\n")
        f.write(f"{params['dt']}      {params['time_end']}       1000000\n")
        f.write("print_step   save_step  plot_step\n")
        f.write(
            f"{params['print_step']}          {params['print_step']}       {params['print_step']}\n"
        )
        f.write("dt_sph  ic_adapt    \n")
        f.write("0.1      1  \n")
        f.write("Ntime curves     max pts in them   \n")
        f.write("      0              6  \n")
        f.write("ic_cases_win      ic_eros\n")
        f.write("    0                0 \n")


def generate_data_file(file_name, params):
    with open(file_name, "w", encoding="utf-8") as f:
        f.write("      1\n")
        f.write(f" ---- {params['problem_name']}\n")
        f.write("Type of SW Algorithm\n")
        f.write("  0\n")
        f.write(" nhist\n")
        f.write("  0\n")
        f.write(" ndimn\n")
        f.write("  2\n")
        f.write(" ic_soil  ic_water  ic_vps  ic_abs\n")
        f.write("   1         0       0       0   \n")
        f.write(" Landslide type of input     h_inf_SW  \n")
        f.write("    6                          0.1\n")
        f.write("pts file name\n")
        f.write(f" {params['problem_name']}\n")
        f.write(" pa_sph,  nnps, sle, skf \n")
        f.write("   2       2     2    1         \n")
        f.write(" sum_den,  av_vel, virt_part , nor_dens  \n")
        f.write("    T         T      F            F       \n")
        f.write(" cgra  dens  cmanning    4..    nfrict     Tauy0   constK  visco   tanfi8  hfrict0    c11   tanfi0   .Bfact     14..   15..Comp  end  \n")
        f.write(f"  {params['c1_graw']}   {params['c2_dens']}  {params['c3_voelmy']}         {params['c4_hungr']}       {params['c5_fric']}         {params['c6_tauy']}     0.0     {params['c8_visco']}      {params['c9_tanfi']}    1.e-3     0.0   0.218      0.0     0.0      0.001\n")
        f.write(" K0 activated?\n")
        f.write("  0\n")
        f.write(" icpwp \n")
        f.write("  0\n")
        f.write("coarse mesh saving utility?\n")
        f.write("  0\n")
        f.write("control points?\n")
        f.write("  0\n")
        f.write("GID filter   1.hs  2.disp 3.v  4.Pw  5 eros   6..Z  7..hrel  8..hw  9..eta  10.. hs+hw  11 dumm   12...dumm\n")
        f.write("               1      1    0    0      0        0        0       0       0     0          0          0\n")
        f.write("T_change_to_W\n")
        f.write("  1.e+12    \n")


def dem2top(layer, file_path):
    provider = layer.dataProvider()
    width = provider.xSize()
    height = provider.ySize()
    pixel_size = layer.rasterUnitsPerPixelX()
    pixel_count = width * height
    extent = layer.extent()

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("ictop\n")
        f.write("11\n")
        f.write("np\tdeltx\n")
        f.write(f"{pixel_count}\t{pixel_size}\n")
        f.write("X Y Z\n")

        y = 0
        for r in range(height, 0, -1):
            x_min = extent.xMinimum()
            x_max = extent.xMaximum()
            y_min = extent.yMaximum() - (r - 1) * pixel_size
            y_max = extent.yMaximum() - r * pixel_size
            block_extent = QgsRectangle(x_min, y_min, x_max, y_max)
            block = provider.block(1, block_extent, width, height, None)

            x = 0
            for i in range(block.width()):
                f.write(f"{x}\t{y}\t{block.value(0, i)}\n")
                x += pixel_size

            y += pixel_size

        f.write("terrain\n")
        f.write("0\n")
