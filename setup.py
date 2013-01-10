#!/usr/bin/env pythonv
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import sys
Version = "0.1.0"

if float("%d.%d" % sys.version_info[:2]) < 2.5:
    sys.stderr.write("Your Python version %d.%d.%d is not supported.\n" % sys.version_info[:3])
    sys.stderr.write("cloudinitd requires Python 2.5 or newer.\n")
    sys.exit(1)

setup(name='pidantic',
      version=Version,
      description='An abstraction to process management for OOI',
      author='Nimbus Development Team',
      author_email='workspace-user@globus.org',
      url='http://www.nimbusproject.org/',
      dependency_links=['http://ooici.net/releases'],
      packages=['pidantic', 'pidantic.fork', 'pidantic.supd', 'pidantic.pyon'],
      keywords="OOI PID process fork supervisord ION",
      long_description="""Some other time""",
      license="Apache2",
      install_requires=['supervisor', 'sqlalchemy==0.7.6', 'gevent'],

      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: Apache Software License',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python',
          'Topic :: System :: Clustering',
          'Topic :: System :: Distributed Computing',
          ],
     )
