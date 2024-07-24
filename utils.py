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
from tempfile import mkdtemp
from typing import Any

from qgis.PyQt.QtCore import QProcess
from qgis.core import (
    Qgis,
    QgsRectangle,
    QgsMessageLog,
    QgsRunProcess,
    QgsRasterLayer,
    QgsBlockingProcess,
    QgsProcessingFeedback,
    QgsProcessingException,
)
from processing.core.ProcessingConfig import ProcessingConfig


PLUGIN_ROOT = os.path.dirname(__file__)
SPH_EXECUTABLE = "SPH_EXECUTABLE"


def sph_executable() -> str:
    """
    Returns path to the SHP executable.
    """
    filePath = ProcessingConfig.getSetting(SPH_EXECUTABLE)
    return filePath if filePath is not None else "sph24"


def execute(commands: list[str], feedback: QgsProcessingFeedback = None):
    """
    Executes SPH tool
    """
    if feedback is None:
        feedback = QgsProcessingFeedback()

    fused_command = " ".join([str(c) for c in commands])
    QgsMessageLog.logMessage(fused_command, "Processing", Qgis.Info)
    feedback.pushInfo("SPH command:")
    feedback.pushCommandInfo(fused_command)
    feedback.pushInfo("SPH output:")

    def onStdOut(ba: bytes):
        val = ba.data().decode("utf-8")
        if "%" in val:
            onStdOut.progress = int(progressRegex.search(val).group(0))
            feedback.setProgress(onStdOut.progress)
        else:
            onStdOut.buffer += val

        if onStdOut.buffer.endswith(("\n", "\r")):
            feedback.pushConsoleInfo(onStdOut.buffer.rstrip())
            onStdOut.buffer = ""

    onStdOut.progress = 0
    onStdOut.buffer = ""

    def onStdErr(ba: bytes):
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


def generate_batch_file(problem_name: str, work_dir: str) -> str:
    """
    Generates script to run SPH tool.

    Returns a full path to the generated script.
    """
    input_file_name = "files.txt"
    input_file = os.path.join(work_dir, input_file_name)
    with open(input_file, "w", encoding="utf-8") as f:
        for i in range(2):
            f.write(f"{problem_name}\n")

    batch_file = os.path.join(work_dir, f"{problem_name}.bat")
    with open(batch_file, "w", encoding="utf-8") as f:
        f.write("set CWDIR=%~dp0\n")
        f.write(f"cd {work_dir}\n")
        f.write(f"SPH24.exe < {input_file_name}\n")
        f.write("cd %WDIR%\n")

    return batch_file


def copy_inputs(
    problem_name: str,
    dem: str,
    pts_file: str,
    master_file: str | None = None,
    config_file: str | None = None,
) -> str:
    """
    Copies SPH executable and input files into a separate directory to create an
    environment for performing analysis.

    Returns full path to the created directory.
    """
    work_dir = mkdtemp(prefix=f"sph-")

    shutil.copy(sph_executable(), work_dir)

    new_path = os.path.join(work_dir, f"{problem_name}.top")
    dem2top(dem, new_path)

    new_path = os.path.join(work_dir, f"{problem_name}.pts")
    shutil.copyfile(pts_file, new_path)

    if master_file is not None:
        new_path = os.path.join(work_dir, f"{problem_name}.master.dat")
        shutil.copyfile(master_file, new_path)

    if config_file is not None:
        new_path = os.path.join(work_dir, f"{problem_name}.dat")
        shutil.copyfile(config_file, new_path)

    return work_dir


def generate_master_file(file_name: str, params: dict[str, Any]):
    """
    Generates configuration file with the model inputs and generic parameters.
    """
    with open(file_name, "w", encoding="utf-8") as f:
        f.write("1\n")
        f.write(f"{params['problem_name']}\n")
        f.write("if_sph if_gfl if_tgfsph     gfl  Monte-Carlo\n")
        f.write("  1      0      0 \n")
        f.write("problem_type   Integ_Alg \n")
        f.write("       1               4\n")
        f.write("file.dat\n")
        f.write(f"{params['problem_name']}\n")
        f.write("dt      time_end   maxtimesteps\n")
        f.write(f"{params['dt']}      {params['time_end']}       1000000\n")
        f.write("print_step   save_step  plot_step\n")
        f.write(
            f"   {params['print_step']}          {params['print_step']}       {params['print_step']}\n"
        )
        f.write("dt_sph  ic_adapt    \n")
        f.write("0.1      1  \n")
        f.write("time_curves      max_pts\n")
        f.write("     0              6  \n")
        f.write("cases_win      ic_eros\n")
        f.write("   0              0 \n")


