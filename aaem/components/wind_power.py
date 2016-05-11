"""
component_template.py

a template for adding components



"""
import numpy as np
from math import isnan
from pandas import DataFrame,concat,read_csv
import os

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



yaml = {'enabled': False,
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        'average load limit': 100.0,
        'percent generation to offset': .30,
        'data':'IMPORT',
        'minimum wind class': 3,
        'wind cost': 'UNKNOWN',
        'secondary load': True,
        'secondary load cost': 200000,
        'road needed for transmission line' : True,
        'transmission line distance': 0,
        'transmission line cost': { True:500000, False:250000},
        'assumed capacity factor': .28,
        'cost > 1000kW': 5801,
        'cost < 1000kW': 10897,
        
        }
        
yaml_defaults = {'enabled': True,
        'lifetime': 15,
        'start year': 2017,
        'average load limit': 0.0, # 0 For testing purposes REMOVE
        }
        
yaml_order = ['enabled', 'lifetime', 'start year']

yaml_comments = {'enabled': '',
        'lifetime': 'number years <int>',
        'start year': 'start year <int>',
        'average load limit': 
                'lower limint in kW on averge load reqired to do project',
        'percent generation to offset': '',
        'minimum wind class': 'minimum wind class for feasability',
        'secondary load': '',
        'secondary load cost': '',
        'road needed for transmission line':'',
        'transmission line distance': 'miles',
        'transmission line cost': 'cost/mile',
        'assumed capacity factor': "TODO read in preprocessor",
        }
       
        
def process_data_import(data_dir):
    """
    """
    data_file = os.path.join(data_dir, "wind_power_data.csv")
    
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    
    return data['value'].to_dict()
        
yaml_import_lib = {'data':process_data_import}




# change to component name (i.e. 'residential buildings')
COMPONENT_NAME = "wind power"


#   do a find and replace on WindPowerto name of component 
# (i.e. 'ResidentialBuildings')
class WindPower(AnnualSavings):
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
        self.generation = self.forecast.get_generation(self.start_year)
        
    
    def run (self):
        """
        run the forecast model
        
        pre:
            self.cd should be the community library from a community data object
        post:
            TODO: define output values. 
            the model is run and the output values are available
        """
        #~ print self.comp_specs['data']
        self.calc_average_load()
        self.calc_generation_offest_proposed()
        if self.average_load > self.comp_specs['average load limit'] and\
            self.comp_specs['data']['Assumed Wind Class'] > \
                self.comp_specs['minimum wind class'] and \
                self.generation_offest_proposed > 0:
        # if the average load is greater that the lower limit run this component
        # else skip    
            
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
        else:
            self.diagnostics.add_note(self.component_name, 
            "communites average load is not large enough to consider project")
 
 
    def calc_average_load (self):
        """ Function doc """
        
        self.average_load = self.generation / constants.hours_per_year
        
    def calc_generation_offest_proposed (self):
        """
        """
        self.generation_offest_proposed = 0
        offset = self.generation*self.comp_specs['percent generation to offset']
        
        if self.comp_specs['data']['Wind Potential'] in ['H','M'] and \
           int(self.comp_specs['data']['existing wind']) < \
                (round(offset/25) * 25):
            self.generation_offest_proposed = round(offset/25) * 25 - \
                    int(self.comp_specs['data']['existing wind'])
        
        self.total_wind_generation = self.generation_offest_proposed + \
                            int(self.comp_specs['data']['existing wind'])
        
        
        self.proposed_generation_wind =  self.generation_offest_proposed * \
                                    self.comp_specs['assumed capacity factor']*\
                                    constants.hours_per_year
        print self.generation_offest_proposed
        print self.total_wind_generation 
        
    def calc_transmission_losses (self):
        """ Function doc """
        self.transmission_losses = self.proposed_generation_wind * \
                                                        self.cd['line losses']
        
    def calc_exess_energy (self):
        """"""
        self.exess_energy = \
            (self.proposed_generation_wind - self.transmission_losses) * 15
            
    def calc_net_generation_wind (self):
        """ Function doc """
        self.net_generation_wind = self.proposed_generation_wind  - \
                                    self.transmission_losses  -\
                                    self.exess_energy
            
    def calc_electric_diesel_reduction (self):
        """ Function doc """
        gen_eff = self.cd["diesel generation efficiency"]
        if gen_eff>13:
            gen_eff = 13
            
        self.electric_diesel_reduction = self.net_generation_wind / gen_eff
        
    def calc_diesel_equiv_captured (self):
        """
        """
        if self.proposed_generation_wind == 0:
            exess_percent = 0
        else:
            exess_percent = self.exess_energy / self.proposed_generation_wind
        exess_captured_percent = exess_percent * .7
        if self.comp_specs['secondary load']:
            net_exess_energy = exess_captured_percent * \
                                self.proposed_generation_wind 
        else:
            net_exess_energy = 0
        #todo fix conversion
        self.diesel_equiv_captured = net_exess_energy * 0.99/0.138/0.8/293  
        
    def calc_loss_heat_recovery (self):
        """ """
        hr_used = True # TODO add to yaml
        self.loss_heat_recovery = 0
        if hr_used:
            self.loss_heat_recovery = self.electric_diesel_reduction * .15 # TODO
        
    def calc_reduction_diesel_used (self):
        """ """
        self.reduction_diesel_used = self.diesel_equiv_captured - \
                                     self.loss_heat_recovery
                                     
    def calc_maintainance_cost (self):
        """ """
        self.maintainance_cost = .01 * self.capital_costs
        
        
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
        powerhouse_control_cost = 0
        if not self.cd['switchgear suatable for RE']:
            powerhouse_control_cost = self.cd['switchgear cost']
        
        road_needed = self.comp_specs['road needed for transmission line']
        transmission_line_cost = self.comp_specs['transmission line distance']*\
            self.comp_specs['transmission line cost'][road_needed]
        
        secondary_load_cost = 0
        if self.comp_specs['secondary load']:
            secondary_load_cost = self.comp_specs['secondary load cost']
            
        if str(self.comp_specs['wind cost']) != 'UNKNOWN':
            wind_cost = str(self.comp_specs['wind cost'])
        else:
            if self.generation_offest_proposed >= 1000:
                cost = self.comp_specs['cost > 1000kW']
            else:
                cost = self.comp_specs['cost < 1000kW']
            wind_cost = self.generation_offest_proposed * cost
        
        self.capital_costs = powerhouse_control_cost + transmission_line_cost +\
                             secondary_load_cost
        
    
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



        
    
component = WindPower

def test ():
    """
    tests the class using the manley data.
    """
    manley_data = CommunityData("../test_case/input_data/","../test_case/baseline_results/config_used.yaml")
    fc = Forecast(manley_data)
    comp = ComponentName(manley_data, fc)
    comp.run()
    return comp,fc # return the object for further testing
