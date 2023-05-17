from .database import Session, Player, Season, TeamSeason, MatchEvent, NewsStory, Match, EventType, MatchStatus

import os
import yaml
import random

from watchdog.observers import Observer
from watchdog.events import FileModifiedEvent, FileClosedEvent
from threading import Timer

from sqlalchemy import and_

INVENT_MINUTE = True


def randomdate(start,end):
	import datetime
	start = int(datetime.datetime(year=(start // 10000), month=(start // 100 % 100), day=(start % 100)).timestamp())
	end = int(datetime.datetime(year=(end // 10000), month=(end // 100 % 100), day=(end % 100)).timestamp())
	newtime = random.randint(start,end)
	return datetime.datetime.fromtimestamp(newtime).strftime("%Y%m%d")


def add_data():
	importfiles = os.listdir('import/seasons')
	for f in importfiles:
		if f.startswith('.'): continue
		filepath = os.path.join('import/seasons',f)
		add_data_from_file(filepath)

	newsfiles = os.listdir('import/news')
	for f in newsfiles:
		if f.startswith('.'): continue
		filepath = os.path.join('import/news',f)
		add_data_from_file(filepath)

def add_data_from_file(filepath):

	if os.path.dirname(filepath) == "import/seasons":
		with open(filepath) as fd:
			season = yaml.safe_load(fd)


		with Session() as session:
			# create or select season
			select = session.query(Season).where(Season.name == season['season'])
			s = session.scalars(select).first() or Season(name=season['season'])

			team_dict = {}
			for player,teaminfo in season['teams'].items():

				# create or select player
				select = session.query(Player).where(Player.name == player)
				p = session.scalars(select).first() or Player(name=player)
				session.add_all([p])

				# create or select teamseason
				select = session.query(TeamSeason).where(
					TeamSeason.player.has(Player.id == p.id) &
					TeamSeason.season.has(Season.id == s.id)
				)
				t = session.scalars(select).first() or TeamSeason(player=p,season=s,name=teaminfo['team'],coat=teaminfo.get('coat',''))
				team_dict[player] = t
				session.add_all([t])

			for result in season['results']:

				match_args = {}

				select = session.query(Match).where(
					Match.season.has(Season.id == s.id) &
					Match.team1.has(TeamSeason.id == team_dict[result['home']].id) &
					Match.team2.has(TeamSeason.id == team_dict[result['away']].id)
				)

				m = session.scalars(select).first() or Match(season=s,team1=team_dict[result['home']],team2=team_dict[result['away']])

				if not result.get('date'): result['date'] = randomdate(*season['daterange'])
				if result.get('cancelled'):
					if result.get('legal_winner') == 'home': m.match_status = 4
					elif result.get('legal_winner') == 'away': m.match_status = 5
					else:  m.match_status = 3

				if isinstance(result.get('home_goals'),int): result['home_goals'] = result['home_goals']*[None]
				if isinstance(result.get('away_goals'),int): result['away_goals'] = result['away_goals']*[None]

				m.date = result.get('date')
				m.match_status = MatchStatus.LIVE if result.get('live') else MatchStatus.FINISHED

				session.add_all([m])
				events = []

				# drop all existing match events, we have no reliable way of 'matching' them
				# (figuring out which one was changed, what was deleted etc)
				# and it doesnt matter since they are not referenced by anything
				session.query(MatchEvent).where(MatchEvent.match == m).delete()

				for goal in result.get('home_goals',[]):
					if goal is None: goal = {}
					if isinstance(goal,str):
						ngoal = {}
						ngoal['player'],ngoal['minute'],ngoal['stoppage'], *_ = goal.split("/") + [None,None]
						goal = ngoal
					if INVENT_MINUTE: goal['minute'] = goal.get('minute') or random.randint(1,90)
					events.append(
						MatchEvent(
							match=m,home_team=True,event_type=EventType.GOAL,
							player=goal.get('player'),minute=goal.get('minute'),minute_stoppage=goal.get('stoppage')
						)
					)
				for goal in result.get('away_goals',[]):
					if goal is None: goal = {}
					if isinstance(goal,str):
						ngoal = {}
						ngoal['player'],ngoal['minute'],ngoal['stoppage'], *_ = goal.split("/") + [None,None]
						goal = ngoal
					if INVENT_MINUTE: goal['minute'] = goal.get('minute') or random.randint(1,90)
					events.append(
						MatchEvent(
							match=m,home_team=False,event_type=EventType.GOAL,
							player=goal.get('player'),minute=goal.get('minute'),minute_stoppage=goal.get('stoppage')
						)
					)

				for goal in result.get('home_own_goals',[]):
					if goal is None: goal = {}
					if isinstance(goal,str):
						ngoal = {}
						ngoal['player'],ngoal['minute'],ngoal['stoppage'], *_ = goal.split("/") + [None,None]
						goal = ngoal
					if INVENT_MINUTE: goal['minute'] = goal.get('minute') or random.randint(1,90)
					events.append(
						MatchEvent(
							match=m,home_team=True,event_type=EventType.OWN_GOAL,
							player=goal.get('player'),minute=goal.get('minute'),minute_stoppage=goal.get('stoppage')
						)
					)
				for goal in result.get('away_own_goals',[]):
					if goal is None: goal = {}
					if isinstance(goal,str):
						ngoal = {}
						ngoal['player'],ngoal['minute'],ngoal['stoppage'], *_ = goal.split("/") + [None,None]
						goal = ngoal
					if INVENT_MINUTE: goal['minute'] = goal.get('minute') or random.randint(1,90)
					events.append(
						MatchEvent(
							match=m,home_team=False,event_type=EventType.OWN_GOAL,
							player=goal.get('player'),minute=goal.get('minute'),minute_stoppage=goal.get('stoppage')
						)
					)

				for card in result.get('home_cards',[]):
					if isinstance(card,str):
						ncard = {}
						ncard['player'],ncard['type'],ncard['minute'],ncard['stoppage'], *_ = card.split("/") + [None,None,None,None]
						card = ncard
					if INVENT_MINUTE: card['minute'] = card.get('minute') or random.randint(1,90)
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
					if INVENT_MINUTE: card['minute'] = card.get('minute') or random.randint(1,90)
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
					if INVENT_MINUTE: sub['minute'] = sub.get('minute') or random.randint(1,90)
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
					if INVENT_MINUTE: sub['minute'] = sub.get('minute') or random.randint(1,90)
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

			session.commit()


	if os.path.dirname(filepath) == "import/news":

		with open(filepath) as fd:
			article = yaml.safe_load(fd)

		with Session() as session:
			select = session.query(NewsStory).where(NewsStory.importfile == os.path.basename(filepath))

			n = session.scalars(select).first() or NewsStory(importfile=os.path.basename(filepath))

			n.date = article['date']
			n.title = article['title']
			n.author = article['author']
			n.image = article['image']
			n.text = article['text']

			session.add_all([n])
			session.commit()



def add_data_and_repeat():
	add_data()
	Timer(15,add_data_and_repeat).start()





class Handler:
	def dispatch(self,event):
		if isinstance(event,FileModifiedEvent) or isinstance(event,FileClosedEvent):
			if not os.path.basename(event.src_path).startswith('.'):
				#print("Importing",event.src_path)
				add_data_from_file(event.src_path)

def add_data_continuously():
	if os.environ.get('USE_MANUAL_FS_POLLING'):
		# for podman (no inotify)
		add_data_and_repeat()
	else:
		add_data()
		observer = Observer()
		observer.schedule(Handler(),"import",recursive=True)
		observer.start()
