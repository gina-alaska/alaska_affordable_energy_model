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

NAN = float('nan')

# subject to change with the new population forecast 
electricty_actuals = {
    "years":
        [2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014],
    "population": # 
        [71,  75,  76,  82,  76,  81,  85,  89,  94,  116, NAN, NAN],
    "residential":
        [124943,125867,121817,115990,112628,110554,
        110465,124966,164364,209675,93291,NAN],
    "community":
        [107254,104899,98198,95902,92973,109814,
        142871,153216,168710,185798,79853,NAN],
    "commercial":
        [3096,5057,5129,5230,4331,5154,4634,8225,4440,5857,3226,NAN],
    "gov":
        [8728,9537,15184,13327,13429,17798,16949,14619,12047,18938,10839,NAN],
    "unbilled":
        [NAN,NAN,NAN,NAN,NAN,NAN,NAN,NAN,NAN,NAN,NAN,NAN]
        }


buildings_by_type = {
                    "education":3,
                    "health care":0,
                    "office":1,
                    "other":3,
                    "public_assembly":1,
                    "public_order":0,
                    "warehouse":1,
                    "unknown":8,
                    }
#NAN unknown estimate should be used instead
sqft_by_type = {
        "education":11523,
        "health care":NAN,
        "office":820,
        "other":4500,
        "public_assembly":1200,
        "public_order":NAN,
        "warehouse":NAN,
        "unknown":NAN,
}
PATH = os.path.join
aea_aaem_root = os.path.dirname(os.getcwd())
data_dir = os.path.join(aea_aaem_root, "data")
res_data = read_csv(PATH(data_dir,"res_data.csv"),index_col=0,header=2).T["Manley Hot Springs"]
com_ben_data = read_csv(PATH(data_dir,"com_benchmark_data.csv"),index_col=0,
                                        header=0,
                                    comment = '#').T["Manley Hot Springs"].T
                                    
com_num_buildings = read_csv(PATH(data_dir,"com_num_buildings.csv"),
                                    index_col = 0, header=1, comment = '#').T["Manley Hot Springs"]



# True == 'yes'/ False == 'no'
manley_data = {
        "community": "Manley Hot Springs",
        "region": "Yukon-Koyukuk/Upper Tanana",
        "current_year": 2014, #year to base npv calculations on
        "population": 89, # number people in 2010
        "HDD": 14593, # Degrees/day
        "households": 41, # houses occupied in 2010
         
        "generation": 440077.00, # kWh/yr 
        "consumption_kWh": 384000, # kWh/year TODO: probably has a better name
        "consumption_HF": 40739, # gallons
        
        
        "dist_to_nearest_comm": 53, # miles
        "cost_power_nearest_comm": 00.1788, # $/kWh pre-PCE
        
        "res_non-PCE_elec_cost": 00.83, # $/kWh
        "elec_non-fuel_cost": 0.4024526823, # TODO: should be calculated
        
        "line_losses": .1210, # %  # or is this an assumption
            
        "fc_start_year":2014,
        "fc_end_year":2040,
        "fc_electricity_used":electricty_actuals,
            
        "it_lifetime" : 20, # years
        "it_start_year" : 2016, # a year 
        "it_phase": "Recon", # orange is supposed to be linked from
                                    #annother tab, but this olny shows up here
        "it_hr_installed": True, 
        "it_hr_operational": True,
        "it_road_needed": True, #road needed for for T&D
        "it_cost_known": False,
        "it_cost": float('nan'), # not available for here
        "it_resource_potential": "N/a",
        "it_resource_certainty": "N/a",
        
        "com_lifetime": 10,
        "com_start_year":2015,
        "com_benchmark_data": com_ben_data,
        "com_num_buildings": com_num_buildings, 
        
        
        "com_buildings":buildings_by_type, #
        "com_unknown_buildings":8,
        "com_sqft_to_retofit": sqft_by_type, # 
        
        
        
        "w&ww_lifetime" : 15, # years
        "w&ww_start_year" : 2015, # a year 
        "w&ww_system_type": "Haul", 
        "w&ww_energy_use_known": False,
        "w&ww_energy_use_electric": float("nan"), # kWh 
        "w&ww_energy_use_hf": float("nan"), # Gallons
        "w&ww_heat_recovery_used": False,
        "w&ww_heat_recovery": float("nan"), # units?
        "w&ww_audit_preformed": False,
        "w&ww_audit_savings_elec": float("nan"), # kWh
        "w&ww_audit_savings_hf": float("nan"), # gal
        "w&ww_audit_cost": float("nan"), # $ -- make cost_from_audit
        
        "res_start_year": 2015,
        "res_lifetime": 15,
        "res_model_data": res_data,

}





