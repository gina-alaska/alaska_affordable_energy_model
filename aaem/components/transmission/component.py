"""
component.py

    Transmission Line component body
"""
import numpy as np
from pandas import DataFrame, read_csv
import os

from aaem.components.annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import diagnostics
import aaem.constants as constants
from config import COMPONENT_NAME, UNKNOWN

class Transmission (AnnualSavings):
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
        self.data_dir = community_data.data_dir
        
       
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
        
    def run (self, scalers = {'captial costs':1.0}):
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
        if len(tag) > 1 and tag[1] != 'transmission':
            self.run = False
            self.reason = "Not a transmission project"
            return 
            
        if not self.cd["model electricity"]:
            self.run = False
            self.reason = ("'model electricity' in the communtiy data"
                           " must be True to run this component")
            return 
        
        if np.isnan(self.comp_specs['nearest community']\
                                    ['Distance to Community']):
            self.run = False
            self.reason = ("no community to intertie with transmission line")
            return 
        
        self.calc_average_load()
        try:
            self.get_intertie_values()
        except IOError:
            self.run = False
            self.reason = ("Community to Intertie to is missing input data")
            return 
        self.calc_pre_intertie_generation()
        self.calc_intertie_offset_generation()
            
        
        if self.cd["model heating fuel"]:
            # change these below
            self.calc_lost_heat_recovery()
            # see NOTE*
        
        #~ return
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
            #~ print self.benefit_cost_ratio
            self.calc_levelized_costs(self.proposed_generation_cost)
    

            
    def calc_average_load (self):
        """
        calculate the average diesel load
        pre:
            self.forecast must have the genneration_by_type table
        post:
            self.generation is the total generation of the first year 
        a kWh value
            self.average_load is the average load for the firest year in kW
        """
        self.generation = self.forecast.generation_by_type['generation diesel']\
                                                            [self.start_year]
        self.average_load = \
                self.forecast.yearly_average_diesel_load.ix[self.start_year]
        
    def get_intertie_values (self):
        """
        get values from the community being connected to (second community)
        pre:
            the input_data for the second communty shoud exist 
        post:
            self.intertie_generation_efficiency is the efficiency kWh/gal
            self.intertie_diesel_prices is an array of prices over the project
        life time
        """
        com = self.comp_specs['nearest community']\
                ['Nearest Community with Lower Price Power'].replace(' ','_')
        path = os.path.join(os.path.split(self.data_dir)[0],com)
        self.connect_to_intertie = False
        if os.path.exists(path+'_intertie'):
            self.connect_to_intertie = True
            path += '_intertie'
            
        #~ print read_csv(os.path.join(path,'interties.csv'),comment='#')
        
        self.intertie_generation_efficiency = \
                read_csv(os.path.join(path,'yearly_electricity_summary.csv'),
                         comment='#',index_col=0)['efficiency'][-3:].mean()
                         
        it_diesel_prices = DieselProjections(path)
        self.intertie_diesel_prices = \
                it_diesel_prices.get_projected_prices (self.start_year,
                                                        self.end_year)

    def calc_intertie_offset_generation (self):
        """
            calculate the generation offset by connecting a transmission line 
        to the community to connect to.
        pre:
            self.forecast needs to have the consumpton forecasted
            self.intertie_generation_efficiency must exist
        post:
            self.annual_tranmission_loss is the percent electrcity lost by
        transmission
            self.intertie_offset_generation is the genneration off set in kWh
            self.intertie_offset_generation_fuel_used is the fuel used 
        in generation gallons
        """
        self.generation = \
                self.forecast.get_generation(self.start_year,self.end_year)
        dist = self.comp_specs['nearest community']['Distance to Community']
        self.annual_tranmission_loss = \
            1 - ((1-self.comp_specs['transmission loss per mile']) ** dist)
        self.intertie_offset_generation = \
                        self.generation * (1 + self.annual_tranmission_loss)
        
        gen_eff = self.intertie_generation_efficiency
        self.intertie_offset_generation_fuel_used = \
                        self.intertie_offset_generation / gen_eff
        #~ print 'self.proposed_generation',self.proposed_generation
        #~ print con
        
    def calc_pre_intertie_generation (self):
        """
        calculate the status quo generation in the community 
        
        pre:
            self.forecast needs to have the generation forecasted 
        post:
            self.pre_intertie_generation is the generaty per year in kWh
            self.pre_intertie_generation_fuel_used is the fuel used 
        in generation gallons
        """
        
        self.pre_intertie_generation = \
            self.forecast.get_generation(self.start_year,self.end_year)
        
        gen_eff = self.cd["diesel generation efficiency"]
        self.pre_intertie_generation_fuel_used = \
                        self.pre_intertie_generation / gen_eff
        
        #~ print 'self.baseline_generatio',self.baseline_generation
        
    def calc_lost_heat_recovery (self):
        """
        calculate the heat recovery
        pre:
            self.cd is ready
        post:
            self.lost_heat_recovery is an array of the heat recovry lost per 
        year in gallons heating fuel
        """
        if not self.cd['heat recovery operational']:

            self.lost_heat_recovery  = [0]
        else:
            gen_eff = self.cd["diesel generation efficiency"]
            self.lost_heat_recovery = \
                (self.generation / gen_eff )* .10
    
    def calc_capital_costs (self):
        """ 
        calculate the captial costs
        
        pre:
            self.comp_specs set up
        post:
            self.captial costs is the total cost of the project $
        """
        road_needed = 'road needed'
        if self.comp_specs['on road system']:
            road_needed = 'road not needed'
        
        dist = self.comp_specs['nearest community']['Distance to Community']
        self.capital_costs = self.comp_specs['est. intertie cost per mile']\
                                             [road_needed] * dist
        #~ print self.capital_costs
        
    
    # Make this do stuff
    def calc_annual_electric_savings (self):
        """
        calcualte the annual elctric savings in dollars
        pre:
            self.intertie_offset_generation_fuel_used, 
            self.intertie_diesel_prices, 
            self.pre_intertie_generation_fuel_used, 
            self.diesel_prices should exist
        post:
            self.annual_electric_savings is the savings in dollars per year
        """
        costs = self.comp_specs['diesel generator o&m']
            
        for kW in costs.keys():
            try:
                if self.average_load < int(kW):
                    maintenance = self.comp_specs['diesel generator o&m'][kW]
                    break
            except ValueError:
                maintenance = self.comp_specs['diesel generator o&m'][kW]
                
        self.baseline_generation_cost = maintenance + \
            (self.pre_intertie_generation_fuel_used * self.diesel_prices)
        
        maintenance = self.capital_costs * self.comp_specs['percent o&m']
        self.proposed_generation_cost = maintenance + \
                self.intertie_offset_generation_fuel_used * \
                self.intertie_diesel_prices
        self.annual_electric_savings = self.baseline_generation_cost -\
                                        self.proposed_generation_cost
        #~ print 'self.annual_electric_savings',self.annual_electric_savings
        
        
    # Make this do sruff. Remember the different fuel type prices if using
    def calc_annual_heating_savings (self):
        """
        calculate the annual heating savings
        pre:
            self.diesel_prices, self.lost_heat_recovery should exist
        post:
            self.annual_heating_savings is the savings in dollars per year
        """
        price = self.diesel_prices + self.cd['heating fuel premium']
        maintenance = self.comp_specs['heat recovery o&m']
        self.annual_heating_savings = -1 * \
                            (maintenance + (self.lost_heat_recovery * price))
                                    
    def get_fuel_total_saved (self):
        """
        returns the total fuel saved in gallons
        """
        #~ print self.lost_heat_recovery
        #~ print self.intertie_offset_generation_fuel_used
        #~ print self.pre_intertie_generation_fuel_used
        #~ gen_eff = self.cd["diesel generation efficiency"]
        #~ fuel_used = self.intertie_offset_generation / gen_eff
        
        generation_diesel_reduction = \
                    np.array(self.pre_intertie_generation_fuel_used\
                                                [:self.actual_project_life]) 
        return - np.array(self.lost_heat_recovery[:self.actual_project_life]) +\
                        generation_diesel_reduction
    
    def get_total_enery_produced (self):
        """
        returns the total energy produced
        """
        return self.pre_intertie_generation[:self.actual_project_life]
