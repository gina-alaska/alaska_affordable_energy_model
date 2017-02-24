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
    
## Building the documentation

    the documentation requires that Sphinx be installed.
    
    pip install Sphinx
    
    To build the docs in the docs/build folder. From the root of the code repo:

    sphinx-build  -b html ./docs/source/ docs/build/
    
    or more generally:
    
    sphinx-build  -b html [path to docs/source/] [path to output folder]

## Seting up the model for the first time

    use the program bin/aaem.
    
    from the alaska affordiable_energy-model_repo
    
    ./bin/aaem <path to location to setup> <path to data repo>
    
    
## Running the model 

    see the documentaion for andvanced instructions on installation and running
    
    
