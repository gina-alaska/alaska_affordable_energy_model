from jinja2 import Environment, PackageLoader
import aaem.driver as driver
from pandas import concat, DataFrame
import os

from importlib import import_module
from aaem.components import comp_lib, comp_order

#WHAT TO DO IF ALL PLOT DATA IS NANS?

class WebSummary(object):
    """ Class doc """
    
    def __init__ (self, model_root, directory, tag = ''):
        """ Class initialiser """
        self.model_root = model_root
        model = driver.Driver(self.model_root)
        self.results = model.load_results(tag)
        
        self.directory = directory
        try:
            os.makedirs(os.path.join(self.directory,'csv'))
        except OSError as e:
            print e
            pass
        #~ print "fine"
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
            except AttributeError as e:
                print e
                pass
        
        return l
        
    def generate_web_summaries (self, com):
        """
        """
        print com
        #~ comps = self.get_viable_components(com)
        self.gennerate_community_summary(com)
        for comp in comp_lib:
            #~ print comp
            try:
                self.get_web_summary(comp_lib[comp])(self, com)
            except (AttributeError, StandardError) as e:
                print comp, e
                template = self.env.get_template('no_results.html')
                #~ if comp in ['Solar Power','Wind Power','Heat Recovery'] :
                pth = os.path.join(self.directory, com + '_' + comp.replace(' ','_').replace('(','').replace(')','').lower() +'.html')
                    #~ t = comp
                #~ print comp, e
                #~ elif comp == 'Wind Power':
                    #~ pth = os.path.join(self.directory, com +'_wind_summary.html')
                    #~ t = 'Wind Power'
                    #~ print comp, e
                #~ elif comp == 'Heat Recovery':
                    #~ pth = os.path.join(self.directory, com +'_heat_recovery_summary.html')
                    #~ t = 'Heat Recovery'
                    #~ print comp, e
                #~ else:
                    #~ continue
                with open(pth, 'w') as html:
                    reason = self.results[com][comp].reason
                    html.write(template.render( 
                                    type = comp, 
                                    com = com ,
                                    reason = reason,
                                    summary_pages = ['Summary'] + comp_order ))
                pass

        
    def get_web_summary(self, component):
        """
        """
        try:
            return self.imported_summaries[component].generate_web_summary
        except AttributeError as e:
            print e
            self.imported_summaries = {}
        except KeyError as e:
            print e
            pass
            
        self.imported_summaries[component] = \
                    import_module("aaem.components." + component).outputs
        return self.imported_summaries[component].generate_web_summary
    

    def generate_all (self):
        """ Function doc """
        keys = sorted([k for k in self.results.keys() if k.find('+') == -1])
        for com in keys:
            self.generate_web_summaries(com)
            return
            
    def gennerate_community_summary(self, community):
        """ Function doc """
        template = self.env.get_template('summary.html')
        pth = os.path.join(self.directory, community + '_summary.html')
        
        comps = []
        for i in [i for i in sorted(self.results.keys()) \
                            if i.find(community) != -1 ]:
            
            for c in self.get_viable_components(i):
                #~ print i, c
                if i.find('hydro') != -1 and c == 'Hydropower':
                    comp = self.results[i]['Hydropower']
                    ratio = comp.get_BC_ratio()
                    name = comp.comp_specs['project details']['name']
                elif i.find('wind') != -1 and c == 'Wind Power':
                    comp = self.results[i]['Wind Power']
                    ratio = comp.get_BC_ratio()
                    name = comp.comp_specs['project details']['name']
                elif i.find('heat_recovery') != -1 and c == 'Heat Recovery':
                    comp = self.results[i]['Heat Recovery']
                    ratio = comp.get_BC_ratio()
                    name = comp.comp_specs['project details']['name']
                else:
                    comp = self.results[i][c]
                    ratio = comp.get_BC_ratio()
                    name = i + ' Modled'
                comps.append({'com':name.decode('unicode_escape').encode('ascii','ignore'),'comp':c, 'r': '{:,.3f}'.format(ratio)})
            
        #~ print comps
        
        
        with open(pth, 'w') as html:
            html.write(template.render( info = comps , com = community,
                                        summary_pages = ['Summary'] + comp_order ))
