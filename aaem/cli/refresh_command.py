"""
refresh_command.py

    A commad for the cli to refresh the data
"""
import pycommand
import sys
import os.path
import shutil
import zipfile
from aaem import driver, __version__
from datetime import datetime
from pandas import read_csv
from default_cases import __DEV_COMS__
import cli_lib

class RefreshCommand(pycommand.CommandBase):
    """
    refesh command class
    refesh command class
    """
    usagestr = 'usage: refresh model_dir data_repo'
    optionList = (
           ('dev', ('d', False, "use only development communities")),
           #~ ('path', ('p', "<name>", "path to location to setup/run  model")),
           #~ ('name', ('n', "<name>", "name of model")),
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
        if self.args and os.path.exists(self.args[0]):
            model_root = os.path.abspath(self.args[0])
        else:
            print "Refresh Error: please provide a path to the model"
            return 0
        if self.args and os.path.exists(self.args[1]):
            repo = os.path.abspath(self.args[1])
        else:
            print "Refresh Error: please provide a path to the aaem data repo"
            return 0

        try:
            fd = open(os.path.join(model_root,'setup','raw_data',"VERSION"),'r')
            ver = fd.read().replace("\n","")
            fd.close()
        except IOError:
            ver = "unknown_version_backup_"+ datetime.strftime(datetime.now(),
                                                                    "%Y%m%d")
        #~ print ver
        try:
            z = zipfile.ZipFile(os.path.join(model_root,
                                "setup","data_"+ver+".zip"),"w")
            for fn in os.listdir(os.path.join(model_root,"setup","raw_data")):
                z.write(os.path.join(model_root,"setup","raw_data",fn),
                                        os.path.join("raw_data",fn))
            for fn in os.listdir(os.path.join(model_root,"setup","input_data")):
                z.write(os.path.join(model_root,"setup","input_data",fn),
                                        os.path.join("input_data",fn))
                if os.path.isdir(os.path.join(model_root,"setup",
                                                              "input_data",fn)):
                    for fn2 in os.listdir(os.path.join(model_root,
                                         "setup","input_data",fn)):
                        z.write(os.path.join(model_root,"setup","input_data",
                                    fn,fn2), os.path.join("input_data",fn,fn2))
            z.close()
            shutil.rmtree(os.path.join(model_root,"setup","input_data"))
        except OSError:
            pass

        try:
            shutil.rmtree(os.path.join(model_root,"setup","raw_data"))
        except OSError:
            pass

        raw = os.path.join(model_root, 'setup', "raw_data")
        os.makedirs(os.path.join(model_root, 'setup',"raw_data"))
        
        cli_lib.copy_model_data (repo, raw)
        #avaliable coms
        if self.flags.dev:
            coms = __DEV_COMS__
            interties = False
        else:
            coms = read_csv(os.path.join(raw,'community_list.csv'),
                         comment="#",index_col=0).Community.tolist()
            interties = True
        try:
            fd = open(os.path.join(model_root,'setup','raw_data',"VERSION"),'r')
            ver = fd.read().replace("\n","")
            ver = 'm'+ __version__ +'_d' +ver
            fd.close()
        except IOError:
            ver = "unknown_version_created_"+ datetime.strftime(datetime.now(),
                                                                    "%Y%m%d")
        coms = sorted(coms)
        driver.setup(coms, raw, model_root, run_name = ver,
                     setup_intertie = interties)
