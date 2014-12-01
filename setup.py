from __future__ import absolute_import

import setuptools

setuptools.setup(
    name = 's3pub',
    version = '0.1.0',
    packages = {'s3pub': 's3pub'},
    entry_points = {
        'console_scripts': [
            's3pub = s3pub.cmdline:main',
        ]
    }
)