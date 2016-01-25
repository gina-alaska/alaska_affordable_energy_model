"""
setup script
"""
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Alaska Affordable Energy Model',
    'author': 'GINA',
    'url': 'https://github.com/gina-alaska/alaska_affordable_energy_model',
    'download_url': 'TODO',
    'author_email': 'TODO',
    'version': '0.1.0',
    'install_requires': ['numpy','scipy','pandas','pyyaml'],
    'packages': ['aaem', 'aaem.components'],
    'scripts': [],
    'name': 'Alaska_Affordable_Energy_Model'
}

setup(**config)
