"""
Heat Recovery component body
----------------------------

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


class HeatRecovery (AnnualSavings):
    """Heat recovery component of the Alaska Affordable Energy Model: Insufficient
    data was available on a community-level to model the costs and benefits of
    heat recovery. Because of this, the module only includes analysis of projects
    that have pre-construction studies.

    .. note::

       Component requires an existing project for a community to be run to
       completion.

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
        Initial value: 'heat recovery' section of community_data

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
            #~ self.comp_specs['expected years to operation']


        self.set_project_life_details(
            self.comp_specs["start year"],
            self.comp_specs["lifetime"]
        )

        ### ADD other initialization stuff
        ### load prerequisites in the following function
        ### if there are no prerequisites you can delete this and the
        ### load_prerequisite_variables function
        ##### no prerequisites needed here commend out loading functionality
        #~ self.load_prerequisite_variables(prerequisites)

    #~ def load_prerequisite_variables (self, comps):
        #~ """
        #~ Parameters
        #~ ----------
        #~ comps :
        #~ """
        #~ # LOAD anything needed from the components passed as input
        #~ pass

    def run (self, scalers = {'capital costs':1.0}):
        """runs the component. The Annual Total Savings,Annual Costs,
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
        self.was_run = True
        self.reason = "OK"
        if self.cd['file id'].find('+') == -1:
            self.was_run = False
            self.reason = "Heat recovery" + \
                " requires that at least a reconnaissance-level heat recovery"+\
                " study has been completed for the community."
            self.diagnostics.add_note(self.component_name, self.reason)
            return

        tag = self.cd['file id'].split('+')
        if len(tag) > 1 and tag[1] != PROJECT_TYPE:
            self.was_run = False
            self.reason = "Not a " + "Heat recovery" + " project."
            self.diagnostics.add_note(self.component_name, self.reason)
            return

        if self.cd["model heating fuel"]:
            try:
                self.calc_proposed_heat_recovery()
            except AttributeError:
                self.was_run = False
                self.reason = "Could not calculate proposed heat recovery."
                self.diagnostics.add_note(self.component_name, self.reason)
                return

        if np.isnan(self.proposed_heat_recovery) or \
                self.proposed_heat_recovery == 0:
            self.was_run = False
            self.reason = "No proposed heat recovery."
            self.diagnostics.add_note(self.component_name, self.reason)
            return

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

            self.calc_levelized_costs(self.comp_specs['o&m per year'])


    def get_fuel_total_saved (self):
        """
        Returns
        -------
        float
            the total fuel saved in gallons
        """
        return self.proposed_heat_recovery

    def get_total_energy_produced (self):
        """
        Returns
        -------
        float
            the total energy produced
        """
        return self.proposed_heat_recovery/ constants.mmbtu_to_gal_HF

    def calc_proposed_heat_recovery (self):
        """calculate the proposed heat recovery

        Attributes
        ----------
        proposed_heat_recovery : float
            calculated or loaded proposed heat recovery

        Notes
        -----
        Proposed_heat_recovery currently is only set if there a project for
        heat recovery in a community.

        """
        ### OLD COMMENTS
        ## if Project details exist:
        ##    proposed_heat_recovery = projects 'proposed gallons diesel offset'

        ##hr_available = %hr * diesel_for_generation
        ##potential_hr = 'Est. potential annual heating fuel gallons displaced'
        ##if hr_opp and waste_heat_available:
        ##    if potential_hr  unknown:
        ##        proposed_heat_recovery = (hr_available * .3) /
        ##                                  'heating conversion efficiency'
        ##    else:
        ##        proposed_heat_recovery = potential_hr/
        ##                                 'heating conversion efficiency'
        ##else:
        ##    proposed_heat_recovery = 0

        p_gallons = self.comp_specs['proposed gallons diesel offset']
        p_btu = self.comp_specs['proposed maximum btu/hr']
        #~ print p_gallons, p_btu
        # is there a project
        if p_gallons != UNKNOWN and p_btu != UNKNOWN:
            self.proposed_heat_recovery = p_gallons
            return

        ## not currently estimating unknown proposed heat recovery
        return
        # else:
        #~ hr_opp = self.comp_specs['estimate data']\
                    #~ ['Waste Heat Recovery Operational']
        #~ waste_heat_available = self.comp_specs['estimate data']\
                    #~ ['Add waste heat Avail']

        #~ potential_hr = self.comp_specs['estimate data']\
                    #~ ['Est. potential annual heating fuel gallons displaced']

        #~ try:
            #~ np.isnan(potential_hr)
        #~ except TypeError:
            #~ potential_hr = np.nan

        #~ generation = self.forecast.generation_by_type['generation diesel']\
                                                            #~ [self.start_year]
        #~ gen_eff = self.cd["diesel generation efficiency"]

        #~ # gallons
        #~ diesel_consumed = generation / gen_eff
        #~ hr_available = (self.comp_specs['percent heat recovered'] / 100.0) * \
                          #~ diesel_consumed

        #~ if hr_opp == 'Yes' and waste_heat_available == 'Yes' and \
           #~ np.isnan(potential_hr):
            #~ potential_hr = ((hr_available) * .30)
        #~ if hr_opp == 'Yes' and waste_heat_available == 'Yes':
            #~ pass #potential_hr
        #~ elif hr_opp == 'Yes' and waste_heat_available == 'No':
            #~ potential_hr = 0
        #~ else:
            #~ potential_hr = 0

        #~ self.proposed_heat_recovery = potential_hr / \
                                #~ self.comp_specs['heating conversion efficiency']

    # Make this do stuff
    def calc_capital_costs (self):
        """Calculate or Load the project Capital Costs.

        Attributes
        ----------
        capital_costs : float
            calculated or loaded capital costs for heat recovery
        """
        #~ print self.comp_specs
        capital_costs = float(self.comp_specs['capital costs'])
        if capital_costs == UNKNOWN:

            install_cost = 50000 * \
                self.comp_specs['estimate pipe distance']/1000.0

            loop_cost = self.comp_specs['estimate pipe cost/ft'] * \
                        self.comp_specs['estimate pipe distance']

            overhead_cost = self.comp_specs['estimate pipe distance']/1000.0 * \
                            140000

            num_buildings = self.comp_specs['number buildings']
            if num_buildings == 'UNKNOWN':
                num_buildings = self.comp_specs['estimate buildings to heat']
            building_cost = num_buildings * \
                                self.comp_specs['estimate cost/building']
            capital_costs = install_cost + loop_cost +\
                            overhead_cost + building_cost
        self.capital_costs = capital_costs
        #~ print self.capital_costs


    def calc_annual_electric_savings (self):
        """Set annual electric savings to zero as this component is for
        improving heating fuel use

        Attributes
        ----------
        annual_electric_savings : float, dollars per year
            set to zero
        """
        self.annual_electric_savings = 0

    def calc_annual_heating_savings (self):
        """Calculate Annual Heating Savings, from proposed Heat recovery and
        Heating Fuel Price.

        Attributes
        ----------
        annual_heating_savings : float, dollars per year
            Savings gained by Heat Recovery improvements
        """
        self.annual_electric_savings = 0
        price = (self.diesel_prices + self.cd['heating fuel premium'])

        self.annual_heating_savings = self.proposed_heat_recovery * price + \
                                      self.comp_specs['o&m per year']
