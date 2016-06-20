"""
component_template.py

a template for adding components



"""
import numpy as np
from math import isnan
from pandas import DataFrame,concat
import os
from copy import deepcopy

from annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import diagnostics
import aaem.constants as constants


import ashp_base 


# change to component name (i.e. 'residential buildings')
COMPONENT_NAME = "ASHP residential"

## List of yaml key/value pairs
yaml = deepcopy(ashp_base.yaml)
yaml[ "btu/hrs"] = 18000
yaml[ "cost per btu/hrs" ] = 6000 

## default values for yaml key/Value pairs
yaml_defaults = deepcopy(ashp_base.yaml_defaults)
    
## order to save yaml
yaml_order = deepcopy(ashp_base.yaml_order) 

## comments for the yaml key/value pairs
yaml_comments = deepcopy(ashp_base.yaml_comments)

       
    
## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = deepcopy(ashp_base.yaml_import_lib)
    
raw_data_files = deepcopy(ashp_base.raw_data_files)

## list of wind preprocessing functions
preprocess_funcs = [deepcopy(ashp_base.preprocess)]

## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = deepcopy(ashp_base.yaml_not_to_save)
    
## component summary
def component_summary (coms, res_dir):
    """
    save thes the summary for biomass cordwood
    """
    out = []
    for c in sorted(coms.keys()):
        #~ it = coms[c]['model'].cd.intertie
        #~ if it is None:
            #~ it = 'parent'
        #~ if it == 'child':
            #~ continue
        if c.find("_intertie") != -1:
            continue
        try:
            
            ashp = coms[c]['model'].comps_used[COMPONENT_NAME]
            try:
                peak_monthly_btu_hr_hh = ashp.peak_monthly_btu_hr_hh
                price =  float(ashp.electricity_prices.ix[ashp.start_year])
                #~ print float(ashp.electricity_prices.ix[ashp.start_year])
            except AttributeError:
                peak_monthly_btu_hr_hh = 0
                price = 0
           
        
            
            l = [c, 
                 ashp.average_cop,
                 ashp.num_houses,
                 peak_monthly_btu_hr_hh,
                 price,
                 ashp.electric_consumption,
                 ashp.heating_oil_saved,
                 ashp.electric_heat_energy_reduction,
                 ashp.get_NPV_benefits(),
                 ashp.get_NPV_costs(),
                 ashp.get_NPV_net_benefit(),
                 ashp.get_BC_ratio(),
                 ashp.reason
                ]
            out.append(l)
            
        except (KeyError,AttributeError) as e:
            #~ print e
            pass
    
    data = DataFrame(out,columns = \
       ['Community',
        "Average Coefficient of Performance (COP)",
        'Number Houses',
        'Peak Household Monthly Btu/hr',
        'Electricity Price [$/kWh]',
        'kWh consumed per year',
        "Displaced Heating Oil [Gal]",
        "Displaced Electricity [kWh]",
        'NPV benefits [$]',
        'NPV Costs [$]',
        'NPV Net benefit [$]',
        'Benefit Cost Ratio',
        'notes']
                    ).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.replace(" ","_") + '_summary.csv')
    fd = open(f_name,'w')
    fd.write(("# " + COMPONENT_NAME + " summary\n"))
    fd.close()
    data.to_csv(f_name, mode='a')

## list of prerequisites for module
prereq_comps = ['residential buildings']

