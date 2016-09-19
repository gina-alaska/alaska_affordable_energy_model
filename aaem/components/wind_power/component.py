"""
component.py

    Wind Power component body
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

class WindPower(AnnualSavings):
    """
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
        self.diagnostics = diag
        if self.diagnostics == None:
            self.diagnostics = diagnostics()
        self.forecast = forecast
        self.cd = community_data.get_section('community')
       
        self.comp_specs = community_data.get_section(COMPONENT_NAME)
        self.component_name = COMPONENT_NAME
        #~ print self.cd['current year']
        self.comp_specs["start year"] = self.cd['current year'] + \
            self.comp_specs["project details"]['expected years to operation']
        self.set_project_life_details(self.comp_specs["start year"],
                                      self.comp_specs["lifetime"],
                        self.forecast.end_year - self.comp_specs["start year"])
                        
        ### ADD other intiatzation stuff
        
        
    
    def run (self, scalers = {'capital costs':1.0}):
        """
        run the forecast model
        
        pre:
            self.cd should be the community library from a community data object
        post:
            TODO: define output values. 
            the model is run and the output values are available
        """
        #~ #~ print self.comp_specs['resource data']
        #~ return
        
        self.run = True
        self.reason = "OK"
        tag = self.cd['name'].split('+')
        if len(tag) > 1 and tag[1] != 'wind':
            self.run = False
            self.reason = "Not a Wind project"
            return 
            
        try:
            #~ self.generation = self.forecast.get_generation(self.start_year)
            self.calc_average_load()
            self.calc_generation_wind_proposed()
        except AttributeError:
            self.diagnostics.add_warning(self.component_name, 
                            "could not be run")
            self.run = False
            self.reason = "could not find average load or proposed generation"
            return
            
        
 
        
        #~ #~ print self.comp_specs['resource data']['Assumed Wind Class'] 
        # ??? some kind of failure message
        if self.average_load is None or \
            (self.average_load > self.comp_specs['average load limit'] and \
            self.load_offset_proposed > 0):
            #~ float(self.comp_specs['resource data']['Assumed Wind Class']) > \
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
            
            
           
            if self.cd["model electricity"]:
                # change these below
                #~ self.calc_baseline_kWh_consumption()
                #~ self.calc_retrofit_kWh_consumption()
                #~ self.calc_savings_kWh_consumption()
                # NOTE*:
                #   some times is it easier to find the savings and use that to
                # calculate the retro fit values. If so, flip the function calls 
                # around, and change the functionality of
                # self.calc_savings_kWh_consumption() below
                pass
            
            if self.cd["model heating fuel"]:
                pass
                # see NOTE*
        
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
            #~ print "wind project not feasiable"
            self.run = False
            if self.load_offset_proposed <= 0: 
                self.reason = "no load offset proposed"
            else:
                self.reason = "average load too small"
            self.diagnostics.add_note(self.component_name, 
            "communites average load is not large enough to consider project")
        #~ print self.benefit_cost_ratio
        
    def calc_average_load (self):
        """
            calculate the average load of the system
            
        pre: 
            self.generation should be a number (kWh/yr)
            
        post:
            self.average_load is a number (kW/yr)
        """
        if self.comp_specs["project details"]['proposed capacity'] != UNKNOWN:
            self.average_load = None
        self.generation = self.forecast.generation_by_type['generation diesel']\
                                                            [self.start_year]
        self.average_load = \
                self.forecast.yearly_average_diesel_load.ix[self.start_year]
        #~ print 'self.average_load',self.average_load
        
    def calc_generation_wind_proposed (self):
        """
            calulate the proposed generation for wind
        pre:
            self.generation should be a number (kWh/yr), 
            'percent generation to offset' is a decimal %
            'resource data' is a wind data object
            'assumed capacity factor' is a decimal %
        
        post:
            self.load_offest_proposed is a number (kW)
            self.generation_wind_proposed is a number (kWh/yr)
        """
        if self.comp_specs["project details"]['proposed capacity'] != UNKNOWN:
            self.load_offset_proposed = \
                    self.comp_specs["project details"]['proposed capacity']
            self.generation_wind_proposed = \
                    self.comp_specs["project details"]['proposed generation']
            return
        
        self.load_offset_proposed = 0
        
        offset = self.average_load*\
                self.comp_specs['percent generation to offset']
        #~ print self.forecast.generation_by_type['generation hydro'].sum()
        hydro = \
            self.forecast.generation_by_type['generation hydro'].fillna(0).sum()
        if hydro > 0:
            offset *= 2
        #~ self.comp_specs['resource data']['existing wind'] = 0
        
        # existing very variable RE
        existing_RE = \
            int(float(self.comp_specs['resource data']['existing wind'])) + \
            int(float(self.comp_specs['resource data']['existing solar']))
        
        if existing_RE < (round(offset/25) * 25): # ???
            #~ print "True"
            self.load_offset_proposed = round(offset/25) * 25 - existing_RE
        
                    
        
        # not needed for now
        #~ self.total_wind_generation = self.generation_load_proposed + \
                    #~ int(self.comp_specs['resource data']['existing wind'])
        
        self.generation_wind_proposed =  self.load_offset_proposed * \
            float(self.comp_specs['resource data']['assumed capacity factor'])*\
                                    constants.hours_per_year
        #~ print 'self.load_offset_proposed',self.load_offset_proposed
        #~ print 'self.generation_wind_proposed',self.generation_wind_proposed 
        
    def calc_transmission_losses (self):
        """
            calculate the line losses on proposed system
            
        pre:
            self.generation_wind_proposed is a number (kWh/yr). 
            self.cd is a CommunityData object
        """
        self.transmission_losses = self.generation_wind_proposed * \
                                                        self.cd['line losses']
        #~ print 'self.transmission_losses',self.transmission_losses
        
    def calc_exess_energy (self):
        """
            calculate the excess energy
            TODO add more:
        """
        #~ print sorted(self.cd.keys())
        self.exess_energy = \
            (self.generation_wind_proposed - self.transmission_losses) * \
            self.comp_specs['percent excess energy']
        #~ print 'self.exess_energy',self.exess_energy
            
    def calc_net_generation_wind (self):
        """
            calculate the proposed net generation
        """
        self.net_generation_wind = self.generation_wind_proposed  - \
                                    self.transmission_losses  -\
                                    self.exess_energy
        #~ print 'self.net_generation_wind',self.net_generation_wind 
            
    def calc_electric_diesel_reduction (self):
        """ 
            calculate the reduction in diesel due to the proposed wind
        """
        gen_eff = self.cd["diesel generation efficiency"]
            
        self.electric_diesel_reduction = self.net_generation_wind / gen_eff
        
        electric_diesel = self.generation/gen_eff
        if self.electric_diesel_reduction > electric_diesel:
            self.electric_diesel_reduction = electric_diesel
            
        
        
        #~ print 'self.electric_diesel_reduction',self.electric_diesel_reduction
        
    def calc_diesel_equiv_captured (self):
        """
            calulate the somthing ???
        """
        if self.generation_wind_proposed == 0:
            exess_percent = 0
        else:
            exess_percent = self.exess_energy / self.generation_wind_proposed
        exess_captured_percent = exess_percent * \
                    self.comp_specs['percent excess energy capturable']
        if self.comp_specs['secondary load']:
            net_exess_energy = exess_captured_percent * \
                                self.generation_wind_proposed 
        else:
            net_exess_energy = 0
       
        #~ conversion = 0.99/0.138/0.8/293 
        conversion = self.comp_specs['efficiency electric boiler']/ \
                     (1/constants.mmbtu_to_gal_HF)/ \
                     self.comp_specs['efficiency heating oil boiler']/\
                     (constants.mmbtu_to_kWh)
        self.diesel_equiv_captured = net_exess_energy * conversion
             
        #~ print 'self.diesel_equiv_captured ',self.diesel_equiv_captured 
        
    def calc_loss_heat_recovery (self):
        """ 
             calulate the somthing ???
        """
        hr_used = self.cd['heat recovery operational']
        self.loss_heat_recovery = 0
        if hr_used:# == 'Yes': 
            self.loss_heat_recovery = self.electric_diesel_reduction * \
            self.comp_specs['percent heat recovered']
        #~ print 'self.loss_heat_recovery',self.loss_heat_recovery
        
    def calc_reduction_diesel_used (self):
        """ 
             calulate the somthing ???
        """
        self.reduction_diesel_used = self.diesel_equiv_captured - \
                                     self.loss_heat_recovery
        #~ print 'self.reduction_diesel_used',self.reduction_diesel_used
        
    def get_fuel_total_saved (self):
        """
        returns the total fuel saved in gallons
        """
        return self.electric_diesel_reduction + self.reduction_diesel_used   
    
    def get_total_enery_produced (self):
        """
        returns the total energy produced
        """
        return self.net_generation_wind
                                     
    def calc_maintainance_cost (self):
        """ 
            calculate the maintainance cost
        """
        
        if str(self.comp_specs['project details']['operational costs']) \
                                                                != 'UNKNOWN':
            self.maintainance_cost = \
                self.comp_specs['project details']['operational costs']
        else:
            self.maintainance_cost = \
                self.comp_specs['percent o&m'] * self.capital_costs
        #~ print 'self.maintainance_cost',self.maintainance_cost
        

    
    
    # Make this do stuff
    def calc_capital_costs (self):
        """
        caclulate the progect capital costs
        """
        powerhouse_control_cost = 0
        if not self.cd['switchgear suatable for RE']:
            powerhouse_control_cost = self.cd['switchgear cost']
        
        road_needed = self.comp_specs['road needed for transmission line']
        

        if str(self.comp_specs['project details']['transmission capital cost'])\
           != 'UNKNOWN':
            transmission_line_cost = \
            int(self.comp_specs['project details']['transmission capital cost'])
        else:
            if str(self.comp_specs['project details']['distance to resource']) \
                != 'UNKNOWN':
                distance = \
                    float(self.comp_specs['project details']\
                        ['distance to resource'])
                distance = distance * constants.feet_to_mi
            else:
                distance = self.comp_specs['default distance to resource']
            transmission_line_cost = distance*\
            self.comp_specs['est. transmission line cost'][road_needed]
        
        secondary_load_cost = 0
        if self.comp_specs['secondary load']:
            secondary_load_cost = self.comp_specs['secondary load cost']
        
        if str(self.comp_specs['project details']['generation capital cost']) \
            != 'UNKNOWN':
            wind_cost = \
              int(self.comp_specs['project details']['generation capital cost'])
        else:
            for i in range(len(self.comp_specs['costs'])):
                if int(self.comp_specs['costs'].iloc[i].name) < \
                                            self.load_offset_proposed:
                    if i == len(self.comp_specs['costs']) - 1:
                        cost = float(self.comp_specs['costs'].iloc[i])
                        break
                    continue
               
                cost = float(self.comp_specs['costs'].iloc[i])
                break
            
            wind_cost = self.load_offset_proposed * cost
        
        
        #~ print powerhouse_control_cost 
        #~ print transmission_line_cost 
        #~ print secondary_load_cost 
        #~ print wind_cost
        self.capital_costs = powerhouse_control_cost + transmission_line_cost +\
                             secondary_load_cost + wind_cost
                             
        #~ print 'self.capital_costs',self.capital_costs
        
    
    # Make this do stuff
    def calc_annual_electric_savings (self):
        """
        """
        price = self.diesel_prices
        #TODO add rural v non rural
        self.base_generation_cost = self.electric_diesel_reduction * price
                        
        
        self.proposed_generation_cost = self.maintainance_cost
        
        self.annual_electric_savings = self.base_generation_cost - \
                            self.proposed_generation_cost
        #~ print 'self.annual_electric_savings',self.annual_electric_savings
        
        
        
    # Make this do sruff. Remember the different fuel type prices if using
    def calc_annual_heating_savings (self):
        """
        """
        price = (self.diesel_prices + self.cd['heating fuel premium'])
        
        #~ self.base_heating_cost =
        
        #~ self.proposed_heating_cost =
        
        
        
        
        self.annual_heating_savings = self.reduction_diesel_used * price
        #~ print 'self.annual_heating_savings',self.annual_heating_savings


    def save_component_csv (self, directory):
        """
        save the output from the component.
        """
        #~ return
        if not self.run:
            #~ fname = os.path.join(directory,
                                   #~ self.component_name + "_output.csv")
            #~ fname = fname.replace(" ","_")
        
            #~ fd = open(fname, 'w')
            #~ fd.write("Wind Power minimum requirments not met\n")
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
                    float(self.comp_specs['resource data']\
                                                ['assumed capacity factor']),
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
                "Wind: Net Benefit ($/year)": self.get_net_beneft(),
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
        
    