PATH = os.path.join
class CommunityData (object):
    """ Class doc """
    
    def __init__ (self, inFile, community):
        """ Class initialiser """
        self.inputs = read_csv(inFile,index_col=0,comment='#').T[community]
        self.static = {}
        self.static['res_model_data'] = read_csv(PATH(data_dir,"res_data.csv"),index_col=0,
                                                         header=2).T[community]
        self.static["com_benchmark_data"] = read_csv(PATH(data_dir,"com_benchmark_data.csv"),
                                           index_col=0,header=1, 
                                           comment = '#').T[community].T
        self.static["fc_electricity_used"] = electricty_actuals
        self.static["com_buildings"]  = buildings_by_type #
        self.static["com_sqft_to_retofit"] = sqft_by_type 
        self.static["com_benchmark_data"] = com_ben_data
        self.static["com_num_buildings"]= com_num_buildings
        
    
    def __getitem__ (self, key):
        """ Function doc """
        try:
            return self.static[key]
        except KeyError:
            pass
        try:
            return self.inputs[key]
        except KeyError, e:
            print e
            raise e
    def __setitem__ (self):
        """ Function doc """
        pass
        
    def __del__ (self):
        """ Function doc """
        pass
    
    
    ## new stuff    
    def read_config (self, config_file):
        """"""
        fd = open(config_file, 'r')
        text = fd.read()
        lib = yaml.load(text)
        fd.close()
        return lib
    
    def validate_config(self, lib):
        """validate a config library"""
        pass
        
    def load_valid_keys (self):
        """ load valid library structure"""
        pass
        
    def load_input(self, community_file, defaults = "defaults"):
        """ """
        cwd = os.path.dirname(os.getcwd())
        self.load_valid_keys()
        
        self.absolute_defaults= self.read_config(PATH("absolute_defaults.yaml"))
        
        if defaults == "defaults":
            self.client_defaults = self.absolute_defaults
        else:
            self.client_defaults = self.read_config(PATH(cwd,defaults)) 
        self.client_inputs = self.read_config(PATH(cwd,community_file)) 
        
        self.validate_config(self.absolute_defaults)
        self.validate_config(self.client_defaults)
        self.validate_config(self.client_inputs)
        
        self.glom_config_files()
        
        
    
    def get_csv_data (self):
        """ get the data that comes from (csv files"""
        pass
            
        
    def glom_config_files (self):
        """ take the defaults and overrides and combine in right order """
        self.model_inputs = {}
        for section in self.absolute_defaults:
            temp = {}
            for key in self.absolute_defaults[section]:
                try:
                    temp[key] = self.client_inputs[section][key]
                except KeyError as e:
                    try:
                        #~ print "defaulting1",key
                        temp[key] = self.client_defaults[section][key]
                    except KeyError as e:
                            #~ print "defaulting2",key
                            temp[key] = self.absolute_defaults[section][key]
            self.model_inputs[section] = temp


    def get_item (self, section, key):
        """ get an item """
        pass
        
    def get_section (self, section):
        """ """
        pass
    
    def save_model_inputs(self, fname):
        """ """
        fd = open(fname, 'w')
        text = yaml.dump(self.model_inputs, default_flow_style=False) 
        fd.write(text)
        fd.close()


        
        
