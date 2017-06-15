"""
Biomass Cordwood component body
-------------------------------

"""
import numpy as np
from pandas import DataFrame
import os

from aaem.components.annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import Diagnostics
import aaem.constants as constants
from config import COMPONENT_NAME, UNKNOWN

import aaem.components.biomass_base as bmb

class BiomassCordwood (bmb.BiomassBase):
    """Biomass Cordwood component of the Alaska Affordable Eenergy Model

    Parameters
    ----------
    commnity_data : CommunityData
        CommintyData Object for a community
    forecast : Forecast
        forcast for a community 
    diagnostics : diagnostics, optional
        diagnostics for tracking error/warining messeges
    prerequisites : dictionary of components, optional
        'Non-residential Energy Efficiency' component is a required prerequisite
        for this component
        
    Attributes
    ----------
    diagnostics : diagnostics
        for tracking error/warining messeges
        initial value: diag or new diagnostics object
    forecast : forecast
        community forcast for estimating future values
        initial value: forecast
    cd : dictionary
        general data for a community.
        Initial value: 'community' section of community_data
    comp_specs : dictionary
        component specific data for a community.
        Initial value: 'Biomass Cordwood' section of community_data
        
    See also
    --------
    aaem.community_data : 
        community data module, see for information on CommintyData Object
    aaem.forecast : 
        forecast module, see for information on Forecast Object
    aaem.diagnostics :
        diagnostics module, see for information on diagnostics Object
    aaem.components.non_residential :
        'Non-residential Energy Efficiency' component is a required prerequisite
        for this component

    """
    def __init__ (self, community_data, forecast, 
                        diag = None, prerequisites = {}):
        """Class initialiser
        
        Parameters
        ----------
        commnity_data : CommunityData
            CommintyData Object for a community
        forecast : Forecast
            forcast for a community 
        diagnostics : diagnostics, optional
            diagnostics for tracking error/warining messeges
        prerequisites : dictionary of components, optional
            prerequisite component data, 
            'Non-residential Energy Efficiency' component

        """
        self.component_name = COMPONENT_NAME
        super(BiomassCordwood, self).__init__(community_data, forecast, 
                                                    diag, prerequisites)
        self.biomass_type = "cordwood"
        self.units = "cords"
        self.reason = "OK"
                        
        ### ADD other intiatzation stuff
        
    
    def run (self, scalers = {'capital costs':1.0}):
        """Runs the component. The Annual Total Savings,Annual Costs, 
        Annual Net Benefit, NPV Benefits, NPV Costs, NPV Net Benefits, 
        Benefit Cost Ratio, Levelized Cost of Energy, 
        and Internal Rate of Return will all be calculated. 
        
        Parameters
        ----------
        scalers: dictionay of valid scalers, optional
            Scalers to adjust normal run variables. 
            See note on accepted  scalers
        
        Attributes
        ----------
        run : bool
            True in the component runs to completion, False otherwise
        reason : string
            lists reason for failure if run == False
            
        Notes
        -----
            Accepted scalers: capital costs.
        """
        tag = self.cd['file id'].split('+')
        self.was_run = True
        self.reason = "OK"
        
        if len(tag) > 1 and tag[1] != 'biomass_wood':
            self.was_run = False
            self.reason = "Not a biomass cordwood project."
            return 
        
        if not self.comp_specs['sufficient biomass']:
            self.diagnostics.add_warning(self.component_name, 
                "There is not sufficient biomass in community")
            self.max_boiler_output = 0
            self.heat_displaced_sqft = 0
            self.biomass_fuel_consumed = 0
            self.fuel_price_per_unit = 0
            self.heat_diesel_displaced = 0
            self.reason = 'Sufficient biomass not available.'
            return
        
        if self.cd["model heating fuel"]:
            self.calc_heat_displaced_sqft()
            self.calc_energy_output()
            
            percent_max = (self.comp_specs["percent at max output"] / 100.0)
            efficiency = percent_max * \
                self.comp_specs["cordwood system efficiency"]
            self.calc_max_boiler_output(efficiency)
            factor = percent_max * self.comp_specs['capacity factor']
            self.calc_biomass_fuel_consumed(factor)
            self.calc_diesel_displaced()
            
        
        if self.cd["model financial"]:
            self.get_diesel_prices()
            
            self.calc_number_boilers()
            self.calc_capital_costs()
            self.fuel_price_per_unit = self.cd['cordwood price']
            self.calc_maintainance_cost()
            
            #~ self.fuel_price_per_unit = self.cd['cordwood price']
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
            
    def calc_number_boilers (self):
        """caclulate the number of boilers
        
        Attributes
        ----------
        number_boilers : int
            Number of boilers to install
        """
        self.number_boilers = \
            round(self.max_boiler_output / \
            self.comp_specs["boiler assumed output"] )
            
    def calc_maintainance_cost(self):
        """Calculate the opperation and maintaince const 
       
        Attributes
        ----------
        maintenance_costs : float
            caclulated captial costs for heat recovery ($)
        """
        operation = self.biomass_fuel_consumed * \
                    self.comp_specs["hours operation per cord"] *\
                    self.comp_specs["operation cost per hour"]
        maintenance  = 10 * self.comp_specs["operation cost per hour"] * \
                       self.number_boilers
        
    
        self.maintenance_cost = operation + maintenance

    def calc_capital_costs (self):
        """Calculate the capital costs
        
        Attributes
        ----------
        capital_costs : float
            caclulated captial costs for heat recovery ($)
        """
        self.capital_costs = self.number_boilers * \
                             self.comp_specs["boiler assumed output"] *\
                             self.comp_specs["cost per btu/hrs"] 
        #~ print self.capital_costs
