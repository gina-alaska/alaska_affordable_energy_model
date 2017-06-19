"""
setup script
"""
#~ try:
from setuptools import setup,find_packages
#~ except ImportError:
    #~ from distutils.core import setup

import aaem

config = {
    'description': 'Alaska Affordable Energy Model',
    'author': 'GINA',
    'url': aaem.__url__,
    'download_url': aaem.__download_url__,
    'author_email': 'TODO',
    'version': aaem.__version__,
    'install_requires': ['numpy','scipy','pandas','pyyaml'],
    'packages': find_packages(),#['aaem', 'aaem.components', 'aaem_summaries', 'aaem.cli'],
    'scripts': [],
    'name': 'Alaska_Affordable_Energy_Model'
}

setup(**config)
