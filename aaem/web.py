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
                if self.results[com][comp].get_BC_ratio() == 'N/A':
                    continue
                if self.results[com][comp].get_BC_ratio() >= cutoff:
                    l.append(comp)
            except AttributeError:
                pass
            
        return l
        
    def generate_web_summaries (self, com):
        """
        """
        #~ comps = self.get_viable_components(com)
        self.gennerate_community_summary(com)
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
            
    def gennerate_community_summary(self, community):
        """ Function doc """
        template = self.env.get_template('summary.html')
        pth = os.path.join(self.directory, community + '.html')
        
        comps = []
        for i in [i for i in sorted(self.results.keys()) \
                            if i.find(community) != -1 ]:
            for c in self.get_viable_components(i):
                if i.find('hydro') != -1 and c == 'Hydropower':
                    comp = self.results[i]['Hydropower']
                    ratio = comp.get_BC_ratio()
                    name = comp.comp_specs['project details']['name']
                elif i.find('wind') != -1 and c == 'wind power':
                    comp = self.results[i]['wind power']
                    ratio = comp.get_BC_ratio()
                    name = comp.comp_specs['project details']['name']
                elif i.find('heat_recovery') != -1 and c == 'heat recovery':
                    comp = self.results[i]['heat recovery']
                    ratio = comp.get_BC_ratio()
                    name = comp.comp_specs['project details']['name']
                else:
                    comp = self.results[i][c]
                    ratio = comp.get_BC_ratio()
                    name = i + ' Modled'
                comps.append({'com':name,'comp':c, 'r': '{:,.3f}'.format(ratio)})
            
        
        
        
        with open(pth, 'w') as html:
            html.write(template.render( info = comps , com = community))
