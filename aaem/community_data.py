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
from diesel_prices import DieselProjections
from defaults import build_defaults
from diagnostics import diagnostics
#~ from preprocessor import MODEL_FILES
from aaem.components import comp_lib

from importlib import import_module

PATH = os.path.join
class CommunityData (object):
    """ Class doc """
    
    def __init__ (self, data_dir, override, default="defaults", diag = None):
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
        self.diagnostics = diag
        if diag == None:
            self.diagnostics = diagnostics()
            
        self.load_input(override, default)
        self.data_dir = os.path.abspath(data_dir)
        self.get_csv_data()
        self.set_item("community","diesel prices",
                      DieselProjections(self.get_item("community","name"),
                      data_dir))
        if self.get_item("community", "model electricity"):
            self.calc_non_fuel_electricty_price ()
        self.check_auto_disable_conditions ()
    
    def check_auto_disable_conditions  (self):
        """
        check for any auto disable conditions and disable those components
        """
        # no conditions at this time 
        pass
        
        #~ st = self.get_item('water wastewater',"data").ix["assumption type used"]
        #~ if st.values[0] == "UNKNOWN":
            #~ self.set_item('water wastewater',"enabled",  False)
            #~ self.diagnostics.add_error("Community Data", 
                    #~ ("(Checking Inputs) Water Wastewater system type unknown."
                     #~ " Fixing by disabling Wastewater component at runtime"))
        
    
    def calc_non_fuel_electricty_price (self, N_slope_price = .15):
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
        percent_diesel = self.get_item('community','generation numbers')\
                         ['generation diesel'].fillna(0)/\
                         self.get_item('community',"generation")
        percent_diesel = float(percent_diesel.values[-1])
        
        adder = percent_diesel * \
            self.get_item("community","diesel prices").projected_prices/\
            generation_eff
            
        adder[np.isnan(adder)] = 0 
        
        price = self.get_item("community","elec non-fuel cost") + adder
        
        start_year = self.get_item("community","diesel prices").start_year
        years = range(start_year,start_year+len(price))
        self.electricity_price = price
        if self.get_item('community',"region") == "North Slope":
            self.electricity_price = [N_slope_price for y in  years]
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
        
        try:
            if self.valid_keys:
                pass
        except AttributeError:
        
            lib = build_defaults(comp_lib)
            #~ lib = yaml.load(absolute)
            #~ print lib
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
        #~ absolute_defaults = yaml.load(absolute)
        absolute_defaults = build_defaults(comp_lib)
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
        IMPORT_FLAGS = ("IMPORT", "--see input_data")
        
        self.community = self.get_item('community','name')
        ## load preprocessed files
        if self.get_item('forecast', "population") in IMPORT_FLAGS:
            self.set_item('forecast', "population", 
                          self.load_pp_csv("population.csv"))
    
        if self.get_item('community',"HDD") in IMPORT_FLAGS:
            try:
                self.set_item('community',"HDD", 
                          int(self.load_pp_csv("hdd.csv").values[0][0]))
            except IOError:
                raise IOError, "Heating Degree Days summary not found"
        
        
        for comp in comp_lib:
            c = comp_lib[comp]
            #~ print c,',' ,comp
            lib = import_module("aaem.components." + c).yaml_import_lib
            keys = lib.keys()
            for k in keys:
                if self.get_item(comp, k) in IMPORT_FLAGS:
                    self.set_item(comp,k, lib[k](self.data_dir))
        
        #~ comp_name = 'residential_buildings'
        #~ lib = import_module("aaem.components." + comp_name).yaml_import_lib
        
        #~ lib['data']()
        #~ self.set_item('residential buildings','data', lib['data'](self.data_dir))
        
        
        
            
        
        
        
        #~ if  self.get_item('residential buildings','data') in IMPORT_FLAGS:
            #~ self.set_item('residential buildings','data',
                          #~ self.load_pp_csv("residential_data.csv"))
            
            #~ self.get_item('residential buildings','data').\
                        #~ ix["Notes"]['value'] = np.nan
            
            #~ if self.get_item('residential buildings','data').\
                    #~ ix["average kWh per house"]['value'] == "CALC_FOR_INTERTIE":
                #~ self.get_item('residential buildings','data').\
                        #~ ix["average kWh per house"]['value'] = np.nan
                        
            #~ self.get_item('residential buildings','data')['value'] =\
                        #~ self.get_item('residential buildings',
                                #~ 'data')['value'].astype(float)

        #~ if self.get_item('water wastewater', "data") in IMPORT_FLAGS:
            #~ self.set_item('water wastewater', "data", 
                          #~ self.load_pp_csv("wastewater_data.csv"))

        region = self.load_pp_csv("region.csv")
        if self.get_item('community',"region") in IMPORT_FLAGS:
            self.set_item('community',"region", region.ix["region"][0])
        if self.get_item('community',"heating fuel premium") in IMPORT_FLAGS:    
            self.set_item('community',"heating fuel premium", 
                         float(region.ix["premium"][0]))
                         
        try:
            prices = self.load_pp_csv("prices.csv")
        except IOError:
            if self.get_item('community',
                                    "res non-PCE elec cost") in IMPORT_FLAGS \
              and self.get_item('community',
                                        "elec non-fuel cost") in IMPORT_FLAGS:
                #~ raise IOError, "Prices not found"
                self.diagnostics.add_error("Community Data", 
                        ("(reading csv) electricity prices not found."
                         " Fixing by disabling financial modeling at runtime"))
                self.set_item("community", "res non-PCE elec cost", False)
                self.set_item("community", "elec non-fuel cost", False)
                self.set_item("community", "model financial", False)
                
        if self.get_item('community',"res non-PCE elec cost") in IMPORT_FLAGS:
            self.set_item("community", "res non-PCE elec cost",
                            np.float(prices.ix["res non-PCE elec cost"]))
        if self.get_item('community',"elec non-fuel cost") in IMPORT_FLAGS:
            self.set_item("community", "elec non-fuel cost",
                            np.float(prices.ix["elec non-fuel cost"]))

        #~ if self.get_item('non-residential buildings',
                                      #~ "com building estimates") in IMPORT_FLAGS:
            #~ self.set_item('non-residential buildings',"com building estimates",
                           #~ self.load_pp_csv("com_building_estimates.csv"))
                           
        #~ if self.get_item('non-residential buildings',
                                        #~ 'com building data') in IMPORT_FLAGS:
            #~ self.set_item('non-residential buildings','com building data',
                                    #~ self.load_pp_csv("community_buildings.csv"))
                                    
        #~ if self.get_item('non-residential buildings',
                                        #~ 'number buildings') in IMPORT_FLAGS:
            #~ self.set_item('non-residential buildings','number buildings',
                #~ int(self.load_pp_csv("com_num_buildings.csv").ix["Buildings"]))
                
        try:
            elec_summary = self.load_pp_csv("yearly_electricity_summary.csv")
        except IOError:
            if self.get_item('community',"line losses") in IMPORT_FLAGS \
              and self.get_item('community',"diesel generation efficiency") \
                                        in IMPORT_FLAGS:
                self.set_item('community','model electricity', False)
            elec_summary = None
                #~ raise IOError, "yearly electricity summary not found"
        
        if elec_summary is None:
            consumption = None
            line_losses = None
            diesel_gen_eff = None
            net_gen = None
            gen_by_type = None
        else:
            consumption = elec_summary[["consumption","consumption residential",
                                "consumption non-residential"]]
            line_losses = np.float(elec_summary["line loss"][-3:].mean())
            diesel_gen_eff = np.float(elec_summary['efficiency'].values[-3:].mean())
            net_gen = elec_summary["net generation"]
            gen_by_type = elec_summary[['generation diesel', 'generation hydro',
                                       'generation natural gas',
                                       'generation wind', 'generation solar',
                                       'generation biomass']]
                                
        if self.get_item('forecast', "electricity") in IMPORT_FLAGS:
            self.set_item('forecast', "electricity",consumption)
        
        
        if self.get_item('community',"line losses") in IMPORT_FLAGS:
            if line_losses is None:
                self.set_item('community',"line losses",line_losses)
            else:
                ll = np.float(elec_summary["line loss"][-3:].mean())
                if ll < 0.0 or np.isnan(ll):
                    try:
                        def_ll = self.get_item('community',"default line losses")
                    except KeyError:
                        def_ll = .1
                    self.diagnostics.add_note("Line Losses",
                                    ("The lineloss was negative " + str(ll) + " "
                                     "correcting to default "+ str(def_ll) + "."))
                    ll = def_ll
                 
                    
                try:
                    max_ll = self.get_item('community',"default line losses")
                except KeyError:
                    max_ll = self.get_item('community',"max line losses")
                if ll > max_ll:
                    self.diagnostics.add_note("Line Losses",
                                    ("The lineloss " + str(ll) + " was greater than"
                                     " max of "+ str(max_ll) + ". setting to max."))
                    ll = max_ll
                
                self.set_item('community',"line losses",ll)
    
        if self.get_item('community',
                                'diesel generation efficiency')in IMPORT_FLAGS:
            if diesel_gen_eff is None\
               or diesel_gen_eff == 0 \
               or np.isnan(diesel_gen_eff):
                self.set_item('community','diesel generation efficiency', 
                                self.get_item('community',
                                    "default diesel generator efficiency"))
            else:
                self.set_item('community','diesel generation efficiency', 
                                                            diesel_gen_eff)
        try:
            if self.get_item('community',"generation") in IMPORT_FLAGS:
                self.set_item('community',"generation", net_gen)
            if self.get_item('community','generation numbers') in IMPORT_FLAGS:
                self.set_item('community','generation numbers', gen_by_type)
        except:
            #~ self.diagnostics.add_warning("Community Data", 
                            #~ "Generation data not available by energy type")
                        #~ temp = elec_summary[['generation']]
            #~ temp['generation diesel'] = temp['generation']
            #~ temp['generation hydro'] = temp['generation'] - \
                                                #~ temp['generation']
            #~ temp['generation natural gas'] = temp['generation'] - \
                                                        #~ temp['generation']
            #~ temp['generation wind'] = temp['generation'] - \
                                                    #~ temp['generation']
            #~ temp['generation solar'] = temp['generation'] - \
                                                    #~ temp['generation']
            #~ temp['generation biomass'] = temp['generation'] - \
                                                    #~ temp['generation']
    
            
            #~ self.set_item('community','generation numbers', temp )
            print "Generation data not available by energy type"
            
        try:
            # special loading case
            try:
                intertie = read_csv(os.path.join(self.data_dir,"interties.csv"),
                            comment = '#', index_col=0,names =['key','value'])
                com_list = intertie.T.values[0].tolist()[1:]
                tied = intertie.ix['Plant Intertied'].values[0]
            except IndexError:
                intertie = read_csv(os.path.join(self.data_dir,"interties.csv"),
                            comment = '#', index_col=0).ix[0]
                tied = intertie.ix['Plant Intertied']
                com_list = intertie.T.values.tolist()[1:]
            #~ print intertie.ix['Plant Intertied'].values[0]
            self.intertie_list = com_list
            if tied == 'No':
                intertie = None
            elif ''.join(com_list).replace("''","") == '':
                # the list of subcommunites is empty, so for modeling purposes 
                #no intertie
                intertie = None
            else:
                if self.get_item('community','name') in com_list:
                    intertie = "child"
                elif self.get_item('community','name').find('_intertie') != -1:
                    intertie = 'parent'
                else:
                    intertie = "child"
        except IOError:
            intertie = None
        self.intertie = intertie
        
        self.copies = self.load_pp_csv("copies.csv")
        
        
        prices = self.load_pp_csv("prices_non-electric_fixed.csv")
                
        if self.get_item('community',"propane price") in IMPORT_FLAGS:
            self.set_item("community", "propane price",
                            np.float(prices.ix["Propane"]))
        if self.get_item('community',"biomass price") in IMPORT_FLAGS:
            self.set_item("community", "biomass price",
                            np.float(prices.ix["Biomass"]))
        
        limits = self.load_pp_csv("generation_limits.csv")
        if self.get_item('community', 'hydro generation limit') in IMPORT_FLAGS:
            try:
                self.set_item('community','hydro generation limit',
                                float(limits.ix["hydro"]))
            except ValueError:
                self.set_item('community','hydro generation limit',
                                float(0))
                                
        if self.get_item('community', 'wind generation limit') in IMPORT_FLAGS:
            try:
                self.set_item('community','wind generation limit',
                                float(limits.ix["wind"]))
            except ValueError:
                self.set_item('community','wind generation limit',
                                float(0))
                                
        diesel_data = self.load_pp_csv("diesel_data.csv")
        
        if self.get_item('community', 
                            'switchgear suatable for RE') in IMPORT_FLAGS:
            sgs = diesel_data.ix['Switchgear Suitable']['value'] == 'Yes'
            self.set_item('community','switchgear suatable for RE',sgs)
        
        if self.get_item('community', 
                            'heat recovery operational') in IMPORT_FLAGS:
            hro = diesel_data.ix['Waste Heat Recovery Opperational']\
                                                            ['value'] == 'Yes'
            self.set_item('community','heat recovery operational',hro)
            
        
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
        #~ rel = os.path.relpath(os.path.dirname(fname),os.path.join("model",".."))
        #~ rt = os.path.join(rel,"input_data")
        
        
        
        copy['residential buildings']['data'] = "IMPORT"
        copy['non-residential buildings']['com building data'] = "IMPORT"
        copy['non-residential buildings']["com building estimates"] =  "IMPORT"

        copy['community']["diesel prices"]="IMPORT"
        copy['forecast']["electricity"] = "IMPORT"
        copy['forecast']["population"] = "IMPORT"
        copy['water wastewater']["data"] = "IMPORT"
        copy["community"]["electric non-fuel prices"] = "IMPORT"
        copy["community"]["generation numbers"] =  "IMPORT"
        copy["community"]["generation"] = "IMPORT"
        
        for comp in comp_lib:
            c = comp_lib[comp]
            try:
                lis= import_module("aaem.components." + c).yaml_not_to_save
            except AttributeError:
                continue
            for item in lis:
                copy[comp][item] =  "IMPORT"
        
        fd = open(fname, 'w')
        text = yaml.dump(copy, default_flow_style=False) 
        comment = \
        ("# some of the items may reference files the input data directory\n"
         "# residential buildings(data)-> residential_data.csv\n" 
         "# non-residential buildings(com building data)"
                                        " -> community_buildings.csv\n"
         "# non-residential buildings(com building estimates)"
                                     " -> com_building_estimates.csv\n"
         "# community(diesel prices) -> \n"
         "# forecast(electricity) -> yearly_electricity_summary.csv\n"
         "# forecast(population) -> population.csv\n"
         "# water wastewater(data) -> wastewater_data.csv\n"
         "# community(electric non-fuel prices) -> prices.csv\n"
         "# community(generation numbers) -> yearly_electricity_summary.csv\n"
         "# community(generation) -> yearly_electricity_summary.csv\n")
        fd.write(comment + text.replace("IMPORT","--see input_data"))
        fd.close()

        del copy
        #~ self.model_inputs = copy
        #~ return comment + text
        
def test(data, overrides, defaults):
    """ 
    test the object
    """
    cd = CommunityData(data, overrides, defaults)
    cd.save_model_inputs("cd_test.yaml")
    cd2 = CommunityData(data, "cd_test.yaml")
    cd2.save_model_inputs("cd_test2.yaml")
    fd = open("cd_test.yaml",'r')
    t1 = fd.read()
    fd.close()
    fd = open("cd_test2.yaml",'r')
    t2 = fd.read()
    fd.close()
    os.remove("cd_test.yaml")
    os.remove("cd_test2.yaml")
    return {"result":t1 == t2, "text":{1:t1, 2:t2}}
    
    
    
    
    
