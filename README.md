# Alaska Affordable Energy Model
The Alaska Affordable Energy Model (AAEM) is a model designed by the [Alaska Energy Authority (AEA)](http://www.akenergyauthority.org) and built by the [University of Alaska Fairbanks’ (UAF)](http://uaf.edu) [Geographic Information Network of Alaska (GINA)](http://gina.alaska.edu). The goal of the AAEM is to provide Alaska with a community energy model and project evaluation tool. It uses community and regional energy data, fuel data, and socio-economic data to:

estimate and forecast heating and electricity consumption by sector,
compare the ability of energy infrastructure project types (efficiency, renewable energy, fuel switching) to reduce the cost of energy in communities,
determine the capital investment needed and the resulting energy savings to communities.
Disclaimer: The results presented in the model results are generated from available data on population, consumption, generation, and information on a technologies analyzed. For some communities this information may be incomplete. If you have, or know of a source of data that could help improve the model please contact The Alaska Energy Authority .

Resources with more details on the Alaska Affordable Energy Model

Alaska Energy Authority's Affordable Energy Strategy
Browse Model Run Results - model version: 0.24.6 data version: 0.24.0
Review the Model Documentation

# alaska_affordable_energy_model
Alaska Energy Authority - Alaska Affordable Energy Model
Created by University of Alaska Fairbanks/GINA

# extra python libraries used:
numpy, scipy, pandas: info on those here: http://www.scipy.org/

ipython: used for devlopement enviroment as opposed to regular python prompt, also at http://www.scipy.org/

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
    
    