class ASHPResidential (ashp_base.ASHPBase):
    """
    cordwood biomass componenet
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
        """
        load variables from prerequisites
        
        pre:
             prerequisites: dictonary of componentes
        """
        res = comps['residential buildings']
        self.pre_ashp_heating_oil_used =  res.init_HF
        self.pre_ashp_heating_electricty_used = res.init_kWh
        self.num_houses = res.init_HH
        #~ print self.pre_ashp_heating_oil_used
        #~ print self.num_houses
        
        
    def calc_heat_energy_produced_per_year (self):
        """
        """
        self.heat_energy_produced_per_year = self.pre_ashp_heating_oil_used * \
                        self.comp_specs["heating oil efficiency"]*(1/constants.mmbtu_to_gal_HF)
        #~ print self.heat_energy_produced_per_year
       
    def calc_electric_heat_energy_reduction (self):
        """
        """
        self.electric_heat_energy_reduction = self.pre_ashp_heating_electricty_used/ self.average_cop
        
    
    def calc_electric_heat_energy_savings (self):
        """
        """
        self.electric_heat_energy_savings = self.electric_heat_energy_reduction *  self.electricity_prices
        self.electric_heat_energy_savings = self.electric_heat_energy_savings.values.T[0]
        
        
    def run (self):
        """
        run the forecast model
        
        pre:
            self.cd should be the community library from a community data object
        post:
            TODO: define output values. 
            the model is run and the output values are available
        """
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
            self.calc_annual_costs(self.cd['interest rate'])
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


    def calc_capital_costs (self):
        """
        calculate the captial costs
        """
        heating_oil = ((self.pre_ashp_heating_oil_used/self.num_houses)*self.comp_specs["heating oil efficiency"]) / constants.mmbtu_to_gal_HF *1e6/ constants.hours_per_year
        electric_heat = (self.pre_ashp_heating_electricty_used/self.num_houses) / constants.mmbtu_to_kWh *1e6/ constants.hours_per_year
        average_btu_per_hr =  heating_oil + electric_heat
        peak_monthly_btu_hr_hh = float(self.comp_specs['data'].ix['Peak Month % of total']) * average_btu_per_hr * 12
        self.peak_monthly_btu_hr_hh=peak_monthly_btu_hr_hh
        
        self.capital_costs = self.num_houses * round((peak_monthly_btu_hr_hh/self.comp_specs["btu/hrs"]) * self.comp_specs["cost per btu/hrs"])*self.regional_multiplier

    def save_component_csv (self, directory):
        """
        save the component output csv in directory
        """
        years = np.array(range(self.project_life)) + self.start_year
    
        try:
            val = self.peak_monthly_btu_hr_hh
            prices = self.electricity_prices.values.T[0].tolist()
        except AttributeError:
            val = 0
            prices = 0
            
        #~ print prices
        df = DataFrame({
                "community":self.cd['name'],
                "Average Coefficient of Performance (COP)": self.average_cop,
                'Number Houses':self.num_houses,
                'Peak Household Monthly Btu/hr': val,
                'Electricity Price [$/kWh]':prices,
                'kWh consumed per year':self.electric_consumption,
                "Displaced Heating Oil [Gal]": self.heating_oil_saved,
                
                
                "Project Capital Cost": self.get_capital_costs(),
                "Total Cost Savings": self.get_total_savings_costs(),
                "Net Benefit": self.get_net_beneft(),
                       }, years)

        order = ["community", "Average Coefficient of Performance (COP)",
                 'Number Houses', 'Peak Household Monthly Btu/hr',
                 'Electricity Price [$/kWh]', 'kWh consumed per year',
                 "Displaced Heating Oil [Gal]", "Project Capital Cost",
                 "Total Cost Savings", "Net Benefit"]
                
        fname = os.path.join(directory,
                                   self.component_name + "_output.csv")
        fname = fname.replace(" ","_")
        
        
        fin_str = "Enabled" if self.cd["model financial"] else "Disabled"
        fd = open(fname, 'w')
        fd.write("# " + self.component_name + " model outputs\n") 
        fd.close()
        
        # save npv stuff
        df2 = DataFrame([self.get_NPV_benefits(),self.get_NPV_costs(),
                            self.get_NPV_net_benefit(),self.get_BC_ratio()],
                       ['NPV Benefits','NPV Cost',
                            'NPV Net Benefit','Benefit Cost Ratio'])
        df2.to_csv(fname, header = False, mode = 'a')
        
        # save to end of project(actual lifetime)
        df[order].ix[:self.actual_end_year].to_csv(fname, index_label="year", 
                                                                    mode = 'a')

component = ASHPResidential

