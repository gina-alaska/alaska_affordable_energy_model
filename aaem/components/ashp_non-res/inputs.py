"""
inputs.py

    input functions for Air Source Heat Pumps - Non-Residential component
"""
#~ import os.path
#~ from pandas import read_csv
import aaem.components.ashp_base as ashp_base
from copy import deepcopy

## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = deepcopy(ashp_base.yaml_import_lib)
