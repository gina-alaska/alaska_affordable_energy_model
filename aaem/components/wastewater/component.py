"""
Water Wastewater Component Body
-------------------------------

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


class WaterWastewaterSystems (AnnualSavings):
    """Water/wastewater systems of the Alaska Affordable Energy Model. This
    module estimates potential improvements in heating and electrical
    efficiency to water and wastewater systems. Consumption and savings are
    calculated based on system type, population, and heating degree days
    per year for a community. Project costs are based on audits, or estimated
    by the community size.

    Parameters
    ----------
    community_data : CommunityData
        CommunityData Object for a community
    forecast : Forecast
        forecast for a community
    diagnostics : diagnostics, optional
        diagnostics for tracking error/warning messages
    prerequisites : dictionary of components, optional
        prerequisite component data this component has no prerequisites
        leave empty

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
        Initial value: 'water wastewater' section of community_data

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
        community_data : CommunityData
            CommunityData Object for a community
        forecast : Forecast
            forecast for a community
        diagnostics : diagnostics, optional
            diagnostics for tracking error/warning messages
        prerequisites : dictionary of components, optional
            prerequisite component data

        """
        self.component_name = COMPONENT_NAME

        self.diagnostics = diag
        if self.diagnostics == None:
            self.diagnostics = diagnostics()

        self.cd = community_data.get_section('community')
        self.comp_specs = community_data.get_section(COMPONENT_NAME)
        self.forecast = forecast

        self.set_project_life_details(
            self.comp_specs["start year"],
            self.comp_specs["lifetime"]
        )

        average = self.comp_specs['average refit cost']
        mult = community_data.get_item('community','regional construction multiplier')
        self.cost_per_person = average * mult

        self.hdd = self.cd["heating degree days"]

        self.pop = self.forecast.get_population(int(self.comp_specs['data']\
                                                           ['Year']))
        self.population_fc = self.forecast.get_population(self.start_year,
                                                                 self.end_year)

    def calc_annual_electric_savings (self):
        """Calculate annual electric savings created by the project.

        Attributes
        ----------
        annual_electric_savings : np.array
            electric savings ($/year) are the difference in the base
        and proposed fuel costs
        """
        self.calc_baseline_kWh_cost()
        self.calc_proposed_kWh_cost ()
        self.annual_electric_savings = self.baseline_kWh_cost - \
                                       self.proposed_kWh_cost

    def calc_baseline_kWh_cost (self):
        """Calculate Baseline electric cost.

        Attributes
        ----------
        baseline_generation_cost : np.array
            current cost of generation ($/year)
        """
        kWh_cost = self.cd["electric non-fuel prices"].\
                                            ix[self.start_year:self.end_year]
        kWh_cost = kWh_cost.T.values[0]
        self.elec_price = kWh_cost
        # kWh/yr*$/kWh
        self.baseline_kWh_cost = self.baseline_kWh_consumption * kWh_cost

    def calc_proposed_kWh_cost (self):
        """Calculate Proposed electric cost.

        Attributes
        ----------
        proposed_generation_cost : np.array
            current cost of generation ($/year)
        """
        kWh_cost = self.cd["electric non-fuel prices"].\
                                            ix[self.start_year:self.end_year]
        kWh_cost = kWh_cost.T.values[0]
        # kWh/yr*$/kWh
        self.proposed_kWh_cost = self.proposed_kWh_consumption * kWh_cost

    def calc_annual_heating_savings (self):
        """Calculate annual heating savings created by the project.

        Attributes
        ----------
        annual_heating_savings : np.array
            heating savings ($/year)
        """
        self.calc_proposed_HF_cost()
        self.calc_baseline_HF_cost()
        # $ / yr
        self.annual_heating_savings = self.baseline_HF_cost - \
            self.proposed_HF_cost

    def calc_proposed_HF_cost (self):
        """Calculate proposed HF cost.

        Attributes
        ----------
        proposed_HF_cost : np.array
            heating savings ($/year)
        """
        self.proposed_HF_cost = np.zeros(self.project_life)
        fuel_cost = self.diesel_prices + self.cd['heating fuel premium']# $/gal
        wood_price = self.cd['cordwood price']
        # are there ever o&m costs
        # $/gal * gal/yr = $/year
        self.proposed_HF_cost += \
                self.proposed_fuel_Hoil_consumption * fuel_cost +\
                self.proposed_fuel_biomass_consumption * wood_price

    def calc_baseline_HF_cost (self):
        """Calculate baseline HF cost.

        Attributes
        ----------
        baseline_HF_cost : np.array
            heating savings ($/year)
        """
        self.baseline_HF_cost = np.zeros(self.project_life)
        fuel_cost = self.diesel_prices + self.cd['heating fuel premium'] #$/gal
        self.hoil_price = fuel_cost
        wood_price = self.cd['cordwood price']
        # $/gal * gal/yr + $/cors * cord/yr= $/year
        self.baseline_HF_cost += \
                self.baseline_fuel_Hoil_consumption * fuel_cost +\
                self.baseline_fuel_biomass_consumption * wood_price

    def run (self, scalers = {'capital costs':1.0}):
        """Runs the component. The Annual Total Savings,Annual Costs,
        Annual Net Benefit, NPV Benefits, NPV Costs, NPV Net Benefits,
        Benefit Cost Ratio, Levelized Cost of Energy,
        and Internal Rate of Return will all be calculated. There must be a
        known Heat Recovery project for this component to run.

        Parameters
        ----------
        scalers: dictionary of valid scalers, optional
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
        tag = self.cd['file id'].split('+')

        self.was_run = True
        self.reason = "OK"

        if len(tag) > 1 and tag[1] != 'water-wastewater':
            self.was_run = False
            self.reason = "Not a water/wastewater project."
            return 
        #~ print self.comp_specs['data']['assumption type used']
        if self.comp_specs['data']['assumption type used'] == 'UNKNOWN':
            self.was_run = False
            self.reason = "Water/wastewater system type unknown."
            #~ print self.reason
            return 

        if self.cd["model electricity"]:
            self.calc_baseline_kWh_consumption()
            self.calc_proposed_kWh_consumption()
            self.calc_savings_kWh_consumption()

        if self.cd["model heating fuel"]:
            self.calc_baseline_HF_consumption()
            self.calc_proposed_HF_consumption()
            self.calc_savings_HF_consumption()

            #~ years = range(self.start_year,self.end_year)
            #~ self.forecast.add_heating_fuel_column(\
                        #~ "heating_fuel_water-wastewater_consumed [gallons/year]",
                         #~ years,
                         #~ self.baseline_HF_consumption*constants.mmbtu_to_gal_HF)
            #~ self.forecast.add_heating_fuel_column(\
                   #~ "heating_fuel_water-wastewater_consumed [mmbtu/year]", years,
                    #~ self.baseline_HF_consumption)

            #~ self.forecast.add_heat_demand_column(\
                        #~ "heat_energy_demand_water-wastewater [mmbtu/year]",
                     #~ years, self.baseline_HF_consumption)

        if self.cd["model financial"]:
            self.calc_capital_costs()

            self.get_diesel_prices()
            self.calc_annual_electric_savings()
            self.calc_annual_heating_savings()
            self.calc_annual_total_savings()

            self.calc_annual_costs(self.cd['interest rate'],
                                            scalers['capital costs'])
            self.calc_annual_net_benefit()
            self.calc_npv(self.cd['discount rate'], self.cd["current year"])
            self.calc_levelized_costs(0)
            #~ self.levelized_cost_of_energy['MMBtu'] *= .5
            #~ self.levelized_cost_of_energy['kWh'] *= .5


    def calc_baseline_kWh_consumption (self):
        """Calculate the baseline electric consumption.

        Attributes
        ----------
        baseline_kWh_consumption : np.array
            kWh/year values(floats) over the project lifetime
        """
        hdd_coeff = np.float64(self.comp_specs['data']['HDD kWh'])
        pop_coeff = np.float64(self.comp_specs['data']['pop kWh'])
        if not np.isnan(np.float64(self.comp_specs['data']['kWh/yr'])) and \
               np.float64(self.comp_specs['data']['kWh/yr']) != 0:
            self.baseline_kWh_consumption =\
                             np.float64(self.comp_specs['data']['kWh/yr'])+ \
                            ((self.population_fc - self.pop) * pop_coeff)
        else: #if not self.cd["w&ww_energy_use_known"]:


            self.baseline_kWh_consumption = \
                            (self.hdd * hdd_coeff + self.pop * pop_coeff) + \
                            ((self.population_fc - self.pop) * pop_coeff)

    def calc_baseline_HF_consumption (self):
        """Calculate the baseline Heating consumption.

        Attributes
        ----------
        baseline_fuel_biomass_consumption : np.array
            coord/year values(floats) over the project lifetime
        baseline_fuel_Hoil_consumption : np.array
            gal/year values(floats) over the project lifetime
        baseline_HF_consumption : np.array
            mmbtu/year values(floats) over the project lifetime
        """
        hdd_coeff = np.float64(self.comp_specs['data']['HDD HF'])
        pop_coeff = np.float64(self.comp_specs['data']['pop HF'])
        if not np.isnan(np.float64(self.comp_specs['data']['HF Used'])) and\
                np.float64(self.comp_specs['data']['HF Used']) != 0:
            self.baseline_HF_consumption = np.zeros(self.project_life)
            self.baseline_HF_consumption += \
                            np.float64(self.comp_specs['data']['HF Used']) +\
                    ((self.population_fc - self.pop) * pop_coeff)
        else:
            hr = self.comp_specs['data']["HR Installed"] == "TRUE"
            hr_coeff = 1.0
            if hr:
                hr_coeff =  self.comp_specs['heat recovery multiplier']
            self.baseline_HF_consumption = \
                    ((self.hdd * hdd_coeff+ self.pop * pop_coeff)  +\
                    ((self.population_fc - self.pop) * pop_coeff))* hr_coeff
        self.baseline_fuel_biomass_consumption = 0
        biomass = self.comp_specs['data']['Biomass'] == "TRUE"
        if biomass:
            self.baseline_fuel_biomass_consumption = \
                            self.baseline_HF_consumption / \
                            constants.mmbtu_to_gal_HF * constants.mmbtu_to_cords
            self.baseline_HF_consumption = 0


        # don't want to detangle that
        self.baseline_fuel_Hoil_consumption = self.baseline_HF_consumption

        self.baseline_HF_consumption = \
            self.baseline_fuel_Hoil_consumption/constants.mmbtu_to_gal_HF + \
            self.baseline_fuel_biomass_consumption/constants.mmbtu_to_cords

    def calc_proposed_kWh_consumption (self):
        """Calculate the proposed electric consumption.

        Attributes
        ----------
        proposed_kWh_consumption : np.array
            kWh/year values(floats) over the project lifetime
        """
        percent = 1 - (self.comp_specs['electricity refit reduction']/100.0)
        con = np.float64(self.comp_specs['data']['kWh/yr'])
        retro_con = np.float64(self.comp_specs['data']['kWh/yr w/ retro']) 
        if (not np.isnan(con) and not np.isnan(retro_con)) and \
                (con != 0 and retro_con != 0):
            percent = retro_con/con
            self.diagnostics.add_note(self.component_name, 
                'Using caclulated electric consumption percent '\
                + str(percent * 100))
        consumption = self.baseline_kWh_consumption * percent
        self.proposed_kWh_consumption = consumption

    def calc_proposed_HF_consumption (self):
        """Calculate the proposed Heating consumption.

        Attributes
        ----------
        proposed_fuel_biomass_consumption : np.array
            coord/year values(floats) over the project lifetime
        proposed_fuel_Hoil_consumption : np.array
            gal/year values(floats) over the project lifetime
        proposed_HF_consumption : np.array
            mmbtu/year values(floats) over the project lifetime
        """
        percent = 1 - (self.comp_specs['heating fuel refit reduction']/100.0)
        con = np.float64(self.comp_specs['data']['HF Used'])
        retro_con = np.float64(self.comp_specs['data']['HF w/Retro'])
        if (not np.isnan(con) and not np.isnan(retro_con))\
            and (con != 0 and retro_con != 0):
            percent = retro_con / con
            self.diagnostics.add_note(self.component_name, 
                'Using caclulated HF consumption percent ' + str(percent * 100))
        consumption = self.baseline_fuel_Hoil_consumption * percent
        self.proposed_fuel_Hoil_consumption = consumption
        consumption = self.baseline_fuel_biomass_consumption * percent
        self.proposed_fuel_biomass_consumption = consumption

        self.proposed_HF_consumption = \
                self.proposed_fuel_Hoil_consumption/constants.mmbtu_to_gal_HF +\
                self.proposed_fuel_biomass_consumption/constants.mmbtu_to_cords

    def calc_savings_kWh_consumption (self):
        """calculate the savings in kWh use

        Attributes
        ----------
        savings_kWh_consumption : np.array
            electric savings
        """
        self.savings_kWh_consumption = self.baseline_kWh_consumption -\
                                       self.proposed_kWh_consumption

    def calc_savings_HF_consumption (self):
        """calculate the savings in HF use

        Attributes
        ----------
        savings_fuel_Hoil_consumption : np.array
            heating oil savings (gal/year)
        savings_fuel_biomass_consumption : np.array
            heating oil savings (cord/year)
        savings_HF_consumption : np.array
            heating oil savings (mmbtu/year)
        """

        self.savings_fuel_Hoil_consumption = \
                self.baseline_fuel_Hoil_consumption - \
                self.proposed_fuel_Hoil_consumption
        self.savings_fuel_biomass_consumption = \
                self.baseline_fuel_biomass_consumption - \
                self.proposed_fuel_biomass_consumption
        self.savings_HF_consumption = \
                self.baseline_HF_consumption - \
                self.proposed_HF_consumption

    def calc_capital_costs (self, cost_per_person = 450):
        """Calculate the capital costs.

        Attributes
        ----------
        capital_costs : float
             total cost of improvements ($), calculated from audit cost and
             population size
        """
        cc = self.comp_specs['data']["Implementation Cost"]
        self.capital_costs = np.float64(cc)
        if np.isnan(self.capital_costs) or self.capital_costs ==0:
            self.capital_costs = float(self.comp_specs["audit cost"]) + \
                                        self.pop *  self.cost_per_person

    def get_fuel_total_saved (self):
        """Get total fuel saved.

        Returns
        -------
        float
            the total fuel saved in gallons
        """
        base_heat = \
            self.baseline_HF_consumption[:self.actual_project_life] *\
            constants.mmbtu_to_gal_HF

        proposed_heat = \
            self.proposed_HF_consumption[:self.actual_project_life] *\
            constants.mmbtu_to_gal_HF


        base_elec = self.baseline_kWh_consumption[:self.actual_project_life] /\
                                self.cd["diesel generation efficiency"]

        proposed_elec = self.baseline_kWh_consumption\
                                                [:self.actual_project_life] / \
                                self.cd["diesel generation efficiency"]
        #~ print (base_elec - proposed_elec)
        return (base_heat - proposed_heat) + (base_elec - proposed_elec)

    def get_total_energy_produced (self):
        """Get total energy produced.

        Returns
        -------
        float
            the total energy produced
        """
        kWh_savings = self.savings_kWh_consumption[:self.actual_project_life]
        HF_savings = self.savings_HF_consumption[:self.actual_project_life]
        try:
            heating_cost_percent = \
                (self.comp_specs['heating cost percent']/100.0)
        except KeyError:
            heating_cost_percent = .5
        return {'kWh': (kWh_savings, 1 - heating_cost_percent),
                'MMBtu': (HF_savings, heating_cost_percent)
               }
