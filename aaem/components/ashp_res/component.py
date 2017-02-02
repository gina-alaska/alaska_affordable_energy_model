"""
Air Source Heat Pumps - Residential component body
--------------------------------------------------

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

import aaem.components.ashp_base as ashp_base

class ASHPResidential (ashp_base.ASHPBase):
    """Non-Residential ASHP of the Alaska Affordable Eenergy Model

    Parameters
    ----------
    commnity_data : CommunityData
        CommintyData Object for a community
    forecast : Forecast
        forcast for a community 
    diagnostics : diagnostics, optional
        diagnostics for tracking error/warining messeges
    prerequisites : dictionary of components, optional
        'Non-residential Energy Efficiency' component is a required prerequisite
        for this component
        
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
        Initial value: 'Non-Residential ASHP' section of community_data
        
    See also
    --------
    aaem.community_data : 
        community data module, see for information on CommintyData Object
    aaem.forecast : 
        forecast module, see for information on Forecast Object
    aaem.diagnostics :
        diagnostics module, see for information on diagnostics Object
    aaem.components.residential :
        'residential Energy Efficiency' component is a required prerequisite
        for this component

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
        self.component_name = COMPONENT_NAME
        super(ASHPResidential, self).__init__(community_data, forecast,
                                                    diag, prerequisites)

        self.reason = "OK"
                        
        ### ADD other intiatzation stuff
        self.ashp_sector_system = "residential"
        
    def load_prerequisite_variables (self, comps):
        """Loads square footage of Residential buildings and average 
        heating consumption per sqft(gal heating fuel/sqft)
        
        Parameters
        ----------
        comps: Dictionary of components
            Dictionary of components, needs 'Non-residential Energy Efficiency'
            key
        
        Attributes
        ----------
        res_sqft : float
            Total square footage that may be refit of residental buildings,
            Will be set to 0 if a value cannot be found in 
            'Residential Energy Efficiency' component
        avg_gal_per_sqft : float
            Heating fuel consumption per square foot. Will be set to 0 if a,
            value cannot be found in 'Residential Energy Efficiency'
            component
            
        Raises
        ------
            KeyError
                if 'Non-residential Energy Efficiency' component not found.
        
        """
        tag = self.cd['name'].split('+')
        if len(tag) > 1 and tag[1].split('_')[0] != 'ASHP_res':
            return 
        res = comps['Residential Energy Efficiency']
        self.pre_ashp_heating_oil_used =  res.init_HF
        self.pre_ashp_heating_electricty_used = res.init_kWh
        self.num_houses = res.init_HH
        self.precent_heated_oil = res.comp_specs['data'].T["Fuel Oil"]
        self.precent_heated_elec = res.comp_specs['data'].T["Electricity"]
        #~ print self.pre_ashp_heating_oil_used
        #~ print self.num_houses
        
        
    def calc_heat_energy_produced_per_year (self):
        """Calculate the heat energy produced per year by ASHP system 
        (TODO: Double check defintion)
        
        Attributes
        ----------
        heat_displaced_sqft : float
            Building Square footage that will be heated by ASHP
        heat_energy_produced_per_year : float
            Heat energe produced per year in BTU
        """
        self.heat_energy_produced_per_year = \
                        self.pre_ashp_heating_oil_used * \
                        self.cd["heating oil efficiency"]*\
                        (1/constants.mmbtu_to_gal_HF)
        #~ print self.heat_energy_produced_per_year
       
    def calc_electric_heat_energy_reduction (self):
        """calculate electric heat energy reduction kWh
        
        Attributes
        ----------
        electric_heat_energy_reduction : float
            reduction in energy used for heating
        
        """
        self.electric_heat_energy_reduction = \
                        self.pre_ashp_heating_electricty_used/ self.average_cop
        
    def calc_electric_heat_energy_savings (self):
        """calculate heat energy savings in $/year
        
        Attributes
        ----------
        electric_heat_energy_savings: array of floats
            savings from 
        """
        self.electric_heat_energy_savings = \
                        self.electric_heat_energy_reduction * \
                        self.electricity_prices
        self.electric_heat_energy_savings = \
                        self.electric_heat_energy_savings.values.T[0]
        #~ print self.electric_heat_energy_savings
        
        
    def run (self, scalers = {'capital costs':1.0}):
        """Runs the component. The Annual Total Savings,Annual Costs, 
        Annual Net Benefit, NPV Benefits, NPV Costs, NPV Net Benefits, 
        Benefit Cost Ratio, Levelized Cost of Energy, 
        and Internal Rate of Return will all be calculated. 
        
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
        if len(tag) > 1 and tag[1] != 'ASHP_res':
            self.run = False
            self.reason = "Not a residential air source heat pump project."
            return 
        
        if self.cd["model heating fuel"]:
            self.calc_heat_energy_produced_per_year()
            self.calc_ashp_system_pramaters()
            self.calc_electric_heat_energy_reduction()
            
        if self.cd["model financial"]:
            self.calc_baseline_heating_oil_cost()
            self.calc_proposed_ashp_operation_cost()
            
            self.calc_capital_costs()
            
            self.calc_annual_electric_savings()
            self.calc_annual_heating_savings()
            
            self.calc_electric_heat_energy_savings()
            #~ print self.electric_heat_energy_savings
            self.annual_heating_savings += self.electric_heat_energy_savings
            
            self.calc_annual_total_savings()
            self.calc_annual_costs(self.cd['interest rate'],
                                            scalers['capital costs'])
            self.calc_annual_net_benefit()
            self.calc_npv(self.cd['discount rate'], self.cd["current year"])
        #~ print 'self.monthly_value_table'
        #~ print self.monthly_value_table
        #~ print 'self.electric_consumption',self.electric_consumption
        #~ print 'self.heating_oil_saved',self.heating_oil_saved
        #~ print 'self.average_cop',self.average_cop
        #~ print 'self.baseline_heating_oil_cost',self.baseline_heating_oil_cost
        #~ print 'self.proposed_ashp_operation_cost',self.proposed_ashp_operation_cost
        #~ print self.capital_costs
        #~ print self.benefit_cost_ratio
            self.calc_levelized_costs(self.proposed_ashp_operation_cost)
        else:
            self.reason = "Financial modeling disabled for this community."

    def calc_capital_costs (self):
        """Calculate or Load the project Captial Costs.
        
        Attributes
        ----------
        total_cap_required : float
            total ASHP capacity provided.
        capital_costs : float
            caclulated or loaded captial costs for heat recovery
        """
        heating_oil = ((self.pre_ashp_heating_oil_used/self.num_houses)*\
                        self.cd["heating oil efficiency"]) / \
                        constants.mmbtu_to_gal_HF *1e6/ \
                        constants.hours_per_year
        electric_heat = (self.pre_ashp_heating_electricty_used/self.num_houses)\
                        / constants.mmbtu_to_kWh *1e6/ constants.hours_per_year
                        
        average_btu_per_hr =  heating_oil + electric_heat
        
        peak_monthly_btu_hr_hh = \
            float(float(self.comp_specs['data'].ix['Peak Month % of total']) *\
            average_btu_per_hr * 12 / \
            (self.precent_heated_oil+self.precent_heated_elec))
            
        self.peak_monthly_btu_hr_hh = peak_monthly_btu_hr_hh
        
        
        min_tem = float(self.comp_specs['data']
                                .ix['Minimum Temp'].astype(float))
                                
        temps = self.comp_specs['perfromance data']['Temperature']
        
        percent = self.comp_specs['perfromance data']\
                                    ['Percent of Total Capacity']
                                    
        percent_of_total_cap = min(percent)
        if min_tem > min(temps):
            m, b = np.polyfit(temps,percent,1) 
            percent_of_total_cap = m * min_tem + b
        percent_of_total_cap = min(1.0, percent_of_total_cap)
        
        
        self.total_cap_required = 2 * self.peak_monthly_btu_hr_hh /\
                                        percent_of_total_cap
        ratio = self.total_cap_required  / self.comp_specs["btu/hrs"]
        if ratio < 1:
            self.diagnostics.add_note(self.component_name,
                "ratio of peak mothly btu/hr/hh to btu/hrs is 1 ")
            ratio = 1.0

        self.capital_costs = self.num_houses * \
                             round((ratio) * \
                             self.comp_specs["cost per btu/hrs"])* \
                             self.regional_multiplier

    def save_component_csv (self, directory):
        """Save the component output csv in directory
        
        Parameters
        ----------
        directory : path
            output directory
            
        """
        if not self.run:
            return
        years = np.array(range(self.project_life)) + self.start_year
    
        try:
            val = self.peak_monthly_btu_hr_hh
            prices = self.electricity_prices.values.T[0].tolist()
        except AttributeError:
            val = 0
            prices = 0
            
        #~ print prices
        df = DataFrame({
                "Community": self.cd['name'],
                "Residential ASHP: Average Coefficient of Performance (COP)": self.average_cop,
                'Residential ASHP: Number Houses': self.num_houses,
                'Residential ASHP: Peak Household Monthly (Btu/hour)': val,
                'Residential ASHP: Electricity Price ($/kWh)':prices,
                'Residential ASHP: kWh consumed per year (kWh/year)':self.electric_consumption,
                "Residential ASHP: Displaced Heating Oil (gallons/year)": self.heating_oil_saved,
                "Residential ASHP: Project Capital Cost ($/year)": self.get_capital_costs(),
                "Residential ASHP: Total Cost Savings ($/year)": self.get_total_savings_costs(),
                "Residential ASHP: Net Benefit ($/year)": self.get_net_benefit(),
                       }, years)

        order = ["Community", 
                 "Residential ASHP: Average Coefficient of Performance (COP)",
                 'Residential ASHP: Number Houses', 
                 'Residential ASHP: Peak Household Monthly (Btu/hour)',
                 'Residential ASHP: Electricity Price ($/kWh)', 
                 'Residential ASHP: kWh consumed per year (kWh/year)',
                 "Residential ASHP: Displaced Heating Oil (gallons/year)", 
                 "Residential ASHP: Project Capital Cost ($/year)",
                 "Residential ASHP: Total Cost Savings ($/year)", 
                 "Residential ASHP: Net Benefit ($/year)"]
                
        fname = os.path.join(directory,
                                   self.cd['name'] + '_' +\
                                   self.component_name.lower() + "_output.csv")
        fname = fname.replace(" ","_")
        
        # save to end of project(actual lifetime)
        df[order].ix[:self.actual_end_year].to_csv(fname, index_label="Year")
        fname = os.path.join(directory,
                           self.cd['name']+'_'+\
                           self.component_name.lower() + "_montly_table.csv")
        fname = fname.replace(" ","_")
        
        self.monthly_value_table.to_csv(fname)
