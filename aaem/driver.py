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
from datetime import datetime

class Driver (object):
    """ 
    Driver for the AAEM.
    """
    
    def __init__ (self, overrides, defaults):
        """ 
        set up driver 
        
        pre:
            infile is an absolute path 
        post:
            model is ready to be run
        """
        self.cd = CommunityData(overrides,defaults)
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
            if self.cd.get_item(comp,"enabled") == False:
                continue
            #~ print comp
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
        
    def save_components_output (self, directory):
        """
        save the output from each component
        pre:
            self.comps_used should be a set of run components
        post:
            for each component in self.comps_used the electric, heating, and
        financial outputs are saved as csv files 
        """
        for comp in self.comps_used:
            self.comps_used[comp].save_csv_outputs(directory + "model_outputs/")
    
    def save_forecast_output (self, directory):
        """ Function doc """
        self.fc.save_forecast(directory+"forecast.csv")
    
    def save_input_files (self, directory):
        """ Function doc """
        self.cd.save_input_files(directory+"config_uesd.yaml")
        


def run_model (config_file):
    """ 
    run the model given an input file
    pre:
        config_file is the absolute path to a yaml file with this format:
            |------ config example -------------
            |overrides: "test_case/manley_data.yaml"
            |defaults: defaults | defaults| 
            |output directory path: # a path
            |output directory suffix: TIMESTAMP # TIMESTAMP|NONE|<string>
            |-------------------------------------
    post:
        The model will have been run, and outputs saved.  
    """
    fd = open(config_file, 'r')
    config = yaml.load(fd)
    fd.close()
    
    
    overrides = os.path.abspath(config['overrides'])
    defaults = "defaults" if config['defaults'] is None else\
                os.path.abspath(config['defaults'])
    
    
    
    out_dir = config['output directory path']
    out_dir = out_dir[:1] if out_dir[-1] == '/' else out_dir 
    out_dir = os.path.abspath(out_dir)
    suffix = config['output directory suffix']
    if suffix == "TIMESTAMP":
        timestamp = datetime.strftime(datetime.now(),"%Y%m%d%H%M%S")
        out_dir+= "_" +timestamp + '/'
    elif suffix != "NONE":
        out_dir+= "_" + suffix + '/'
    else:
        out_dir+= '/'

    print out_dir
    
    
    
    
    model = Driver(overrides, defaults)
    model.load_comp_lib()
    model.run_components()
    # save functionality needs to be written at component level
    #~ model.save_components_output(out_dir)
    #~ model.save_forecast_output(out_dir)
    #~ model.save_input_files(out_dir)
    
    
    
        






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
