"""
component.py

    Hydropower component body
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

class Hydropower (AnnualSavings):
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
        try:
            self.comp_specs["start year"] = self.cd['current year'] + \
            self.comp_specs["project details"]['expected years to operation']
        except TypeError:
            self.comp_specs["start year"] = self.cd['current year']
        self.set_project_life_details(self.comp_specs["start year"],
                                      self.comp_specs["lifetime"],
                        self.forecast.end_year - self.comp_specs["start year"])
        
        self.load_prerequisite_variables(prerequisites)
        
    def load_prerequisite_variables (self, comps):
        """
        load variables from prerequisites
        
        pre:
             prerequisites: dictonary of componentes
        """
        # not used here
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
        if len(tag) > 1 and tag[1] != 'hydro':
            self.run = False
            self.reason = "Not a Hydropower project"
            return 
        
        if self.comp_specs["project details"] is None:
            self.run = False
            self.reason = "No Project Data"
            return 
        
        if not self.cd["model electricity"]:
            self.run = False
            self.reason = "Electricty must be modeled to analyze hydropower." +\
                                " It was not for this community"
            return 
            
        try:
            self.calc_average_load()
            self.calc_generation_proposed()
        except AttributeError:
            self.diagnostics.add_warning(self.component_name, 
                            "could not be run")
            self.run = False
            self.reason = "Could not calculate average load or " + \
                            "proposed generation"
            return
            
        if self.load_offset_proposed is None:
            self.run = False
            self.reason = "No project data provided"
            return
            
        if self.cd["model heating fuel"]:
            self.calc_heat_recovery ()
        
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
            
            
            o_m = self.net_generation_proposed * \
                    self.cd['diesel generator o&m cost']
        
            self.calc_levelized_costs(o_m)
            
    def calc_average_load (self):
        """
            calculate the average load of the system
            
        pre: 
            self.generation should be a number (kWh/yr)
            
        post:
            self.average_load is a number (kW/yr)
        """
        self.generation = self.forecast.generation_by_type['generation diesel']\
                                                            [self.start_year]
        self.average_load = \
                self.forecast.yearly_average_diesel_load.ix[self.start_year]
        #~ print 'self.average_load',self.average_load
 
    def calc_generation_proposed (self):
        """
            calulate the proposed generation for wind
        pre:
            self.generation should be a number (kWh/yr), 
            'percent generation to offset' is a decimal %
            'resource data' is a wind data object
            'assumed capacity factor' is a decimal %
        
        post:
            self.load_offest_proposed is a number (kW)
            self.gross_generation_proposed is a number (kWh/yr)
            self.net_generation_proposed is a number (kWh/yr)
        """
        if self.comp_specs["project details"]['proposed capacity'] == UNKNOWN:
            self.load_offset_proposed = None
            self.gross_generation_proposed = None
            self.net_generation_proposed = None
            
        else:
            self.load_offset_proposed = \
                    self.comp_specs["project details"]['proposed capacity']
            self.gross_generation_proposed = \
                    self.comp_specs["project details"]['proposed generation']
            tansmission_losses = self.cd['line losses'] *\
                                 self.gross_generation_proposed
            exess_energy = \
                (self.gross_generation_proposed - tansmission_losses) * \
                self.cd['percent excess energy']
            
            self.percent_excess_energy = exess_energy / \
                                         self.gross_generation_proposed   
            
            self.net_generation_proposed = self.gross_generation_proposed -\
                                           tansmission_losses -\
                                           exess_energy
        
            if self.net_generation_proposed > self.generation:
                self.net_generation_proposed = self.generation
                                           
        #~ print 'self.load_offset_proposed', self.load_offset_proposed
        #~ print 'self.gross_generation_proposed', self.gross_generation_proposed
        #~ print 'self.net_generation_proposed', self.net_generation_proposed


    def calc_heat_recovery (self):
        """
        caclulate heat recovery values used by component
        pre:
            self.percent_excess_energy is the precentage of excess energy
        created in generation
            self.gross_generation_proposed is a floating point value
        post:
            self.generation_diesel_reduction, self.lost_heat_recovery, 
        and self.generation_diesel_reduction
            
        """
        # %
       
        captured_percent = self.percent_excess_energy * \
                    self.cd['percent excess energy capturable']
        
        #kWh/year
        captured_energy = captured_percent * self.gross_generation_proposed
        
        #~ conversion: gal <- kwh
        conversion = self.cd['efficiency electric boiler']/ \
                     (1/constants.mmbtu_to_gal_HF)/ \
                     self.cd['efficiency heating oil boiler']/\
                     (constants.mmbtu_to_kWh)
        self.captured_energy = captured_energy * conversion # gallons/year
        
        # gal/year <- kWh*year/ (kWh/gal) 
        gen_eff = self.cd["diesel generation efficiency"]
        self.generation_diesel_reduction = self.net_generation_proposed /\
                                            gen_eff
                                            
        #~ electric_diesel = self.generation /gen_eff
        #~ if self.generation_diesel_reduction > electric_diesel:
            #~ self.generation_diesel_reduction = electric_diesel
        
        # gal/year
        if not self.cd['heat recovery operational']:

            self.lost_heat_recovery  = 0
        else:
            self.lost_heat_recovery = self.generation_diesel_reduction * \
                                self.comp_specs['percent heat recovered']
        
        #~ print 'self.captured_energy', self.captured_energy
        #~ print 'self.lost_heat_recovery', self.lost_heat_recovery

    # Make this do stuff
    def calc_capital_costs (self):
        """
        calculate the capital costs
        
        pre:
            the project details section of the hydro section is initlized
        according to structure shown in load project detials
        post:
            self.capital_costs is the total cost of the project in dollars
        """
        transmission_cost = \
            self.comp_specs['project details']['transmission capital cost']
        generator_cost = \
            self.comp_specs['project details']['generation capital cost']
        self.capital_costs = transmission_cost + generator_cost
        #~ print 'self.capital_costs', self.capital_costs
        
    
    # Make this do stuff
    def calc_annual_electric_savings (self):
        """
        calculates the annual electric savings
        pre:
            self.capital_costs should be caclulated
            self.comp_specs and self.cd should have all values nessary for 
        this component.
            self.diesel_prices should be intilized
        post:
            self.annual_electric_savings is the annual elctric savings in 
        dollars
        """
        proposed_generation_cost = self.capital_costs * \
                                self.comp_specs['percent o&m']
                        
        
        maintianice_cost = self.net_generation_proposed * \
                        self.cd['diesel generator o&m cost']  
        
        price = self.diesel_prices
        
        fuel_cost = price * self.generation_diesel_reduction
        
        baseline_generation_cost = fuel_cost + maintianice_cost
        
        self.annual_electric_savings = baseline_generation_cost - \
                                        proposed_generation_cost 
        #~ print 'self.annual_electric_savings', self.annual_electric_savings
        
        
    # Make this do sruff. Remember the different fuel type prices if using
    def calc_annual_heating_savings (self):
        """
        calcualte the annual heating savings
        pre:
            self.diesel_prices should be initilzed as a np.array of 
        floats ($/gal)
            self.cd should have all values initilzed as designed
            self.captured_energy and self.lost_heat_recovery are [gallons]
        post:
            self.annual_heating_savings is an array or scaler in dollars
        
        """
        price = (self.diesel_prices + self.cd['heating fuel premium'])
        
        self.annual_heating_savings = \
                (self.captured_energy - self.lost_heat_recovery) *\
                price
        #~ print 'self.annual_heating_savings', self.annual_heating_savings
        
    def get_fuel_total_saved (self):
        """
        returns the total fuel saved in gallons
        """
    
        return (self.captured_energy - self.lost_heat_recovery) + \
                self.generation_diesel_reduction
    
    def get_total_enery_produced (self):
        """
        returns the total energy produced
        """
        return self.net_generation_proposed
        
    def save_component_csv (self, directory):
        """
        save the output from the component.
        """
        #~ return
        if not self.run:
            return
        
        
        years = np.array(range(self.project_life)) + self.start_year
    
        # ??? +/- 
        # ???
        df = DataFrame({
                'Hydro: Capacity (kW)':self.load_offset_proposed,
                "Hydro: Generation (kWh/year)": self.net_generation_proposed,
                'Hydro: Energy Captured by Secondary Load'
                    ' (gallons of heating oil equivalent)':self.captured_energy,

                'Hydro: Utility Diesel Displaced (gallons/year)':
                                            self.captured_energy - \
                                            self.lost_heat_recovery,
                'Hydro: Heat Recovery Lost (gallons/year)':
                                            self.lost_heat_recovery, 
                "Hydro: Heat Recovery Cost Savings ($/year)": 
                                            self.get_heating_savings_costs(),
                "Hydro: Electricity Cost Savings ($/year)": 
                                            self.get_electric_savings_costs(),
                "Hydro: Project Capital Cost ($/year)": 
                                            self.get_capital_costs(),
                "Hydro: Total Cost Savings ($/year)":
                                            self.get_total_savings_costs(),
                "Hydro: Net Benefit ($/year)": self.get_net_benefit(),
                       }, years)

        df["Community"] = self.cd['name']
        
        ol = ["Community",
              'Hydro: Capacity (kW)',
              'Hydro: Energy Captured by Secondary Load'
                        ' (gallons of heating oil equivalent)',
              'Hydro: Utility Diesel Displaced (gallons/year)',
              'Hydro: Heat Recovery Lost (gallons/year)',
              "Hydro: Generation (kWh/year)",
              "Hydro: Heat Recovery Cost Savings ($/year)",
              "Hydro: Electricity Cost Savings ($/year)",
              "Hydro: Project Capital Cost ($/year)",
              "Hydro: Total Cost Savings ($/year)",
              "Hydro: Net Benefit ($/year)"]

        fname = os.path.join(directory,
                             self.cd['name'] + '_' + \
                             self.component_name.lower() + "_output.csv")
        fname = fname.replace(" ","_")
        
        df[ol].ix[:self.actual_end_year].to_csv(fname, index_label="Year")
