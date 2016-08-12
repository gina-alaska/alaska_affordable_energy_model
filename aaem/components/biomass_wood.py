"""
component_template.py

a template for adding components



"""
import numpy as np
from math import isnan
from pandas import DataFrame,concat
import os
from copy import deepcopy

from annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import diagnostics
import aaem.constants as constants


import biomass_base as bmb


# change to component name (i.e. 'residential buildings')
COMPONENT_NAME = "biomass cordwood"

## List of yaml key/value pairs
yaml = deepcopy(bmb.yaml)
yaml["hours of storage for peak"] = 4
yaml["percent at max output"] = .5
yaml["cordwood system efficiency"] = .88
yaml["hours operation per cord"] = 5.0
yaml["operation cost per hour"] = 20.00
yaml["energy density"] = 16000000
yaml["boiler assumed output"] = 325000
yaml["cost per btu/hr"] = .6

## default values for yaml key/Value pairs
yaml_defaults = deepcopy(bmb.yaml_defaults)
    
## order to save yaml
yaml_order = deepcopy(bmb.yaml_order) + ["hours of storage for peak",
                               "percent at max output", 
                               "cordwood system efficiency",
                               "hours operation per cord",
                               "operation cost per hour",
                               "boiler assumed output",
                               "cost per btu/hr"]

## comments for the yaml key/value pairs
yaml_comments = deepcopy(bmb.yaml_comments)
yaml_comments["hours of storage for peak"] = "<float>"
yaml_comments["percent at max output"] = "<float>"
yaml_comments["cordwood system efficiency"] = "<float>"
yaml_comments["hours operation per cord"] = "<float>"
yaml_comments["operation cost per hour"] = "<float>"
yaml_comments["energy density"] = "<float>"
yaml_comments["boiler assumed output"] = "<float>"
yaml_comments["cost per btu/hr"] = "<float>"
       
    
## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = deepcopy(bmb.yaml_import_lib)
    
raw_data_files = deepcopy(bmb.raw_data_files)

## list of wind preprocessing functions
preprocess_funcs = [deepcopy(bmb.preprocess)]

## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = []
    
## component summary
def component_summary (coms, res_dir):
    """
    save thes the summary for biomass cordwood
    """
    out = []
    for c in sorted(coms.keys()):
        #~ it = coms[c]['model'].cd.intertie
        #~ if it is None:
            #~ it = 'parent'
        #~ if it == 'child':
            #~ continue
        if c.find("_intertie") != -1:
            continue
        try:
            
           
            biomass = coms[c]['model'].comps_used[COMPONENT_NAME]
            
            try:
                break_even = biomass.break_even_cost
            except AttributeError:
                break_even = 0
               
            
            try:
                levelized_cost = biomass.levelized_cost_of_energy
            except AttributeError:
                levelized_cost = 0
            
            l = [c, 
                 biomass.max_boiler_output,
                 biomass.heat_displaced_sqft,
                 biomass.biomass_fuel_consumed,
                 biomass.fuel_price_per_unit,
                 biomass.comp_specs['energy density'],
                 biomass.heat_diesel_displaced,
                 break_even,
                 levelized_cost,
                 biomass.get_NPV_benefits(),
                 biomass.get_NPV_costs(),
                 biomass.get_NPV_net_benefit(),
                 biomass.get_BC_ratio(),
                 biomass.reason
                ]
            out.append(l)
            
        except (KeyError,AttributeError) as e:
            #~ print e
            pass
    try:
        cols = ['Community',
            'Maximum Biomass Boiler Output [Btu/hr]',
            'Biomass Heat Displacement square footage [Sqft]',
            'Proposed ' + biomass.biomass_type + \
                            " Consumed [" + biomass.units +"]",
            'Price [$/' + biomass.units + ']',
            "Energy Density [Btu/" + biomass.units + "]",
            'Displaced Heating Oil by Biomass [Gal]',
            'Break Even Diesel Price [$/gal]',
            'Levelized Cost Of Energy [$/MMBtu]',
            'Bioimass Cordwood NPV benefits [$]',
            'Biomass Cordwood NPV Costs [$]',
            'Biomass Cordwood NPV Net benefit [$]',
            'Biomass Cordwood Benefit Cost Ratio',
            'notes'
                ]
    except UnboundLocalError:
        return
    
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.replace(" ","_") + '_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write(("# " + COMPONENT_NAME + " summary\n"))
    #~ fd.close()
    data.to_csv(f_name, mode='w')
    
