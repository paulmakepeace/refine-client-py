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

setup(name='refine-client',
      version='0.2.1',
      description=('The OpenRefine Python Client Library provides an '
                   'interface to communicating with an OpenRefine server.'),
      long_description=read('README.rst'),
      author='Paul Makepeace',
      author_email='paulm@paulm.com',
      url='https://github.com/PaulMakepeace/refine-client-py',
      packages=find_packages(exclude=['tests']),
      install_requires=['urllib2_file'],
      platforms=['Any'],
      classifiers = [
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Text Processing',
      ],
      test_suite='tests',
)
