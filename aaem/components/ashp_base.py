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
COMPONENT_NAME = "air source heat pumps base"

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
    return  "# " + ppo.com_id + " compdata data\n"+ \
            ppo.comments_dataframe_divide
    
def preprocess (ppo):
    """"""
    
    out_file = os.path.join(ppo.out_dir,"wind_power_data.csv")

    fd = open(out_file,'w')
    fd.write(preprocess_header(ppo))
    fd.close()

    # create data and uncomment this
    #~ data.to_csv(out_file, mode = 'a',header=False)
    
    ppo.MODEL_FILES['COMP_DATA'] = "comp_data.csv" # change this

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
class ComponentName (AnnualSavings):
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
       
        try:
            self.comp_specs = community_data.get_section(self.componenet_name)
        except AttributeError:
            self.comp_specs = community_data.get_section(COMPONENT_NAME)

        self.set_project_life_details(self.comp_specs["start year"],
                                      self.comp_specs["lifetime"],
                        self.forecast.end_year - self.comp_specs["start year"])
                        
        ### ADD other intiatzation stuff
        
    def calc_cop_per_month (self):
        """
        calculate the coefficient of performance (COP) per month
        COP = output/input
        """
        #find m & b from performance data
        
        # apply to months 
        pass
        
    def calc_heat_energy_produced_per_year (self):
        """
        """
        pass # depends on child to implement
        
    def calc_heat_energy_produced_per_month (self):
        """
        calc the mmbtu consumbed per month
        
        pre: mmbtu per year
        """
        # mmbty/mon = mmbtu/year * montly%s 
    
    def calc_electric_energy_input_per_month (self):
        """
        """
        # mmbtu/mon -> kwh/mon / COP
        
    def calc_heating_oil_consumed_per_month (self):
        """"""
        # per month if cop = 0 : consumprion mmbtu -> gal / eff
        
    def calc_heating_oil_saved_per_month (self):
        """"""
        # for each month mmbtu -> gal /eff - heating_oil_consumed
    
    def calc_electric_consumption (self):
        """
        """
        
    def calc_heating_oil_saved (self):
        
    def calc_averag_cop (self):
        
    def calc_baseline_heating_oil_cost (self):
        self.baseline_heating_oil_cost = consumption * price
    
    def calc_proposed_ashp_cost (self):
        

    
    def run (self):
        """
        run the forecast model
        
        pre:
            self.cd should be the community library from a community data object
        post:
            TODO: define output values. 
            the model is run and the output values are available
        """
        pass
 
 
    # Make this do stuff
    def calc_capital_costs (self):
        """ Function Doc"""
        self.capital_costs = np.nan
        
    
    # Make this do stuff
    def calc_annual_electric_savings (self):
        """
        """
        self.annual_electric_savings = 0
        
        
    # Make this do sruff. Remember the different fuel type prices if using
    def calc_annual_heating_savings (self):
        """
        """
        self.annual_heating_savings = self.baseline_heating_oil_cost - \
                                      self.proposed_ashp_cost

component = ComponentName

def test ():
    """
    tests the class using the manley data.
    """
    manley_data = CommunityData("../test_case/input_data/","../test_case/baseline_results/config_used.yaml")
    fc = Forecast(manley_data)
    comp = ComponentName(manley_data, fc)
    comp.run()
    return comp,fc # return the object for further testing
