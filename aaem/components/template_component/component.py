"""
Template component body
-----------------------

"""
import numpy as np
from pandas import DataFrame
import os

from aaem.components.annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import Diagnostics
import aaem.constants as constants
from config import COMPONENT_NAME, PROJECT_TYPE, UNKNOWN

#   do a find and replace on ComponentName to name of component 
# (i.e. 'ResidentialBuildings')
class ComponentName (AnnualSavings):
    """<TEMPLATE> of the Alaska Affordable Eenergy Model

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
        Initial value: 'Template' section of community_data
        
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
        
        self.comp_specs["start year"] = self.cd['current year'] + \
            self.comp_specs["project details"]['expected years to operation']

        self.set_project_life_details(
            self.comp_specs["start year"],
            self.comp_specs["lifetime"]
        )
        
        ### ADD other intiatzation stuff  
        ### load prerequisites in the following function
        ### if there are no prerequisites you can delete this and the 
        ### load_prerequisite_variables function
        self.load_prerequisite_variables(prerequisites)
        
    def load_prerequisite_variables (self, comps):
        """load variables from prerequisites
        
        Parameters
        ----------
        comps : dict
            dictionary of prerequisite components
        """
        # LOAD anything needed from the components passed as input
        # WRITE this
        pass
        
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
        
        ### UPDATE PROJECT TYPE to a string represeting the project tag
        if len(tag) > 1 and tag[1] != PROJECT_TYPE:
            self.was_run = False
            self.reason = "Not a PROJECT_TYPE project"
            return 
        
        if self.cd["model electricity"]:
            # add functions for caclulating electricity related values
            pass
            
        
        if self.cd["model heating fuel"]:
            # add functions for caclulating Heating Fuel related values
            pass
        
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
    
    
    # Make this do stuff
    def calc_capital_costs (self):
        """Calculate the capital costs.
            
        Attributes
        ----------
        capital_costs : float
             total cost of improvments ($), calculated from transmission and
             generagion costs
        """
        self.capital_costs = np.nan
        
    
    # Make this do stuff
    def calc_annual_electric_savings (self):
        """Calculate annual electric savings created by the project.
            
        Attributes
        ----------
        annual_electric_savings : np.array
            electric savings ($/year) are the difference in the base 
        and proposed fuel costs
        """
        self.annual_electric_savings = 0
        
        
    # Make this do sruff. Remember the different fuel type prices if using
    def calc_annual_heating_savings (self):
        """Calculate annual heating savings created by the project.
            
        Attributes
        ----------
        annual_heating_savings : np.array
            heating savings ($/year) 
        """
        self.annual_heating_savings = 0
        
    # return savings in gallons
    def get_fuel_total_saved (self):
        """Get total fuel saved.
        
        Returns 
        -------
        float
            the total fuel saved in gallons
        """
        return 0
        #~ return <savings>
    
    # return savings mmbtu
    def get_total_energy_produced (self):
        """Save the component output csv in directory.

        Parameters
        ----------
        directory : path
            output directory

        """
        return 0 
        #~ return <savings>
