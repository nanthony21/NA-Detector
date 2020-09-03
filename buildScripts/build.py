import logging
import os
import shutil
import subprocess

"""This builds the conda package and saves it to `build`
It should be run from the base conda env."""

buildScriptDir = os.path.dirname(os.path.abspath(__file__))  # Location of build scripts
rootDir = os.path.dirname(os.path.dirname(buildScriptDir))  # Parent directory of project.
buildDir = os.path.join(buildScriptDir, 'build')

# Clean
if os.path.exists(buildDir):
    shutil.rmtree(buildDir)
os.mkdir(buildDir)

# Build and save to the outputDirectory
proc = subprocess.Popen(f"conda-build {rootDir} --output-folder {buildDir} -c conda-forge", stdout=None,
                        stderr=subprocess.PIPE)
logger = logging.getLogger(__name__)
logger.info("Waiting for conda-build")
proc.wait()
result, error = proc.communicate()  # Unfortunately conda-build returns errors in STDERR even if the build succeeds.
if proc.returncode != 0:
    raise OSError(error.decode())
else:
    logger.info("Success")

# Upload to Anaconda
# The user can enable conda upload in order to automatically do this after build.
