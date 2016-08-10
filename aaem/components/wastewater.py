"""
wastewater.py
Water & Wastewater Systems

ross spicer
created: 2015/09/09

    AAEM Water & Wastewater Systems component

"""
import numpy as np
import os
from pandas import DataFrame, read_csv

from annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import diagnostics
import aaem.constants as constants

"""water wastewater:
  enabled: False
  lifetime:  ABSOLUTE DEFAULT # number years <int>  
  start year:  ABSOLUTE DEFAULT # start year <int>
  audit cost: 10000 # price <float> (ex. 10000)
  average refit cost: 360.00 # cost/per person <float>
  data: IMPORT

  electricity refit reduction: .25 # decimal precent <float> percent saved by preforming electricity refit 
  heating fuel refit reduction: .35 # decimal precent <float> percent saved by preforming heating fuel refit 
  
  
  heat recovery multiplier:
    True: .5 # precent as decimal <float> 
    False: 1.0 # precent as decimal <float> 
"""

yaml = {'enabled': False,
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        'audit cost': 10000,
        'average refit cost': 360.00,
        'data': 'IMPORT',
        'electricity refit reduction': .25,
        'heating fuel refit reduction': .35,
        'heat recovery multiplier': {True: .5, False: 1.0}
            }

yaml_defaults = {'enabled': True,
        'lifetime': 15,
        'start year': 2017,
        }

yaml_order = ['enabled','lifetime','start year','audit cost',
             'average refit cost', 'data', 'electricity refit reduction',
             'heating fuel refit reduction', 'heat recovery multiplier']

yaml_comments = {
    'enabled':'',
    'lifetime': 'number years <int>',
    'start year': 'start year <int>',
    'audit cost': 'price <float> (ex. 10000)',
    'average refit cost': 'cost/per person <float>',
    'data': '',
    'electricity refit reduction': 
        'decimal precent <float> percent saved by preforming electricity refit',
    'heating fuel refit reduction': 
        'decimal precent <float> percent saved by heating fuel refit',
    'heat recovery multiplier': ''
    }

def process_data_import(data_dir):
    """
    """
    data_file = os.path.join(data_dir, "wastewater_data.csv")
    
    data = read_csv(data_file, comment = '#', index_col=0, header=0)    
    
    return data

yaml_import_lib = {'data': process_data_import}

## list of prerequisites for module
prereq_comps = []

