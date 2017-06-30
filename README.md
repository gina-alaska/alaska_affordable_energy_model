# Alaska Affordable Energy Model
The Alaska Affordable Energy Model (AAEM) is a model designed by the [Alaska Energy Authority (AEA)](http://www.akenergyauthority.org) and built by the [University of Alaska Fairbanks’ (UAF)](http://uaf.edu) [Geographic Information Network of Alaska (GINA)](http://gina.alaska.edu). The goal of the AAEM is to provide Alaska with a community energy model and project evaluation tool. It uses community and regional energy data, fuel data, and socio-economic data to:

- estimate and forecast heating and electricity consumption by sector,
- compare the ability of energy infrastructure project types (efficiency, renewable energy, fuel switching) to reduce the cost of energy in communities,
- determine the capital investment needed and the resulting energy savings to communities.


Disclaimer: The results presented in the model results are generated from available data on population, consumption, generation, and information on a technologies analyzed. For some communities this information may be incomplete. If you have, or know of a source of data that could help improve the model please contact The Alaska Energy Authority .

Resources with more details on the Alaska Affordable Energy Model:
- [Alaska Energy Authority's Affordable Energy Strategy](http://www.akenergyauthority.org/Policy-Planning/AlaskaAffordableEnergyStrategy)
- [Browse Model Run Results](http://model-results.akenergyinventory.org) - model version: 1.0.0 data version: 1.0.0
- [Review the Model Documentation](http://model-docs.akenergyinventory.org)
- [Alaska Energy Data Gateway](https://akenergygateway.alaska.edu/)


## Installing dependencies
Dependencies for the Alaska Affordable Energy Model can be installed using [pip](https://pypi.python.org/pypi/pip)

    pip install --user -r requirements.txt

 [see more info on dependencies in the documentation](http://model-docs.akenergyinventory.org/software.html)

## Installation

    see: https://github.com/gina-alaska/alaska_affordable_energy_model/wiki#setting-up-a-workstation-to-run-the-model

## Building the AAEM documentation

    Building the documentation requires that Sphinx be installed.

    pip install Sphinx

    To build the docs in the docs/build folder, from the root of the code repository:

    sphinx-build  -b html ./docs/source/ docs/build/

    or more generally:

    sphinx-build  -b html <path to model docs/source> <path to build documentation>

    Alternatively, online model documentation is available at: http://model-docs.akenergyinventory.org

## Initial model setup

    From the AAEM repository directory on your local system:

    ./bin/aaem setup <path_to_model_results> <path_to_local_data>

    where <path_to_model_results> is a directory that will be created for the model configuration and results, and

    <path_to_local_data> is the path to your local Github data repository (cloned from https://github.com/gina-alaska/alaska_affordable_energy_model-data).

## Running the model

    See the documentation for advanced instructions on installation and running:

    http://model-docs.akenergyinventory.org

## Citation

We ask that you include the following citation in publications that make use of this model:
    
## Contributors

Contributors to the AAEM include:
  * Alaska Energy Authority: Neil McMahon
  * UAF/GINA: Jessie Cherry, Jennifer Delamere, Rawser Spicer, Jason Grimes, Dayne Broderson, Will Fisher
  * Alaska Energy Data Gateway: Brenden Hernandez
  
## Contacts
  For more information on the AAEM and its supporting data, contact: Neil McMahon, Planning Manager, Alaska Energy Authority, NMcMahon@aidea.org

  Model support questions can be addressed to: support+aaem@gina.alaska.edu
