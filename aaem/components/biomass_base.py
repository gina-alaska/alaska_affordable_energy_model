"""
biomass_base.py

biomass component base 
"""
import numpy as np
from math import isnan
from pandas import DataFrame,concat, read_csv
import os

from annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import diagnostics
import aaem.constants as constants



COMPONENT_NAME = "biomass base"

## List of yaml key/value pairs
yaml = {'enabled': False,
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        'heating oil efficiency': .75,
        'energy density': 'ABSOLUTE DEFAULT',
        'data': 'IMPORT',
        'percent sqft assumed heat displacement': .3,
        }

## default values for yaml key/Value pairs
yaml_defaults = {'enabled': True,
        'lifetime': 20,
        'start year': 2017,
        }
    
## order to save yaml
yaml_order = ['enabled', 'lifetime', 'start year','heating oil efficiency',
               'energy density', 'data']

## comments for the yaml key/value pairs
yaml_comments = {'enabled': '',
        'lifetime': 'number years <int>',
        'start year': 'start year <int>',
        'heating oil efficiency': '% as decimal <float>',
        'energy density': 'BTU/fuel unit (specified in child) <float>',
        'data': 'biomass data'}
        
## Functions for CommunityData IMPORT keys
def process_data_import(data_dir):
    """
    """
    data_file = os.path.join(data_dir, "biomass_data.csv")
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    data = data['value'].to_dict()
    data['Peak Month % of total'] = float(data['Peak Month % of total'])
    data['Capacity Factor'] = float(data['Capacity Factor'])
    data['Distance'] = float(data['Distance'])
    return data

## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = {'data':process_data_import,}

## preprocessing functons 
def preprocess_header (ppo):
    """
    pre: 
        ppo is a preprocessor object
    post:
        returns the biomass header
    """
    return  "# " + ppo.com_id + " biomass data\n"+ \
            "# biomass data from biomass_data.csv preprocessed into a \n" +\
            "# based on the row for the given community \n" +\
            ppo.comments_dataframe_divide
    
def preprocess (ppo):
    """
    preprocess biomass data
    pre: 
        ppo is a preprocessor object
    post:
        saves "biomass_data.csv", and updates MODEL_FILES
    """
    data = read_csv(os.path.join(ppo.data_dir,"biomass_data.csv"),
                        comment = '#',index_col = 0).ix[ppo.com_id]
                        
    out_file = os.path.join(ppo.out_dir,"biomass_data.csv")

    fd = open(out_file,'w')
    fd.write(preprocess_header(ppo))
    fd.write("key,value\n")
    fd.close()

    # create data and uncomment this
    data.to_csv(out_file, mode = 'a',header=False)
    
    ppo.MODEL_FILES['COMP_DATA'] = "biomass_data.csv" # change this

## List of raw data files required for wind power preproecssing 
raw_data_files = ['biomass_data.csv']

## list of wind preprocessing functions
preprocess_funcs = [preprocess]

## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = []



       
#   do a find and replace on ComponentName to name of component 
# (i.e. 'ResidentialBuildings')
class BiomassBase (AnnualSavings):
    """
    class containing data and functions common to biomass componentes 
    """
    def __init__ (self, community_data, forecast, diag = None):
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
       
        self.comp_specs = community_data.get_section(self.component_name)
        

        self.set_project_life_details(self.comp_specs["start year"],
                                      self.comp_specs["lifetime"],
                        self.forecast.end_year - self.comp_specs["start year"])
    
        #~ print self.comp_specs['data']
                
        self.non_res_sqft = 0
        self.avg_gal_per_sqft = 0
        self.biomass_type = "NA"
        self.units = "NA"
        self.get_non_res_values(community_data.get_item(
                                            'non-residential buildings',
                                            'com building data'))
        
    def get_non_res_values (self, non_res):
        """
            get the values nessaery to run the biomass component from
        the non residential buildings component 
        
        pre:
            non_res is a run non residential buildings componet
        post:
            self.non_res_sqft, and self.avg_gal_per_sqft
        are numbers
        """
        self.non_res_sqft = non_res['Square Feet'].sum()
    
        try:
            self.avg_gal_per_sqft = non_res['Fuel Oil'].sum()/ self.non_res_sqft
        except ZeroDivisionError:
            self.avg_gal_per_sqft = 0
        
    def calc_heat_displaced_sqft (self):
        """ 
            calculates the sqft for which biomass will displace heating oil
        as the heating fuel
        
        pre:
            self.non_res_sqft and 'percent sqft assumed heat displacement' in
        in comp_specs are numbers
        """
        self.heat_displaced_sqft = self.non_res_sqft * \
            self.comp_specs['percent sqft assumed heat displacement']
        
    def calc_energy_output (self):
        """
        the net and monthly energy calculated
        
        pre:
            self.avg_gal_per_sqft, self.comp_specs['heating oil efficiency'],
        and self.comp_specs['data']['Peak Month % of total'] 
        post:
            the net and monthly energy calculated
        """
        self.average_net_energy_output = self.avg_gal_per_sqft * \
                                    ((constants.mmbtu_to_gal_HF ** -1) * 1E6 /\
                                    constants.hours_per_year) * \
                                    self.comp_specs['heating oil efficiency']
        self.peak_monthly_energy_output = self.average_net_energy_output * 12 *\
                                self.comp_specs['data']['Peak Month % of total']
        
    def calc_max_boiler_output (self, efficiency):
        """
        calculate the max boiler out put
        """
        self.max_boiler_output_per_sf = self.peak_monthly_energy_output / \
                                        efficiency
        self.max_boiler_output = self.max_boiler_output_per_sf * \
                                    self.heat_displaced_sqft
        
    def calc_biomass_fuel_consumed (self, capacity_factor):
        """
        calc amount of biomass fuel consumed
        """
        self.biomass_fuel_consumed = capacity_factor * self.max_boiler_output *\
                                     constants.hours_per_year /\
                                     self.comp_specs['energy density']
        
    def calc_diesel_displaced (self):
        """
        calculate the disel of set by biomass
        """
        self.heat_diesel_displaced = self.biomass_fuel_consumed * \
                                     self.comp_specs['energy density'] * \
                                     (constants.mmbtu_to_gal_HF / 1e6)
        
    def calc_maintainance_cost(self):
        """
        calculate the maintanence costs
        """
        self.maintenance_cost = 0
        
    def calc_proposed_biomass_cost (self, price):
        """ 
            calcualte cost of biomass fuel
        """
        self.proposed_biomass_cost = price * self.biomass_fuel_consumed
        
    def calc_displaced_heating_oil_price (self):
        """
            calculate cost of displaced diesel
        """
        price = (self.diesel_prices + self.cd['heating fuel premium'])
        self.displaced_heating_oil_price = price * self.heat_diesel_displaced 
        #~ print 'self.displaced_heating_oil_price'
        #~ print self.displaced_heating_oil_price
    
    def run (self):
        """
        run the forecast model
        
        pre:
            self.cd should be the community library from a community data object
        post:
            TODO: define output values. 
            the model is run and the output values are available
        """
        pass
        
        # Make this do stuff
    def calc_capital_costs (self):
        """
        caclulate the captial costs
        """
        pass
        
    
    # Make this do stuff
    def calc_annual_electric_savings (self):
        """
        no electric savings 
        """
        self.annual_electric_savings = 0
        
        
    # Make this do sruff. Remember the different fuel type prices if using
    def calc_annual_heating_savings (self):
        """
        clacluate the annual heating savings
        """
        self.annual_heating_savings = self.displaced_heating_oil_price -\
                                      self.proposed_biomass_cost 
                                
    def save_component_csv (self, directory):
        """
        save the component output csv in directory
        """
        fuel_consumed_key = 'Proposed ' +self.biomass_type \
                                        + " Consumed [" + self.units +"]"
        eng_density_key = "Energy Density [Btu/"+self.units+"]"
        years = np.array(range(self.project_life)) + self.start_year
    
        df = DataFrame({
                "community":self.cd['name'],
                "Maximum Boiler Output [Btu/hr]": self.max_boiler_output,
                'Heat Displacement square footage [Sqft]':
                                                self.heat_displaced_sqft,
                eng_density_key: self.comp_specs['energy density'],
                fuel_consumed_key: self.biomass_fuel_consumed,
                'Price [$/' + self.units + ']':self.heat_displaced_sqft,
                "Displaced Heating Oil [Gal]": self.heat_diesel_displaced,
                
                
                "Project Capital Cost": self.get_capital_costs(),
                "Total Cost Savings": self.get_total_savings_costs(),
                "Net Benefit": self.get_net_beneft(),
                       }, years)

        order = ["community", "Maximum Boiler Output [Btu/hr]",
                 eng_density_key, fuel_consumed_key,
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
    
    

component = BiomassBase

    
