"""
inputs.py

    input functions for Biomass - Pellet component
"""
import os.path
from pandas import read_csv

import aaem.components.biomass_base as bmb
from copy import deepcopy

## import for road system data
def road_import (data_dir):
    """
    import the road system boolean
    """
    data_file = os.path.join(data_dir, "road_system.csv")
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    data = data['value'].to_dict()
    on_road = data["On Road/SE"].lower() == "yes"
    return on_road
    
## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = deepcopy(bmb.yaml_import_lib)
yaml_import_lib["on road system"] = road_import
