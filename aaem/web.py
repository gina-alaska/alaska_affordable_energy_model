from jinja2 import Environment, PackageLoader
import aaem.driver as driver
from pandas import concat
import os



class WebSummary(object):
    """ Class doc """
    
    def __init__ (self, model_root, directory):
        """ Class initialiser """
        self.model_root = model_root
        model = driver.Driver(self.model_root)
        self.results = model.load_results()
        
        self.directory = directory
        try:
            os.makedirs(self.directory)
        except OSError:
            pass
            
        self.env = Environment(loader=PackageLoader('aaem','templates/'))

    def get_viable_comps (self, com, cutoff = 1):
        """ Function doc """
        l = []
        for comp in self.results[com]:
            try:
                if self.results[com][comp].get_BC_ratio() >= cutoff:
                    l.append(comp)
            except AttributeError:
                pass
        return l
        
        
    def generate_wind_summary (self, community = 'Shishmaref'):
        """
        """
        template = self.env.get_template('wind.html')
        
        wp = self.results[community]['wind power']

        fc = wp.forecast
        generation = fc.generation_by_type['generation_diesel [kWh/year]'].\
                                            ix[wp.start_year:wp.actual_end_year]
                                            
        eff = wp.cd['diesel generation efficiency']
        diesel_price = wp.diesel_prices[:wp.actual_project_life]

        net_benefit = wp.get_net_beneft()[:wp.actual_project_life]

        base_cost = generation/eff * diesel_price
        prop_cost = base_cost - net_benefit
        costs_table = concat([base_cost,prop_cost],axis = 1)
        costs_table['year'] = costs_table.index

        table1 = costs_table[['year','generation_diesel [kWh/year]']].\
                        astype(int).values.tolist()
        table1.insert(0,['year','Base Case Cost', 'Cost With Wind'])
        
        
        base_con = generation/eff 
        cons_table = concat([base_con,
                                base_con-wp.electric_diesel_reduction],axis=1)
        
        cons_table['year'] = cons_table.index
        
        table2  = cons_table[['year','generation_diesel [kWh/year]']].\
                        astype(int).values.tolist()
        table2.insert(0,['year',
                         'Base Case Diesel Consumed',
                         'Wind Diesel Consumed'])
        
        
        info = [{'words':'Investments Needed', 
                    'value': '${:,.0f}'.format(wp.get_NPV_costs())},
                {'words':'Net Lifetime Savings', 
                    'value': '${:,.0f}'.format(wp.get_NPV_benefits())},
                {'words':'Expected kWh/year', 
                    'value': '{:,.0f}'.format(wp.load_offset_proposed*8760)},
                {'words':'Proposed Capacity(kW)', 
                    'value': '{:,.0f}'.format(wp.load_offset_proposed)},
                {'words':'Assumed Wind Class', 
                    'value': int(float(wp.comp_specs['resource data']\
                                                    ['Assumed Wind Class']))},
                {'words':'Assumed Capacity Factor', 
                    'value': wp.comp_specs['resource data']\
                                                 ['assumed capacity factor']},
                {'words':'Existing Wind', 
                    'value': wp.comp_specs['resource data']['existing wind'],
                    'units': 'kW'},
                {'words':'Existing Solar',
                    'value': wp.comp_specs['resource data']['existing solar'], 
                    'units' :'kW'},
                ]
        
        charts = [{'name':'costs', 'data': table1, 
                    'title': 'Estimated Electricity Generation Fuel Costs'},
                  {'name':'consumption', 'data': table2, 
                    'title':'Diesel Consumed for Generation Electricity'}]
            
        pth = os.path.join(self.directory, community +'_wind_summary.html')
        with open(pth, 'w') as html:
            html.write(template.render( info = info,
                                        type = "Wind Power", 
                                        com = community ,
                                        charts = charts ))
        
