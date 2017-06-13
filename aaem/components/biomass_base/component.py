"""
Biomass - Base component body
-----------------------------

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

class BiomassBase (AnnualSavings):
    """Base Biomass of the Alaska Affordable Eenergy Model. Base component
    does noting on it's own.

    Parameters
    ----------
    commnity_data : CommunityData
        CommintyData Object for a community
    forecast : Forecast
        forcast for a community 
    diagnostics : diagnostics, optional
        diagnostics for tracking error/warining messeges
    prerequisites : dictionary of components, optional
        Non-residential buildings is required
        
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
        Initial value: 'Biomass Base' section of community_data
        
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
            prerequisite component data, None

        """
        self.diagnostics = diag
        if self.diagnostics == None:
            self.diagnostics = diagnostics()
        self.forecast = forecast
        self.cd = community_data.get_section('community')
       
        self.comp_specs = community_data.get_section(self.component_name)
        

        self.set_project_life_details(
            self.comp_specs["start year"],
            self.comp_specs["lifetime"]
        )
    
        #~ print self.comp_specs['data']
                
        self.non_res_sqft = 0
        self.avg_gal_per_sqft = 0
        self.biomass_type = "NA"
        self.units = "NA"
        self.load_prerequisite_variables(prerequisites)
        
        
        
    def load_prerequisite_variables (self, comps):
        """Load variables from prerequisites, placeholder for child 
        components if needed.
        
        Parameters
        ----------
        comps : Dict
            Dictionary of components
        """
        tag = self.cd['file id'].split('+')
        
        if len(tag) > 1 and tag[1].split('_')[0] != 'biomass':
            return 
        non_res = comps['Non-residential Energy Efficiency']
        self.get_non_res_values(non_res)
        
    def get_non_res_values (self, non_res):
        """Get the values nessaery to run the biomass component from
        the non residential buildings component.
        
        Parameters
        ----------
        non_res : aaem.components.non_residential.CommunityBuildings 
            is a run non residential buildings componet
        
        Attributes
        ----------
        non_res_sqft : float
            square feet in community
        avg_gal_per_sqft : float
            average gallons per sq. ft. used in heating 
        """
        try:
            self.non_res_sqft = non_res.total_sqft_to_retrofit
            self.avg_gal_per_sqft = non_res.baseline_fuel_Hoil_consumption/ \
                                                            self.non_res_sqft
        except (ZeroDivisionError, AttributeError):
            self.avg_gal_per_sqft = 0
        
    def calc_heat_displaced_sqft (self):
        """Calculates the sqarefootage for which biomass will displace heating 
        oil as the heating fuel
        
        Attributes
        ----------
        heat_displaced_sqft : float
            Square footage assumed to be heated by biomass.
        """
        percent = \
            (self.cd['assumed percent non-residential sqft heat displacement']\
            /100.0)
        self.heat_displaced_sqft = self.non_res_sqft * percent
            
        
    def calc_energy_output (self):
        """Calculate the net and monthly energy output of heating oil.
        
        Attributes
        ----------
        average_net_energy_output : float
            averge energy output of heating oil(mmbtu/sq. ft./hr).
        peak_monthly_energy_output : float
            peak energy out put for a month (mmbtu/sq. ft./hr)
        """
        self.average_net_energy_output = self.avg_gal_per_sqft * \
                                    ((constants.mmbtu_to_gal_HF ** -1) * 1E6 /\
                                    constants.hours_per_year) * \
                                    self.cd['heating oil efficiency']
        self.peak_monthly_energy_output = self.average_net_energy_output * 12 *\
                                self.comp_specs['peak month % of total']
        
    def calc_max_boiler_output (self, efficiency):
        """Calculate the max boiler output.
        
        Parameters
        ----------
        efficiency : float
            Efficiency of biomass fuel.
            
        Attributes
        ----------
        max_boiler_output_per_sf : float
            boiler energy output per squarefoot (mmbtu/sq. ft.)
        max_boiler_output_per : float
            boiler energy output (mmbtu/hr)
        """
        self.max_boiler_output_per_sf = \
            float(self.peak_monthly_energy_output) / efficiency
        self.max_boiler_output = self.max_boiler_output_per_sf * \
                                    self.heat_displaced_sqft
        
    def calc_biomass_fuel_consumed (self, capacity_factor):
        """Calculate biomass fuel consumed
        
        Parameters
        ----------
        capacity_factor : float
            TODO:
            
        Attributes
        ----------
        biomass_fuel_consumed : float
            biomass fuel conusmed (units/year)
        """
        self.biomass_fuel_consumed = capacity_factor * self.max_boiler_output *\
                                     constants.hours_per_year /\
                                     self.comp_specs['energy density']
                                             
    def calc_diesel_displaced (self):
        """Calculate the disel of set by biomass
        
        Attributes
        ----------
        heat_diesel_displaced : float
            heating fuel displaced (gal/year)
        """
        self.heat_diesel_displaced = self.biomass_fuel_consumed * \
                                     self.comp_specs['energy density'] * \
                                     (constants.mmbtu_to_gal_HF / 1e6)
        
    def calc_maintainance_cost(self):
        """Calculate the maintanence costs placeholder
        
        Attributes
        ----------
        maintenance_cost : float
            set to zero
        """
        self.maintenance_cost = 0
        
    def calc_proposed_biomass_cost (self, price):
        """Calcualte cost of biomass fuel.
        
        Attributes
        ----------
        proposed_biomass_cost : Array of floats
            proposed biomass cost ($/year)
        """
        self.proposed_biomass_cost = price * self.biomass_fuel_consumed + \
                        self.maintenance_cost
        
    def calc_displaced_heating_oil_price (self):
        """
            calculate cost of displaced diesel
        """
        price = (self.diesel_prices + self.cd['heating fuel premium'])
        self.displaced_heating_oil_price = price * self.heat_diesel_displaced 
        #~ print 'self.displaced_heating_oil_price'
        #~ print self.displaced_heating_oil_price
    
    def run (self, scalers = {'capital costs':1.0}):
        """
        run the forecast model
        
        pre:
            self.cd should be the community library from a community data object
        post:
            TODO: define output values. 
            the model is run and the output values are available
        """
        pass
        
        # Make this do stuff
    def calc_capital_costs (self):
        """Caclulate the capital costs placeholder.
        """
        pass
        
    
    # Make this do stuff
    def calc_annual_electric_savings (self):
        """Set electric savings to zero as there are none.
        
        Attributes
        ----------
        annual_electric_savings : float
            set to zero
        """
        self.annual_electric_savings = 0
        
        
    # Make this do sruff. Remember the different fuel type prices if using
    def calc_annual_heating_savings (self):
        """Calcluate the annual heating savings
        
        Attributes
        ----------
        annual_heating_savings : Array, Floats
            savings in heating cost ($/year)
        """
        self.annual_heating_savings = self.displaced_heating_oil_price -\
                                      self.proposed_biomass_cost 
        
    def get_fuel_total_saved (self):
        """Get total fuel saved
        
        Returns
        ------- 
        float
            the total fuel saved in gallons
        """
        return self.heat_diesel_displaced
                                
    def get_total_enery_produced (self):
        """Get total energy produced
        
        Returns
        ------- 
        float
            the total energy produced
        """
        return self.biomass_fuel_consumed * self.comp_specs['energy density']/ 1e6

    def save_component_csv (self, directory):
        """Save the component output csv in directory, place holder

        Parameters
        ----------
        directory : path
            output directory

        """
        if not self.was_run:
            return
        
        fuel_consumed_key = self.component_name + \
                            ': Proposed ' + self.biomass_type \
                            + " Consumed (" + self.units + ")"
        eng_density_key = self.component_name + \
                            ": Energy Density (Btu/" + self.units + ")"
        years = np.array(range(self.project_life)) + self.start_year
    
        df = DataFrame({
                "Community": self.cd['name'],
                self.component_name + \
                    ": Maximum Boiler Output (Btu/hour)": 
                                            self.max_boiler_output,
                self.component_name + \
                    ': Heat Displacement square footage (Sqft)':
                                            self.heat_displaced_sqft,
                eng_density_key:            self.comp_specs['energy density'],
                fuel_consumed_key:          self.biomass_fuel_consumed,
                self.component_name + \
                    ': Price ($/' + self.units + ')': 
                                            self.heat_displaced_sqft,
                self.component_name + \
                    ": Displaced Heating Oil (gallons)": 
                                            self.heat_diesel_displaced,
                self.component_name + \
                    ": Project Capital Cost ($/year)": 
                                            self.get_capital_costs(),
                self.component_name + \
                    ": Total Cost Savings ($/year)": 
                                            self.get_total_savings_costs(),
                self.component_name + \
                    ": Net Benefit ($/year)": 
                                            self.get_net_benefit(),
                       }, years)

        order = ["Community", 
                self.component_name +": Maximum Boiler Output (Btu/hour)",
                eng_density_key, 
                fuel_consumed_key,
                self.component_name +": Displaced Heating Oil (gallons)", 
                self.component_name +": Project Capital Cost ($/year)",
                self.component_name +": Total Cost Savings ($/year)", 
                self.component_name +": Net Benefit ($/year)"]
                
        fname = os.path.join(directory,
                                self.cd['name'] + '_' +\
                                self.component_name.lower().replace('(','').\
                                replace(')','') + "_output.csv")
        fname = fname.replace(" ","_")
    
        # save to end of project(actual lifetime)
        df[order].ix[:self.actual_end_year].to_csv(fname, index_label="year")
