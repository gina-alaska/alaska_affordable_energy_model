"""
driver.py

    will run the model
"""
from community_data import CommunityData
from forecast import Forecast

from components.residential_buildings import ResidentialBuildings
from components.community_buildings import CommunityBuildings
from components.wastewater import WaterWastewaterSystems

from pandas import DataFrame, read_pickle
import numpy as np

import yaml
import os.path
from importlib import import_module

class Driver (object):
    """ 
    Driver for the AAEM.
    """
    
    def __init__ (self, config_file):
        """ 
        set up driver 
        
        pre:
            infile is an absolute path 
        post:
            model is ready to be run
        """
        fd = open(config_file, 'r')
        lib = yaml.load(fd)
        fd.close()
        self.cd = CommunityData(lib["overrides"], lib["defaults"])
        self.fc = Forecast(self.cd)
        self.load_comp_lib()
        
    def load_comp_lib (self):
        """
        load the component library
        pre:
            comp_lib.yaml is a library of all available model components
        post:
            self.comp_lib is a dictonarey the maps the names of components in
        absolute defaults, to the python modules. 
        """
        fd = open("comp_lib.yaml", 'r')
        self.comp_lib = yaml.load(fd)
        #~ print self.comp_lib
        fd.close()
        
    def run_components (self):
        """
        run enabled components
        pre:
            self.comp_lib exists
        post:
            self.comps_used is a dictionary of the used components. 
        """
        self.comps_used = {}
        for comp in self.comp_lib:
            ## TODO implment in yaml
            #~ if self.cd[comp]["enabled"] == False:
                #~ continue
            component = self.get_component(self.comp_lib[comp])(self.cd,self.fc)
            component.run()
            self.comps_used[comp] = component
        
        
    def get_component (self, comp_name):
        """
        import a component
        pre:
            comp name is the name of a component
        post:
            returns imported module
        """
        return import_module("components." + comp_name).component







def test (com_data_file = "test_case/manley_data.yaml"):
    """
    """
    cd = CommunityData(com_data_file, "test_case/data_defaults.yaml")
    
    fc = Forecast(cd)
    
    rb = ResidentialBuildings(cd, fc)
    rb.run()
    cb = CommunityBuildings(cd, fc)
    cb.run()
    ww = WaterWastewaterSystems(cd, fc)
    ww.run()
    cd.save_model_inputs("../test_case/saved_inputs_from_test_driver.yaml")
    #~ fc.calc_electricity_totals()
    #~ fc.forecast_population()
    fc.forecast_consumption()
    fc.forecast_generation()
    fc.forecast_average_kW()
    #~ fc.forecast_households()
    fc.calc_total_HF_forecast()
    #~ fc.population[0] = 11
    df = DataFrame( {"pop": fc.population,
                     "HH" : fc.households,
                     "kWh consumed" : fc.consumption,
                     "kWh generation": fc.generation,
                     "avg. kW": fc.average_kW,
                     "res HF": fc.res_HF,
                     "com HF":fc.com_HF,
                     "ww HF":fc.www_HF,
                     "total HF": fc.total_HF,}, 
                     np.array(range(len(fc.population))) + fc.start_year)
                     
    if com_data_file == "test_case/manley_data.yaml":
        df.to_csv("../test_case/run_df.csv",columns =["pop","HH","kWh consumed",
                                                    "kWh generation","avg. kW",
                                                    "res HF", "com HF","ww HF",
                                                    "total HF"])
        base_df = read_pickle("../test_case/base.pckl")
        (base_df == df).to_csv("../test_case/test_truth_table.csv", 
                                          columns =["pop","HH", "kWh consumed",
                                                    "kWh generation","avg. kW",
                                                    "res HF", "com HF", "ww HF",
                                                    "total HF"])
    

    return df, (cd,fc,rb,cb,ww)
