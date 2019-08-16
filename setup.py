#!/usr/bin/env python
"""python setup.py install"""

# Copyright (c) 2011 Paul Makepeace, Real Programmers. All rights reserved.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import os
from setuptools import setup
from setuptools import find_packages


def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()

setup(name='openrefine-client',
      version='0.3.7',
      description=('The OpenRefine Python Client Library provides an '
                   'interface to communicating with an OpenRefine server. '
                   'This fork extends the command line interface (CLI).'),
      long_description=read('README.md'),
      long_description_content_type='text/markdown',
      author='Felix Lohmeier',
      author_email='felix.lohmeier@opencultureconsulting.com',
      url='https://github.com/opencultureconsulting/openrefine-client',
      packages=find_packages(exclude=['tests']),
      install_requires=['urllib2_file'],
      python_requires='>=2.7, !=3.*',
      entry_points={
          'console_scripts': [ 'openrefine-client = google.refine.__main__:main' ]
      },
      platforms=['Any'],
      keywords='openrefine client batch processing docker etl code4lib',
      classifiers = [
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Text Processing',
      ],
      test_suite='tests',
)
