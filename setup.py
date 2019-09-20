from setuptools import setup, find_packages
from distutils.core import Extension

DISTNAME = 'criticalityMaps'
VERSION = '0.0.2'
PACKAGES = find_packages()
EXTENSIONS = []
DESCRIPTION = 'WNTR utility for generating criticality maps'
LONG_DESCRIPTION = open('README.md').read()
AUTHOR = 'Patrick Hassett'
MAINTAINER_EMAIL = 'pshassett@humboldt.edu'
LICENSE = 'MIT'
URL = 'https://github.com/pshassett/WNTRCriticalityMaps'
INSTALL_REQUIRES = ['networkx',
                    'pandas',
                    'numpy',
                    'scipy',
                    'matplotlib',
                    'plotly',
                    'wntr',
                    'pyyaml',
                    'utm',
                    'jinja2',
                    'six']

setuptools_kwargs = {
    'zip_safe': False,
    'install_requires': INSTALL_REQUIRES,
    'scripts': [],
    'include_package_data': True
}

setup(name=DISTNAME,
      version=VERSION,
      packages=PACKAGES,
      ext_modules=EXTENSIONS,
      description=DESCRIPTION,
      long_description=LONG_DESCRIPTION,
      long_description_content_type='text/markdown',
      author=AUTHOR,
      maintainer_email=MAINTAINER_EMAIL,
      license=LICENSE,
      url=URL,
      **setuptools_kwargs)

