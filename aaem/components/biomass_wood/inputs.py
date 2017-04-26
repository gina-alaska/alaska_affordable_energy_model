"""
Biomass Cordwood inputs
-----------------------

    input functions for Biomass cordwood component
    
    .. note::
        Uses Biomass Base input functions
    
"""
#~ import os.path
#~ from pandas import read_csv
import aaem.components.biomass_base as bmb
from copy import deepcopy

## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = deepcopy(bmb.yaml_import_lib)
