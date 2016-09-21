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
        """
        load variables from prerequisites
        
        pre:
             prerequisites: dictonary of componentes
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
                self.reason = "could not find proposed heat recovery"
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
        heat_recovery(gal diesel) = generation diesel (gal diesel) * .05 / .75
        
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
        b1 = self.comp_specs['estimate data']\
                    ['Waste Heat Recovery Opperational']
        b2 = self.comp_specs['estimate data']\
                    ['Add waste heat Avail']
                    
              
        
        #~ current_hr = self.comp_specs['estimate data']\
                    #~ ['Est. current annual heating fuel gallons displaced'] 
        #~ try:
            #~ np.isnan(current_hr)
        #~ except TypeError:
            #~ current_hr = np.nan            
        
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
        hr_available = self.cd['percent heat recovered'] * \
                          diesel_consumed
        #notes
        #if b1 == 'Yes' and b2 == 'Yes':
        #   if hr_used is known and hr_proposed is not
        #      hr_used, hr_proposed = .30 * hr_available
        #   if hr_used is unknown and hr_proposed is unknown
        #      hr_used= .70 * hr_available, hr_proposed = .30 * hr_available
        #if b1 == 'Yes' and b2 == 'no':
        #   if hr_used is known:
        #       hr_used
        #   else:
        #       hr_used = hr_avaiavble
        #if b1 == 'No' and b2 == 'No':
        #   system needs to be installed        
        if b1 == 'Yes' and b2 == 'Yes' and np.isnan(potential_hr):
            potential_hr = ((hr_available) * .30)
        if b1 == 'Yes' and b2 == 'Yes':
            pass #potential_hr 
        elif b1 == 'Yes' and b2 == 'No':
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
