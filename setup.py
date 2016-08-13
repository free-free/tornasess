# coding:utf-8
from setuptools import setup,find_packages




setup(
    name="tornado_session",
    version="0.1",
    author="HuangBiao",
    author_email="19941222hb@gmail.com",
    description="A tornado session implementation",
    license="MIT",
    packages=find_packages(),
    install_requires=['tornadis'],
    include_package_data=True
)