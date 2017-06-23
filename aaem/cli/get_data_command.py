"""
run_command.py

    A command for the cli to run the model
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
    run command class
    """
    usagestr = ('usage: get-data path_to_data_repo path_to_output')
    optionList = (
            ('force',('f', False, "force overwrite of existing directories")),
           )
    description =('Construct data for model from github and api sources'
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
        from pprint import pprint
        #~ pprint(metadata)

        for f in files:
            shutil.copy2(os.path.join(repo,f),out)
        
        self.getpce_data(out)
        self.geteia_data(out)

        with open(os.path.join(out, '__metadata.yaml'),'w') as meta:
            meta.write(yaml.dump(self.metadata, default_flow_style=False))
        
        
        with open(os.path.join(out,'VERSION'),'w') as v:
            v.write('generated from command')
        
        
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
        
    def geteia_data(self, out):
        name = 'eia_sales.csv'
        data = get_api_data('eia_861_retail_sales')
        
        order = [
            u'id', u'year', u'utility', u'residential_revenues',
            u'residential_customers', u'commercial_revenues', u'commercial_sales', u'commercial_customers',
            u'industrial_revenues', u'indestrial_customers', u'total_revenue',
            u'total_sales', u'total_customers',
            ]
        col_names = [
            'id', 'year', 'utility', 'Residential Thousand Dollars', 'Residential Megwatthours',
            'Residential Count', 'Commercial Thousand dollars', 'Commercial Megwatthours', 'Commercial Count',
            'Industrial Thousand Dollars', 'Industrial Megwatthours', 'Industrial Count', 'Total Thousand Dollars',
            'Total Megawatthours', 'Total CustomerCount'
            ]

        data[order].to_csv(os.path.join(out,name),index = col_names)
        
        self.metadata[name] = 'api - ' + str(datetime.now()) 
        
