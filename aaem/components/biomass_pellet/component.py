"""
component.py

    Biomass - Pellet component body
"""
import numpy as np
from pandas import DataFrame
import os

from aaem.components.annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import diagnostics
import aaem.constants as constants
from config import COMPONENT_NAME, UNKNOWN

import aaem.components.biomass_base as bmb

class BiomassPellet (bmb.BiomassBase):
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
        self.component_name = COMPONENT_NAME
        super(BiomassPellet, self).__init__(community_data, forecast, 
                                                    diag, prerequisites)
        self.biomass_type = "pellets"
        self.units = "tons"
        self.reason = "OK"
        
    def run (self, scalers = {'capital costs':1.0}):
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
        
        tag = self.cd['name'].split('+')
        if len(tag) > 1 and tag[1] != 'biomass_pellet':
            self.run = False
            self.reason = ("Not a biomass pellet project")
            return 
        
        if not self.cd["on road system"]:
            self.diagnostics.add_warning(self.component_name, 
                                    "not on road system")
            self.max_boiler_output = 0
            self.heat_displaced_sqft = 0
            self.biomass_fuel_consumed = 0
            self.fuel_price_per_unit = 0
            self.heat_diesel_displaced = 0
            self.reason = "Not on road system"
            return
        
        if self.cd["model heating fuel"]:
            self.calc_heat_displaced_sqft()
            self.calc_energy_output()
            efficiency = self.comp_specs["pellet efficiency"]
            self.calc_max_boiler_output(efficiency)
            factor = self.comp_specs['data']['Capacity Factor']
            self.calc_biomass_fuel_consumed(factor)
            self.calc_diesel_displaced()
            
        
        if self.cd["model financial"]:
            self.get_diesel_prices()
            
            self.calc_capital_costs()
            self.calc_maintainance_cost()
            
            
            self.fuel_price_per_unit = self.cd['pellet price']
            
            self.calc_proposed_biomass_cost(self.fuel_price_per_unit)
            self.calc_displaced_heating_oil_price()
            
            
            self.calc_annual_electric_savings()
            self.calc_annual_heating_savings()
            
            self.calc_annual_total_savings()
            self.calc_annual_costs(self.cd['interest rate'],
                                            scalers['capital costs'])
            self.calc_annual_net_benefit()
            self.calc_npv(self.cd['discount rate'], self.cd["current year"])
            
            fuel_cost = self.biomass_fuel_consumed * self.fuel_price_per_unit
            self.calc_levelized_costs(self.maintenance_cost +  fuel_cost)

            
    def calc_maintainance_cost(self):
        """
        calculate maitiance costs
        """
        
        self.maintenance_cost = self.capital_costs * .01

    def calc_capital_costs (self):
        """
        calculate the capital costs
        """
        self.capital_costs = self.max_boiler_output * \
                                self.comp_specs["cost per btu/hr"]
        #~ print self.capital_costs

