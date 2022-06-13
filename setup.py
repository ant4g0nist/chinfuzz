#!/usr/bin/env python
import os
import logging
import setuptools
from os import path
from importlib import util
from setuptools import setup

logger = logging.getLogger(__name__)

# read the contents of your README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

spec = util.spec_from_file_location(
    "chinfuzz.version", os.path.join("chinfuzz", "version.py")
)

# noinspection PyUnresolvedReferences
mod = util.module_from_spec(spec)
spec.loader.exec_module(mod)
version = mod.version

pwd = os.getcwd()
path_to_my_atheris = f"{pwd}/chinfuzz/thirdparty/atheris"
path_to_my_pytezos = f"{pwd}/chinfuzz/thirdparty/pytezos"

setup(
    install_requires=[
        "halo>=0.0.31",
        "rich>=11.0.0",
        "chinstrap>=1.0.10",
        f"atheris @ file://localhost/{path_to_my_atheris}#egg=atheris"
    ],
    license="MIT License",
    name="chinfuzz",
    version=version,
    python_requires=">=3.7",
    description="Chinfuzz enables code coverage fuzzing for Tezos smart contracts",
    author="ant4g0nist",
    author_email="me@chinstrap.io",
    url="https://github.com/ant4g0nist/chinfuzz",
    scripts=["bin/chinfuzz"],
    # entry_points = {
    #     'console_scripts': ['chinfuzz=chinfuzz:main'],
    # },
    packages=setuptools.find_packages(),
    package_dir={
        "chinfuzz.resources.fuzz": "chinfuzz.resources.fuzz"
    },
    package_data={
        "chinfuzz.resources.fuzz": ["*"],
    },
    include_package_data=True,
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Build Tools",
    ],
)
