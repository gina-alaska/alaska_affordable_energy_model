"""
refresh_command.py

    A command for the cli to creates a clean model structure.  Used when code base or data change.
"""
import pycommand
import os.path
from pandas import read_csv
from default_cases import __DEV_COMS__
import cli_lib

from aaem import driver

class RefreshCommand(pycommand.CommandBase):
    """
    refresh command class
    refresh command class
    """
    usagestr = 'usage: refresh model_dir data_repo [tag]'
    optionList = (
           ('dev', ('d', False, "use only development communities")),
           ('force',('f', False, "force refresh of existing directory")),
           ('make_globals',
                ('g', False, "make a separate config for global values")
           )
    )

    description = ('Refresh the data from the data repo\n\n'
                   'options: \n'
                   "  " + str([o[0] + ': ' + o[1][2] + '. Use: --' +\
                   o[0] + ' (-'+o[1][0]+') ' +  (o[1][1] if o[1][1] else "")  +\
                   '' for o in optionList]).replace('[','').\
                   replace(']','').replace(',','\n ')
            )

    def run(self):
        """
        run the command
        """
        if self.args and len(self.args) < 2:
            msg = "REFRESH ERROR: please provide a path to the model and " +\
                                  "a path to the aaem data repo"
            cli_lib.print_error_message(msg, RefreshCommand.usagestr)
            return 0

        if self.args and os.path.exists(self.args[0]):
            model_root = os.path.abspath(self.args[0])
        else:
            msg = "REFRESH ERROR: please provide a path to the model"
            cli_lib.print_error_message(msg, RefreshCommand.usagestr)
            return 0

        if self.args and os.path.exists(self.args[1]):
            repo = os.path.abspath(self.args[1])
        else:
            msg = "REFRESH ERROR: please provide a path to the aaem data repo"
            cli_lib.print_error_message(msg, RefreshCommand.usagestr)
            return 0

        if self.args:
            try:
                tag = self.args[2]
            except IndexError:
                tag = None

        force = True
        if self.flags.force is None:
            force = False

        if self.flags.dev:
            coms = __DEV_COMS__
            interties = False
        else:
            coms = read_csv(os.path.join(repo,'community_list.csv'),
                         comment="#",index_col=0).Community.tolist()


        make_globals = True
        if self.flags.make_globals is None:
            make_globals = False

        #~ coms = ['Brevig Mission']
        my_setup = driver.Setup(model_root, repo, sorted(coms), tag)
        if not my_setup.setup(
                    force = force,
                    ng_coms=['Barrow','Nuiqsut'],
                    make_globals = make_globals
                ):
            pth = os.path.join(model_root, my_setup.tag)
            msg = "REFRESH ERRO: " + pth + \
                    " exists. Use force flag (-f) to overwrite"
            cli_lib.print_error_message(msg, RefreshCommand.usagestr)
