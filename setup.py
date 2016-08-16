# coding:utf-8
from setuptools import setup,find_packages
import re

from tornasess import __version__

setup(
    name="tornado_session",
    version=__version__,
    author="HuangBiao",
    author_email="19941222hb@gmail.com",
    description="A tornado session implementation",
    license="MIT",
    packages=find_packages(),
    install_requires=re.split(r"\r*\n+",open("requirements.txt","r").read())[0:-1],
    include_package_data=True
)
