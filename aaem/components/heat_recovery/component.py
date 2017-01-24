"""
component.py

    Heat Recovery component body
"""
import numpy as np
from pandas import DataFrame
import os

from aaem.components.annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import diagnostics
import aaem.constants as constants
from config import COMPONENT_NAME, PROJECT_TYPE, UNKNOWN

class HeatRecovery (AnnualSavings):
    """ Heat Recovery of the Alaska Affordable Eenergy Model

    :param commnity_data: CommintyData Object for a community
    :type commnity_data: CommunityData
    :param forecast: forcast for a community 
    :type forecast: Forecast
    :param forecast: forcast for a community 
    :type forecast: Forecast
    :param forecast: forcast for a community 
    :type forecast: Forecast

    .. note::

       An example of intersphinx is this: you **cannot** use :mod:`pickle` on this class.
    """
    def __init__ (self, community_data, forecast, 
                        diag = None, prerequisites = {}):
        """Class initialiser
        
        :param commnity_data: the first value
        :param arg2: the first value
        :param arg3: the first value
        :type arg1: int, float,...
        :type arg2: int, float,...
        :type arg3: int, float,...
        :returns: arg1/arg2 +arg3
        :rtype: int, float

        """
        self.diagnostics = diag
        if self.diagnostics == None:
            self.diagnostics = diagnostics()
        self.forecast = forecast
        self.cd = community_data.get_section('community')
        
        self.comp_specs = community_data.get_section(COMPONENT_NAME)
        self.component_name = COMPONENT_NAME
        
        self.comp_specs["start year"] = self.cd['current year'] + \
            self.comp_specs["project details"]['expected years to operation']


        self.set_project_life_details(self.comp_specs["start year"],
                                      self.comp_specs["lifetime"],
                        self.forecast.end_year - self.comp_specs["start year"])
        
        ### ADD other intiatzation stuff  
        ### load prerequisites in the following function
        ### if there are no prerequisites you can delete this and the 
        ### load_prerequisite_variables function
        self.load_prerequisite_variables(prerequisites)
        
    def load_prerequisite_variables (self, comps):
        """returns (arg1 / arg2) + arg3

        This is a longer explanation, which may include math with latex syntax
        :math:`\\alpha`.
        Then, you need to provide optional subsection in this order (just to be
        consistent and have a uniform documentation. Nothing prevent you to
        switch the order):

          - parameters using ``:param <name>: <description>``
          - type of the parameters ``:type <name>: <description>``
          - returns using ``:returns: <description>``
          - examples (doctest)
          - seealso using ``.. seealso:: text``
          - notes using ``.. note:: text``
          - warning using ``.. warning:: text``
          - todo ``.. todo:: text``

        **Advantages**:
         - Uses sphinx markups, which will certainly be improved in future
           version
         - Nice HTML output with the See Also, Note, Warnings directives


        **Drawbacks**:
         - Just looking at the docstring, the parameter, type and  return
           sections do not appear nicely

        :param arg1: the first value
        :param arg2: the first value
        :param arg3: the first value
        :type arg1: int, float,...
        :type arg2: int, float,...
        :type arg3: int, float,...
        :returns: arg1/arg2 +arg3
        :rtype: int, float

        :Example:

        >>> import template
        >>> a = template.MainClass1()
        >>> a.function1(1,1,1)
        2

        .. note:: can be useful to emphasize
            important feature
        .. seealso:: :class:`MainClass2`
        .. warning:: arg2 must be non-zero.
        .. todo:: check that arg2 is non zero.
        """
        # LOAD anything needed from the components passed as input
        # WRITE this
        pass
        
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
        if self.cd['name'].find('+') == -1:
            self.run = False
            self.reason = PROJECT_TYPE + \
                " component requires a known project to run"
            self.diagnostics.add_note(self.component_name, self.reason)
            return 
        
        tag = self.cd['name'].split('+')
        if len(tag) > 1 and tag[1] != PROJECT_TYPE:
            self.run = False
            self.reason = "Not a " + PROJECT_TYPE + " project"
            self.diagnostics.add_note(self.component_name, self.reason)
            return 
        
        if self.cd["model heating fuel"]:
            try:
                self.calc_proposed_heat_recovery()
            except AttributeError:
                self.run = False
                self.reason = "Could not caclulate proposed heat recovery"
                self.diagnostics.add_note(self.component_name, self.reason)
                return 
                
        if np.isnan(self.proposed_heat_recovery) or \
                self.proposed_heat_recovery == 0:
            self.run = False
            self.reason = "No proposed heat recovery"
            self.diagnostics.add_note(self.component_name, self.reason)
            return 
        
        if self.cd["model financial"]:
            # AnnualSavings functions (don't need to write)
            self.get_diesel_prices()
            
            # change these below
            self.calc_capital_costs()
            self.calc_annual_electric_savings()
            self.calc_annual_heating_savings()
            
            # AnnualSavings functions (don't need to write)
            self.calc_annual_total_savings()
            self.calc_annual_costs(self.cd['interest rate'],
                                            scalers['capital costs'])
            self.calc_annual_net_benefit()
            self.calc_npv(self.cd['discount rate'], self.cd["current year"])
            
            self.calc_levelized_costs(self.comp_specs['o&m per year'])
            
    
    def get_fuel_total_saved (self):
        """
        returns the total fuel saved in gallons
        """
        return self.proposed_heat_recovery
    
    def get_total_enery_produced (self):
        """
        returns the total energy produced
        """
        return self.proposed_heat_recovery/ constants.mmbtu_to_gal_HF
 
    def calc_proposed_heat_recovery (self):
        """
        calculate the proposed heat recovery 
        
        if Project details exist:
            proposed_heat_recovery = projects 'proposed gallons diesel offset'
            
        hr_available = %hr * diesel_for_generation
        potential_hr = 'Est. potential annual heating fuel gallons displaced'
        if hr_opp and waste_heat_available:
            if potential_hr  unknown:
                proposed_heat_recovery = (hr_available * .3) / 
                                          'heating conversion efficiency'
            else:
                proposed_heat_recovery = potential_hr/
                                         'heating conversion efficiency'
        else:
            proposed_heat_recovery = 0
        
        """
        p_gallons = self.comp_specs["project details"]\
                            ['proposed gallons diesel offset']
        p_btu = self.comp_specs["project details"]\
                            ['proposed Maximum btu/hr']
                            
        # is there a project
        if p_gallons != UNKNOWN and p_btu != UNKNOWN:
            self.proposed_heat_recovery = p_gallons
            return
        # else:
        hr_opp = self.comp_specs['estimate data']\
                    ['Waste Heat Recovery Opperational']
        waste_heat_available = self.comp_specs['estimate data']\
                    ['Add waste heat Avail']
                    
        potential_hr = self.comp_specs['estimate data']\
                    ['Est. potential annual heating fuel gallons displaced']
        
        try:
            np.isnan(potential_hr)
        except TypeError:
            potential_hr = np.nan            
        
        generation = self.forecast.generation_by_type['generation diesel']\
                                                            [self.start_year]
        gen_eff = self.cd["diesel generation efficiency"]
        
        # gallons 
        diesel_consumed = generation / gen_eff
        hr_available = self.comp_specs['percent heat recovered'] * \
                          diesel_consumed

        if hr_opp == 'Yes' and waste_heat_available == 'Yes' and \
           np.isnan(potential_hr):
            potential_hr = ((hr_available) * .30)
        if hr_opp == 'Yes' and waste_heat_available == 'Yes':
            pass #potential_hr 
        elif hr_opp == 'Yes' and waste_heat_available == 'No':
            potential_hr = 0
        else:
            potential_hr = 0
            
        self.proposed_heat_recovery = potential_hr / \
                                self.comp_specs['heating conversion efficiency']
    
    # Make this do stuff
    def calc_capital_costs (self):
        """ Function Doc"""
        capital_costs = self.comp_specs["project details"]['capital costs']
        if capital_costs == UNKNOWN:

            install_cost = 50000 * \
                            self.comp_specs['estimate pipe distance']/1000.0

            loop_cost = self.comp_specs['estimate pipe cost/ft'] * \
                        self.comp_specs['estimate pipe distance']
                        
            overhead_cost = self.comp_specs['estimate pipe distance']/1000.0 * \
                            140000
            building_cost = self.comp_specs['estimate buildings to heat'] * \
                                self.comp_specs['estimate cost/building']
            capital_costs = install_cost + loop_cost +\
                            overhead_cost + building_cost
        self.capital_costs = capital_costs
        
    
    def calc_annual_electric_savings (self):
        """
        """
        self.annual_electric_savings = 0
        
    # Make this do sruff. Remember the different fuel type prices if using
    def calc_annual_heating_savings (self):
        """
        """
        price = (self.diesel_prices + self.cd['heating fuel premium'])
        
        self.annual_heating_savings = self.proposed_heat_recovery * price + \
                                      self.comp_specs['o&m per year']
