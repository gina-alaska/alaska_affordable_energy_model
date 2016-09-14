


import aaem.web as web

ws = web.WebSummary('model/m0.19.1_d0.19.0/', './web')

ws.generate_wind_summary()
ws.generate_wind_summary('Stebbins')
