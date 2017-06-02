"""
defaults.py

for generating default config structures
"""


from pandas import DataFrame

base_order = [
    'model electricity',
    'model heating fuel',
    'model financial',
    'model as intertie',
    'file id',
    'natural gas used',
    'interest rate',
    'discount rate',
    'current year',

    'name',
    'alternate name',
    'region',
    'regional construction multiplier',
    'GNIS ID',
    'FIPS ID',
    'senate district',
    'house district',
    'population',
    'intertie', 
    'heating degree days',
    'heating fuel premium',
    'on road system',
    
    'diesel prices',
    'electric non-fuel prices',
    
    'residential non-PCE electric price',
    'electric non-fuel price',
    'propane price',
    'cordwood price',
    'pellet price',
    'natural gas price',
    
    
    'utility info',
    'percent diesel generation',
    'line losses',
    'diesel generation efficiency',
    'heat recovery operational',
    'switchgear suatable for renewables',
    'total capacity',
    
    'hydro generation limit',
    'solar generation limit',
    'wind generation limit',
    'hydro capacity',
    'solar capacity',
    'wind capacity',
    
    'max wind generation percent',
    
    'percent excess energy',
    'percent excess energy capturable',
    'efficiency electric boiler',
    'efficiency heating oil boiler',
    
    'diesel generator o&m cost percent',
    'switchgear cost',
]

base_structure = {
    'community': {
        'model electricity': bool,
        'model heating fuel': bool,
        'model financial': bool,
        'model as intertie': bool,
        'file id': str,
        'natural gas used': bool,
        'interest rate':float,
        'discount rate':float,
        'current year': int,
    
        'name': str,
        'alternate name': str,
        'region': str,
        'regional construction multiplier': float,
        'GNIS ID': int,
        'FIPS ID': int,
        'senate district': list,
        'house district': list,
        'population': DataFrame,
        'intertie': [list, str], 
        'heating degree days': float,
        'heating fuel premium': float,
        'on road system': bool,
        
        'diesel prices': DataFrame,
        'electric non-fuel prices': DataFrame,
        
        'residential non-PCE electric price': float,
        'electric non-fuel price': float,
        'propane price': float,
        'cordwood price': float,
        'pellet price': float,
        'natural gas price': float,
        
        
        'utility info': DataFrame,
        'percent diesel generation': float,
        'line losses': float,
        'diesel generation efficiency': float,
        'heat recovery operational': bool,
        'switchgear suatable for renewables': bool,
        'total capacity': float,
        
        'hydro generation limit': float,
        'solar generation limit': float,
        'wind generation limit': float,
        'hydro capacity': float,
        'solar capacity': float,
        'wind capacity': float,
        
        'max wind generation percent': float,
        
        'percent excess energy': float,
        'percent excess energy capturable': float,
        'efficiency electric boiler': float,
        'efficiency heating oil boiler': float,
        
        'diesel generator o&m cost percent': float,
        'switchgear cost': float,
    }

}


base_comments = {
    'community': {
        'model electricity': bool,
        'model financial': bool,
        'file id': str,
        'natural gas used': bool,
        'interest rate':float,
        'discount rate':float,
        'current year': int,
            
    
        'name': str,
        'alternate name': str,
        'region': str,
        'regional construction multiplier': float,
        'GNIS ID': int,
        'FIPS ID': int,
        'senate district': list,
        'house district': list,
        'population': DataFrame,
        'intertie': [list, str], 
        'heating degree days': float,
        'heating fuel premium': float,
        'on road system': bool,
        
        'diesel prices': DataFrame,
        'electric non-fuel prices': DataFrame,
        
        'electric non-fuel price': float,
        'propane price': float,
        'cordwood price': float,
        'pellet price': float,
        'natural gas price': float,
        
        
        'untility info': DataFrame,
        'percent diesel generation': float,
        'line losses': float,
        'diesel generation efficiency': float,
        'heat recovery operational': bool,
        'switchgear suatable for renewables': bool,
        'total capacity': float,
        
        'hydro generation limit': float,
        'solar generation limit': float,
        'wind generation limit': float,
        'hydro capacity': float,
        'solar capacity': float,
        'wind capacity': float,
        
        'max wind generation percent': float,
        
        'percent excess energy': float,
        'percent excess energy capturable': float,
        'efficiency electric boiler': float,
        'efficiency heating oil boiler': float,
        
        'diesel generator o&m cost percent':float,
        'switchgear cost': float,
    }

}