def generate_data_file(file_name: str, params: dict[str, Any]):
    """
    Generates configuration file with specific model parameters.
    """
    with open(file_name, "w", encoding="utf-8") as f:
        f.write("  1\n")
        f.write(f"{params['problem_name']}\n")
        f.write("SWalg\n")
        f.write("  0\n")
        f.write("nhist\n")
        f.write("  0\n")
        f.write("ndimn\n")
        f.write("   2\n")
        f.write("soil  water  vps  ic_abs\n")
        f.write(" 1      0     0     0\n")
        f.write("icunk     h_inf_SW  \n")
        f.write("  6         0.1\n")
        f.write("file.pts\n")
        f.write(f"{params['problem_name']}\n")
        f.write("pa_sph,  nnps, sle, skf \n")
        f.write("  2       2     1    1         \n")
        f.write("sum_den,  av_vel, virt_part , nor_dens  \n")
        f.write("   T         T      F            F       \n")
        f.write(
            "cgra   dens  cmanning  eros_Coef    nfrict     Tauy0   constK  visco   tanfi8  hfrict0    c11   tanfi0   .Bfact     hrelpw   Comp  \n"
        )
        f.write(
            f" {params['cgra']}   {params['dens']}   {params['cmanning']}           {params['eros_coef']}          {params['nfrict']}         {params['tauy0']}     0.0     {params['visco']}    {params['tanfi8']}    1.e-3     0.0     0.      0.0       0.0      0.001\n"
        )
        f.write("K0\n")
        f.write("  0\n")
        f.write("icpwp \n")
        f.write("  0\n")
        f.write("coarse\n")
        f.write("  0\n")
        f.write("chk_pts\n")
        f.write("  0\n")
        f.write(
            "Gid_Mask_SW   1.hs  2.disp 3.v  4.Pwb  5 eros   6.Z  7.hrel  8.hw  9.eta  10.hs+hw  11.hsat   12.Pw\n"
        )
        f.write(
            "               1      1    0    0      0        0        0       0       0     0       0          0\n"
        )
        f.write("T_change_to_W\n")
        f.write("  1.e+12    \n")


def dem2top(layer: QgsRasterLayer, file_path: str):
    """
    Converts a single-band raster layer representing DEM to a text format (.top)
    required by SPH tool.

    The .top format is basically a raster in the XYZ format with the custom
    header and footer.
    """
    provider = layer.dataProvider()
    width = provider.xSize()
    height = provider.ySize()
    pixel_size = layer.rasterUnitsPerPixelX()
    pixel_count = width * height
    extent = layer.extent()

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("ictop\n")
        f.write("  10\n")
        f.write("  np      deltx\n")
        f.write(f" {pixel_count}     {pixel_size}    \n")
        f.write("Topo_x Topo_y Topo_z\n")

        for row in range(height):
            x_min = extent.xMinimum()
            x_max = extent.xMaximum()
            y_min = extent.yMaximum() - row * pixel_size
            y_max = extent.yMaximum() - (row + 1) * pixel_size
            block_extent = QgsRectangle(x_min, y_min, x_max, y_max)
            block = provider.block(1, block_extent, width, height, None)

            for col in range(width):
                x = extent.xMinimum() + (col + 0.5) * pixel_size
                y = extent.yMaximum() - (row + 0.5) * pixel_size
                f.write(f"{x}\t{y}\t{block.value(row, col)}\n")

        f.write("topo_props\n")
        f.write("  0\n")


def copy_outputs(work_dir: str, problem_name: str, output_dir: str):
    """
    Copies output files produced by the SPH tool to the output directory.
    """
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    for suffix in ("post.msh", "post.res"):
        output_name = os.path.join(work_dir, f"{problem_name}.{suffix}")
        if os.path.exists(output_name):
            shutil.copy(output_name, output_dir)
