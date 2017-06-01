"""
Transmission Configuration 
--------------------------
    
    Contains Transmission configuration info for community
    data yaml file, and other set-up requirements
    
    **Unique Configuration keys**
    
        'transmission loss per mile'
        'nearest community'
        'heat recovery o&m' 
        'est. intertie cost per mile'
        'percent o&m'
        'diesel generator o&m'
    
"""
from aaem.components import definitions
from aaem.community_data import CommunityData
import os

COMPONENT_NAME = "Transmission and Interties"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

order = [
    'enabled',
    'lifetime',
    'start year',
    
    'transmission loss per mile',
    'nearest community with lower price',
    'distance to community',
    'maximum savings',
    
    'percent o&m',
    'heat recovery o&m' ,
    'est. intertie cost per mile',
    'diesel generator o&m',
]

## List of yaml key/value pairs
structure = {
    "Transmission and Interties" : {
        'enabled': bool,
        'lifetime': int,
        'start year': int,
        
        'transmission loss per mile': float,
        'nearest community with lower price': str,
        'distance to community': float,
        'maximum savings': float,

        'percent o&m': float,
        'heat recovery o&m' : float,
        'est. intertie cost per mile': {
            'road needed': float, 
            'road not needed': float
        },
        'diesel generator o&m': float,
    }
}

comments = {
    'enabled': definitions.ENABLED,
    'lifetime': definitions.LIFETIME,
    'start year': definitions.START_YEAR_WITH_TYPE,
    
    'transmission loss per mile': '[float] percent of energy lost per mile',
    'nearest community with lower price': 
        '[str] name of community to connect to',
    'distance to community': 
        '[float] distance(mi) from community to connect to',
    'maximum savings': '[float] max possible savings',

    'percent o&m': '[float]',
    'heat recovery o&m' : '[float]',
    'est. intertie cost per mile': '[dict]',
    'diesel generator o&m': '[dict]',
}


def load_other_community(community_data,
    community_config, global_config, scalers):
    """
    """
    community_data.new_intetie_data = None

    com = community_data.get_item(
        'Transmission and Interties',
        'nearest community with lower price'
    )
    if com is None:
        return
    if com == '':
        return
    com = com.replace(' ','_')
    rt_path = os.path.split(community_config)[0]
    #~ print rt_path, com
    path = os.path.join(rt_path, com)
    #~ self.connect_to_intertie = False
    if os.path.exists(path +'_intertie.yaml'):
        #~ self.connect_to_intertie = True
        path += '_intertie'
    path += '.yaml'
    community_data.new_intetie_data = CommunityData(
        path, 
        global_config,
        community_data.diagnostics,
        scalers
    )


plugins = [load_other_community]
## list of prerequisites for module
prereq_comps = [] 
