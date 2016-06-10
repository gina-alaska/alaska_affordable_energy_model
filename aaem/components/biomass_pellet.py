"""
component_template.py

a template for adding components



"""
import numpy as np
from math import isnan
from pandas import DataFrame,concat
import os

from annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import diagnostics
import aaem.constants as constants


import biomass_base as bmb


# change to component name (i.e. 'residential buildings')
COMPONENT_NAME = "biomass pellet"

## List of yaml key/value pairs
yaml = bmb.yaml
yaml["energy density"] = 17600000
yaml["pellet efficiency"] = .8
yaml["cost per btu/hr"] = .54
yaml["default pellet price"] = 400


## default values for yaml key/Value pairs
yaml_defaults = bmb.yaml_defaults
    
## order to save yaml
yaml_order = bmb.yaml_order + ["energy density"]

## comments for the yaml key/value pairs
yaml_comments = bmb.yaml_comments
yaml_comments["energy density"] = "energy density of pellets (btu/ton) <float>"
yaml_comments["pellet efficiency"] = \
                        "effcicieny of pellets (% as decimal) <float>"
yaml_comments["cost per btu/hr"] = "cost per btu/hr ($) <float>"
yaml_comments["default pellet price"] = "pellet cost per ton ($) <float>" 
       
    
## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = bmb.yaml_import_lib
    
raw_data_files = bmb.raw_data_files

## list of wind preprocessing functions
preprocess_funcs = [bmb.preprocess]

## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = []
    
## component summary
def component_summary (coms, res_dir):
    """
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
            
            l = [c, 
                 biomass.max_boiler_output,
                 biomass.heat_displaced_sqft,
                 biomass.biomass_fuel_consumed,
                 biomass.fuel_price_per_unit,
                 biomass.comp_specs['energy density'],
                 biomass.heat_diesel_displaced,
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
    
    data = DataFrame(out,columns = \
       ['Community',
        'Maximum Boiler Output [Btu/hr]',
        'Heat Displacement square footage [Sqft]',
        'Proposed ' + biomass.biomass_type + " Consumed [" + biomass.units +"]",
        'Price [$/' + biomass.units + ']',
        "Energy Density [Btu/" + biomass.units + "]",
        "Displaced Heating Oil [Gal]",
        'NPV benefits [$]',
        'NPV Costs [$]',
        'NPV Net benefit [$]',
        'Benefit Cost Ratio',
        'notes']
                    ).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.replace(" ","_") + '_summary.csv')
    fd = open(f_name,'w')
    fd.write(("# " + COMPONENT_NAME + " summary\n"))
    fd.close()
    data.to_csv(f_name, mode='a')

#   do a find and replace on ComponentName to name of component 
# (i.e. 'ResidentialBuildings')
class BiomassPellet (bmb.BiomassBase):
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
        self.component_name = COMPONENT_NAME
        super(BiomassPellet, self).__init__(community_data, forecast, diag)
        self.biomass_type = "pellets"
        self.units = "tons"
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
        if self.cd["model heating fuel"]:
            self.calc_heat_displaced_sqft()
            self.calc_energy_output()
            efficiency = self.comp_specs["pellet efficiency"]
            self.calc_max_boiler_output(efficiency)
            factor = self.comp_specs['data']['Capacity Factor']
            self.calc_biomass_fuel_consumed(factor)
            self.calc_diesel_displaced()
            
        
        if self.cd["model financial"]:
            # AnnualSavings functions (don't need to write)
            self.get_diesel_prices()
            
            # change these below
            self.calc_capital_costs()
            self.calc_maintainance_cost()
            
            
            self.fuel_price_per_unit = self.comp_specs["default pellet price"]
            
            self.calc_proposed_biomass_cost(self.fuel_price_per_unit)
            self.calc_displaced_heating_oil_price()
            
            
            self.calc_annual_electric_savings()
            self.calc_annual_heating_savings()
            
            # AnnualSavings functions (don't need to write)
            self.calc_annual_total_savings()
            self.calc_annual_costs(self.cd['interest rate'])
            self.calc_annual_net_benefit()
            self.calc_npv(self.cd['discount rate'], self.cd["current year"])

            
    def calc_maintainance_cost(self):
        """
        """
        
        self.maintenance_cost = self.capital_costs * .01

    def calc_capital_costs (self):
        """ Function Doc"""
        self.capital_costs = self.max_boiler_output * \
                                self.comp_specs["cost per btu/hr"]
        #~ print self.capital_costs

component = BiomassPellet

def test ():
    """
    tests the class using the manley data.
    """
    manley_data = CommunityData("../test_case/input_data/","../test_case/baseline_results/config_used.yaml")
    fc = Forecast(manley_data)
    comp = ComponentName(manley_data, fc)
    comp.run()
    return comp,fc # return the object for further testing
