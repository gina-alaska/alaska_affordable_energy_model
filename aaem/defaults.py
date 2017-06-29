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
    'intertie',
    'senate district',
    'house district',
    'community goals',
    'regional goals',
    'population',
     
    'heating degree days',
    'heating fuel premium',
    'on road system',
    
    'diesel prices',
    'heating fuel prices',
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
    'switchgear suitable for renewables',
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
    'number diesel generators',
    'largest generator',
    'diesel generator sizing',
    
    'assumed percent non-residential sqft heat displacement',
    'heating oil efficiency',
    
    'cpi multipliers'
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
        'community goals': list,
        'regional goals': list,
        'population': DataFrame,
        'intertie': [list, str], 
        'heating degree days': float,
        'heating fuel premium': float,
        'on road system': bool,
        
        'diesel prices': DataFrame,
        'heating fuel prices': DataFrame,
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
        'switchgear suitable for renewables': bool,
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
        'number diesel generators': [int, str],
        'largest generator': [int, str],
        'diesel generator sizing': str,
        
        'assumed percent non-residential sqft heat displacement': float,
        'heating oil efficiency': float,
        
        'cpi multipliers': [list],
    }

}


base_comments = {
    'community': {
        'model electricity': 
            '[bool] indicates that electricity portions should be run',
        'model financial': 
            '[bool] indicates that financial portions should be run',
        'file id': '[str] unique id for this file',
        'natural gas used': 
            '[bool] indicates natural gas is used instead of diesel as primary heating fuel',
        'interest rate': '[float] interst rate for projcect loans',
        'discount rate': '[float] discount rate for NPV calculations',
        'current year': '[int] year to base calculations around',
            
    
        'name': '[str] name of commuity',
        'alternate name': '[str] alternate name for community',
        'region': '[str] energy region',
        'regional construction multiplier': '[float] construction multipler to use in calculations',
        'GNIS ID': '[int] GNIS ID for community',
        'FIPS ID': '[int] FIPS ID for community',
        'senate district': 
            '[list] list of state senate districts for community',
        'house district': '[list] list of state house districts for community',
        'community goals': '[list] list of goals for community',
        'regional goals': '[list] list of goals for region',
        'population': '[DataFrame] population data',
        'intertie': 
            '[list, str] list of intertie communites, or "not an intertie"', 
        'heating degree days': 
            '[float] yearly heating degree days for a community',
        'heating fuel premium':
            '[float] heating fuel premium for a community [$/gal]',
        'on road system': 
            '[bool] indicates community is on road system or marine highway',
        
        'diesel prices': '[DataFrame] diesel price forecast',
        'heating fuel prices': '[DataFrame] known heating fuel prices',
        'electric non-fuel prices': '[DataFrame] electric price forecast',
        
        'electric non-fuel price':
            '[float] non fuel electric price for the community [$/kWh]',
        'propane price': '[float] propane price for the community [$/gal]',
        'cordwood price': '[float] cordwood price for the community [$/cord]',
        'pellet price':'[float] pellet price for the community [$/ton]',
        'natural gas price': 
            '[float] natural gas price for the community [$/mcf]',
        
        'utility info': '[DataFrame] historic info on communities utility',
        'percent diesel generation': 
            '[float] percent generation from diesel in a community',
        'line losses': '[float] percent line loss from transmission',
        'diesel generation efficiency': 
            '[float] efficiency form diesel generation [gal/kWh]',
        'heat recovery operational': 
            '[bool] indcates if heat recovery is operational',
        'switchgear suitable for renewables': 
            '[bool] indcates if switch gear can support renewables',
        'total capacity': '[float] total diesel capacity [kW]',
        
        'hydro generation limit': 
            '[float] expected hydropower generation [kWh]',
        'solar generation limit': 
            '[float] expected solar power generation [kWh]',
        'wind generation limit': 
            '[float] expected wind power generation [kWh]',
        'hydro capacity': '[float] hydropower generation capacity [kW]',
        'solar capacity':'[float] solar power generation capacity [kW]',
        'wind capacity':'[float] wind power generation capacity [kW]',
        
        'max wind generation percent': 
            '[float] precent of wind power available at capacity',
        
        'percent excess energy': '[float] percent excess energy from generaton',
        'percent excess energy capturable': 
            '[float] percent excess energy from generaton capturable'
            ' by heat recovery',
        'efficiency electric boiler': '[float] efficiency of electric boiler',
        'efficiency heating oil boiler':
            '[float] efficiency of heating oil boiler',
        
        'diesel generator o&m cost percent': '[float]',
        'switchgear cost': '[float] cost of installing switch gear [$]',
        'number diesel generators': 
            "[int, str] number of generators or 'UNKNOWN'",
        'largest generator':
             '[int] capacity of largest diesel generator [kW]',
        'diesel generator sizing': '[str] description of disel generator size',
        
        'assumed percent non-residential sqft heat displacement':
            '[float] percent of square feet heated assumed to be of set by new heating fuel source',
        'heating oil efficiency': '[float] heating oil efficiency',
            
        'cpi multipliers': '[list] cpi multipliers',
        
        'model heating fuel': '[bool] indicates that heating related portions of AAEM should be run', 
        'model as intertie': '[bool] indicates that community should be run as the parent community of intertie'
    }

}
