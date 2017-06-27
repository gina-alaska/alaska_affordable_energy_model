"""
Diesel Efficiency component body
--------------------------------

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

class DieselEfficiency(AnnualSavings):
    """Diesel Efficiency component of the Alaska Affordable Eenergy Model

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
        Initial value: 'Disel Efficiency' section of community_data
        
    See also
    --------
    aaem.community_data : 
        community data module, see information on CommintyData Object
    aaem.forecast : 
        forecast module, see information on Forecast Object
    aaem.diagnostics :
        diagnostics module, see information on diagnostics Object

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
            prerequisite component data

        """
        self.diagnostics = diag
        if self.diagnostics == None:
            self.diagnostics = diagnostics()
        self.forecast = forecast
        self.cd = community_data.get_section('community')
        
        self.comp_specs = community_data.get_section(COMPONENT_NAME)
        self.component_name = COMPONENT_NAME
        
        #~ self.comp_specs["start year"] = self.cd['current year'] + \
            #~ self.comp_specs["project details"]['expected years to operation']

        self.set_project_life_details(
            self.comp_specs["start year"],
            self.comp_specs["lifetime"]
        )
        
        
    def run (self, scalers = {'capital costs':1.0}):
        """runs the component. The Annual Total Savings,Annual Costs, 
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
        self.was_run = True
        self.reason = "OK"
        tag = self.cd['file id'].split('+')
        if len(tag) > 1 and tag[1] != 'diesel_efficiency':
            self.was_run = False
            self.reason = "Not a diesel efficiency project."
            return 
        
        if not self.cd["model electricity"]:
            self.was_run = False
            self.reason = "Electricity must be modeled to analyze diesel" +\
                                " efficiency. It was not for this community"

            return 
            # change these below
            
        self.calc_average_load()
        #~ print  self.average_load
        if np.isnan( self.average_load ):
            self.was_run = False
            self.reason = (
                "The Average diesel load is not available for this community. "
                "Is diesel generation present?"
            )
            return 
        self.calc_max_capacity()
        self.calc_baseline_generation_fuel_use()
        
        self.calc_proposed_generation_fuel_use()

        
        if self.cd["model financial"]:
        
            self.get_diesel_prices()
            
            # change these below
            self.calc_capital_costs()
            self.calc_oppex()
            self.calc_annual_electric_savings()
            self.calc_annual_heating_savings()
            
            # AnnualSavings functions (don't need to write)
            self.calc_annual_total_savings()
            self.calc_annual_costs(self.cd['interest rate'],
                                            scalers['capital costs'])
            self.calc_annual_net_benefit()
            self.calc_npv(self.cd['discount rate'], self.cd["current year"])
            self.calc_levelized_costs(0)
        
    def calc_average_load (self):
        """calculate the average load of the system
            
        Attributes
        ----------
        generation: array
            array of diesel generation values per year (kWh/year)
        average_load: float
            averge diesel generation load in first year of project (kW)
        
        """
        self.generation = self.forecast.generation['generation diesel']\
                                .ix[self.start_year:self.end_year].values
        self.average_load = \
                self.forecast.yearly_average_diesel_load.ix[self.start_year]
        
        #~ print 'self.average_load',self.average_load
 

    def calc_baseline_generation_fuel_use (self):
        """calculates baseline generation fuel use
        
        Attributes
        ----------
        baseline_diesel_efficiency : float
            the diesel generation efficiency before any imporvements
            are made (Gal/kWh) [
        baseline_generation_fuel_use : np.array
            fuel used per year before improvements (gal) 
        """
        self.baseline_diesel_efficiency = \
                        self.cd["diesel generation efficiency"]
        self.baseline_generation_fuel_use = self.generation / \
                                        self.baseline_diesel_efficiency 
    
    def calc_proposed_generation_fuel_use (self):
        """calculates proposed generation fuel use
       
        Attributes
        ----------
        proposed_diesel_efficiency : float
            the diesel generation efficiency before any imporvements 
            are made (Gal/kWh) 
        proposed_generation_fuel_use : np.array
            fuel used per year after improvments (gal) 
        """
        self.proposed_diesel_efficiency = \
                        self.cd["diesel generation efficiency"] * \
                        (1 + (self.comp_specs['efficiency improvment']/100.0))
        self.proposed_generation_fuel_use = self.generation / \
                                        self.proposed_diesel_efficiency 
                                        
    def calc_max_capacity (self):
        """calculate max load and capacity
        
        Attributes
        ---------- 
        max_load : float
            maximum load over project lifetime (KWh)
        max_capacity: float
            proposed max capacity (KWh)
        """
        self.max_load = self.generation[:self.actual_project_life].max() / \
                                                    constants.hours_per_year
        self.max_capacity = 13.416 * self.max_load ** (1 - 0.146)  
    
    def calc_capital_costs (self):
        """calculate the capital costs
            
        Attributes
        ----------
        capital_costs : float
             total cost of improvments ($), calculated from max_capacity
        """
        self.capital_costs = (1.8 + .001 * self.max_capacity) * 1000000
    
    def calc_oppex (self):
        """calculate the operational costs

        Attributes
        ----------
        oppex : float 
            operational costs per year ($) read from o&m costs table 
        """
        #~ key = 'else'
        #~ for max_load in sorted(self.comp_specs['o&m costs'].keys())[:-1]:
            #~ if self.average_load <= max_load:
                #~ key = max_load
                #~ break
                
        costs = self.comp_specs['o&m costs']
            
        for kW in costs.keys():
            try:
                if self.average_load < int(kW):
                    maintenance = self.comp_specs['o&m costs'][kW]
                    break
            except ValueError:
                maintenance = self.comp_specs['o&m costs'][kW]
        
        self.oppex =  maintenance#self.comp_specs['o&m costs'][key]
        
        
    def calc_annual_electric_savings (self):
        """calculate annual electric savings created by the project
            
        Attributes
        ----------
        annual_electric_savings : np.array
            electric savings ($/year) are the difference in the base 
        and proposed fuel costs
        """
        price = self.diesel_prices
        
        base = self.baseline_generation_fuel_use * price + self.oppex
        #~ print self.baseline_generation_fuel_use
        proposed = self.proposed_generation_fuel_use * price + self.oppex
        
        self.annual_electric_savings = base - proposed
        
    def calc_annual_heating_savings (self):
        """calculate annual heating savings created by the project
            
        Attributes
        ----------
        annual_heating_savings : flaot
            no savings from heating
        """
        self.annual_heating_savings = 0
        
    def get_fuel_total_saved (self):
        """get total fuel saved
        
        Returns 
        -------
        float
            the total fuel saved in gallons
        """
        return self.baseline_generation_fuel_use - \
                self.proposed_generation_fuel_use
    
    def get_total_energy_produced (self):
        """get total energy produced
        
        Returns
        ------- 
        float
            the total energy produced
        """
        return self.generation# / constants.mmbtu_to_gal_HF
        
    def save_component_csv (self, directory):
        """Save the component output csv in directory

        Parameters
        ----------
        directory : path
            output directory

        """
        if not self.was_run:
            return
        
        years = np.array(range(self.project_life)) + self.start_year

        df = DataFrame({
                "Diesel Efficiency: Generation (kWh/year)": self.generation,
                'Diesel Efficiency: Baseline Diesel'
                    ' Generator Efficiency [Gal/kWh]':
                                            self.baseline_diesel_efficiency,
                'Diesel Efficiency: Proposed Diesel'
                    ' Generator Efficiency [Gal/kWh]':
                                            self.proposed_diesel_efficiency,
                'Diesel Efficiency: Utility Diesel Baseline (gallons/year)':
                                        self.baseline_generation_fuel_use,
                'Diesel Efficiency: Utility Diesel Proposed (gallons/year)':
                                        self.proposed_generation_fuel_use,
                'Diesel Efficiency: Utility Diesel Displaced (gallons/year)':
                                        self.baseline_generation_fuel_use - \
                                        self.proposed_generation_fuel_use,
                "Diesel Efficiency: Electricity Cost Savings ($/year)": 
                                            self.get_electric_savings_costs(),
                "Diesel Efficiency: Project Capital Cost ($/year)": 
                                            self.get_capital_costs(),
                "Diesel Efficiency: Total Cost Savings ($/year)":
                                            self.get_total_savings_costs(),
                "Diesel Efficiency: Net Benefit ($/year)":
                                                self.get_net_benefit(),
                       }, years)

        df["Community"] = self.cd['name']
        
        ol = ["Community",
              "Diesel Efficiency: Generation (kWh/year)",
              'Diesel Efficiency: Baseline Diesel'
                    ' Generator Efficiency [Gal/kWh]',
              'Diesel Efficiency: Proposed Diesel'
                    ' Generator Efficiency [Gal/kWh]',
              'Diesel Efficiency: Utility Diesel Baseline (gallons/year)',
              'Diesel Efficiency: Utility Diesel Proposed (gallons/year)',
              'Diesel Efficiency: Utility Diesel Displaced (gallons/year)',
              "Diesel Efficiency: Electricity Cost Savings ($/year)",
              "Diesel Efficiency: Project Capital Cost ($/year)",
              "Diesel Efficiency: Total Cost Savings ($/year)",
              "Diesel Efficiency: Net Benefit ($/year)"]
        fname = os.path.join(directory,
                             self.cd['name'] + '_' + \
                             self.component_name.lower() + "_output.csv")
        fname = fname.replace(" ","_")
        
        df[ol].ix[:self.actual_end_year].to_csv(fname, index_label="Year")
