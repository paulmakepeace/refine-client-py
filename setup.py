#!/usr/bin/env python
"""python setup.py install"""

import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='refine-client-py',
      version='0.1.0',
      description=('The Google Refine Python Client Library provides an '
                   'interface to communicating with a Google Refine server.'),
      long_description=read('README.rst'),
      author='Paul Makepeace',
      author_email='paulm@paulm.com',
      url='https://github.com/PaulMakepeace/refine-client-py',
      packages=['google.refine'],
      # XXX how do I include test/data/*.csv in setup.py sdist but not install it?
      #package_data={'': ['tests/data/*.csv']},
      install_requires=[
        #'MultipartPostHandler',     # for urllib2_file
      ],    
      classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      test_suite='tests',
)