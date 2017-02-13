"""
Transmission Component Body
---------------------------

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
from aaem.diesel_prices import DieselProjections

class Transmission (AnnualSavings):
    """Transmission of the Alaska Affordable Eenergy Model

    Parameters
    ----------
    commnity_data : CommunityData
        CommintyData Object for a community
    forecast : Forecast
        forcast for a community 
    diagnostics : diagnostics, optional
        diagnostics for tracking error/warining messeges
    prerequisites : dictionary of components, optional
        prerequisite component data this component has no prerequisites 
        leave empty
        
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
        Initial value: 'Transsmission' section of community_data
        
    See also
    --------
    aaem.community_data : 
        community data module, see for information on CommintyData Object
    aaem.forecast : 
        forecast module, see for information on Forecast Object
    aaem.diagnostics :
        diagnostics module, see for information on diagnostics Object

    """
    def __init__ (self, community_data, forecast, 
                        diag = None, prerequisites = {}):
        """Class initialiser.
        
        Parameters
        ----------
        commnity_data : CommunityData
            CommintyData Object for a community
        forecast : Forecast
            forcast for a community 
        diagnostics : diagnostics, optional
            diagnostics for tracking error/warining messeges
        prerequisites : dictionary of components, optional
            prerequisite component data

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
        
    def run (self, scalers = {'capital costs':1.0}):
        """Runs the component. The Annual Total Savings,Annual Costs, 
        Annual Net Benefit, NPV Benefits, NPV Costs, NPV Net Benefits, 
        Benefit Cost Ratio, Levelized Cost of Energy, 
        and Internal Rate of Return will all be calculated. There must be a 
        known Heat Recovery project for this component to run.
        
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
        self.run = True
        self.reason = "OK"
        tag = self.cd['name'].split('+')
        if len(tag) > 1 and tag[1] != 'transmission':
            self.run = False
            self.reason = "Not a transmission project."
            return 
            
        if not self.cd["model electricity"]:
            self.run = False
            self.reason = "Electricity must be modeled to analyze "+\
                                "transmission. It was not for this community."
            return 
        if np.isnan(self.comp_specs['nearest community']\
                                    ['Distance to Community']):
            self.run = False
            self.reason = ("There are no communities within 30 miles with"
                            " lower cost of electricity.")
            return 
        
        self.calc_average_load()
        try:
            self.get_intertie_values()
        except IOError:
            self.run = False
            self.reason = ("Could not find data on community to intertie to.")
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
            self.calc_annual_costs(self.cd['interest rate'],
                                            scalers['capital costs'])
            self.calc_annual_net_benefit()
            self.calc_npv(self.cd['discount rate'], self.cd["current year"])
            #~ print self.benefit_cost_ratio
            self.calc_levelized_costs(self.proposed_generation_cost)
    

            
    def calc_average_load (self):
        """Caclulate the Average Diesel load of the current system
        
        Attributes
        ----------
        average_load : float 
            average disel load of current system
        """
        #~ self.generation = self.forecast.generation_by_type['generation diesel']\
                                                            #~ [self.start_year]
        self.average_load = \
                self.forecast.yearly_average_diesel_load.ix[self.start_year]
        
    def get_intertie_values (self):
        """Get values from the community being connected to (second community)
        
        .. Note::
            the input_data for the second communty shoud exist 
        
        Attributes
        ----------
        intertie_generation_efficiency : float 
            the generator efficiency kWh/gal
        intertie_diesel_prices : np.array
            diesel prices over the project lifetime
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
        """Calculate the generation offset by connecting a transmission line 
        to the community to connect to.
        
        Attributes
        ----------
        annual_tranmission_loss : float
            the percent electrcity lost through transmission
        intertie_offset_generation : float
            the genneration offset in kWh
        intertie_offset_generation_fuel_used : float
            is the fuel used in generation gallons
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
        """Calculate the status quo generation in the community .
        
        Attributes
        ----------
        pre_intertie_generatio : float
            current generation per year in kWh
        pre_intertie_generation_fuel_used : float
            the fuel used in generation (gallons)
        """
        
        self.pre_intertie_generation = \
            self.forecast.get_generation(self.start_year,self.end_year)
        
        gen_eff = self.cd["diesel generation efficiency"]
        self.pre_intertie_generation_fuel_used = \
                        self.pre_intertie_generation / gen_eff
        
        #~ print 'self.baseline_generatio',self.baseline_generation
        
    def calc_lost_heat_recovery (self):
        """Calculate the heat recovery
        
        Attributes:
        lost_heat_recovery : np.array 
            the heat recovry lost per year (gal of heating fuel)
        """
        if not self.cd['heat recovery operational']:

            self.lost_heat_recovery  = [0]
        else:
            gen_eff = self.cd["diesel generation efficiency"]
            self.lost_heat_recovery = \
                (self.generation / gen_eff )* .10
    
    def calc_capital_costs (self):
        """Calculate the capital costs.
            
        Attributes
        ----------
        capital_costs : float
             total cost of improvments ($), calculated from transmission and
             generagion costs
        """
        road_needed = 'road needed'
        if self.cd['on road system']:
            road_needed = 'road not needed'
        
        dist = self.comp_specs['nearest community']['Distance to Community']
        self.capital_costs = self.comp_specs['est. intertie cost per mile']\
                                             [road_needed] * dist
        #~ print self.capital_costs
        
    
    # Make this do stuff
    def calc_annual_electric_savings (self):
        """Calculate annual electric savings created by the project.
            
        Attributes
        ----------
        baseline_generation_cost : np.array
            current cost of generation ($/year)
        proposed_generation_cost : np.array
            proposed cost of generation ($/year)
        annual_electric_savings : np.array
            electric savings ($/year) are the difference in the base 
        and proposed fuel costs
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
        """Calculate annual heating savings created by the project.
            
        Attributes
        ----------
        annual_heating_savings : np.array
            heating savings ($/year) 
        """
        price = self.diesel_prices + self.cd['heating fuel premium']
        maintenance = self.comp_specs['heat recovery o&m']
        self.annual_heating_savings = -1 * \
                            (maintenance + (self.lost_heat_recovery * price))
                                    
    def get_fuel_total_saved (self):
        """Get total fuel saved.
        
        Returns 
        -------
        float
            the total fuel saved in gallons
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
        """Get total energy produced.
        
        Returns
        ------- 
        float
            the total energy produced
        """
        return self.pre_intertie_generation[:self.actual_project_life]
