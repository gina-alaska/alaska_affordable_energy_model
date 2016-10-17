from jinja2 import Environment, PackageLoader
import aaem.driver as driver
from pandas import concat, DataFrame
import os
import shutil

from importlib import import_module
from aaem.components import comp_lib, comp_order
from aaem import __file__

#WHAT TO DO IF ALL PLOT DATA IS NANS?
#~ import aaem
class WebSummary(object):
    """ Class doc """
    
    def __init__ (self, model_root, directory, tag = ''):
        """ Class initialiser """
        self.model_root = model_root
        model = driver.Driver(self.model_root)
        self.results = model.load_results(tag)
        #~ print self.results
        self.directory = directory
        try:
            os.makedirs(os.path.join(self.directory,'csv'))
        except OSError as e:
            #~ print e
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
                #~ print e
                pass
        
        return l
        
    def generate_web_summaries (self, com):
        """
        """
        #~ print com
        #~ comps = self.get_viable_components(com)
        self.gennerate_community_summary(com)
        self.summary_1(com)
        #~ self.get_web_summary(comp_lib['Biomass for Heat (Cordwood)'])(self, com)
        #~ return 
        
        for comp in comp_lib:
            #~ print comp
            try:
                self.get_web_summary(comp_lib[comp])(self, com)
            except (AttributeError, RuntimeError) as e:
                #~ print comp, e
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
                                    sections = self.get_summary_pages(),
                                    communities = self.get_all_coms()))
                pass

    def copy_etc (self):
        
        pth = os.path.dirname(__file__)
        shutil.copytree(os.path.join(pth,'templates','css'),os.path.join(self.directory,'css'))
        shutil.copytree(os.path.join(pth,'templates','js'),os.path.join(self.directory,'js'))
        shutil.copytree(os.path.join(pth,'templates','fonts'),os.path.join(self.directory,'fonts'))
        shutil.copy(os.path.join(pth,'templates','summary.css'),self.directory)
        
        
        
    def get_web_summary(self, component):
        """
        """
        try:
            return self.imported_summaries[component].generate_web_summary
        except AttributeError as e:
            #~ print e
            self.imported_summaries = {}
        except KeyError as e:
            #~ print e
            pass
            
        self.imported_summaries[component] = \
                    import_module("aaem.components." + component).outputs
        return self.imported_summaries[component].generate_web_summary
    

    def get_all_coms (self):
        """ Function doc """
        return sorted([k for k in self.results.keys() if k.find('+') == -1])
    
    def get_summary_pages (self):
        return [{'name':'Summary', 'pages':['summary']}, 
                {'name':'Efficiency Projects', 'pages':["Residential Energy Efficiency",
                                                        "Non-residential Energy Efficiency",
                                                        "Water and Wastewater Efficiency"]
                },
                {'name':'Electricity Projects', 'pages':["Wind Power",
                                                         'Solar Power',
                                                          'Hydropower',
                                                         'Transmission and Interties',
                                                         'Diesel Efficiency']
                },
                {'name':'Heating Projects', 'pages':['Biomass for Heat (Cordwood)',
                                                     'Biomass for Heat (Pellet)',
                                                      'Residential ASHP',
                                                      'Non-Residential ASHP',
                                                      'Heat Recovery']
                }
               ]

    def generate_all (self):
        """ Function doc """
        keys = sorted([k for k in self.results.keys() if k.find('+') == -1])
        self.copy_etc()
        for com in keys:#["Stebbins","Adak","Brevig_Mission"]:
            #~ print com
            self.generate_web_summaries(com)
            #~ return
            
            
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
                    name = i + ' Modeled'
                comps.append({'com':name.decode('unicode_escape').encode('ascii','ignore'),'comp':c, 'r': '{:,.3f}'.format(ratio)})
            
        #~ print comps
        
        
        with open(pth, 'w') as html:
            html.write(template.render( info = comps , com = community,
                                        sections = self.get_summary_pages(),
                                        communities = self.get_all_coms()))
                                        
                                        
    def summary_1 (self, com):
        """ Function doc """
        template = self.env.get_template('component.html')
        res = self.results[com]
        population = res['community data'].get_item('forecast','population')
        p1 = population
        p1['year'] = p1.index
        population_table = self.make_table(p1[['year','population']])
        print com
        
        charts = [
        {'name':'population', 'data': str(population_table).replace('nan','null'), 
         'title': 'Population Forecast',
         'type': "'other'"},
            ]
    
        try:
            consumption = res['forecast'].consumption_to_save
            c1 = consumption
            c1['year'] = c1.index
            consumption_table = self.make_table(c1[['year',
                            "consumption kWh", 
                               'residential kWh',
                               'non-residential kWh']])
            charts.append({'name':'consumption', 'data': str(consumption_table).replace('nan','null'), 
            'title':'Electricity consumed Consumed',
            'type': "'other'"})
        except AttributeError:
            try:
                consumption = res['forecast'].consumption
                c1 = consumption
                c1['year'] = c1.index
                consumption_table = self.make_table(c1[['year',
                                "consumption kWh" ]])
                charts.append({'name':'consumption', 'data': str(consumption_table).replace('nan','null'), 
                'title':'Electricity consumed Consumed',
                'type': "'other'"})
            except AttributeError:
                pass
            #~ self.consumption.columns = ["consumption kWh"]
        

            

        pth = os.path.join(self.directory, com + '_' +\
                    'summary_1'.replace(' ','_').replace('(','').replace(')','').lower() + '.html')
        with open(pth, 'w') as html:
            html.write(template.render( type = 'summary 1', 
                                    com = com ,
                                    charts = charts,
                                    summary_pages = ['Summary'] + comp_order ,
                                    sections = self.get_summary_pages(),
                                    communities = self.get_all_coms()
                                    ))
                        
        #~ print consumption_table
        
    def make_table (self, xs, ys = None):
        """
        make a table
        
        inputs:
        outputs:    
            returns plotting_table, a table that can be used to make a google chart
        """
        if type(xs) == DataFrame and len(xs.columns) > 1:
            x_name = xs.columns[0]
            y_name = list(xs.columns[1:])
        else:
            # todo:fix order
            x_name = xs.keys()[0]
            y_name = ys.keys()
            xs.update(ys)
            xs = DataFrame(xs)[[x_name]+y_name]
            
        plotting_table = xs.round().values.tolist()
        plotting_table.insert(0,[x_name]+y_name)
        return plotting_table 
    
                                        


