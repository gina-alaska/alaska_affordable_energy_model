"""
component_template.py

a template for adding components



"""
import numpy as np
from math import isnan
from pandas import DataFrame,concat

from annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import diagnostics
import aaem.constants as constants


## steps for using
### 1) copy this file as component_name.py and go throug this file folloing the 
###    commented instructions
### 2) add new components things to default yaml file
### 3) add the component to __init__ in this directory



# change to component name (i.e. 'residential buildings')
COMPONENT_NAME = "solar power"

## List of yaml key/value pairs
yaml = {'enabled': False,
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        }

## default values for yaml key/Value pairs
yaml_defaults = {'enabled': True,
        'lifetime': 20,
        'start year': 2017,
        }
    
## order to save yaml
yaml_order = ['enabled', 'lifetime', 'start year']

## comments for the yaml key/value pairs
yaml_comments = {'enabled': '',
        'lifetime': 'number years <int>',
        'start year': 'start year <int>'}
       
## Functions for CommunityData IMPORT keys
def process_data_import(data_dir):
    """
    """
    pass

## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = {}# fill in
    
## preprocessing functons 
def preprocess_header (ppo):
    """
    """
    return  "# " + ppo.com_id + " solar power data\n"+ \
            ppo.comments_dataframe_divide
    

def preprocess (ppo):
    """"""
    return
    out_file = os.path.join(ppo.out_dir,"wind_power_data.csv")

    fd = open(out_file,'w')
    fd.write(preprocess_header(ppo))
    fd.close()

    # create data and uncomment this
    #~ data.to_csv(out_file, mode = 'a',header=False)
    
    ppo.MODEL_FILES['SOLAR_DATA'] = "solar_power_data.csv" # change this

## List of raw data files required for wind power preproecssing 
raw_data_files = []# fillin

## list of wind preprocessing functions
preprocess_funcs = [preprocess]

## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = []
    
## component summary
def component_summary (coms, res_dir):
    """
    """
    pass
    
        

#   do a find and replace on ComponentName to name of component 
# (i.e. 'ResidentialBuildings')
class SolarPower (AnnualSavings):
    """
    """
    def __init__ (self, community_data, forecast, diag = None):
        """
        Class initialiser

        pre:
            community_data is a CommunityData object. diag (if provided) should 
        be a Diagnostics object
        post:
            the model can be run
        """
        self.diagnostics = diag
        if self.diagnostics == None:
            self.diagnostics = diagnostics()
        self.forecast = forecast
        self.cd = community_data.get_section('community')
       
        self.comp_specs = community_data.get_section(COMPONENT_NAME)
        self.component_name = COMPONENT_NAME

        self.set_project_life_details(self.comp_specs["start year"],
                                      self.comp_specs["lifetime"],
                        self.forecast.end_year - self.comp_specs["start year"])
                        
        ### ADD other intiatzation stuff
        
    
    def run (self):
        """
        run the forecast model
        
        pre:
            self.cd should be the community library from a community data object
        post:
            TODO: define output values. 
            the model is run and the output values are available
        """
        if self.cd["model electricity"]:
            # change these below
            self.calc_baseline_kWh_consumption()
            self.calc_retrofit_kWh_consumption()
            self.calc_savings_kWh_consumption()
            # NOTE*:
            #   some times is it easier to find the savings and use that to
            # calculate the retro fit values. If so, flip the function calls 
            # around, and change the functionality of
            # self.calc_savings_kWh_consumption() below
            
        
        if self.cd["model heating fuel"]:
            # change these below
            self.calc_baseline_fuel_consumption()
            self.calc_retrofit_fuel_consumption()
            self.calc_savings_fuel_consumption()
            # see NOTE*
        
        if self.cd["model financial"]:
            # AnnualSavings functions (don't need to write)
            self.get_diesel_prices()
            
            # change these below
            self.calc_capital_costs()
            self.calc_annual_electric_savings()
            self.calc_annual_heating_savings()
            
            # AnnualSavings functions (don't need to write)
            self.calc_annual_total_savings()
            self.calc_annual_costs(self.cd['interest rate'])
            self.calc_annual_net_benefit()
            self.calc_npv(self.cd['discount rate'], self.cd["current year"])
 
    # Make this do stuff
    def calc_baseline_kWh_consumption (self):
        """ Function doc """
        self.baseline_kWh_consumption = np.zeros(self.project_life)
    
    # Make this do stuff
    def calc_retrofit_kWh_consumption (self):
        """ Function doc """
        self.retrofit_kWh_consumption = np.zeros(self.project_life)
    
    # use this or change it see NOTE* above
    def calc_savings_kWh_consumption(self):
        """
        calculate the savings in electricity consumption(in kWh) for a community
        
        pre:
            self.baseline_kWh_consumption and self.retrofit_kWh_consumption
        should be array of the same length or scaler numbers (units kWh)
    
        post:
            self.savings_kWh_consumption is an array or scaler of numbers 
        (units kWh)
        """
        self.savings_kWh_consumption = self.baseline_kWh_consumption -\
                                       self.retrofit_kWh_consumption
        
    # Make this do stuff
    def calc_baseline_fuel_consumption (self):
        """ Function doc """
        self.baseline_fuel_consumption = np.zeros(self.project_life)
     
    # Make this do stuff
    def calc_retrofit_fuel_consumption (self):
        """ Function doc """
        self.retrofit_fuel_consumption = np.zeros(self.project_life)
        
    # use this or change it see NOTE* above
    def calc_savings_fuel_consumption(self):
        """
        calculate the savings in fuel consumption(in mmbtu) for a community
        
        pre:
            self.baseline_fuel_consumption and self.retrofit_fue;_consumption
        should be array of the same length or scaler numbers (units mmbtu)
    
        post:
            self.savings_fuel_consumption is an array or scaler of numbers 
        (units mmbtu)
        """
        self.savings_fuel_consumption = self.baseline_fuel_consumption -\
                                        self.retrofit_fuel_consumption
    
    
    # Make this do stuff
    def calc_capital_costs (self):
        """ Function Doc"""
        self.capital_costs = np.nan
        
    
    # Make this do stuff
    def calc_annual_electric_savings (self):
        """
        """
        price = 0 
        self.annual_electric_savings = self.savings_kWh_consumption * price
        
        
    # Make this do sruff. Remember the different fuel type prices if using
    def calc_annual_heating_savings (self):
        """
        """
        price = 0 
        self.annual_heating_savings = self.savings_fuel_consumption * price



        
    
component = SolarPower

def test ():
    """
    tests the class using the manley data.
    """
    manley_data = CommunityData("../test_case/input_data/","../test_case/baseline_results/config_used.yaml")
    fc = Forecast(manley_data)
    comp = SolarPower(manley_data, fc)
    comp.run()
    return comp,fc # return the object for further testing
