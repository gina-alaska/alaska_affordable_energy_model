


import aaem.web as web

ws = web.WebSummary('model/m0.19.1_d0.19.0/', './web')

#~ ws.gennerate_community_summary( 'Adak' )

#~ ws.generate_web_summaries('Shishmaref')
#~ ws.generate_web_summaries('Stebbins')
#~ ws.generate_web_summaries('Alatna')

ws.generate_all()