## component summary
def component_summary (coms, res_dir):
    """
    creates a log for the non-residental component outputs by community
    
    pre:
        coms: the run model outputs: a dictionary 
                    {<"community_name">:
                        {'model':<a run driver object>,
                        'output dir':<a path to the given communites outputs>
                        },
                     ... repeated for each community
                    }
        res_dir: directory to save the log in
    
    post:
        a csv file "non-residential_summary.csv"log is saved in res_dir   
    
    """
    out = []
    for c in sorted(coms.keys()):
        if c.find('+') != -1 or c.find("_intertie") != -1:
            continue
        try:
            www = coms[c]['model'].comps_used['water wastewater']
            try:
                oil_p, elec_p =  www.hoil_price[0], www.elec_price[0]
            except AttributeError:
                oil_p, elec_p = 0,0
            
            savings = www.baseline_fuel_Hoil_consumption -\
                      www.refit_fuel_Hoil_consumption
            out.append([c,
                www.get_NPV_benefits(),www.get_NPV_costs(),
                www.get_NPV_net_benefit(),www.get_BC_ratio(),
                oil_p, elec_p ,
                #~ www.num_buildings , www.refit_sqft_total,
                www.break_even_cost,
                www.levelized_cost_of_energy['MMBtu'],
                www.levelized_cost_of_energy['kWh'],
                www.baseline_fuel_Hoil_consumption[0],
                www.baseline_kWh_consumption[0],
                savings[0],
                (www.baseline_kWh_consumption - www.refit_kWh_consumption)[0]
                ])
        except (KeyError,AttributeError) as e:
            #~ print c +":"+ str(e)
            pass
            
            
    cols = ['community',
            'Water/Wastewater Efficiency NPV Benefit',
            'Water/Wastewater Efficiency NPV Cost',
            'Water/Wastewater Efficiency NPV Net Benefit',
            'Water/Wastewater Efficiency B/C Ratio',
            'Heating Oil Price - year 1',
            '$ per kWh - year 1',
            #~ 'Number Water/Wastewater Buildings',
            #~ 'Water/Wastewater Total Square Footage',
            'Break Even Diesel Price [$/gal]',
            'Levelized Cost of Energy [$/MMBtu]',
            'Levelized Cost of Energy [$/kWh]',
            'Water/Wastewater Heating Oil Consumed(gal) - year 1',
            'Water/Wastewater Electricity Consumed(kWh) - year 1',
            'Water/Wastewater Efficiency Heating Oil Saved[gal/year]',
            'Water/Wastewater Efficiency Electricity Saved[kWh/year]']
            
    data = DataFrame(out,columns = cols).set_index('community').round(2)
    f_name = os.path.join(res_dir,'water-wastewater_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write("# non residental building component summary by community\n")
    #~ fd.close()
    data.to_csv(f_name, mode='w')

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
        self.component_name = 'water wastewater'
        
        self.diagnostics = diag
        if self.diagnostics == None:
            self.diagnostics = diagnostics()
        
        self.cd = community_data.get_section('community')
        self.comp_specs = community_data.get_section('water wastewater')
        self.forecast = forecast
        
        self.set_project_life_details(self.comp_specs["start year"],
                                      self.comp_specs["lifetime"],
                        self.forecast.end_year - self.comp_specs["start year"])
        
        average = self.comp_specs['average refit cost']
        mult = community_data.get_item('construction multipliers',
                                       self.cd["region"])  
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
        self.calc_base_electric_cost()
        self.calc_proposed_electric_cost ()
        self.annual_electric_savings = self.baseline_kWh_cost - \
                                       self.refit_kWh_cost
    
    def calc_base_electric_cost (self):
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
        
    def calc_proposed_electric_cost (self):
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
        self.refit_kWh_cost = self.refit_kWh_consumption * kWh_cost
    
    def calc_annual_heating_savings (self):
        """
        calculate the annual heating savings 
        pre:
            none
        post:
            self.annual_heating_savings is an np.array of $/year values (floats) 
        over the project lifetime
        """
        self.calc_proposed_heating_cost()
        self.calc_base_heating_cost()
        # $ / yr
        self.annual_heating_savings = self.baseline_HF_cost - self.refit_HF_cost
        
    def calc_proposed_heating_cost (self):
        """
        calcualte the savings for the proposed heating savings
        pre:
            self.diesel_prices is an array of dollar values over the project 
        lifetime (floats)
            'heating fuel premium' $/gal (float)
        post:
           self.refit_HF_cost is an np.array of $/year values (floats) over the
        project lifetime
        """
        self.refit_HF_cost = np.zeros(self.project_life)
        fuel_cost = self.diesel_prices + self.cd['heating fuel premium']# $/gal
        wood_price = self.cd['cordwood price']
        # are there ever o&m costs
        # $/gal * gal/yr = $/year 
        self.refit_HF_cost += \
                self.refit_fuel_Hoil_consumption * fuel_cost +\
                self.refit_fuel_biomass_consumption * wood_price
        
    def calc_base_heating_cost (self):
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
        
    def run (self):
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
            self.calc_refit_kWh_consumption()
            self.calc_savings_kWh_consumption()
        
        if self.cd["model heating fuel"]:
            self.calc_baseline_HF_consumption()
            self.calc_refit_HF_consumption()
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
            
            self.calc_annual_costs(self.cd['interest rate'])
            self.calc_annual_net_benefit()
            self.calc_npv(self.cd['discount rate'], self.cd["current year"])
            self.calc_levelized_costs(0)

    
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
            
    def calc_refit_kWh_consumption (self):
        """
        calculate post refit kWh use
        pre:
            self.comp_specs['electricity refit reduction'] < 1, > 0 (float) 
            self.comp_specs['data'].ix['kWh/yr'] is a price (kWh/yr) (float)
            self.comp_specs['data'].ix['kWh/yr w/ retro'] is a price (kWh/yr) 
        (float)
            NOTE: if the prices are Nan or 0 they are not used
        post:
            self.refit_kWh_consumption is an array of kWh/yr (floats) over 
        the project lifetime 
        """
        percent = 1 - self.comp_specs['electricity refit reduction']
        con = np.float64(self.comp_specs['data'].ix['kWh/yr'])
        retro_con = np.float64(self.comp_specs['data'].ix['kWh/yr w/ retro']) 
        if (not (np.isnan(con) and np.isnan(retro_con))) and \
                (con != 0 and retro_con != 0):
            percent = retro_con/con
        consumption = self.baseline_kWh_consumption * percent
        self.refit_kWh_consumption = consumption 

    def calc_refit_HF_consumption (self):
        """
        calculate post refit HF use
        pre:
            self.comp_specs['heating fuel refit reduction'] < 1, > 0 (float) 
            self.comp_specs['data'].ix['HF Used'] is a price (gal/yr) (float)
            self.comp_specs['data'].ix['HF w/retro'] is a price (gal/yr) (float)
            NOTE: if the prices are Nan or 0 they are not used
        post:
            self.refit_HF_consumption is an array of gal/yr values (floats) over 
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
        self.refit_fuel_Hoil_consumption = consumption
        consumption = self.baseline_fuel_biomass_consumption * percent
        self.refit_fuel_biomass_consumption = consumption
        
        self.refit_HF_consumption = \
                self.refit_fuel_Hoil_consumption/constants.mmbtu_to_gal_HF +\
                self.refit_fuel_biomass_consumption/constants.mmbtu_to_cords
        
    def calc_savings_kWh_consumption (self):
        """
        calculate the savings in kWh use
        pre:
            self.baseline_kWh_consumption, self.refit_kWh_consumption are
        arrays of kWh/year (floats) over the project lifetime
        post:
            self.savings_kWh_consumption arrays of kWh/year savings(floats) 
        over the project lifetime
        """
        self.savings_kWh_consumption = self.baseline_kWh_consumption -\
                                       self.refit_kWh_consumption
                                       
    def calc_savings_HF_consumption (self):
        """
        calculate the savings in HF use
        pre:
            self.baseline_HF_consumption, self.refit_HF_consumption are
        arrays of gal/year (floats) over the project lifetime
        post:
            self.savings_HF_consumption arrays of gal/year savings(floats) 
        over the project lifetime
        """
        
        self.savings_fuel_Hoil_consumption = \
                self.baseline_fuel_Hoil_consumption - \
                self.refit_fuel_Hoil_consumption
        self.savings_fuel_biomass_consumption = \
                self.baseline_fuel_biomass_consumption - \
                self.refit_fuel_biomass_consumption
        self.savings_HF_consumption = \
                self.baseline_HF_consumption - \
                self.refit_HF_consumption
            
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
            self.baseline_fuel_Hoil_consumption[:self.actual_project_life]
        
        proposed_heat = \
            self.refit_fuel_Hoil_consumption[:self.actual_project_life]
            
        
        base_elec = self.baseline_kWh_consumption[:self.actual_project_life] /\
                                self.cd["diesel generation efficiency"]
        
        proposed_elec = self.baseline_kWh_consumption\
                                                [:self.actual_project_life] / \
                                self.cd["diesel generation efficiency"]
        
        return (base_heat - proposed_heat) + (base_elec - proposed_elec)
                                
    def get_total_enery_produced (self):
        """
        returns the total energy produced
        """
        return {'kWh': 
                    self.refit_kWh_consumption[:self.actual_project_life], 
                'MMBtu':
                    self.refit_fuel_Hoil_consumption\
                                                [:self.actual_project_life]*\
                        (1/constants.mmbtu_to_gal_HF)
               }
    
# set WaterWastewaterSystems as component 
component = WaterWastewaterSystems
    


