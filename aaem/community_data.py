"""
community_data.py
ross spicer
created: 2015/09/16

     community data module
"""
from pandas import read_csv, DataFrame
import yaml
import os.path
import numpy as np
## w&ww - water and wastewater
## it - intertie
## fc - forecast
## com - non-residential buildings 
from defaults import base_structure, base_comments
from diagnostics import Diagnostics
#~ from preprocessor import MODEL_FILES
from aaem.components import comp_lib, comp_order

from importlib import import_module
## read in config IO stuff, it's two lines because it was too long for one
from aaem.config_IO import read_config, merge_configs, save_config
from aaem.config_IO import validate_dict

from importlib import import_module
#~ import aaem.config as config

PATH = os.path.join
class CommunityData (object):
    """ Class doc """
    
    def __init__ (self, community_config, global_config = None, diag = None, 
        scalers = {'diesel price':1.0, 'diesel price adder':0},
        intertie_config = None):
        """
        """
        self.diagnostics = diag
        if diag == None:
            self.diagnostics = Diagnostics()
            
        if type(community_config) is dict and type(global_config) is dict:
            self.data = merge_configs(self.load_structure(), global_config)
            self.data = merge_configs(self.data, community_config)
        else: 
            self.data = self.load_config(community_config, global_config)
            
            
        valid, reason = self.validate_config()
        if not valid:
            raise StandardError, 'INVALID CONFIG FILE: ' + reason

        self.intertie = None
        
        intertie = self.get_item('community', 'intertie')
        if type (intertie) is list:
            if self.get_item('community', 'model as intertie') :
                self.intertie = 'parent'
            else:
                self.intertie = 'child'
         
        self.intertie_data = None
        
        ## load if community is part of an intertie but not the intertie 
        ## it's self. I.E. load info for Bethel or Oscarville,
        ## but not Bethel_intertie
        if not self.intertie is None and \
                not self.get_item('community', 'model as intertie'):
            self.diagnostics.add_note(
                'Community Data',
                'Attempting to find intertie data'
            )
            ## is the intertie_config a dict of file, also use same globals
            if type(intertie_config) is dict \
                    or (type(intertie_config) is str \
                    and os.path.isfile(intertie_config)):
                self.diagnostics.add_note(
                    'Community Data',
                    'using provided intertie_config argument'
                )
                self.intertie_data = CommunityData(
                    intertie_config, 
                    global_config,
                    self.diagnostics,
                    scalers
                )
            ## try to find the file
            elif os.path.isfile(community_config):
                rt_path = os.path.split(community_config)
                it_file = \
                    self.get_item('community','intertie')[0].\
                        replace(' ','_').replace("'",'')\
                     + '_intertie.yaml'
                it_file = os.path.join(rt_path[0], it_file)
                if os.path.isfile(it_file):
                    self.diagnostics.add_note(
                        'Community Data',
                        'Found interte data at ' + it_file
                    )
                    
                    self.intertie_data = CommunityData(
                        it_file,
                        global_config,
                        self.diagnostics,
                        scalers
                    )
            else:
                self.diagnostics.add_note(
                    'Community Data',
                    'Could not find intertie_data Leaving it as None'
                )
                ## self.intertie_data = None is initlized 
                
                        
                        
            
        
        # modify diesel prices and electric non-fuel prices
        

    
        self.check_auto_disable_conditions ()
        
        #~ self.load_construction_multipliers(construction_multipliers)
        
    
    def check_auto_disable_conditions  (self):
        """
        check for any auto disable conditions and disable those components
        """
        # no conditions at this time 
        pass
        
        #~ st = self.get_item('Water & Wastewater Efficiency',"data").ix["assumption type used"]
        #~ if st.values[0] == "UNKNOWN":
            #~ self.set_item('Water & Wastewater Efficiency',"enabled",  False)
            #~ self.diagnostics.add_error("Community Data", 
                    #~ ("(Checking Inputs) Water Wastewater system type unknown."
                     #~ " Fixing by disabling Wastewater component at runtime"))
        
    def modify_diesel_prices(self,
        scalers = {'diesel price':1.0, 'diesel price adder':0}):
            
        pass
    
    
    def modify_non_fuel_electricty_prices (self, N_slope_price = .15):
        """
        calculate the electricity price
        
        pre:
            community: diesel generation efficiency should be a numeric type
                       > 0
            community: elec non-fuel cost: is a floating point dollar value
            community: diesel prices: is a diesel projections object. 
        post:
            community: electric non-fuel prices: is a data frame of dollar 
                       values indexed by year
        """
        # TODO: 1 is 100% need to change to a calculation
        pass
    
    
    def validate_config(self):
        """
        validate a config library
        
        pre:
            lib should be a dictionary object
        post:
            returns true if lib is a valid config object; otherwise false
        """
        return validate_dict(self.data, self.load_structure())
        
        
        
    def load_structure (self):
        """ 

        """
        try:
            return self.structure
        except AttributeError:
            pass
        
        structure = base_structure
        
        for comp in comp_lib:
            module = \
                import_module('aaem.components.' + comp_lib[comp] + '.config')
            structure = merge_configs(structure, module.structure)
            
        self.structure = structure
        return structure
        
    def load_config (self, community_file, global_file = None):
        """ 
        loads the input files and creates the model input object
        
        pre: 
            community_file, and defaults should be .yaml files
        post:
            self.data is is usable
        """
        community = read_config(community_file)
        
        global_ = {}
        if not global_file is None:
            global_ = read_config(global_file)
        
        return merge_configs(
            merge_configs(
                self.load_structure(),
                global_
            ),
            community
        )
        


    def get_item (self, section, key):
        """ 
        get an item 
        
        pre:
            self.data exists
            section is a config section, and key is a key in said section
        post:
            returns an item 
        """
        return self.data[section][key]
        
    def get_section (self, section):
        """
        gets a sction
        pre:
            self.data exists
            section is a config section
        post:
            returns a section library 
        """
        return self.data[section]
        
    def set_item (self, section, key, data):
        """
        set an item 
        
        pre:
            self.data exists
            section is a config section, and key is a key in said section, and 
        data is the type that make sense there.
        post:
            self.data[section][key] is data 
        """
        self.data[section][key] = data
        
    
        

        
    def save (self, fname):
        """ 
        save the inputs used
        
        pre:
            self.model_inputs exists, fname is the path to a file
        pre:
            a valid .yaml config file is created
        """
        ## save work around 
        import copy
        copy = copy.deepcopy(self.data)
        
        
        comment = "config used"

        #~ conf, orders, comments, defaults = \
            #~ config.get_config(config.non_component_config_sections)
        
        #~ for comp in comp_lib:

            #~ cfg = import_module("aaem.components." + comp_lib[comp]+ '.config')
            #~ order = list(cfg.yaml_order) + \
                    #~ list(set(cfg.yaml_order) ^ set(cfg.yaml.keys()))
            #~ orders[comp] = order
            #~ comments[comp] = cfg.yaml_comments
            
        #~ section_order = config.non_component_config_sections + comp_order
        save_config(fname,copy,  {})
        del copy
        #~ self.data = copy
        #~ return comment + text
        

    
    
    
    
