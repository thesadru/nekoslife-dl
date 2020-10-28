#!/usr/bin/env python3
from setuptools import setup,find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

with open('version', 'r') as f:
    version = f.read()

with open('requirements.txt','r') as f:
    install_requires = [i.strip('\n') for i in f.readlines()]

setup(
    name='nekoslife-dl',
    version=version,
    author='thesadru',
    author_email='dan0.suman@gmail.com',
    description='Downloads images from nekos.life using the v3 API.',
    packages=find_packages('src'),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    url='https://github.com/thesadru/nekoslife-dl',
    keywords=['nekos','life','nekoslife','download','view','better','api','v3'],
    install_requires=install_requires,
    extras_require={},
    long_description=long_description,
    long_description_content_type='text/markdown'
)