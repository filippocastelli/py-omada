from setuptools import setup, find_packages

import re
VERSIONFILE="pyomada/__version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))


with open("README.md", "r") as fh:
    long_description = fh.read()
    
with open("requirements.txt", "r") as fh:
    requirements = fh.read().splitlines()
    
setup(
    name="pyomada",
    version=verstr,
    description="A Python interface for OMADA API.",
    packages=find_packages(exclude=("tests",)),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=requirements,
    url="https://github.com/filippocastelli/pyomada",
    author="Filippo Maria Castelli",
    author_email="filippocastelli42@gmail.com",
    entry_points={
        "console_scripts": [
            "enable_radios=pyomada.enable_radios:main",
        ]
    }
)
