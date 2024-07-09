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
from tempfile import NamedTemporaryFile

from qgis.PyQt.QtCore import QProcess
from qgis.core import (
    Qgis,
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


def generate_batch_file(file_name):
    input_file = NamedTemporaryFile(mode="wt", suffix=".txt", encoding="utf-8", delete=False)
    input_file_name = input_file.name
    input_file.close()
    with open(input_file_name, "w", encoding="utf-8") as f:
        for i in range(2):
            f.write(f"{file_name}\n" )

    batch_file = NamedTemporaryFile(mode="wt", suffix=".bat", encoding="utf-8", delete=False)
    batch_file_name = batch_file.name
    batch_file.close()

    with open(batch_file_name, "w", encoding="utf-8") as f:
        f.write(f"{sph_executable()} < {input_file_name}\n" )

    return batch_file_name, input_file_name


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
