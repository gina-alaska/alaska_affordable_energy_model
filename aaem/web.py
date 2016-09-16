from jinja2 import Environment, PackageLoader
import aaem.driver as driver
from pandas import concat, DataFrame
import os

from importlib import import_module
from aaem.components import comp_lib

class WebSummary(object):
    """ Class doc """
    
    def __init__ (self, model_root, directory):
        """ Class initialiser """
        self.model_root = model_root
        model = driver.Driver(self.model_root)
        self.results = model.load_results()
        
        self.directory = directory
        try:
            os.makedirs(os.path.join(self.directory,'csv'))
        except OSError:
            pass
            
        self.env = Environment(loader=PackageLoader('aaem','templates/'))

    def get_viable_components (self, com, cutoff = 1):
        """ Function doc """
        l = []
        for comp in self.results[com]:
            try:
                if self.results[com][comp].get_BC_ratio() >= cutoff:
                    l.append(comp)
            except AttributeError:
                pass
            
        return l
        
    def generate_web_summaries (self, com):
        """
        """
        #~ comps = self.get_viable_components(com)
        
        for comp in comp_lib:
            try:
                self.get_web_summary(comp_lib[comp])(self, com)
            except AttributeError as e:
                print e
                pass
            except KeyError:
                pass
            except ValueError:
                pass
        
    def get_web_summary(self, component):
        """
        """
        try:
            return self.imported_summaries[component].generate_web_summary
        except AttributeError:
            self.imported_summaries = {}
        except KeyError:
            pass
            
        self.imported_summaries[component] = \
                    import_module("aaem.components." + component).outputs
        return self.imported_summaries[component].generate_web_summary
    

    def generate_all (self):
        """ Function doc """
        keys = sorted([k for k in self.results.keys() if k.find('+') == -1])
        for com in keys:
            self.generate_web_summaries(com)
