"""
component_template.py

a template for adding components



"""
import os

import numpy as np
from math import isnan
from pandas import DataFrame,concat,read_csv

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
        'average load limit': 50.0,
        'data': 'IMPORT',
        'cost': 'UNKNOWN',
        'cost per kW': 8000,
        'road needed': False,
        'road needed for transmission line' : True,
        'transmission line distance': 0,
        'percent o&m': .01,
        'percent generation to offset': .30,
        'percent solar degradation': .992,
        'o&m cost per kWh': .02,
        }

## default values for yaml key/Value pairs
yaml_defaults = {'enabled': True,
        'lifetime': 20,
        'start year': 2017,
        }
    
## order to save yaml
yaml_order = ['enabled', 'lifetime', 'start year']

## comments for the yaml key/value pairs
yaml_comments = {'enabled': '<boolean>',
        'lifetime': 'number years <int>',
        'start year': 'start year <int>',
        'average load limit': 'lower limit on the average load <float>',
        'data': 'data for component',
        'cost': 
            'cost in $ for project if known otherwise UNKNOWN <float|string>',
        'cost per kW': 
            'dollar cost per kW if cost of the project is UNKNOWN <float>',
        'road needed for transmission line' : '<boolean>',
        'transmission line distance': 
            'distance in miles of proposed transmission line <float>',
        'percent o&m': 
            ('yearly maintenance cost'
             ' as percent as decimal of total cost <float>'),
        'percent generation to offset': 
            'pecent of the generation in kW to offset with solar power <float>',
        'percent solar degradation': 
            ('the precent of the of solar panel'
             ' that carries over from the previous year'),
        'o&m cost per kWh': 'cost of repairs for generator per kWh <float>',
         }
       
## Functions for CommunityData IMPORT keys
def process_data_import(data_dir):
    """
    """
    data_file = os.path.join(data_dir, "solar_power_data.csv")
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    data = data['value'].to_dict()
    data["HR Opperational"] = data["HR Opperational"] == 'True'
    data['Output per 10kW Solar PV'] = float(data['Output per 10kW Solar PV'])
    return data

## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = {'data':process_data_import,}
    
## preprocessing functons 
def preprocess_header (ppo):
    """
    """
    return  "# " + ppo.com_id + " solar power data\n"+ \
            ppo.comments_dataframe_divide
    

def preprocess (ppo):
    """"""
    data = read_csv(os.path.join(ppo.data_dir,"solar_data.csv"),
                        comment = '#',index_col = 0).ix[ppo.com_id]
    
    val =  data['Output per 10kW Solar PV']
    #~ return
    out_file = os.path.join(ppo.out_dir,"solar_power_data.csv")

    fd = open(out_file,'w')
    fd.write(preprocess_header(ppo))
    fd.write("key,value\n")
    fd.write('Output per 10kW Solar PV,' + str(val) + '\n')
    fd.write("HR Opperational,True\n")
    fd.close()

    # create data and uncomment this
    #~ data.to_csv(out_file, mode = 'a',header=False)
    
    ppo.MODEL_FILES['SOLAR_DATA'] = "solar_power_data.csv" # change this

## List of raw data files required for wind power preproecssing 
raw_data_files = ['solar_data.csv']# fillin

## list of wind preprocessing functions
preprocess_funcs = [preprocess]

## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = []
    
