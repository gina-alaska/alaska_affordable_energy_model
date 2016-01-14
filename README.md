# alaska_affordable_energy_model
Alaska Energy Authority - Alaska Affordable Energy Model
Created by University of Alaska Fairbanks/GINA

# extra python libraries used:
numpy, scipy, pandas: info on those here: http://www.scipy.org/

ipython: used for devlopen enviroment as opposed to regular python prompt, also at http://www.scipy.org/

pyyaml: for reading yaml

## Installing dependencies
Dependencies for the Alask Affordable Energy Model can be installed using [pip](https://pypi.python.org/pypi/pip)

    pip install --user -r requirements.txt

## Install Development version

    python setup.py develop

## Uninstall Development version

    python setup.py develop -u

## development python examples:
from an interactive python prompt (can be done from any where if installed using python setup.py develop)

general example:

    >>> from aaem import driver
    >>> driver.setup("Community", "path to aaem data repo", "path model testing directory")
    >>> driver.run("path model testing directory/Community_driver.yaml")

Manley example:

    >>> from aaem import driver
    >>> driver.setup("Manley Hot Springs", "Desktop/alaska_affordable_energy_model-data", "./test")
    >>> driver.run("./test/Manley_Hot_Springs_driver.yaml")
    
input data, config info, and results will be in the directory specified as the last argument to setup
