"""
Wind Power Component Body
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

class WindPower(AnnualSavings):
    """Wind power component of the Alaska Affordable Energy Model: This
    module estimates potential reduction in diesel fuel use from the
    installation of wind power systems. Proposed wind generation is
    from existing projects or estimated from a proposed capacity. Financial
    savings result from decrease in diesel used in generation due to wind systems.
    The cost to build or improve wind infrastructure are also estimated.

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
        Initial value: 'wind power' section of community_data

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

        ### ADD other initialization stuff



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

        self.was_run = True
        self.reason = "OK"
        tag = self.cd['file id'].split('+')
        if len(tag) > 1 and tag[1] != 'wind':
            self.was_run = False
            self.reason = "Not a Wind project"
            return

        try:
            #~ self.generation = self.forecast.get_generation(self.start_year)
            self.calc_average_load()
            self.calc_generation_wind_proposed()
        except AttributeError:
            self.diagnostics.add_warning(self.component_name,
                            "could not be run")
            self.was_run = False
            self.reason = ("Could not Calculate average load or "
                                    "proposed generation")
            return




        #~ #~ print self.comp_specs['wind class']
        # ??? some kind of failure message
        if self.average_load is None or \
            (self.average_load > self.comp_specs['average load limit'] and \
            self.load_offset_proposed > 0):
            #~ float(self.comp_specs['wind class']) > \
                #~ self.comp_specs['minimum wind class'] and \

        # if the average load is greater that the lower limit run this component
        # else skip

            self.calc_transmission_losses()
            self.calc_exess_energy()
            self.calc_net_generation_wind()
            self.calc_electric_diesel_reduction()
            self.calc_diesel_equiv_captured()
            self.calc_loss_heat_recovery()
            self.calc_reduction_diesel_used()


            if self.cd["model financial"]:
                # AnnualSavings functions (don't need to write)
                self.get_diesel_prices()

                # change these below
                self.calc_capital_costs()
                self.calc_maintainance_cost()
                self.calc_annual_electric_savings()
                self.calc_annual_heating_savings()

                # AnnualSavings functions (don't need to write)
                self.calc_annual_total_savings()
                self.calc_annual_costs(self.cd['interest rate'],
                                            scalers['capital costs'])
                self.calc_annual_net_benefit()
                self.calc_npv(self.cd['discount rate'], self.cd["current year"])
                #~ print self.benefit_cost_ratio
                self.calc_levelized_costs(self.maintainance_cost)
        else:
            #~ print "wind project not feasible"
            self.was_run = False
            if self.load_offset_proposed <= 0:
                self.reason = "Proposed load offset less than 0"
            else:
                self.reason = \
                    "Average load too small for viable wind generation."
            self.diagnostics.add_note(self.component_name,
            "communities average load is not large enough to consider project")
        #~ print self.benefit_cost_ratio

    def calc_average_load (self):
        """Calculate the Average Diesel load of the current system

        Attributes
        ----------
        generation: np.array
            current diesel generation
        average_load : float
            average diesel load of current system
        """
        if self.comp_specs['proposed capacity'] != UNKNOWN:
            self.average_load = None
        self.generation = self.forecast.generation['generation diesel']\
                                                            [self.start_year]
        self.average_load = \
                self.forecast.yearly_average_diesel_load.ix[self.start_year]
        #~ print 'self.average_load',self.average_load

    def calc_generation_wind_proposed (self):
        """Calculate the proposed generation for wind.

        Attributes
        ----------
        load_offset_proposed : float
            kW capacity
        generation_wind_proposed : float
            kWh/year
        """
        if self.comp_specs['proposed capacity'] != UNKNOWN:
            self.load_offset_proposed = \
                    self.comp_specs['proposed capacity']
            self.generation_wind_proposed = \
                    self.comp_specs['proposed generation']

            if self.generation_wind_proposed == UNKNOWN:
                self.generation_wind_proposed = self.load_offset_proposed *\
                                    float(self.comp_specs\
                                        ['capacity factor'])*\
                                    constants.hours_per_year

            return

        self.load_offset_proposed = 0

        offset = self.average_load*\
            (self.comp_specs['percent generation to offset'] / 100.0)
        #~ print self.forecast.generation['generation hydro'].sum()

        # removed on purpose
        #~ hydro = \
            #~ self.forecast.generation['generation hydro'].fillna(0).sum()
        #~ if hydro > 0:
            #~ offset *= 2

        # existing very variable RE
        existing_RE = \
            int(float(self.cd['wind capacity'])) + \
            int(float(self.cd['solar capacity']))

        if existing_RE < (round(offset/25) * 25): # ???
            #~ print "True"
            self.load_offset_proposed = round(offset/25) * 25 - existing_RE



        # not needed for now
        #~ self.total_wind_generation = self.generation_load_proposed + \
                    #~ int(self.comp_specs['wind capacity'])

        self.generation_wind_proposed =  self.load_offset_proposed * \
            float(self.comp_specs['capacity factor'])*\
                                    constants.hours_per_year
        #~ print 'self.load_offset_proposed',self.load_offset_proposed
        #~ print 'self.generation_wind_proposed',self.generation_wind_proposed

    def calc_transmission_losses (self):
        """calculate the line losses on proposed system

        Attributes
        ----------
        transmission_losses : float
            transmission losses (kWh/year)
        """
        #~ print self.generation_wind_proposed, self.cd['line losses']
        self.transmission_losses = self.generation_wind_proposed * \
            (self.cd['line losses'] / 100.0)
        #~ print 'self.transmission_losses',self.transmission_losses

    def calc_exess_energy (self):
        """Calculate the excess energy.

        Attributes
        ----------
        excess_energy : float
            excess energy(kWh/year)
        """
        #~ print sorted(self.cd.keys())
        self.exess_energy = \
            (self.generation_wind_proposed - self.transmission_losses) * \
            (self.cd['percent excess energy'] / 100.0)
        #~ print 'self.exess_energy',self.exess_energy

    def calc_net_generation_wind (self):
        """Calculate the proposed net generation.

        Attributes
        ----------
        net_wind_generation : float
            net wind generation (kWh/year)
        """
        self.net_generation_wind = self.generation_wind_proposed  - \
                                    self.transmission_losses  -\
                                    self.exess_energy
        #~ print 'self.net_generation_wind',self.net_generation_wind

    def calc_electric_diesel_reduction (self):
        """Calculate the reduction in diesel due to the proposed wind.

        Attributes
        ----------
        electric_diesel_reduction : float
            reduction in generation diesel (gal/year)
        """
        gen_eff = self.cd["diesel generation efficiency"]

        self.electric_diesel_reduction = self.net_generation_wind / gen_eff

        electric_diesel = self.generation/gen_eff
        if self.electric_diesel_reduction > electric_diesel:
            self.electric_diesel_reduction = electric_diesel

    def calc_diesel_equiv_captured (self):
        """calculate heat energy captured

        Attributes
        ----------
        diesel_equiv_captured : float
            Gal/year
        """
        if self.generation_wind_proposed == 0:
            exess_percent = 0
        else:
            exess_percent = self.exess_energy / self.generation_wind_proposed
        exess_captured_percent = exess_percent * \
            (self.cd['percent excess energy capturable'] / 100.0)
        if self.comp_specs['secondary load']:
            net_exess_energy = exess_captured_percent * \
                                self.generation_wind_proposed
        else:
            net_exess_energy = 0

        #~ conversion = 0.99/0.138/0.8/293
        conversion = self.cd['efficiency electric boiler']/ \
                     (1/constants.mmbtu_to_gal_HF)/ \
                     self.cd['efficiency heating oil boiler']/\
                     (constants.mmbtu_to_kWh)
        self.diesel_equiv_captured = net_exess_energy * conversion

        #~ print 'self.diesel_equiv_captured ',self.diesel_equiv_captured

    def calc_loss_heat_recovery (self):
        """Calculate heat recovery lost.

        Attributes
        ----------
        loss_heat_recovery : float
            Gal/year
        """
        hr_used = self.cd['heat recovery operational']
        self.loss_heat_recovery = 0
        if hr_used:# == 'Yes':
            self.loss_heat_recovery = self.electric_diesel_reduction * \
                (self.comp_specs['percent heat recovered'] / 100.0)
        #~ print 'self.loss_heat_recovery',self.loss_heat_recovery

    def calc_reduction_diesel_used (self):
        """Calculate Diesel generation reduction.

        Attributes
        ----------
        reduction_diesel_used : float
            Gal/year
        """
        self.reduction_diesel_used = self.diesel_equiv_captured - \
                                     self.loss_heat_recovery
        #~ print 'self.reduction_diesel_used',self.reduction_diesel_used

    def get_fuel_total_saved (self):
        """Get total fuel saved.

        Returns
        -------
        float
            the total fuel saved in gallons
        """
        return self.electric_diesel_reduction + self.reduction_diesel_used

    def get_total_energy_produced (self):
        """Get total energy produced.

        Returns
        -------
        float
            the total energy produced
        """
        return self.net_generation_wind

    def calc_maintainance_cost (self):
        """Calculate the maintenance costs.

        Attributes
        ----------
        maintainance_costs : float
             total cost of improvements ($), calculated from transmission and
             generation costs
        """

        if str(self.comp_specs['operational costs']) \
                                                                != 'UNKNOWN':
            self.maintainance_cost = \
                self.comp_specs['operational costs']
        else:
            self.maintainance_cost = \
                (self.comp_specs['percent o&m'] / 100.0) * self.capital_costs
        #~ print 'self.maintainance_cost',self.maintainance_cost




    # Make this do stuff
    def calc_capital_costs (self):
        """Calculate the capital costs.

        Attributes
        ----------
        capital_costs : float
            total cost of improvements ($),
        cost_per_kwh: float
            cost per kW used to determine capital costs  ($/kW)
        """
        powerhouse_control_cost = 0
        if not self.cd['switchgear suatable for renewables']:
            powerhouse_control_cost = self.cd['switchgear cost']

        #~ road_needed = self.comp_specs['road needed for transmission line']


        if str(self.comp_specs['transmission capital cost'])\
           != 'UNKNOWN':
            transmission_line_cost = \
            int(self.comp_specs['transmission capital cost'])
        else:
            if str(self.comp_specs['distance to resource']) \
                != 'UNKNOWN':
                distance = \
                    float(self.comp_specs\
                        ['distance to resource'])
            transmission_line_cost = \
                distance*self.comp_specs['est. transmission line cost']

        secondary_load_cost = 0
        if self.comp_specs['secondary load']:
            secondary_load_cost = self.comp_specs['secondary load cost']

        if str(self.comp_specs['generation capital cost']) \
            != 'UNKNOWN':
            wind_cost = \
              int(self.comp_specs['generation capital cost'])
            self.cost_per_kw = np.nan
        else:
            for i in range(len(self.comp_specs['estimated costs'])):
                if int(self.comp_specs['estimated costs'].iloc[i].name) < \
                                            self.load_offset_proposed:
                    if i == len(self.comp_specs['estimated costs']) - 1:
                        cost = float(self.comp_specs['estimated costs'].iloc[i])
                        break
                    continue

                cost = float(self.comp_specs['estimated costs'].iloc[i])
                break

            wind_cost = self.load_offset_proposed * cost
            self.cost_per_kw = cost

        #~ print powerhouse_control_cost
        #~ print transmission_line_cost
        #~ print secondary_load_cost
        #~ print wind_cost
        self.capital_costs = powerhouse_control_cost + transmission_line_cost +\
                             secondary_load_cost + wind_cost

        #~ print 'self.capital_costs',self.capital_costs


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
        price = self.diesel_prices
        #TODO add rural v non rural
        self.base_generation_cost = self.electric_diesel_reduction * price


        self.proposed_generation_cost = self.maintainance_cost

        self.annual_electric_savings = self.base_generation_cost - \
                            self.proposed_generation_cost
        #~ print 'self.annual_electric_savings',self.annual_electric_savings



    # Make this do stuff. Remember the different fuel type prices if using
    def calc_annual_heating_savings (self):
        """Calculate annual heating savings created by the project.

        Attributes
        ----------
        annual_heating_savings : np.array
            heating savings ($/year)
        """
        price = (self.diesel_prices + self.cd['heating fuel premium'])

        #~ self.base_heating_cost =

        #~ self.proposed_heating_cost =




        self.annual_heating_savings = self.reduction_diesel_used * price
        #~ print 'self.annual_heating_savings',self.annual_heating_savings


    def save_component_csv (self, directory):
        """Save the output from the component.

        Parameters
        ----------
        directory : path
            path to save at
        """
        #~ return
        if not self.was_run:
            #~ fname = os.path.join(directory,
                                   #~ self.component_name + "_output.csv")
            #~ fname = fname.replace(" ","_")

            #~ fd = open(fname, 'w')
            #~ fd.write("Wind Power minimum requirements not met\n")
            #~ fd.close()
            return


        years = np.array(range(self.project_life)) + self.start_year

        # ??? +/-
        # ???
        df = DataFrame({
                'Wind: Capacity (kW)':self.load_offset_proposed,
                "Wind: Generation (kWh/year)": self.net_generation_wind,
                'Wind: Energy Captured by Secondary Load'
                    ' (gallons of heating oil equivalent)':
                                                    self.diesel_equiv_captured,
                'Wind: Assumed capacity factor':
                    float(self.comp_specs['capacity factor']),
                'Wind: Utility Diesel Displaced (gallons/year)':
                                            self.electric_diesel_reduction,
                'Wind: Heat Recovery Lost (gallons/year)':
                                            self.loss_heat_recovery,
                "Wind: Heat Recovery Cost Savings ($/year)":
                                            self.get_heating_savings_costs(),
                "Wind: Electricity Cost Savings ($/year)":
                                            self.get_electric_savings_costs(),
                "Wind: Project Capital Cost ($/year)":
                                            self.get_capital_costs(),
                "Wind: Total Cost Savings ($/year)":
                                            self.get_total_savings_costs(),
                "Wind: Net Benefit ($/year)": self.get_net_benefit(),
                       }, years)

        df["Community"] = self.cd['name']

        ol = ["Community",
              'Wind: Capacity (kW)',
              'Wind: Energy Captured by Secondary Load'
                        ' (gallons of heating oil equivalent)',
              'Wind: Assumed capacity factor',
              'Wind: Utility Diesel Displaced (gallons/year)',
              'Wind: Heat Recovery Lost (gallons/year)',
              "Wind: Generation (kWh/year)",
              "Wind: Heat Recovery Cost Savings ($/year)",
              "Wind: Electricity Cost Savings ($/year)",
              "Wind: Project Capital Cost ($/year)",
              "Wind: Total Cost Savings ($/year)",
              "Wind: Net Benefit ($/year)"]
        fname = os.path.join(directory,
                             self.cd['name'] + '_' + \
                             self.component_name.lower() + "_output.csv")
        fname = fname.replace(" ","_")

        df[ol].ix[:self.actual_end_year].to_csv(fname, index_label="Year")
