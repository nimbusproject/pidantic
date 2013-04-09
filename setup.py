#!/usr/bin/env pythonv

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import sys
VERSION = "0.1.2"

if float("%d.%d" % sys.version_info[:2]) < 2.5:
    sys.stderr.write("Your Python version %d.%d.%d is not supported.\n" % sys.version_info[:3])
    sys.stderr.write("pidantic requires Python 2.5 or newer.\n")
    sys.exit(1)

setup(
    name='pidantic',
    version=VERSION,
    description='An abstraction to process management for OOI',
    author='Nimbus Development Team',
    author_email='workspace-user@globus.org',
    url='https://github.com/nimbusproject/pidantic',
    download_url="http://www.nimbusproject.org/downloads/pidantic-%s.tar.gz" % VERSION,
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
