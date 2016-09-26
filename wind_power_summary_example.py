


import aaem.web as web

ws = web.WebSummary('model/m0.20.0_d0.20.0/', './web', tag = 'web')

#~ ws.gennerate_community_summary( 'Adak' )

#~ ws.generate_web_summaries('Shishmaref')
#~ ws.generate_web_summaries('Stebbins')
#~ ws.generate_web_summaries('Alatna')

ws.generate_all()