## component summary
def component_summary (coms, res_dir):
    """
    """
    out = []
    for c in sorted(coms.keys()):
        it = coms[c]['model'].cd.intertie
        if it is None:
            it = 'parent'
        if it == 'child':
            continue
        try:
            solar = coms[c]['model'].comps_used['solar power']
            
            assumed_out = solar.comp_specs['data']['Output per 10kW Solar PV']
            
            average_load = solar.average_load
            
            proposed_capacity = solar.proposed_load + 0
            
            existing_capacity = 0
            
            capa_fac = 0
            
            net_gen = solar.generation_proposed [0]
            
            secondary_load = 0
            
            loss_heat = self.fuel_used
            
            print c, assumed_out, average_load, proposed_capacity, existing_capacity,capa_fac,net_gen,secondary_load,loss_heat
        except (KeyError,AttributeError) as e:
            print e
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
        self.run = True
        
        try:
            self.calc_average_load()
            self.calc_proposed_generation()
        except:
            self.diagnostics.add_warning(self.component_name, 
            "could not be run")
            self.run = False
            return
        
        if self.cd["model financial"]:
            # AnnualSavings functions (don't need to write)
            self.get_diesel_prices()
            
            # change these below
            self.calc_capital_costs()
            self.calc_maintenance_cost()
            self.calc_annual_electric_savings()
            self.calc_annual_heating_savings()
            
            # AnnualSavings functions (don't need to write)
            self.calc_annual_total_savings()
            self.calc_annual_costs(self.cd['interest rate'])
            self.calc_annual_net_benefit()
            self.calc_npv(self.cd['discount rate'], self.cd["current year"])
            
    def calc_average_load (self):
        """ """
        self.generation = self.forecast.get_generation(self.start_year)
        self.average_load = self.generation / constants.hours_per_year
        #~ print self.average_load
        
    def calc_proposed_generation (self):
        """ Function doc """
        self.proposed_load = self.average_load * \
                        self.comp_specs['percent generation to offset']
        self.generation_proposed = self.proposed_load *\
                        self.comp_specs['data']['Output per 10kW Solar PV'] /\
                        10
                        
        self.generation_proposed = self.generation_proposed *\
                            self.comp_specs['percent solar degradation']**\
                            np.arange(self.project_life)
        #~ print 'self.calc_proposed_generation'
        #~ print self.proposed_load
        #~ print self.generation_proposed
        
    def calc_maintenance_cost (self):
        """ """
        self.maintenance_cost = self.capital_costs * \
                    self.comp_specs['percent o&m']
        #~ print "self.calc_maintenance_cost"
        #~ print self.maintenance_cost
    
    # Make this do stuff
    def calc_capital_costs (self):
        """ Function Doc"""
        component_cost = self.comp_specs['cost']
        if str(component_cost) == 'UNKNOWN':
            component_cost = self.proposed_load * self.comp_specs['cost per kW']
            
        powerhouse_cost = 0
        if not self.cd['switchgear suatable for RE']:
            powerhouse_cost = self.cd['switchgear cost']
            
        self.capital_costs = powerhouse_cost + component_cost
        #~ print 'self.calc_capital_costs'
        #~ print self.capital_costs
    
    # Make this do stuff
    def calc_annual_electric_savings (self):
        """
        """
        self.proposed_generation_cost = self.maintenance_cost
        
        
        price = self.diesel_prices# + self.cd['heating fuel premium'])
        gen_eff = self.cd["diesel generation efficiency"]
        # ???
        if gen_eff>13 or gen_eff==0 or np.isnan(gen_eff):
            gen_eff = 13
        self.fuel_used = self.generation_proposed/gen_eff
        
        # fuel cost + maintance cost
        self.baseline_generation_cost = (self.fuel_used * price) +\
                (self.generation_proposed * self.comp_specs['o&m cost per kWh'])
        
        self.annual_electric_savings = self.baseline_generation_cost - \
                                       self.proposed_generation_cost
                                       
        #~ print self.baseline_generation_cost
        #~ print self.proposed_generation_cost
        #~ print self.annual_electric_savings
        
        
    # Make this do sruff. Remember the different fuel type prices if using
    def calc_annual_heating_savings (self):
        """
        """
        gen_eff = self.cd["diesel generation efficiency"]
        if gen_eff>13 or gen_eff==0 or np.isnan(gen_eff):
            gen_eff = 13
        self.fuel_used = self.generation_proposed/gen_eff * .15
    
        price = (self.diesel_prices + self.cd['heating fuel premium'])
        self.annual_heating_savings = self.fuel_used * price
        #~ print self.fuel_used
        #~ print self.annual_heating_savings

        
    
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
