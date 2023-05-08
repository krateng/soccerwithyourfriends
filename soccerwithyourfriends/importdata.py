from .database import Session, Player, Season, TeamSeason, MatchEvent, NewsStory, Match, EventType, MatchStatus

import os
import yaml

def add_data():
	
	
	importfiles = os.listdir('content/import')
	data = []
	for f in importfiles:
		filepath = os.path.join('content/import',f)
		with open(filepath) as fd:
			data.append(yaml.safe_load(fd))
	
	with Session() as session:	
		for season in data:
			s = Season(name=season['season'])
			
			team_dict = {}
			for player,teaminfo in season['teams'].items():
				p = Player(name=player)
				t = TeamSeason(player=p,season=s,name=teaminfo['team'],coat=teaminfo.get('coat',''))
				team_dict[player] = t

			for result in season['results']:
				if result.get('cancelled'):
					if result.get('legal_winner') == 'home': m = Match(season=s,team1=team_dict[result['home']],team2=team_dict[result['away']],match_status=4)
					elif result.get('legal_winner') == 'away': m = Match(season=s,team1=team_dict[result['home']],team2=team_dict[result['away']],match_status=5)
					else: m = Match(season=s,team1=team_dict[result['home']],team2=team_dict[result['away']],match_status=3)
					session.add_all([m])
				else:
					if isinstance(result['home_goals'],int): result['home_goals'] = result['home_goals']*[{}]
					if isinstance(result['away_goals'],int): result['away_goals'] = result['away_goals']*[{}]

					m = Match(
						season=s,
						team1=team_dict[result['home']],
						team2=team_dict[result['away']],
						date=result.get('date'),
						match_status=MatchStatus.LIVE if result.get('live') else None
					)
					
					events = []
					for goal in result['home_goals']:
						if goal is None: goal = {}
						if isinstance(goal,str):
							ngoal = {}
							ngoal['player'],ngoal['minute'],ngoal['stoppage'], *_ = goal.split("/") + [None,None]
							goal = ngoal
						events.append(
							MatchEvent(
								match=m,home_team=True,event_type=EventType.GOAL,
								player=goal.get('player'),minute=goal.get('minute'),minute_stoppage=goal.get('stoppage')
							)
						)
					for goal in result['away_goals']:
						if goal is None: goal = {}
						if isinstance(goal,str):
							ngoal = {}
							ngoal['player'],ngoal['minute'],ngoal['stoppage'], *_ = goal.split("/") + [None,None]
							goal = ngoal
						events.append(
							MatchEvent(
								match=m,home_team=False,event_type=EventType.GOAL,
								player=goal.get('player'),minute=goal.get('minute'),minute_stoppage=goal.get('stoppage')
							)
						)
					for card in result.get('home_cards',[]):
						if isinstance(card,str):
							ncard = {}
							ncard['player'],ncard['type'],ncard['minute'],ncard['stoppage'], *_ = card.split("/") + [None,None,None,None]
							card = ncard
							card['type'] = {
								'yellow':EventType.BOOKING,
								'yellowred':EventType.SECOND_BOOKING,
								'red':EventType.STRAIGHT_RED
							}[card['type']]
						events.append(
							MatchEvent(
								match=m,home_team=True,event_type=card.get('type'),
								player=card.get('player'),minute=card.get('minute'),minute_stoppage=card.get('stoppage')
							)
						)
					for card in result.get('away_cards',[]):
						if isinstance(card,str):
							ncard = {}
							ncard['player'],ncard['type'],ncard['minute'],ncard['stoppage'], *_ = card.split("/") + [None,None,None,None]
							card = ncard
							card['type'] = {
								'yellow':EventType.BOOKING,
								'yellowred':EventType.SECOND_BOOKING,
								'red':EventType.STRAIGHT_RED
							}[card['type']]
						events.append(
							MatchEvent(
								match=m,home_team=False,event_type=card.get('type'),
								player=card.get('player'),minute=card.get('minute'),minute_stoppage=card.get('stoppage')
							)
						)
						
					for sub in result.get('home_subs',[]):
						if isinstance(sub,str):
							nsub = {}
							nsub['out'],nsub['in'],nsub['minute'],nsub['stoppage'], *_ = sub.split("/") + [None,None,None,None]
							sub = nsub
						events.append(
							MatchEvent(
								match=m,home_team=True,event_type=EventType.SUBSTITUTION_OFF,
								player=sub.get('out'),minute=sub.get('minute'),minute_stoppage=sub.get('stoppage')
							)
						)
						events.append(
							MatchEvent(
								match=m,home_team=True,event_type=EventType.SUBSTITUTION_ON,
								player=sub.get('in'),minute=sub.get('minute'),minute_stoppage=sub.get('stoppage')
							)
						)
					for sub in result.get('away_subs',[]):
						if isinstance(sub,str):
							nsub = {}
							nsub['out'],nsub['in'],nsub['minute'],nsub['stoppage'], *_ = sub.split("/") + [None,None,None,None]
							sub = nsub
						events.append(
							MatchEvent(
								match=m,home_team=False,event_type=EventType.SUBSTITUTION_OFF,
								player=sub.get('out'),minute=sub.get('minute'),minute_stoppage=sub.get('stoppage')
							)
						)
						events.append(
							MatchEvent(
								match=m,home_team=False,event_type=EventType.SUBSTITUTION_ON,
								player=sub.get('in'),minute=sub.get('minute'),minute_stoppage=sub.get('stoppage')
							)
						)
						
					session.add_all(events)
					session.add_all([m])
		session.commit()
	
	newsfiles = os.listdir('content/news')
	data = []
	for f in newsfiles:
		filepath = os.path.join('content/news',f)
		with open(filepath) as fd:
			data.append(yaml.safe_load(fd))
	
	
	with Session() as session:
		news = []
		for article in data:
			if 'original_text' in article: del article['original_text']
			news.append(NewsStory(**article))
		
		session.add_all(news)
		session.commit()
