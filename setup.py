import glob
import os
import os.path
import shutil
from distutils import log
from distutils.cmd import Command
from setuptools import setup


class CleanAllCommand(Command):
    CLEAN_FILES = [
        "dist",
        "build",
        ".pytest_cache",
        ".eggs",
        "*.egg-info",
        "*.log",
        "*.txt",
        "*.checkpoint",
    ]
    description = "Clean all artifacts"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        for path_spec in self.CLEAN_FILES:
            abs_paths = glob.glob(os.path.normpath(os.path.join(path_spec)))
            for path in [str(p) for p in abs_paths]:
                self.announce(
                    "removing {}".format(os.path.relpath(path)), level=log.INFO
                )
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)


if __name__ in ["__main__", "builtins"]:
    setup(cmdclass={"clean_all": CleanAllCommand})
