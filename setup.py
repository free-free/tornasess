# coding:utf-8
from setuptools import setup,find_packages
import re
import os

from tornasess import __version__

def read(f):
    return open(os.path.join(os.path.dirname(__file__),f)).read().strip()


setup(
    name="tornasess",
    version=__version__,
    author="HuangBiao",
    author_email="19941222hb@gmail.com",
    description="A tornado session implementation",
    long_description=read("READM.rst"),
    license="MIT",
    url="https://github.com/free-free/tornasess",
    packages=find_packages(),
    install_requires=re.split(r"\r*\n+",read("requirements.txt")),
    include_package_data=True,
    keywords=['tornado','session'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
