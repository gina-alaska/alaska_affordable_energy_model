"""
Air Source Heat Pump Residential inputs
---------------------------------------

    input functions for Air Source Heat Pump Residential component
    
    .. note::
        Uses ASHP Base input functions
    
"""
import os.path
#~ from pandas import read_csv
import aaem.components.ashp_base as ashp_base
from copy import deepcopy

## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = deepcopy(ashp_base.yaml_import_lib)
