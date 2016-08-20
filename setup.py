# coding:utf-8
from setuptools import setup,find_packages
import re
import os


def read(f):
    return open(os.path.join(os.path.dirname(__file__),f)).read().strip()

def find_version(f):
    file_content = read(f)
    try:
        version = re.findall(r'^__version__ = "([^\'\"]+)"\r?$',
            file_content, re.M)[0]
    except IndexError:
        raise RuntimeError("Unable to determine version.")
    return version


setup(
    name="tornasess",
    version=find_version("tornasess/__init__.py"),
    author="HuangBiao",
    author_email="19941222hb@gmail.com",
    description="A tornado session implementation",
    long_description=read("README.rst"),
    license="MIT",
    url="https://github.com/free-free/tornasess",
    packages=find_packages(),
    install_requires=["tornado","asyncmc","tornado_hbredis"],
    include_package_data=True,
    keywords=['tornado','session'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content'
    ]
)
