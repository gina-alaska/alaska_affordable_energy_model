"""
Air Sorce Heat Pump Residential Configuration 
---------------------------------------------
    
    Contains Air Sorce Heat Pump Residential configuration info for community
    data yaml file, and other set-up requirements
    
    **Unique Configuration keys**
    
        btu/hrs: btu/hrs
        
        cost per btu/hrs: cost of heating $/btu/hr
        
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


## list of prerequisites for module
prereq_comps = ['Residential Energy Efficiency']