## list of prerequisites for module
prereq_comps = deepcopy(bmb.prereq_comps)

class BiomassCordwood (bmb.BiomassBase):
    """
    cordwood biomass componenet
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
        self.component_name = COMPONENT_NAME
        super(BiomassCordwood, self).__init__(community_data, forecast, 
                                                    diag, prerequisites)
        self.biomass_type = "cordwood"
        self.units = "cords"
        self.reason = "OK"
                        
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
        s_key = 'Sufficient Biomass for 30% of Non-residential buildings'
        
        tag = self.cd['name'].split('+')
        if len(tag) > 1 and tag[1] != 'biomass_wood':
            self.run = False
            self.reason = "Not a biomass wood project"
            return 
        
        if not self.comp_specs['data'][s_key]:
            self.diagnostics.add_warning(self.component_name, 
                                    "not " + s_key)
            self.max_boiler_output = 0
            self.heat_displaced_sqft = 0
            self.biomass_fuel_consumed = 0
            self.fuel_price_per_unit = 0
            self.heat_diesel_displaced = 0
            self.reason = "not " + s_key
            return
        
        if self.cd["model heating fuel"]:
            self.calc_heat_displaced_sqft()
            self.calc_energy_output()
            efficiency = self.comp_specs["percent at max output"]*\
                         self.comp_specs["cordwood system efficiency"]
            self.calc_max_boiler_output(efficiency)
            factor = self.comp_specs["percent at max output"] * \
                     self.comp_specs['data']['Capacity Factor']
            self.calc_biomass_fuel_consumed(factor)
            self.calc_diesel_displaced()
            
        
        if self.cd["model financial"]:
            self.get_diesel_prices()
            
            self.calc_number_boilers()
            self.calc_capital_costs()
            self.calc_maintainance_cost()
            
            self.fuel_price_per_unit = self.cd['cordwood price']
            self.calc_proposed_biomass_cost(self.fuel_price_per_unit)
            self.calc_displaced_heating_oil_price()
            
            
            self.calc_annual_electric_savings()
            self.calc_annual_heating_savings()
            
            self.calc_annual_total_savings()
            self.calc_annual_costs(self.cd['interest rate'])
            self.calc_annual_net_benefit()
            self.calc_npv(self.cd['discount rate'], self.cd["current year"])
            
            self.calc_levelized_costs(self.maintenance_cost)
            
    def calc_number_boilers (self):
        """
        caclulate the number of boilers
        """
        self.number_boilers = \
            round(self.max_boiler_output / \
            self.comp_specs["boiler assumed output"] )
            
    def calc_maintainance_cost(self):
        """
        calculate the opperation and maintaince const 
        """
        operation = self.biomass_fuel_consumed * \
                    self.comp_specs["hours operation per cord"] *\
                    self.comp_specs["operation cost per hour"]
        maintenance  = 10 * self.comp_specs["operation cost per hour"] * \
                       self.number_boilers
        
        fuel_cost = self.biomass_fuel_consumed * biomass.fuel_price_per_unit
        
        self.maintenance_cost = operation + maintenance + fuel_cost

    def calc_capital_costs (self):
        """
        calculate the captial costs
        """
        self.capital_costs = self.number_boilers * \
                             self.comp_specs["boiler assumed output"] *\
                             self.comp_specs["cost per btu/hr"] 
        #~ print self.capital_costs

component = BiomassCordwood

