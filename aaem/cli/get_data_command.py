"""
get_data_command.py

    A command for the cli to get data for the model
"""
import pycommand
#~ from default_cases import __DEV_COMS_RUN__ as __DEV_COMS__ 
import os
import shutil
#~ import sys
import cli_lib
import yaml
#~ from aaem import driver
from datetime import datetime
from aaem.getapi import get_api_data

class GetDataCommand(pycommand.CommandBase):
    """
    get data command class
    """
    usagestr = ('usage: get-data path_to_data_repo path_to_output')
    optionList = (
            ('force',('f', False, "force overwrite of existing directories")),
           )
    description =('Construct data for model from github and api sources, This command should be considered EXPERMENTAL'
                    'options: \n'
                   "  " + str([o[0] + ': ' + o[1][2] + '. Use: --' +\
                   o[0] + ' (-'+o[1][0]+') ' +  (o[1][1] if o[1][1] else "")  +\
                   '' for o in optionList]).replace('[','').\
                   replace(']','').replace(',','\n') 
                )
                
    def run(self):
        """
        run the command
        """
        # get arguments
        print "WARNING: this command may not produce desired results"
        if len(self.args) != 2:
            msg = ("GET-DATA ERROR: provide path to the repo, and a"
                    " path to output")
            cli_lib.print_error_message(msg, GetDataCommand.usagestr)
            return 0
            
        if self.args and os.path.exists(self.args[0]):
            repo = os.path.abspath(self.args[0])
            print repo
        else:
            msg = "GET-DATA ERROR: path to the repo must exist"
            cli_lib.print_error_message(msg, GetDataCommand.usagestr)
            return 0 
        
        
        out = os.path.abspath(self.args[1])
        #~ else:
            #~ msg = "GET-DATA ERROR: needs an output directory"
            #~ cli_lib.print_error_message(msg, GetDataCommand.usagestr)
            #~ return 0    
        print out
        
        force = True
        if self.flags.force is None:
            force = False
            
        if os.path.exists(out) and force:
            shutil.rmtree(out)
        elif not os.path.exists(out):
            pass
        else:
            msg =  "RUN ERROR: " + out + \
                            " exists. Use force flag (-f) to overwrite"
            cli_lib.print_error_message(msg, GetDataCommand.usagestr)
            return 0 
        
        os.makedirs(out)
        
        with open(os.path.join(repo,'VERSION'),'r') as v:
            version = v.read().strip()
        
        formats = ['csv', 'yaml']
        files = [f for f in os.listdir(repo) if f.split('.')[-1] in formats]
        self.metadata = {f: 'repo - '+ version for f in files}
        #~ from pprint import pprint
        #~ pprint(metadata)

        for f in files:
            shutil.copy2(os.path.join(repo,f),out)
        
        try:
            self.id_data = self.get_id_data()
        except:
            self.id_data = None
            print 'Error retrieving community ID data. Using repo version'
        
        try:
            self.getpce_data(out)
        except:
            print 'Error retrieving PCE data. Using repo version'

        #~ self.geteia_data(out)# wont work api doesn't have proper forgien keys
        
        try:
            self.getdph_data(out)
        except:
            print 'Error retrieving power house data. Using repo version'
            
        try:
            self.getfps_data(out)
        except:
            print 'Error retrieving fuel price survey. Using repo version'

        with open(os.path.join(out, '__metadata.yaml'),'w') as meta:
            meta.write(yaml.dump(self.metadata, default_flow_style=False))
        
        
        with open(os.path.join(out,'VERSION'),'w') as v:
            v.write('generated_from_command')
        
        
    def getpce_data(self, out):
        name = 'power-cost-equalization-pce-data.csv'
        data = get_api_data('pcedata')
        
        order = [
            u'pce_id', u'community_names', u'year', u'month',
            u'residential_rate', u'pce_rate', u'effective_rate', u'fuel_price',
            u'fuel_used_gal', u'fuel_cost', u'diesel_efficiency',
            u'diesel_kwh_generated', u'hydro_kwh_generated',
            u'other_1_kwh_type', u'other_1_kwh_generated', u'other_2_kwh_type',
            u'other_2_kwh_generated', u'purchased_from', u'kwh_purchased',
            u'powerhouse_consumption_kwh', u'residential_kwh_sold',
            u'commercial_kwh_sold', u'community_kwh_sold',
            u'government_kwh_sold', u'unbilled_kwh',
            ]
        data[order].to_csv(os.path.join(out,name),index = False)
        
        self.metadata[name] = 'api - ' + str(datetime.now()) 
        
    def get_id_data (self):
        data = get_api_data('community')
        data = data.set_index('id')
        return data
        
    def geteia_data(self, out): # possible future use
        name = 'eia_sales.csv'
        data = get_api_data('eia_861_retail_sales')
        
        data['Community'] = ''
        
        order = [
            u'year', u'utility', 'Community',
            u'residential_revenues', u'residential_sales', u'residential_customers',
            u'commercial_revenues', u'commercial_sales', u'commercial_customers',
            u'industrial_revenues', u'industrial_sales', u'industrial_customers',
            u'total_revenue', u'total_sales', u'total_customers',
            ]
        col_names = [
            'Data Year', 'Utility Number', 'Community', 
            'Residential Thousand Dollars', 'Residential Megwatthours', 'Residential Count',
            'Commercial Thousand dollars', 'Commercial Megwatthours','Commercial Count',
            'Industrial Thousand Dollars', 'Industrial Megwatthours', 'Industrial Count',
            'Total Thousand Dollars', 'Total Megawatthours', 'Total CustomerCount'
            ]
        
        
        ### LOOP FOR REPLACING IDS
        #~ for cid in sorted(list(data['id'].values)):
            #~ data['id'].replace(
                #~ [cid],
                #~ [self.id_data.ix[cid]['name']],
                #~ inplace=True
            #~ )
            
                
        data = data[order]
        data.columns = col_names
        data.to_csv(os.path.join(out,name),index = False)
        
        self.metadata[name] = 'api - ' + str(datetime.now()) 
        
    # Get diesel powerhouse data
    def getdph_data(self, out):
        name = 'diesel_powerhouse_data.csv'
        data = get_api_data('power_house')
        
        #~ data['Community'] = ''

        order = [
            'community', 'total_generators', 'total_capacity',
            'Largest generator (in kW)','Sizing',
            "control_switchgear", "waste_heat_recovery_operational",
            "add_waste_heat_available",
            "est_curret_annual_heating_fuel_displaced",
            "est_potential_annual_heating_fuel_displaced"
            ]
        col_names = [
            'Community', 'Total Number of generators', 'Total Capacity (in kW)',
            'Largest generator (in kW)','Sizing',
            "Switchgear Suitable", "Waste Heat Recovery Opperational",
            "Add waste heat Avail",
            "Est. current annual heating fuel gallons displaced",
            "Est. potential annual heating fuel gallons displaced"
            ]
        
        
        #~ ### LOOP FOR REPLACING IDS
        for cid in sorted(list(data['community'].values)):
            data['community'].replace(
                [cid],
                [self.id_data.ix[cid]['name']],
                inplace=True
            )
        
        data['Sizing'] = 'unknown'
        data['Largest generator (in kW)'] = 'unknown'
    
        data = data[order]
        data.columns = col_names
        
        
        data.to_csv(os.path.join(out,name),index = False)
        self.metadata[name] = 'api - ' + str(datetime.now()) 
        
    def getfps_data(self, out):
        """get fuel price survey data
        """
        name = 'fuel-price-survey-data.csv'
        data = get_api_data('ahfc_fuel_survey_data')
        
        #~ data['Community'] = ''

        order = [
            'community__name',
            'community__gnis_feature_id',
            'community__census_code',
            'year','month',
            'no_1_fuel_oil_price','no_2_fuel_oil_price',
            'propane_price',
            'birch_price','spruce_price','unspecified_wood_price'
            ]
        
        order = [
            'community__name',
            'community__gnis_feature_id',
            'community__census_code',
            'year','month',
            'no_1_fuel_oil_price','no_2_fuel_oil_price',
            'propane_price',
            'birch_price','spruce_price','unspecified_wood_price'
            ]
        
        ### LOOP FOR REPLACING IDS
        #~ for cid in sorted(list(data['community__name'].values)):
            #~ data['community__name'].replace(
                #~ [cid],
                #~ [self.id_data.ix[cid]['name']],
                #~ inplace=True
            #~ )
        
        data['Sizing'] = 'unknown'
        data['Largest generator (in kW)'] = 'unknown'
    
        data = data[order]
        #~ data.columns = col_names
        
        
        data.to_csv(os.path.join(out,name),index = False)
        self.metadata[name] = 'api - ' + str(datetime.now()) 
