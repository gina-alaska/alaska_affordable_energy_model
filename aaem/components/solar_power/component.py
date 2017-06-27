"""
Solar Power component body
--------------------------

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

class SolarPower (AnnualSavings):
    """Solar Power of the Alaska Affordable Eenergy Model

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
        Initial value: 'Solar Power' section of community_data
        
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
       
        self.comp_specs = community_data.get_section(COMPONENT_NAME)
        self.component_name = COMPONENT_NAME

        self.set_project_life_details(
            self.comp_specs["start year"],
            self.comp_specs["lifetime"]
        )
                        
        ### ADD other intiatzation stuff
        
    
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
        self.was_run = True
        self.reason = "OK"
        
        
        tag = self.cd['file id'].split('+')
        if len(tag) > 1 and tag[1] != 'solar':
            self.was_run = False
            self.reason = "Not a solar project."
            return 
        
        try:
            self.calc_average_load()
            self.calc_proposed_generation()
        except:
            self.diagnostics.add_warning(self.component_name, 
            "could not be run")
            self.was_run = False
            self.reason = "Could not calculate average load," + \
                            " or proposed generation."

            return
            
        
        if self.average_load < self.comp_specs['average load limit'] or \
           not self.proposed_load > 0:
            self.diagnostics.add_note(self.component_name, 
            "model did not meet minimum generation requirments")
            self.was_run = False
            #~ print self.proposed_load, self.average_load, self.comp_specs['average load limit']
            if self.average_load < self.comp_specs['average load limit']:
                self.reason = "Average load too small for viable solar power."
            else: 
                self.reason = "Proposed load was less than 0."
            return
        
        
        self.calc_generation_fuel_used()
        self.calc_fuel_displaced()
        
        if self.cd["model financial"]:
            # AnnualSavings functions (don't need to write)
            self.get_diesel_prices()
            
            # change these below
            self.calc_capital_costs()
            self.calc_maintenance_cost()
            self.calc_annual_electric_savings()
            self.calc_annual_heating_savings()
            
            # AnnualSavings functions (don't need to write)
            self.calc_annual_total_savings()
            self.calc_annual_costs(self.cd['interest rate'],
                                            scalers['capital costs'])
            self.calc_annual_net_benefit()
            self.calc_npv(self.cd['discount rate'], self.cd["current year"])
            
            
            #~ print self.get_NPV_benefits()
            #~ print self.get_NPV_costs()
            #~ print self.get_NPV_net_benefit()
            #~ print self.get_BC_ratio()
            self.calc_levelized_costs(self.maintenance_cost)
            
            
    def calc_average_load (self):
        """Caclulate the Average Diesel load of the current system
        
        Attributes
        ----------
        average_load : float 
            average disel load of current system
        """
        #~ self.generation = self.forecast.get_generation(self.start_year)
        #~ self.generation = \
            #~ self.forecast.generation_by_type['generation diesel']\
            #~ [self.start_year]
        self.average_load = \
                self.forecast.yearly_average_diesel_load.ix[self.start_year]
        #~ print self.average_load
        
    def calc_proposed_generation (self):
        """Calulate the proposed generation for Solar Power.
        
        Attributes
        ----------
        Proposed Load: float
             Proposed sloar power load (kW)
        generation_proposed : float
            Proposed sloar power generatiod (kWh/yr)
        """
        self.proposed_load = self.average_load * \
            (self.comp_specs['percent generation to offset'] / 100.0)
        #~ print self.proposed_load
        existing_RE = self.cd['solar capacity'] + \
                      self.cd['wind capacity']
        #~ print existing_RE, self.comp_specs['data']['Installed Capacity'], self.comp_specs['data']['Wind Capacity']
        self.proposed_load = max(self.proposed_load - existing_RE, 0)
        
        #~ self.total_load = self.proposed_load + \
                        #~ self.comp_specs['data']['Installed Capacity']               
        
        self.generation_proposed = self.proposed_load *\
                        self.comp_specs['output per 10kW solar PV'] / 10.0
                        
        self.generation_proposed = self.generation_proposed *\
            ((100 - self.comp_specs['percent solar degradation'])/100.0)**\
            np.arange(self.project_life)
        #~ print 'self.calc_proposed_generation'
        #~ print self.proposed_load
        #~ print self.generation_proposed
        
    def calc_generation_fuel_used (self):
        """
        """
        gen_eff = self.cd["diesel generation efficiency"]
        self.generation_fuel_used = self.generation_proposed/gen_eff
        
    def calc_fuel_displaced (self):
        """Calculate fuel displaced py solar power.
        
        Attributes
        ----------
        fuel_displaced : float
            fuel displaced by solar power (gal)
        """
        gen_eff = self.cd["diesel generation efficiency"]
        if self.cd['heat recovery operational']:
            self.fuel_displaced = self.generation_proposed/gen_eff * .15
        else:
            self.fuel_displaced = self.generation_proposed * 0
        
    def calc_maintenance_cost (self):
        """Calculate Maintenace costs.
        
        Attributes
        ----------
        maintenance_cost : float
            maintenance cost as a percentage of the captial costs
        """
        self.maintenance_cost = self.capital_costs * \
            (self.comp_specs['percent o&m']/100.0)
        #~ print "self.calc_maintenance_cost"
        #~ print self.maintenance_cost
    
    def calc_capital_costs (self):
        """Calculate the capital costs.
            
        Attributes
        ----------
        capital_costs : float
             total cost of improvments ($), calculated from transmission and
             generagion costs
        """
        component_cost = self.comp_specs['cost']
        if str(component_cost) == 'UNKNOWN':
            component_cost = self.proposed_load * self.comp_specs['cost per kW']
            
        powerhouse_cost = 0
        if not self.cd['switchgear suatable for renewables'] and \
            self.comp_specs['switch gear needed for solar']:
            powerhouse_cost = self.cd['switchgear cost']
            
        self.capital_costs = powerhouse_cost + component_cost
        #~ print 'self.calc_capital_costs'
        #~ print self.capital_costs
    

    def calc_annual_electric_savings (self):
        """Calculate annual electric savings created by the project.
            
        Attributes
        ----------
        annual_electric_savings : np.array
            electric savings ($/year) are the difference in the base 
        and proposed fuel costs
        """
        self.proposed_generation_cost = self.maintenance_cost
        
        price = self.diesel_prices
        # fuel cost + maintance cost
        self.baseline_generation_cost = (self.generation_fuel_used * price)# +\
                #~ (self.generation_proposed * self.comp_specs['o&m cost per kWh'])
        
        self.annual_electric_savings = self.baseline_generation_cost - \
                                       self.proposed_generation_cost
                                       
        #~ print self.baseline_generation_cost
        #~ print self.proposed_generation_cost
        #~ print self.annual_electric_savings
        
        
    # Make this do sruff. Remember the different fuel type prices if using
    def calc_annual_heating_savings (self):
        """Calculate annual heating savings created by the project.
            
        Attributes
        ----------
        annual_heating_savings : np.array
            heating savings ($/year) 
        """
        price = (self.diesel_prices + self.cd['heating fuel premium'])
        self.annual_heating_savings = self.fuel_displaced * price
        #~ print self.fuel_displaced
        #~ print self.annual_heating_savings
        
    def get_fuel_total_saved (self):
        """Get total fuel saved.
        
        Returns 
        -------
        float
            the total fuel saved in gallons
        """
        base_gen_fuel = self.generation_fuel_used[:self.actual_project_life]
        post_gen_fuel = 0

        return (base_gen_fuel - post_gen_fuel) + \
                    self.fuel_displaced[:self.actual_project_life]
    
    def get_total_energy_produced (self):
        """Get total energy produced.
        
        Returns
        ------- 
        float
            the total energy produced
        """
        gen = self.generation_proposed[:self.actual_project_life]
        return gen
        
    def save_component_csv (self, directory):
        """Save the component output csv in directory.

        Parameters
        ----------
        directory : path
            output directory

        """
        if not self.was_run:
            #~ fname = os.path.join(directory,
                                   #~ self.component_name + "_output.csv")
            #~ fname = fname.replace(" ","_")
        
            #~ fd = open(fname, 'w')
            #~ fd.write("Wind Power minimum requirments not met\n")
            #~ fd.close()
            return
        
        
        years = np.array(range(self.project_life)) + self.start_year
    
        df = DataFrame({
                'Solar: Capacity (kW)': self.proposed_load,
                "Solar: Generation (kWh/year)": 
                                            self.generation_proposed,
                'Solar: Utility Diesel Displaced (gallons/year)':
                                            self.generation_fuel_used,
                'Solar: Heating Fuel Displaced (gallons/year)':self.fuel_displaced,
                "Solar: Heat Recovery Cost Savings ($/year)": 
                                        self.get_heating_savings_costs(),
                "Solar: Electricity Cost Savings ($/year)": 
                                        self.get_electric_savings_costs(),
                "Solar: Project Capital Cost ($/year)":
                                        self.get_capital_costs(),
                "Solar: Total Cost Savings ($/year)": 
                                        self.get_total_savings_costs(),
                "Solar: Net Benefit ($/year)": self.get_net_benefit(),
                       }, years)

        df["Community"] = self.cd['name']
        
        ol = ["Community",'Solar: Capacity (kW)',
              "Solar: Generation (kWh/year)",
              'Solar: Utility Diesel Displaced (gallons/year)',
              'Solar: Heating Fuel Displaced (gallons/year)',
              "Solar: Heat Recovery Cost Savings ($/year)",
              "Solar: Electricity Cost Savings ($/year)",
              "Solar: Project Capital Cost ($/year)",
              "Solar: Total Cost Savings ($/year)",
              "Solar: Net Benefit ($/year)"]
        fname = os.path.join(directory,
                                   self.cd['name'] + '_' +\
                                   self.component_name.lower() + "_output.csv")
        fname = fname.replace(" ","_")
        
        
        # save to end of project(actual lifetime)
        df[ol].ix[:self.actual_end_year].to_csv(fname, index_label="Year")
