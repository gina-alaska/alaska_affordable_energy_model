"""
community_data.py
ross spicer
created: 2015/09/16

    a place holder for an eventual community data module. the manley_data
is here for testing
"""
from pandas import read_csv
import yaml
import os.path

## w&ww - water and wastewater
## it - intertie
## fc - forecast
## com - community buildings 
from diesel_prices import DieselProjections



PATH = os.path.join
class CommunityData (object):
    """ Class doc """
    
    def __init__ (self, data_dir, override, default="defaults"):
        self.load_input(override, default)
        self.data_dir = os.path.abspath(data_dir)
        self.get_csv_data()
        self.set_item("community","diesel prices",
                      DieselProjections(self.get_item("community","name"),
                      data_dir))
        
        
    
    ## new stuff    
    def read_config (self, config_file):
        """
        read a .yaml config file
        
        pre: 
            config_file is in the .yaml format
        post:
            returns a library generated from .yaml file
        """
        fd = open(config_file, 'r')
        lib = yaml.load(fd)
        fd.close()
        return lib
    
    def validate_config(self, lib):
        """
        validate a config library
        
        pre:
            lib should be a dictionary object
        post:
            returns true if lib is a valid config object; otherwise false
        """
        self.load_valid_keys()
        if not set(lib.keys()).issubset(set(self.valid_keys.keys())):
            return False
        for section in lib:
            if not set(lib[section].keys())\
                            .issubset(set(self.valid_keys[section])):
                return False
        return True
        
    def load_valid_keys (self):
        """ 
        load valid library structure
        
        pre:
            absolout_defaults.yaml shoud have all of the keys nessaey for 
        config files
        post:
            self.valid keys is a dict of sections with lists of keys as values
        ex. {section1:{key1,key2,key3}, section2:{keyA,keyB,keyC}}
        """
        absolutes = os.path.join("absolute_defaults.yaml")
        lib = self.read_config(absolutes)
        keys = {}
        for section in lib:
            temp = []
            for key in lib[section]:
                temp.append(key)
            keys[section]=temp
        self.valid_keys = keys
        
    def load_input(self, community_file, defaults_file = "defaults"):
        """ 
        loads the input files and creates the model input object
        
        pre: 
            community_file, and defaults should be .yaml files
        post:
            self.model_inputs is is usable
        """
        cwd = os.path.dirname(os.getcwd())
        
        absolutes = os.path.join("absolute_defaults.yaml")
        defaults = defaults_file
        overrides = community_file
        
        
        absolute_defaults = self.read_config(absolutes)
        
        if defaults_file == "defaults":
            client_defaults = absolute_defaults
        else:
            client_defaults = self.read_config(defaults) 
        client_inputs = self.read_config(overrides) 
        
        if not self.validate_config(absolute_defaults):
            raise RuntimeError, \
                    "absolute defaults do not meet the config standards"
        if not self.validate_config(client_defaults):
            raise RuntimeError, \
                    "client defaults do not meet the config standards"
        if not self.validate_config(client_inputs):
            raise RuntimeError, \
                    "client inputs do not meet the config standards"
        
        self.glom_config_files(client_inputs, 
                                client_defaults, absolute_defaults)
    
        
    def glom_config_files (self, client_inputs, 
                            client_defaults, absolute_defaults):
        """ 
        take the defaults and overrides and combine in right order 
        
        pre:
            client_inputs, client_defaults, absolute_defaults are valid config
        libraries
        post:
            self.model_inputs is a valid library 
        """
        self.model_inputs = {}
        for section in absolute_defaults:
            temp = {}
            for key in absolute_defaults[section]:
                try:
                    temp[key] = client_inputs[section][key]
                except KeyError as e:
                    try:
                        temp[key] = client_defaults[section][key]
                    except KeyError as e:
                            temp[key] = absolute_defaults[section][key]
            self.model_inputs[section] = temp


    def get_item (self, section, key):
        """ 
        get an item 
        
        pre:
            self.model_inputs exists
            section is a config section, and key is a key in said section
        post:
            returns an item 
        """
        return self.model_inputs[section][key]
        
    def get_section (self, section):
        """
        gets a sction
        pre:
            self.model_inputs exists
            section is a config section
        post:
            returns a section library 
        """
        return self.model_inputs[section]
        
    def set_item (self, section, key, data):
        """
        set an item 
        
        pre:
            self.model_inputs exists
            section is a config section, and key is a key in said section, and 
        data is the type that make sense there.
        post:
            self.model_inputs[section][key] is data 
        """
        self.model_inputs[section][key] = data
        
    def get_csv_data (self):
        """ 
        get the data that comes from the csv files
        
        pre: 
            self.model_inputs exits
            TODO: complete
        post:
            csvitems are in self.model_inputs 
        """
        self.community = self.get_item('community','name')
        if self.get_item('residential buildings','res model data') == "IMPORT":
            self.set_item('residential buildings','res model data',
                                            self.load_csv('res model data'))
            self.set_item('community','region',
                self.model_inputs['residential buildings']\
                                 ['res model data']['energy_region'])
            del(self.model_inputs['residential buildings']\
                                 ['res model data']['energy_region'])
        if self.get_item('community buildings','com benchmark data')== "IMPORT":
            self.set_item('community buildings','com benchmark data',
                                            self.load_csv('com benchmark data'))
        if self.get_item('community buildings',"com num buildings")== "IMPORT":
            self.set_item('community buildings',"com num buildings",
                                            self.load_csv("com num buildings"))
                                            
        if self.get_item('community',"HDD") == "IMPORT":
            self.set_item('community',"HDD", int(self.load_csv("hdd")))
        
        ## different type csv
        if self.get_item('community buildings',
                                        "com building estimates")== "IMPORT":
            self.set_item('community buildings',"com building estimates",
             read_csv(os.path.join(self.data_dir, "com_building_estimates.csv"),
                         index_col = 0, header=1, comment = '#').T)
                         
        
        ## load preprocessed files
        if self.get_item('forecast', "population") == "IMPORT":
            self.set_item('forecast', "population", 
                          self.load_pp_csv("population.csv"))
        if self.get_item('forecast', "electricity") == "IMPORT":
            self.set_item('forecast', "electricity", 
                          self.load_pp_csv("electricity.csv"))
        
        
            
    def load_pp_csv(self, f_name):
        """
        load a preprocessed csv file
        
        
        """
        return read_csv(os.path.join(self.data_dir, f_name),
                        comment = '#', index_col=0, header=0)

        
            
    def load_csv (self, file_key):
        """ 
        load a single csv file as a pandas data frame like object
        
        pre:
            file_key should resolve to a valid csv file name 
        post:
            returns a pandas data frame like object
        """
        return read_csv(os.path.join(self.data_dir, 
                        self.make_csv_name(file_key)), comment = '#', 
                        index_col=0, header=0).T[self.community].T
        
    
    def make_csv_name (self, file_key):
        """
        create the csv file name
        
        pre:
            file_key is matchs <text1> <text2> ... <text N>
        post:
            returns <text1>_<text2>_..._<text N>.csv
        """
        return file_key.replace(" ","_")+".csv"
    
    def save_model_inputs(self, fname):
        """ 
        save the inputs used
        
        pre:
            self.model_inputs exists, fname is the path to a file
        pre:
            a valid .yaml config file is created
        """
        ## save work around 
        self.set_item('residential buildings','res model data', "IMPORT")
        self.set_item('community buildings','com benchmark data', "IMPORT")
        self.set_item('community buildings',"com num buildings", "IMPORT")
        self.set_item('community buildings',"com building estimates", "IMPORT")
        self.set_item('water wastewater', "ww assumptions", "IMPORT")
        self.set_item('community', "diesel prices", "IMPORT")
        self.set_item('forecast', "electricity", "IMPORT")
        self.set_item('forecast', "population", "IMPORT")
        
        fd = open(fname, 'w')
        text = yaml.dump(self.model_inputs, default_flow_style=False) 
        fd.write(text)
        fd.close()

