from setuptools import setup, find_packages
import os
import pathlib

CWD = pathlib.Path(__file__).parent.resolve()

VERSION = '1.0.0' 
PYTHON_REQUIRES = ">=3.10"
URL = "https://github.com/changyy/google-csv-helper"
DOWNLOAD_URL = "https://pypi.org/project/google-csv-helper/"
DESCRIPTION = 'A simple tool that takes CSV reports from Google Adsense, Google Admob, and Google Analytics and outputs them in JSON / Pandas.DataFrame format.'
LONG_DESCRIPTION = DESCRIPTION
INSTALL_REQUIRES = []
with open(os.path.join(CWD, "requirements.txt"), 'r') as f:
    INSTALL_REQUIRES = [s.strip() for s in f.read().split("\n")]

setup(
    name="google-csv-helper", 
    version=VERSION,
    author="Yuan-Yi Chang",
    author_email="<changyy.csie@gmail.com>",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=INSTALL_REQUIRES,
    keywords=['python', 'google', 'csv', 'adsense', 'admob', 'report'],
    python_requires=PYTHON_REQUIRES,
    url=URL,
    download_url=DOWNLOAD_URL,
    classifiers= [
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X",
    ]
)
