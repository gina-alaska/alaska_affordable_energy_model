"""
config.py

    Air Source Heat Pumps - Residential config info for community data yaml file
"""
import aaem.components.ashp_base as ashp_base
from copy import deepcopy

COMPONENT_NAME = "Residential ASHP"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

## List of yaml key/value pairs
yaml = deepcopy(ashp_base.yaml)
yaml[ "btu/hrs"] = 18000
yaml[ "cost per btu/hrs" ] = 6000 

## default values for yaml key/Value pairs
yaml_defaults = deepcopy(ashp_base.yaml_defaults)
    
## order to save yaml
yaml_order = deepcopy(ashp_base.yaml_order) 

## comments for the yaml key/value pairs
yaml_comments = deepcopy(ashp_base.yaml_comments)


## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = deepcopy(ashp_base.yaml_not_to_save)

## list of prerequisites for module
prereq_comps = ['Residential Energy Efficiency']

DESCRIPTION = """
    This component calculates the potential heating oil offset by installing new air source heat pumps for residential buildings. 
"""
