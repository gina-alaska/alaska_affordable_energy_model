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
        'percent generation to offset': .15,
        'switch gear needed for solar': False,
        'percent solar degradation': .992,
        'o&m cost per kWh': .02,
        }

## default values for yaml key/Value pairs
yaml_defaults = {'enabled': True,
        'lifetime': 20,
        'start year': 2020,
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
    try:
        existing = read_csv(os.path.join(ppo.data_dir,"solar_data_existing.csv"),
                        comment = '#',index_col = 0).ix[ppo.com_id]
        existing = existing['Installed Capacity (kW)']
        if np.isnan(existing):
            existing = 0
    except KeyError:
        existing = 0 
    
    try:
        wind_cap = read_csv(os.path.join(ppo.data_dir,
                                "wind_data_existing.csv"),
                            comment = '#',index_col = 0).ix[ppo.com_id]
        wind_cap = wind_cap['Rated Power (kW)']
        if np.isnan(wind_cap):
            wind_cap = 0
    except (IOError,KeyError):
        wind_cap = 0 
    
    val =  data['Output per 10kW Solar PV']
    #~ return
    out_file = os.path.join(ppo.out_dir,"solar_power_data.csv")

    fd = open(out_file,'w')
    fd.write(preprocess_header(ppo))
    fd.write("key,value\n")
    fd.write("Installed Capacity," + str(existing) + '\n')
    fd.write("Wind Capacity," + str(wind_cap) + '\n')
    fd.write('Output per 10kW Solar PV,' + str(val) + '\n')
    #~ fd.write("HR Opperational,True\n")
    fd.close()

    # create data and uncomment this
    #~ data.to_csv(out_file, mode = 'a',header=False)
    
    ppo.MODEL_FILES['SOLAR_DATA'] = "solar_power_data.csv"

## List of raw data files required for wind power preproecssing 
raw_data_files = ['solar_data.csv', 'solar_data_existing.csv',
                    "wind_data_existing.csv"]

## list of wind preprocessing functions
preprocess_funcs = [preprocess]

## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = ["data"]
    
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
            
            existing_capacity = solar.comp_specs['data']['Installed Capacity']
        
            wind_capacity = solar.comp_specs['data']['Wind Capacity']
            try:
                net_gen = solar.generation_proposed [0]
                
                
                loss_heat = solar.fuel_displaced[0]
                
                hr_op = solar.cd['heat recovery operational']
                
                net_heating =   -1* loss_heat
                
                eff = solar.cd["diesel generation efficiency"]
                red_per_year = solar.generation_fuel_used[0]
            except AttributeError:
                net_gen = 0
            
                loss_heat = 0
                hr_op = solar.cd['heat recovery operational']
                
                net_heating = 0
                
                eff = solar.cd["diesel generation efficiency"]
                red_per_year = 0
            
            l = [c, 
                 assumed_out,
                 average_load,
                 
                 proposed_capacity,
                 existing_capacity,
                 wind_capacity,
                 net_gen,
                 
                 loss_heat,
                 
                 hr_op,
                 net_heating,
                 red_per_year,
                 eff,
                 solar.get_NPV_benefits(),
                 solar.get_NPV_costs(),
                 solar.get_NPV_net_benefit(),
                 solar.get_BC_ratio(),
                 solar.reason
            ]
            out.append(l)
            
        except (KeyError,AttributeError) as e:
            #~ print e
            pass
    
    
    
    cols = ['Community',
            'Assumed  Output per 10kW Solar PV Array',
            'Average Diesel Load [kw]',
            'Solar Capacity Proposed [kW]',
            'Existing Solar Capacity [kW]',
            'Existing Wind Capacity [kW]',
            'Net Proposed Solar Generation [kWh]',
            'Loss of Recovered Heat from Proposed Solar [gal]',
            'Heat Recovery Operational',
            'Net in Heating Oil Consumption from Proposed Solar [gal]',
            'Proposed Solar Reduction in Utility Diesel Consumed per year',
            'Diesel Generator Efficiency',
            'Solar NPV benefits [$]',
            'Solar NPV Costs [$]',
            'Solar NPV Net benefit [$]',
            'Solar Benefit Cost Ratio',
            'notes']
    
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                'solar_power_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write(("# solar summary\n"))
    #~ fd.close()
    data.to_csv(f_name, mode='a')
    
## list of prerequisites for module
prereq_comps = []

class SolarPower (AnnualSavings):
    """
    """
    def __init__ (self, community_data, forecast, 
                        diag = None, prerequisites = {}):
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
        self.reason = "OK"
        try:
            self.calc_average_load()
            self.calc_proposed_generation()
        except:
            self.diagnostics.add_warning(self.component_name, 
            "could not be run")
            self.run = False
            self.reason = "could not find average load or proposed generation"
            return
            
        
        if self.average_load < self.comp_specs['average load limit'] or \
           not self.proposed_load > 0:
            self.diagnostics.add_note(self.component_name, 
            "model did not meet minimum generation requirments")
            self.run = False
            self.reason = "average load too small or proposed load <= 0"
            return
        
        
        self.calc_generation_fuel_used()
        self.calc_fuel_displaced()
        
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
            
            
            #~ print self.get_NPV_benefits()
            #~ print self.get_NPV_costs()
            #~ print self.get_NPV_net_benefit()
            #~ print self.get_BC_ratio()
            
            
    def calc_average_load (self):
        """ """
        #~ self.generation = self.forecast.get_generation(self.start_year)
        self.generation = self.forecast.generation_by_type['generation diesel']\
                                                            [self.start_year]
        self.average_load = self.generation / constants.hours_per_year
        #~ print self.average_load
        
    def calc_proposed_generation (self):
        """ Function doc """
        self.proposed_load = self.average_load * \
                        self.comp_specs['percent generation to offset']
                        
        existing_RE = self.comp_specs['data']['Installed Capacity'] + \
                      self.comp_specs['data']['Wind Capacity']
        
        self.proposed_load = max(self.proposed_load - existing_RE, 0)
        
        #~ self.total_load = self.proposed_load + \
                        #~ self.comp_specs['data']['Installed Capacity']               
        
        self.generation_proposed = self.proposed_load *\
                        self.comp_specs['data']['Output per 10kW Solar PV'] /\
                        10
                        
        self.generation_proposed = self.generation_proposed *\
                            self.comp_specs['percent solar degradation']**\
                            np.arange(self.project_life)
        #~ print 'self.calc_proposed_generation'
        #~ print self.proposed_load
        #~ print self.generation_proposed
        
    def calc_generation_fuel_used (self):
        gen_eff = self.cd["diesel generation efficiency"]
        self.generation_fuel_used = self.generation_proposed/gen_eff
        
    def calc_fuel_displaced (self):
        """ Function doc """
        gen_eff = self.cd["diesel generation efficiency"]
        if self.cd['heat recovery operational']:
            self.fuel_displaced = self.generation_proposed/gen_eff * .15
        else:
            self.fuel_displaced = self.generation_proposed * 0
        
    def calc_maintenance_cost (self):
        """ """
        self.maintenance_cost = self.capital_costs * \
                    self.comp_specs['percent o&m']
        #~ print "self.calc_maintenance_cost"
        #~ print self.maintenance_cost
    
    def calc_capital_costs (self):
        """ Function Doc"""
        component_cost = self.comp_specs['cost']
        if str(component_cost) == 'UNKNOWN':
            component_cost = self.proposed_load * self.comp_specs['cost per kW']
            
        powerhouse_cost = 0
        if not self.cd['switchgear suatable for RE'] and \
            self.comp_specs['switch gear needed for solar']:
            powerhouse_cost = self.cd['switchgear cost']
            
        self.capital_costs = powerhouse_cost + component_cost
        #~ print 'self.calc_capital_costs'
        #~ print self.capital_costs
    

    def calc_annual_electric_savings (self):
        """
        """
        self.proposed_generation_cost = self.maintenance_cost
        
        
        price = self.diesel_prices
        # fuel cost + maintance cost
        self.baseline_generation_cost = (self.generation_fuel_used * price) +\
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
        price = (self.diesel_prices + self.cd['heating fuel premium'])
        self.annual_heating_savings = self.fuel_displaced * price
        #~ print self.fuel_displaced
        #~ print self.annual_heating_savings
        
    def save_component_csv (self, directory):
        """
        save the output from the component.
        """
        if not self.run:
            fname = os.path.join(directory,
                                   self.component_name + "_output.csv")
            fname = fname.replace(" ","_")
        
            fd = open(fname, 'w')
            fd.write("Wind Power minimum requirments not met\n")
            fd.close()
            return
        
        
        years = np.array(range(self.project_life)) + self.start_year
    
        # ??? +/- 
        # ???
        df = DataFrame({
                'Solar Capacity [kW]': self.proposed_load,
                "Solar Generation [kWh/yr]": 
                                            self.generation_proposed,
                'Utility Diesel Displaced [gal]':self.generation_fuel_used,
                'Heating Fuel Displaced[Gal]':self.fuel_displaced,
                "Heat Recovery Cost Savings": 
                                        self.get_heating_savings_costs(),
                "Electricity Cost Savings": 
                                    self.get_electric_savings_costs(),
                "Project Capital Cost": self.get_capital_costs(),
                "Total Cost Savings": self.get_total_savings_costs(),
                "Net Benefit": self.get_net_beneft(),
                       }, years)

        df["community"] = self.cd['name']
        
        ol = ["community",'Solar Capacity [kW]',
                "Solar Generation [kWh/yr]",
                'Utility Diesel Displaced [gal]',
                'Heating Fuel Displaced[Gal]',
                "Heat Recovery Cost Savings",
                "Electricity Cost Savings",
                "Project Capital Cost",
                "Total Cost Savings",
                "Net Benefit"]
        fname = os.path.join(directory,
                                   self.component_name + "_output.csv")
        fname = fname.replace(" ","_")
        
        
        fin_str = "Enabled" if self.cd["model financial"] else "Disabled"
        fd = open(fname, 'w')
        fd.write("# " + self.component_name + " model outputs\n")
        
        fd.close()
        
        # save npv stuff
        df2 = DataFrame([self.get_NPV_benefits(),self.get_NPV_costs(),
                            self.get_NPV_net_benefit(),self.get_BC_ratio()],
                       ['NPV Benefits','NPV Cost',
                            'NPV Net Benefit','Benefit Cost Ratio'])
        df2.to_csv(fname, header = False, mode = 'a')
        
        # save to end of project(actual lifetime)
        df[ol].ix[:self.actual_end_year].to_csv(fname, index_label="year", 
                                                                    mode = 'a')

        
    
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
