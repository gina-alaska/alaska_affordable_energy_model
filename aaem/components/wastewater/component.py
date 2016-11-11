"""
component.py

    Water/Waste Water efficiency component body
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


class WaterWastewaterSystems (AnnualSavings):
    """
    AAEM Water & Wastewater Systems component
    """
    
    def __init__ (self, community_data, forecast, 
                        diag = None, prerequisites = {}):
        """ 
        Class initialiser 
        
        pre-conditions:
            community_data is a community data object as defied in 
        community_data.py
            forecast is a forecast object as defined as in forecast.py
            diag (if provided) should be a diagnostics as defined in 
        diagnostics.py
        
        Post-conditions: 
            self.component is the component name (string)
            self.diagnostics is a diagnostics object
            self.cd is the community section of the input community_data object
            self.comp_specs is the wastewater specific part of the 
        community_data object 
            self.cost_per_person $/person to refit (float) for the communities 
        region
            self.forecast is the input forecast object
            self.hdd heating degree days (float)
            self.pop population in year used in estimates (float)
            self.population_fc is the forecast population over the project life 
        time
        """
        self.component_name = COMPONENT_NAME
        
        self.diagnostics = diag
        if self.diagnostics == None:
            self.diagnostics = diagnostics()
        
        self.cd = community_data.get_section('community')
        self.comp_specs = community_data.get_section(COMPONENT_NAME)
        self.forecast = forecast
        
        self.set_project_life_details(self.comp_specs["start year"],
                                      self.comp_specs["lifetime"],
                        self.forecast.end_year - self.comp_specs["start year"])
        
        average = self.comp_specs['average refit cost']
        mult = community_data.get_item('community','construction multiplier')
        self.cost_per_person = average * mult 
        
        
        
        self.hdd = self.cd["HDD"]
        
        
        #~ print self.comp_specs['data']['value']
        #~ print self.comp_specs['data']
        self.pop = self.forecast.get_population(int(self.comp_specs['data']\
                                                            ['value']['Year']))
        self.population_fc = self.forecast.get_population(self.start_year,
                                                                 self.end_year)

    def calc_annual_electric_savings (self):
        """
        calculate the annual electric savings
        pre:
             none
        post:
            self.annual_electric_savings is an np.array of $/year values 
        """
        self.calc_baseline_kWh_cost()
        self.calc_proposed_kWh_cost ()
        self.annual_electric_savings = self.baseline_kWh_cost - \
                                       self.proposed_kWh_cost
    
    def calc_baseline_kWh_cost (self):
        """
        calcualte the savings for the base electric savings
        pre:
            "elec non-fuel cost" is a dollar value (float).
            self.diesel_prices is an array of dollar values over the project 
        lifetime (floats)
            'diesel generation efficiency' is in Gal/kWh (float)
        post:
           self.baseline_kWh_cost is an np.array of $/year values (floats) over
        the project lifetime
        """
        kWh_cost = self.cd["electric non-fuel prices"].\
                                            ix[self.start_year:self.end_year-1]
        kWh_cost = kWh_cost.T.values[0]
        self.elec_price = kWh_cost
        # kWh/yr*$/kWh
        self.baseline_kWh_cost = self.baseline_kWh_consumption * kWh_cost
        
    def calc_proposed_kWh_cost (self):
        """
        calcualte the savings for the base electric savings
        pre:
            "elec non-fuel cost" is a dollar value (float).
            self.diesel_prices is an array of dollar values over the project 
        lifetime (floats)
            'diesel generation efficiency' is in Gal/kWh (float)
        post:
           self.baseline_kWh_cost is an np.array of $/year values (floats) over
        the project lifetime
        """
        kWh_cost = self.cd["electric non-fuel prices"].\
                                            ix[self.start_year:self.end_year-1]
        kWh_cost = kWh_cost.T.values[0]
        # kWh/yr*$/kWh
        self.proposed_kWh_cost = self.proposed_kWh_consumption * kWh_cost
    
    def calc_annual_heating_savings (self):
        """
        calculate the annual heating savings 
        pre:
            none
        post:
            self.annual_heating_savings is an np.array of $/year values (floats) 
        over the project lifetime
        """
        self.calc_proposed_HF_cost()
        self.calc_baseline_HF_cost()
        # $ / yr
        self.annual_heating_savings = self.baseline_HF_cost - self.proposed_HF_cost
        
    def calc_proposed_HF_cost (self):
        """
        calcualte the savings for the proposed heating savings
        pre:
            self.diesel_prices is an array of dollar values over the project 
        lifetime (floats)
            'heating fuel premium' $/gal (float)
        post:
           self.proposed_HF_cost is an np.array of $/year values (floats) over the
        project lifetime
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
        """
        calcualte the savings for the base heating savings
        pre:
            self.diesel_prices is an array of dollar values over the project 
        lifetime (floats)
            'heating fuel premium' $/gal (float)
        post:
           self.baseline_HF_cost is an np.array of $/year values (floats) over 
        the project lifetime
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
        """
        runs the model for the inputs section of the wastewater tab
        pre-conditions:
            None
        post-conditions:
            The model component is run
        """
        tag = self.cd['name'].split('+')
        
        self.run = True
        self.reason = "OK"
        
        if len(tag) > 1 and tag[1] != 'water-wastewater':
            self.run = False
            self.reason = "Not a Water/Wastewater project"
            return 
            
        if self.cd["model electricity"]:
            self.calc_baseline_kWh_consumption()
            self.calc_proposed_kWh_consumption()
            self.calc_savings_kWh_consumption()
        
        if self.cd["model heating fuel"]:
            self.calc_baseline_HF_consumption()
            self.calc_proposed_HF_consumption()
            self.calc_savings_HF_consumption()
    
            years = range(self.start_year,self.end_year)
            self.forecast.add_heating_fuel_column(\
                        "heating_fuel_water-wastewater_consumed [gallons/year]",
                         years, 
                         self.baseline_HF_consumption*constants.mmbtu_to_gal_HF)
            self.forecast.add_heating_fuel_column(\
                   "heating_fuel_water-wastewater_consumed [mmbtu/year]", years,
                    self.baseline_HF_consumption)
            
            self.forecast.add_heat_demand_column(\
                        "heat_energy_demand_water-wastewater [mmbtu/year]",
                     years, self.baseline_HF_consumption)
        
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
            self.levelized_cost_of_energy['MMBtu'] *= .5
            self.levelized_cost_of_energy['kWh'] *= .5

    
    def calc_baseline_kWh_consumption (self):
        """
        calculate electric savings
        pre:
            self.hdd, self.pop, self.population_fc should be as defined in 
        __init__
            self.comp_specs['data'] should have 'kWh/yr', 'HDD kWh', 
        and 'pop kWh' as values (floats) with the units kWh/yr, kWh/HDD,
         and KWh/person 
        
            NOTE: If known 'kWh/yr' is NaN or 0 an estimate will be created.
        post:
            self.baseline_kWh_consumption array of kWh/year values(floats) over
        the project lifetime
        """
        hdd_coeff = np.float64(self.comp_specs['data'].ix['HDD kWh'])
        pop_coeff = np.float64(self.comp_specs['data'].ix['pop kWh'])
        if not np.isnan(np.float64(self.comp_specs['data'].ix['kWh/yr'])) and \
               np.float64(self.comp_specs['data'].ix['kWh/yr']) != 0:
            self.baseline_kWh_consumption =\
                             np.float64(self.comp_specs['data'].ix['kWh/yr'])+ \
                            ((self.population_fc - self.pop) * pop_coeff)
        else: #if not self.cd["w&ww_energy_use_known"]:
            
            
            self.baseline_kWh_consumption = \
                            (self.hdd * hdd_coeff + self.pop * pop_coeff) + \
                            ((self.population_fc - self.pop) * pop_coeff)
                            
    def calc_baseline_HF_consumption (self):
        """
        calculate heating fuel savings
        pre:
            self.hdd, self.pop, self.population_fc should be as defined in 
        __init__
            self.comp_specs['data'] should have 'HF Used',
        'heat recovery multiplier', 'HDD HF', and 'pop HF' as values (floats) 
        with the units gal/yr, unitless, Gal/HDD, and Gal/person 
            self.comp_specs['data']'s 'HR Installed' is (True or False)(String)
            NOTE: If known 'gal/yr' is NaN or 0 an estimate will be created.
        post:
            self.baseline_kWh_consumption array of kWh/year values(floats) over
        the project lifetime
        """
        hdd_coeff = np.float64(self.comp_specs['data'].ix['HDD HF'])
        pop_coeff = np.float64(self.comp_specs['data'].ix['pop HF'])
        if not np.isnan(np.float64(self.comp_specs['data'].ix['HF Used'])) and\
                np.float64(self.comp_specs['data'].ix['HF Used']) != 0:
            self.baseline_HF_consumption = np.zeros(self.project_life)
            self.baseline_HF_consumption += \
                            np.float64(self.comp_specs['data'].ix['HF Used']) +\
                    ((self.population_fc - self.pop) * pop_coeff)
        else:
            hr = self.comp_specs['data'].ix["HR Installed"].values[0] == "TRUE"
            hr_coeff =  self.comp_specs['heat recovery multiplier'][hr]
            self.baseline_HF_consumption = \
                    ((self.hdd * hdd_coeff+ self.pop * pop_coeff)  +\
                    ((self.population_fc - self.pop) * pop_coeff))* hr_coeff
        self.baseline_fuel_biomass_consumption = 0 
        biomass = self.comp_specs['data'].ix['Biomass'].values[0] == "TRUE"
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
        """
        calculate post refit kWh use
        pre:
            self.comp_specs['electricity refit reduction'] < 1, > 0 (float) 
            self.comp_specs['data'].ix['kWh/yr'] is a price (kWh/yr) (float)
            self.comp_specs['data'].ix['kWh/yr w/ retro'] is a price (kWh/yr) 
        (float)
            NOTE: if the prices are Nan or 0 they are not used
        post:
            self.proposed_kWh_consumption is an array of kWh/yr (floats) over 
        the project lifetime 
        """
        percent = 1 - self.comp_specs['electricity refit reduction']
        con = np.float64(self.comp_specs['data'].ix['kWh/yr'])
        retro_con = np.float64(self.comp_specs['data'].ix['kWh/yr w/ retro']) 
        if (not (np.isnan(con) and np.isnan(retro_con))) and \
                (con != 0 and retro_con != 0):
            percent = retro_con/con
        consumption = self.baseline_kWh_consumption * percent
        self.proposed_kWh_consumption = consumption 

    def calc_proposed_HF_consumption (self):
        """
        calculate post refit HF use
        pre:
            self.comp_specs['heating fuel refit reduction'] < 1, > 0 (float) 
            self.comp_specs['data'].ix['HF Used'] is a price (gal/yr) (float)
            self.comp_specs['data'].ix['HF w/retro'] is a price (gal/yr) (float)
            NOTE: if the prices are Nan or 0 they are not used
        post:
            self.proposed_HF_consumption is an array of gal/yr values (floats) over 
        the project lifetime 
        """
        percent = 1 - self.comp_specs['heating fuel refit reduction']
        if (not (np.isnan(np.float64(self.comp_specs['data'].ix['HF w/Retro']))\
            and np.isnan(np.float64(self.comp_specs['data'].ix['HF Used']))))\
            and (np.float64(self.comp_specs['data'].ix['HF Used']) != 0 and\
                 np.float64(self.comp_specs['data'].ix['HF w/Retro'])):
            percent = np.float64(self.comp_specs['data'].ix['HF w/Retro'])/\
                      np.float64(self.comp_specs['data'].ix['HF Used'])
        consumption = self.baseline_fuel_Hoil_consumption * percent
        self.proposed_fuel_Hoil_consumption = consumption
        consumption = self.baseline_fuel_biomass_consumption * percent
        self.proposed_fuel_biomass_consumption = consumption
        
        self.proposed_HF_consumption = \
                self.proposed_fuel_Hoil_consumption/constants.mmbtu_to_gal_HF +\
                self.proposed_fuel_biomass_consumption/constants.mmbtu_to_cords
        
    def calc_savings_kWh_consumption (self):
        """
        calculate the savings in kWh use
        pre:
            self.baseline_kWh_consumption, self.proposed_kWh_consumption are
        arrays of kWh/year (floats) over the project lifetime
        post:
            self.savings_kWh_consumption arrays of kWh/year savings(floats) 
        over the project lifetime
        """
        self.savings_kWh_consumption = self.baseline_kWh_consumption -\
                                       self.proposed_kWh_consumption
                                       
    def calc_savings_HF_consumption (self):
        """
        calculate the savings in HF use
        pre:
            self.baseline_HF_consumption, self.proposed_HF_consumption are
        arrays of gal/year (floats) over the project lifetime
        post:
            self.savings_HF_consumption arrays of gal/year savings(floats) 
        over the project lifetime
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
        """
        calculate the capital costs
        
        pre:
            self.comp_specs['data'].ix["Implementation Cost"] is the actual
        cost of refit (float), if it is NAN or 0 its not used.
            "audit_cost" is a dollar value (float)
            self.cost_per_person is a dollar value per person > 0
            self.pop is a population value (floats) > 0
        post:
            self.capital_costs is $ value (float)
        """
        cc = self.comp_specs['data'].ix["Implementation Cost"]
        self.capital_costs = np.float64(cc)
        if np.isnan(self.capital_costs) or self.capital_costs ==0:
            self.capital_costs = float(self.comp_specs["audit cost"]) + \
                                        self.pop *  self.cost_per_person
                                        
    def get_fuel_total_saved (self):
        """
        returns the total fuel saved in gallons
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
                                
    def get_total_enery_produced (self):
        """
        returns the total energy produced
        """
        return {'kWh': 
                    self.proposed_kWh_consumption[:self.actual_project_life], 
                'MMBtu':
                    self.proposed_HF_consumption[:self.actual_project_life]
               }
