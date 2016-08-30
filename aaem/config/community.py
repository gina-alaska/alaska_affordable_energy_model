"""
"""
section_name = 'community'

items = {
    'name': 'ABSOLUTE DEFAULT NAME',
    'region': 'IMPORT',
    'construction multiplier': 'IMPORT',
    'current year': 'ABSOLUTE DEFAULT',
    'model financial': True,
    'model electricity': True,
    'model heating fuel': True,
    'natural gas used': False,
    'interest rate': .05, 
    'discount rate': .03,
    'heating fuel premium': 'IMPORT',
    'diesel generation efficiency': 'IMPORT',
    'diesel generator o&m cost' : 0.02,
    'generation': 'IMPORT',
    'consumption kWh': 'ABSOLUTE DEFAULT',
    'consumption HF': 'IMPORT',
    'line losses': 'IMPORT',
    'max line losses': .4,
    'default line losses': .1,
    'default diesel generator efficiency': 12,
    'res non-PCE elec cost': 'IMPORT',
    'elec non-fuel cost': 'IMPORT',
    'HDD': 'IMPORT',
    'diesel prices': 'IMPORT',
    'electric non-fuel prices': 'IMPORT',
    'propane price': 'IMPORT',
    'cordwood price': 'IMPORT',
    'pellet price': 'IMPORT',
    'natural gas price': 0,
    'hydro generation limit': 'IMPORT' ,
    'wind generation limit': 'IMPORT' ,
    'wind generation precent': .2,
    'generation numbers': 'IMPORT',
    'switchgear suatable for RE': 'IMPORT',
    'switchgear cost': 150000,
    'heat recovery operational': 'IMPORT',
    }
    
order = [   
    'name',
    'region',
    'construction multiplier',
    'current year',
    'model financial',
    'model electricity',
    'model heating fuel',
    'natural gas used',
    'interest rate', 
    'discount rate',
    'heating fuel premium',
    'diesel generation efficiency',
    'default diesel generator efficiency',
    'generation',
    'consumption kWh',
    'consumption HF',
    'line losses',
    'max line losses',
    'default line losses',
    'res non-PCE elec cost',
    'elec non-fuel cost',
    'HDD',
    'diesel prices',
    'electric non-fuel prices',
    'propane price',
    'biomass price',
    'natural gas price',
    'hydro generation limit',
    'wind generation limit',
    'wind generation precent',
    'generation numbers',
    'switchgear suatable for RE',
    'switchgear cost',
    'heat recovery operational',
    ]
    
comments = {
    'name': 'Name of community <String>',
    'region': 'Name of region <String>',
    'construction multiplier': '<float>',
    'current year': 
        'Year for which the NPV calculations are based <int>',
    'model financial': 
        'Flag to run the models financal portions <bool>',
    'model electricity': 
        'Flag to run the models electric portions <bool>',
    'model heating fuel': 
        'Flag to run the models heating portions <bool>',
    'natural gas used':  
        'Flag indcating the use of natrual gas <bool>',
    'interest rate': 
        'Interest rate for projects (% as decimal) <float>', 
    'discount rate': 
        'Discount rate for projects (% as decimal) <float>',
    'heating fuel premium': 
        'Premium added to Heating Oil costs ($) <float>',
    'diesel generation efficiency': 
        'efficiency of diesel generator (kWh/gal) <float>',
    'default diesel generator efficiency':
        'default diesel generation efficiency (kWh/gal) <float>',
    'generation': 'Generation (read from file)',
    'consumption kWh': 'ABSOLUTE DEFAULT',
    'consumption HF': 'Heating Fuel consumption (read from file)',
    'line losses': 
        'Percent kWh lost in transmission (% as decimal) <float>',
    'max line losses':  
        'maximum for line losses (% as decimal) <float>',
    'default line losses': 
        'default for line losses (% as decimal) <float>',
    'res non-PCE elec cost': 
        'price of non PCE elctricity ($) <float>',
    'elec non-fuel cost': 
        'cost of electricity not associated with fuel ($) <float>',
    'HDD': 'Heating Degree Days <float>',
    'diesel prices': 'prices of diesel (read from file)',
    'electric non-fuel prices': 
        'electric non-fuel prices (read from file)',
    'propane price': 'propane price ($) <float>',
    'biomass price': 'biomass price ($) <float>',
    'natural gas price': 'natural gas price ($) <float>',
    'hydro generation limit': 
        'Maximum Hydro generation for current system (kWh) <float>',
    'wind generation limit': 
        'Maximum Wind generation for current system (kWh) <float>' ,
    'wind generation precent':
        ('Percent of maximum wind generation '
         'useable (% as decimal) <float>'),
    'generation numbers': '(read from file)',
    'switchgear suatable for RE': 
        ('Flag indicating if power house controls are suatable '
         'for renewable sources <bool>'),
    'switchgear cost': 
        'cost of switch gear ($) <float>',
    'heat recovery operational': 
        'Flag indcation if the heatrecovery is operational <bool>',
        }
                
defaults = {
    'current year': 2015,
    'model financial': True,
    'model electricity': True,
    'model heating fuel': True,
    'interest rate': .05, 
    'discount rate': .03,
            }
    
