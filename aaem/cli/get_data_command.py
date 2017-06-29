"""
get_data_command.py

    A command for the cli to pull in data from the Alaska Energy Data Gateway.
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
        metadata = {f: 'repo - '+ version for f in files}
        from pprint import pprint
        #~ pprint(metadata)


        for f in files:
            shutil.copy2(os.path.join(repo,f),out)

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

        metadata[name] = 'api - ' + str(datetime.now())


        with open(os.path.join(out, '__metadata.yaml'),'w') as meta:
            meta.write(yaml.dump(metadata, default_flow_style=False))


        with open(os.path.join(out,'VERSION'),'w') as v:
            v.write('generated from command')
