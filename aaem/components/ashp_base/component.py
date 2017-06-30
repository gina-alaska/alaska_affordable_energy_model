"""
Air Source Heat Pumps - Base component body
-------------------------------------------

"""
import numpy as np
from pandas import DataFrame, concat
import os


from aaem.components.annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import Diagnostics
import aaem.constants as constants
from config import COMPONENT_NAME, UNKNOWN

class ASHPBase (AnnualSavings):
    """Air source heat pump base of the Alaska Affordable Energy Model: Base component
    does nothing on it's own.

    Parameters
    ----------
    community_data : CommunityData
        CommunityData Object for a community
    forecast : Forecast
        forecast for a community
    diagnostics : diagnostics, optional
        diagnostics for tracking error/warning messages
    prerequisites : dictionary of components, optional
        none required

    Attributes
    ----------
    diagnostics : diagnostics
        for tracking error/warning messages
        initial value: diag or new diagnostics object
    forecast : forecast
        community forecast for estimating future values
        initial value: forecast
    cd : dictionary
        general data for a community.
        Initial value: 'community' section of community_data
    comp_specs : dictionary
        component specific data for a community.
        Initial value: 'ASHP Base' section of community_data

    See also
    --------
    aaem.community_data :
        community data module, see information on CommunityData Object
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
        community_data : CommunityData
            CommunityData Object for a community
        forecast : Forecast
            forecast for a community
        diagnostics : diagnostics, optional
            diagnostics for tracking error/warning messages
        prerequisites : dictionary of components, optional
            prerequisite component data, None

        """
        self.diagnostics = diag
        if self.diagnostics == None:
            self.diagnostics = diagnostics()
        self.forecast = forecast
        self.cd = community_data.get_section('community')

        try:
            self.comp_specs = community_data.get_section(self.component_name)
        except AttributeError:
            self.comp_specs = community_data.get_section(COMPONENT_NAME)

        self.set_project_life_details(
            self.comp_specs["start year"],
            self.comp_specs["lifetime"]
        )

        self.ashp_sector_system = "N/a"

        ### ADD other initialization stuff
        self.load_prerequisite_variables(prerequisites)
        self.regional_multiplier = \
                community_data.get_item('community',
                'regional construction multiplier'
                )

    def load_prerequisite_variables (self, comps):
        """Load variables from prerequisites, placeholder for child
        components if needed

        Parameters
        ----------
        comps : Dict
            Dictionary of components
        """
        # written in child classes
        pass

    def calc_cop_per_month (self):
        """calculate the coefficient of performance (COP) per month
        COP = output/input

        Attributes
        ----------
        monthly_value_table: DataFrame
            DataFrame of monthly values related to ASHP systems
        """
        #find m & b from performance data
        temp = self.comp_specs['performance data']['Temperature']
        cop = self.comp_specs['performance data']['COP']
        m, b = np.polyfit(temp,cop,1)
        #~ print m, b
        # apply to months
        mtk = ['Avg. Temp (F) JUL','Avg. Temp (F) AUG','Avg. Temp (F) SEP',
               'Avg. Temp (F) OCT','Avg. Temp (F) NOV','Avg. Temp (F) DEC',
               'Avg. Temp (F) JAN','Avg. Temp (F) FEB','Avg. Temp (F) MAR',
               'Avg. Temp (F) APR','Avg. Temp (F) MAY','Avg. Temp (F) JUN']
        #~ print self.comp_specs['data']
        monthly_temps = self.comp_specs['data'].ix[mtk].astype(float)

        monthly_temps = monthly_temps.T

        for c in monthly_temps.columns:
            mon = c[-3:]
            monthly_temps[mon] = monthly_temps[c]
            del monthly_temps[c]

        monthly_temps = monthly_temps.T
        monthly_temps['Temperature'] =  monthly_temps["value"]
        del monthly_temps['value']

        monthly_cop =  m * monthly_temps + b

        maxes = monthly_temps >= max(temp)
        monthly_cop[maxes] = max(cop)
        zeros =  monthly_temps < min(temp)
        monthly_cop[zeros] = 0
        monthly_cop['COP'] = monthly_cop['Temperature']
        del monthly_cop['Temperature']

        self.monthly_value_table = concat([monthly_temps,monthly_cop],axis = 1)
        del monthly_temps
        del monthly_cop
        #~ print self.monthly_value_table


    def calc_heat_energy_produced_per_year (self):
        """Calculate the heat energy produced per year by ASHP system
        (TODO: Double check definition) defined in child components
        """
        #~ self.heat_energy_produced_per_year = None
        pass # depends on child to implement

    def calc_heat_energy_produced_per_month (self):
        """calc the mmbtu consumed per month

        Attributes
        ----------
        monthly_value_table['mmbtu/mon']
            mmbtu per month is added to the monthly_value_table
        """
        # mmbty/mon = mmbtu/year * montly%s
        mtk = ['% Heating Load JUL','% Heating Load AUG','% Heating Load SEP',
               '% Heating Load OCT','% Heating Load NOV','% Heating Load DEC',
               '% Heating Load JAN','% Heating Load FEB','% Heating Load MAR',
               '% Heating Load APR','% Heating Load MAY','% Heating Load JUN']
        monthly_percents = self.comp_specs['data'].ix[mtk].astype(float).T
        for c in monthly_percents.columns:
            mon = c[-3:]
            monthly_percents[mon] = monthly_percents[c]
            del monthly_percents[c]
        monthly_percents = monthly_percents.T
        self.monthly_value_table['% of total heating'] = monthly_percents
        del monthly_percents

        self.monthly_value_table['mmbtu/mon'] = \
                self.heat_energy_produced_per_year *\
                self.monthly_value_table['% of total heating']

        #~ print self.monthly_value_table

    def calc_electric_energy_input_per_month (self):
        """calculate kWh produced per month

        Attributes
        ----------
        monthly_value_table['kWh consumed']
            adds kWh consumed per month to the monthly_value_table
        """
        # mmbtu/mon -> kwh/mon / COP
        #~ idx = self.monthly_value_table['COP'] > 0

        self.monthly_value_table['kWh consumed'] = \
                (self.monthly_value_table['mmbtu/mon']*\
                constants.mmbtu_to_kWh / \
                self.monthly_value_table['COP'] ).replace([np.inf,-np.inf],0)
        pass

    def calc_heating_oil_consumed_per_month (self):
        """calculate heating oil consumed per month

        Attributes
        ----------
        monthly_value_table['Heating Oil Consumed (gal)']
            adds kWh consumed per month to the monthly_value_table
        """
        # per month if cop = 0 : consumption mmbtu -> gal / eff
        idx = self.monthly_value_table['COP'] == 0

        self.monthly_value_table["Heating Oil Consumed (gal)"] = 0
        self.monthly_value_table["Heating Oil Consumed (gal)"][idx] = \
                self.monthly_value_table['mmbtu/mon']*\
                constants.mmbtu_to_gal_HF /\
                self.cd['heating oil efficiency']

    def calc_heating_oil_saved_per_month (self):
        """calculate heating oil saved per month

        Attributes
        ----------
        monthly_value_table['Heating Oil saved(gal)']
            adds kWh consumed per month to the monthly_value_table
        """
        # for each month mmbtu -> gal /eff - heating_oil_consumed
        #~ idx = self.monthly_value_table['COP'] == 0

        self.monthly_value_table["Heating Oil Saved (gal)"] = \
                self.monthly_value_table['mmbtu/mon']*\
                constants.mmbtu_to_gal_HF /\
                self.cd['heating oil efficiency'] - \
                self.monthly_value_table["Heating Oil Consumed (gal)"]

    def calc_electric_consumption (self):
        """calculate the electric consumption for the year

        Attributes
        ----------
        electric_consumption: float
            estimated electric consumption for a year
        """
        self.electric_consumption = \
            self.monthly_value_table['kWh consumed'].sum()

    def calc_heating_oil_saved (self):
        """Calculates heating oil saved per year with ASHP system

        Attributes
        ----------
        heating_oil_saved : float
            Savings  in heating oil from ASHP system per year
        """
        self.heating_oil_saved = \
            self.monthly_value_table['Heating Oil Saved (gal)'].sum()

    def calc_average_cop (self):
        """Calculate average yearly coefficient of power(cop) of ASHP system

        Attributes
        ----------
        average_cop : float
            average yearly coefficient of power(cop) of ASHP system
        """
        self.monthly_value_table['mmbtu/mon'].sum()
        consumed_Hoil =\
            self.monthly_value_table['Heating Oil Consumed (gal)'].sum()

        factor_1 = (self.monthly_value_table['COP'] *\
                   self.monthly_value_table['% of total heating']).sum()
        factor_2 = self.monthly_value_table['% of total heating']\
                                    [self.monthly_value_table['COP'] > 0].sum()

        self.average_cop = factor_1 / factor_2

    def calc_baseline_heating_oil_cost (self):
        """Calculate base line heating fuel cost

        Attributes
        ----------
        baseline_heating_oil_cost: array of floats
            cost of heating oil per year ($/gal)
        """
        self.get_diesel_prices()
        price = self.diesel_prices + self.cd['heating fuel premium']
        self.baseline_heating_oil_cost = self.heating_oil_saved * price

    def calc_proposed_ashp_operation_cost (self):
        """Calculate cost of operation for new ASHP system

        Attributes
        ----------
        proposed_ashp_operation_cos: array of floats
            cost of electricity for ASHP operation per year ($/kWh)
        """
        self.get_electricity_prices()
        #~ print self.electricity_prices, self.electric_consumption
        cost = self.electricity_prices * self.electric_consumption +\
                                       self.comp_specs["o&m per year"]
        self.proposed_ashp_operation_cost = cost.tolist()

    def calc_ashp_system_parameters (self):
        """Calls each of the functions for calculating the ASHP
        operation parameters
        """
        self.calc_cop_per_month()
        #~ self.calc_heat_energy_produced_per_year()
        self.calc_heat_energy_produced_per_month()
        self.calc_electric_energy_input_per_month()
        self.calc_heating_oil_consumed_per_month()
        self.calc_heating_oil_saved_per_month()
        self.calc_electric_consumption()
        self.calc_heating_oil_saved()
        self.calc_average_cop()

    def run (self, scalers = {'capital costs':1.0}):
        """run placeholder for child components

        Parameters
        ----------
        scalers: dictionary of valid scalers, optional
            Scalers to adjust normal run variables.
            See note on accepted  scalers

        Notes
        -----
            Accepted scalers: capital costs.
        """
        #~ self.calc_heat_energy_produced_per_year()
        #~ self.calc_ashp_system_parameters()
        #~ self.calc_baseline_heating_oil_cost()
        #~ self.calc_proposed_ashp_operation_cost()
        #~ print self.monthly_value_table
        #~ print self.electric_consumption
        #~ print self.heating_oil_saved
        #~ print self.average_cop
        #~ print self.baseline_heating_oil_cost
        #~ print self.proposed_ashp_operation_cost
        pass # depends on child to implement


    # Make this do stuff
    def calc_capital_costs (self):
        """sets capital costs to nan, placeholder for child components

        Attributes
        ----------
        capital_costs : float
            set to Nan
        """
        self.capital_costs = np.nan


    # Make this do stuff
    def calc_annual_electric_savings (self):
        """electric savings placeholder for child components

        Attributes
        ----------
        annual_electric_savings : float
            set to zero
        """
        self.annual_electric_savings = 0


    # Make this do stuff. Remember the different fuel type prices if using
    def calc_annual_heating_savings (self):
        """calculate heating savings per year

        Attributes
        ----------
        annual_heating_savings : float
            base heating cost minus the proposed ashp operation cost
        """
        self.annual_heating_savings = self.baseline_heating_oil_cost - \
                                      self.proposed_ashp_operation_cost

    def get_fuel_total_saved (self):
        """Get total fuel saved

        Returns
        -------
        float
            the total fuel saved in gallons
        """
        #~ eff = self.cd["diesel generation efficiency"]
        #~ proposed = self.electric_consumption/eff
        return self.heating_oil_saved #- proposed

    def get_total_energy_produced (self):
        """Get total energy produced

        Returns
        -------
        float
            the total energy produced
        """
        return self.heat_energy_produced_per_year #+ \
                #~ self.electric_consumption * (1/constants.mmbtu_to_kWh)


    def save_component_csv (self, directory):
        """Save the component output csv in directory, place holder

        Parameters
        ----------
        directory : path
            output directory

        """
        pass
