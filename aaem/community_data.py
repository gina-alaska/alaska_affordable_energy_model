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
## com - community buildings 
from diesel_prices import DieselProjections
from defaults import absolute


PATH = os.path.join
class CommunityData (object):
    """ Class doc """
    
    def __init__ (self, data_dir, override, default="defaults"):
        """
            set up the object
        
        pre-conditions:
            data_dir: should be a directory 
                it should contain:
                    com_building_estimates.csv,
                    community_buildings.csv,
                    com_num_buildings.csv,
                    cpi.csv,
                    diesel_fuel_prices.csv,
                    hdd.csv,
                    interties.csv,
                    population.csv,
                    prices.csv,
                    region.csv,
                    residential.csv,
                    wastewater_data.csv,
                    yearly_electricity_summary.csv,
            override: a community_data.yaml file
            default: optionally a community_data.yaml file
        post-conditions:
            the community data object is initialized
        """
        self.load_input(override, default)
        self.data_dir = os.path.abspath(data_dir)
        self.get_csv_data()
        self.set_item("community","diesel prices",
                      DieselProjections(self.get_item("community","name"),
                      data_dir))
        self.calc_non_fuel_electricty_price ()
        self.check_auto_disable_conditions ()
        self.update_project_lifetime ()
        
    def update_project_lifetime (self):
        """ 
        updates the project lifetime to be until the end of the forecast period
        
        pre:
            self.model_inputs should be initilized
        post:
            project lifetimes are integers > 0
        """
        end = self.get_item('forecast', 'end year')
        for each in self.model_inputs:
            if 'lifetime' in self.model_inputs[each].keys():
                start = self.get_item(each, 'start year')
                self.set_item(each, 'lifetime', end - start)
        
    
    def check_auto_disable_conditions  (self):
        """
        check for any auto disable conditions and disable those components
        """
        st = self.get_item('water wastewater',"data").ix["assumption type used"]
        if st.values[0] == "UNKNOWN":
            self.set_item('water wastewater',"enabled",  False)
        
    
    def calc_non_fuel_electricty_price (self):
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
        generation_eff = self.get_item("community",
                                            "diesel generation efficiency")
        price = self.get_item("community","elec non-fuel cost") +\
            1.00 * self.get_item("community","diesel prices").projected_prices/\
                            generation_eff
        
        start_year = self.get_item("community","diesel prices").start_year
        years = range(start_year,start_year+len(price))
        self.electricity_price =price
        df = DataFrame({"year":years,
                        "price":self.electricity_price}).set_index("year")
        self.set_item("community","electric non-fuel prices",df)
        
    
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
        #~ absolutes = os.path.join("absolute_defaults.yaml")
        #~ lib = self.read_config(absolutes)
        lib = yaml.load(absolute)
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
        
        #~ absolutes = os.path.join("absolute_defaults.yaml")
        defaults = defaults_file
        overrides = community_file
        
        
        #~ absolute_defaults = self.read_config(absolutes)
        absolute_defaults = yaml.load(absolute)
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
            files listed in __init__ shild be in the data_dir
        post:
            csvitems are in self.model_inputs 
        """
        self.community = self.get_item('community','name')
        #~ if self.get_item('community buildings','com benchmark data')== "IMPORT":
            #~ self.set_item('community buildings','com benchmark data',
                                            #~ self.load_csv('com benchmark data'))
        #~ if self.get_item('community buildings',"com num buildings")== "IMPORT":
            #~ self.set_item('community buildings',"com num buildings",
                                            #~ self.load_csv("com num buildings"))
                                            
        if self.get_item('community',"HDD") == "IMPORT":
            self.set_item('community',"HDD", int(self.load_csv("hdd")))
        
        ## different type csv
        #~ if self.get_item('community buildings',
                                        #~ "com building estimates")== "IMPORT":
            #~ self.set_item('community buildings',"com building estimates",
             #~ read_csv(os.path.join(self.data_dir, "com_building_estimates.csv"),
                         #~ index_col = 0, header=1, comment = '#').T)
        
        ## load preprocessed files
        if self.get_item('forecast', "population") == "IMPORT":
            self.set_item('forecast', "population", 
                          self.load_pp_csv("population.csv"))
        #~ if self.get_item('forecast', "electricity") == "IMPORT":
            #~ self.set_item('forecast', "electricity", 
                          #~ self.load_pp_csv("electricity.csv"))

        if  self.get_item('residential buildings','data') == "IMPORT":
            self.set_item('residential buildings','data',
                          self.load_pp_csv("residential_data.csv"))

        if self.get_item('water wastewater', "data") == "IMPORT":
            self.set_item('water wastewater', "data", 
                          self.load_pp_csv("wastewater_data.csv"))

        region = self.load_pp_csv("region.csv")
        if self.get_item('community',"region") == "IMPORT":
            self.set_item('community',"region", region.ix["region"][0])
        if self.get_item('community',"heating fuel premium") == "IMPORT":    
            self.set_item('community',"heating fuel premium", 
                         float(region.ix["premium"][0]))
                         
        try:
            prices = self.load_pp_csv("prices.csv")
        except IOError:
            if self.get_item('community',"res non-PCE elec cost") == "IMPORT" \
              and self.get_item('community',"elec non-fuel cost") == "IMPORT":
                raise IOError, "Prices not found"
                
        if self.get_item('community',"res non-PCE elec cost") == "IMPORT":
            self.set_item("community", "res non-PCE elec cost",
                            np.float(prices.ix["res non-PCE elec cost"]))
        if self.get_item('community',"elec non-fuel cost") == "IMPORT":
            self.set_item("community", "elec non-fuel cost",
                            np.float(prices.ix["elec non-fuel cost"]))

        if self.get_item('community buildings',
                                        "com building estimates") == "IMPORT":
            self.set_item('community buildings',"com building estimates",
                           self.load_pp_csv("com_building_estimates.csv"))
                           
        if self.get_item('community buildings','com building data')== "IMPORT":
            self.set_item('community buildings','com building data',
                                    self.load_pp_csv("community_buildings.csv"))
                                    
        if self.get_item('community buildings','number buildings')== "IMPORT":
            self.set_item('community buildings','number buildings',
                int(self.load_pp_csv("com_num_buildings.csv").ix["Buildings"]))
                
        try:
            elec_summary = self.load_pp_csv("yearly_electricity_summary.csv")
        except IOError:
            if self.get_item('community',"line losses") == "IMPORT" \
              and self.get_item('community',"diesel generation efficiency") \
                                        == "IMPORT":
                raise IOError, "yearly electricity summary not found"
        
        if self.get_item('forecast', "electricity") == "IMPORT":
            self.set_item('forecast', "electricity",elec_summary[["consumption",
                                                "consumption residential",
                                                "consumption non-residential"]])
        
        
        if self.get_item('community',"line losses") == "IMPORT":
            self.set_item('community',"line losses", 
            np.float(elec_summary["line loss"][-3:].mean()))

        if self.get_item('community','diesel generation efficiency')== "IMPORT":
            self.set_item('community','diesel generation efficiency', 
                          np.float(elec_summary['efficiency'].values[-1]))
        try:
            if self.get_item('community',"generation") == "IMPORT":
                self.set_item('community',"generation", 
                                elec_summary["net generation"])
            if self.get_item('community','generation numbers') == "IMPORT":
                self.set_item('community','generation numbers', 
                              elec_summary[['generation diesel', 'generation hydro',
                                           'generation natural gas',
                                           'generation wind', 'generation solar',
                                           'generation biomass']])
        except:
            #~ self.diagnostics.add_warning("Community Data", 
                            #~ "Generation data not available by energy type")
                        #~ temp = elec_summary[['generation']]
            #~ temp['generation diesel'] = temp['generation']
            #~ temp['generation hydro'] = temp['generation'] - temp['generation']
            #~ temp['generation natural gas'] = temp['generation'] - \
                                                            #~ temp['generation']
            #~ temp['generation wind'] = temp['generation'] - temp['generation']
            #~ temp['generation solar'] = temp['generation'] - temp['generation']
            #~ temp['generation biomass'] = temp['generation'] - temp['generation']
    
            
            #~ self.set_item('community','generation numbers', temp )
            print "Generation data not available by energy type"
        
    def load_pp_csv(self, f_name):
        """
        load a preprocessed csv file
        
        pre:
            f_name must exist in self.data_dir
        post:
            returns a data frame from the file
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
        import copy
        copy = copy.deepcopy(self.model_inputs)
        
        self.set_item('residential buildings','data', "IMPORT")
        self.set_item('community buildings','com building data', "IMPORT")
        self.set_item('community buildings',"com building estimates", "IMPORT")

        self.set_item('community', "diesel prices", "IMPORT")
        self.set_item('forecast', "electricity", "IMPORT")
        self.set_item('forecast', "population", "IMPORT")
        self.set_item('water wastewater', "data", "IMPORT")
        self.set_item("community","electric non-fuel prices","IMPORT")
        self.set_item("community","generation numbers","IMPORT")
        self.set_item("community","generation","IMPORT")
        
        fd = open(fname, 'w')
        text = yaml.dump(self.model_inputs, default_flow_style=False) 
        fd.write(text)
        fd.close()

        del self.model_inputs
        self.model_inputs = copy
