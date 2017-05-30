"""
Hydropower component body
-------------------------

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

class Hydropower (AnnualSavings):
    """Hydropower component of the Alaska Affordable Eenergy Model
    
    .. note::

       Component Requires an existing project for a communty to be run to 
       completion.

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
        Initial value: 'Hydropower' section of community_data
        
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
            prerequisite component data

        """
        self.diagnostics = diag
        if self.diagnostics == None:
            self.diagnostics = diagnostics()
        self.forecast = forecast
        self.cd = community_data.get_section('community')
        #~ print self.cd
        self.comp_specs = community_data.get_section(COMPONENT_NAME)
        #~ print self.comp_specs
        self.component_name = COMPONENT_NAME
        
        ## moved to preprocessor
        #~ try:
            #~ self.comp_specs["start year"] = self.cd['current year'] + \
            #~ self.comp_specs['expected years to operation']
        #~ except TypeError:
            #~ self.comp_specs["start year"] = self.cd['current year']
        self.set_project_life_details(
            self.comp_specs["start year"],
            self.comp_specs["lifetime"]
        )
        
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
        if len(tag) > 1 and tag[1] != 'hydro':
            self.run = False
            self.reason = "Not a hydropower project."
            return 
        
        if self.comp_specs["name"] == 'none':
            self.run = False
            self.reason = "No project data."
            return 
        
        if not self.cd["model electricity"]:
            self.run = False
            self.reason = "Electricity must be modeled to analyze hydropower."+\
                                " It was not for this community."
            return 
            
        try:
            self.calc_average_load()
            self.calc_generation_proposed()
        except AttributeError as e:
            self.diagnostics.add_warning(self.component_name, 
                            "could not be run")
            self.run = False
            self.reason = "Could not calculate average load, or " + \
                            "proposed generation."
            return
            
        if self.load_offset_proposed is None:
            self.run = False
            self.reason = "Hydropower" + \
                " requires that at least a reconnaissance-level heat recovery"+\
                " study has been completed for the community."
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
                    (self.cd['diesel generator o&m cost percent'] / 100.0)
        
            self.calc_levelized_costs(o_m)
            
    def calc_average_load (self):
        """Calculate the average load of the system.
            
        Attributes
        ----------
        generation: float
            generation values in first year of project (kWh)
        average_load: float
            averge diesel generation load in first year of project (kW)
        
        """
        self.generation = self.forecast.generation['generation diesel']\
                                                            [self.start_year]
        self.average_load = \
                self.forecast.yearly_average_diesel_load.ix[self.start_year]
        #~ print 'self.average_load',self.average_load
 
    def calc_generation_proposed (self):
        """Calulate the proposed generation for Hydropower.
        
        Attributes
        ----------
        load_offest_proposed : float
            hydropower load offset (kW)
        gross_generation_proposed : float
            hydropower generation proposed (kWh/yr)
        net_generation_proposed : float
            net hydropower generation(kWh/yr)
        """
        if self.comp_specs['proposed capacity'] == UNKNOWN:
            self.load_offset_proposed = None
            self.gross_generation_proposed = None
            self.net_generation_proposed = None
            
        else:
            self.load_offset_proposed = \
                   float( self.comp_specs['proposed capacity'])
            self.gross_generation_proposed = \
                    float(self.comp_specs['proposed generation'])
                                        
            tansmission_losses = (self.cd['line losses'] / 100.0) *\
                self.gross_generation_proposed
            exess_energy = \
                (self.gross_generation_proposed - tansmission_losses) * \
                (self.cd['percent excess energy'] / 100.0)
            self.percent_excess_energy = exess_energy / \
                self.gross_generation_proposed   
            
            self.net_generation_proposed = self.gross_generation_proposed -\
                                           tansmission_losses -\
                                           exess_energy
            #~ print  self.net_generation_proposed
            if self.net_generation_proposed > self.generation:
                self.net_generation_proposed = self.generation
                                           
        #~ print 'self.load_offset_proposed', self.load_offset_proposed
        #~ print 'self.gross_generation_proposed', self.gross_generation_proposed
        #~ print 'self.net_generation_proposed', self.net_generation_proposed


    def calc_heat_recovery (self):
        """Caclulate heat recovery values used by component.
        
        Attributes
        ----------
        generation_diesel_reduction : float
            (gal)
        lost_heat_recovery : float
            (gal)
        generation_diesel_reduction : float
            (gal)
        """
        # %
       
        captured_percent = self.percent_excess_energy * \
            (self.cd['percent excess energy capturable'] / 100.0)
        
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
                (self.comp_specs['percent heat recovered'] / 100.0)
        
        #~ print 'self.captured_energy', self.captured_energy
        #~ print 'self.lost_heat_recovery', self.lost_heat_recovery

    # Make this do stuff
    def calc_capital_costs (self):
        """Calculate the capital costs.
            
        Attributes
        ----------
        capital_costs : float
             total cost of improvments ($), calculated from transmission and
             generagion costs
        """
        transmission_cost = \
            float(self.comp_specs['transmission capital cost'])
        generator_cost = \
            float(self.comp_specs['generation capital cost'])
        
        self.capital_costs = transmission_cost + generator_cost
        #~ print 'self.capital_costs', self.capital_costs
        
    
    # Make this do stuff
    def calc_annual_electric_savings (self):
        """Calculate annual electric savings created by the project.
            
        Attributes
        ----------
        annual_electric_savings : np.array
            electric savings ($/year) are the difference in the base 
        and proposed fuel costs
        """
        #~ print self.capital_costs, (self.comp_specs['percent o&m'] / 100.0)
        proposed_generation_cost = self.capital_costs * \
            (self.comp_specs['percent o&m'] / 100.0)
                        
        
        maintianice_cost = self.net_generation_proposed * \
            (self.cd['diesel generator o&m cost percent'] /100.0)
        
        price = self.diesel_prices
        
        fuel_cost = price * self.generation_diesel_reduction
        
        baseline_generation_cost = fuel_cost + maintianice_cost
        
        self.annual_electric_savings = baseline_generation_cost - \
                                        proposed_generation_cost 
        #~ print 'self.annual_electric_savings', self.annual_electric_savings
        
        
    # Make this do sruff. Remember the different fuel type prices if using
    def calc_annual_heating_savings (self):
        """Calculate annual heating savings created by the project.
            
        Attributes
        ----------
        annual_heating_savings : np.array
            heating savings ($/year) 
        """
        price = (self.diesel_prices + self.cd['heating fuel premium'])
        
        self.annual_heating_savings = \
                (self.captured_energy - self.lost_heat_recovery) *\
                price
        #~ print 'self.annual_heating_savings', self.annual_heating_savings
        
    def get_fuel_total_saved (self):
        """Get total fuel saved.
        
        Returns 
        -------
        float
            the total fuel saved in gallons
        """
    
        return (self.captured_energy - self.lost_heat_recovery) + \
                self.generation_diesel_reduction
    
    def get_total_enery_produced (self):
        """Get total energy produced.
        
        Returns
        ------- 
        float
            the total energy produced
        """
        return self.net_generation_proposed
        
    def save_component_csv (self, directory):
        """Save the component output csv in directory.

        Parameters
        ----------
        directory : path
            output directory

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
