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


def get_all_import_files():
	result = []

	importfiles = os.listdir('import/seasons')
	for f in importfiles:
		if f.startswith('.'): continue
		filepath = os.path.join('import/seasons',f)
		result.append(filepath)

	newsfiles = os.listdir('import/news')
	for f in newsfiles:
		if f.startswith('.'): continue
		filepath = os.path.join('import/news',f)
		result.append(filepath)

	return result

def add_data():
	for f in get_all_import_files():
		add_data_from_file(f)

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
				t = session.scalars(select).first() or TeamSeason(player=p,season=s)
				t.name = teaminfo['team']
				t.coat = teaminfo.get('coat','')
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

				# just go through all events and compare them in order
				# if nothing changed, they should be in the same order and match
				# if something shifts all the events, it doesn't really matter
				# that it gets a new id since they are not referenced by anything
				select = session.query(MatchEvent).where(MatchEvent.match == m)
				existing_match_events = session.scalars(select).all()

				for goal in result.get('home_goals',[]):
					if goal is None: goal = {}
					if isinstance(goal,str):
						ngoal = {}
						ngoal['player'],ngoal['minute'],ngoal['stoppage'], *_ = goal.split("/") + [None,None]
						goal = ngoal
					if INVENT_MINUTE: goal['minute'] = goal.get('minute') or random.randint(1,90)

					e = existing_match_events.pop(0) if existing_match_events else MatchEvent(match=m)

					e.home_team=True
					e.event_type=EventType.GOAL
					e.player=goal.get('player')
					e.minute=goal.get('minute')
					e.minute_stoppage=goal.get('stoppage')

					events.append(e)

				for goal in result.get('away_goals',[]):
					if goal is None: goal = {}
					if isinstance(goal,str):
						ngoal = {}
						ngoal['player'],ngoal['minute'],ngoal['stoppage'], *_ = goal.split("/") + [None,None]
						goal = ngoal
					if INVENT_MINUTE: goal['minute'] = goal.get('minute') or random.randint(1,90)

					e = existing_match_events.pop(0) if existing_match_events else MatchEvent(match=m)

					e.home_team=False
					e.event_type=EventType.GOAL
					e.player=goal.get('player')
					e.minute=goal.get('minute')
					e.minute_stoppage=goal.get('stoppage')

					events.append(e)

				for goal in result.get('home_own_goals',[]):
					if goal is None: goal = {}
					if isinstance(goal,str):
						ngoal = {}
						ngoal['player'],ngoal['minute'],ngoal['stoppage'], *_ = goal.split("/") + [None,None]
						goal = ngoal
					if INVENT_MINUTE: goal['minute'] = goal.get('minute') or random.randint(1,90)

					e = existing_match_events.pop(0) if existing_match_events else MatchEvent(match=m)

					e.home_team=True
					e.event_type=EventType.OWN_GOAL
					e.player=goal.get('player')
					e.minute=goal.get('minute')
					e.minute_stoppage=goal.get('stoppage')

					events.append(e)

				for goal in result.get('away_own_goals',[]):
					if goal is None: goal = {}
					if isinstance(goal,str):
						ngoal = {}
						ngoal['player'],ngoal['minute'],ngoal['stoppage'], *_ = goal.split("/") + [None,None]
						goal = ngoal
					if INVENT_MINUTE: goal['minute'] = goal.get('minute') or random.randint(1,90)

					e = existing_match_events.pop(0) if existing_match_events else MatchEvent(match=m)

					e.home_team=False
					e.event_type=EventType.OWN_GOAL
					e.player=goal.get('player')
					e.minute=goal.get('minute')
					e.minute_stoppage=goal.get('stoppage')

					events.append(e)

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

					e = existing_match_events.pop(0) if existing_match_events else MatchEvent(match=m)

					e.home_team=True
					e.event_type=card.get('type')
					e.player=card.get('player')
					e.minute=card.get('minute')
					e.minute_stoppage=card.get('stoppage')

					events.append(e)

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

					e = existing_match_events.pop(0) if existing_match_events else MatchEvent(match=m)

					e.home_team=False
					e.event_type=card.get('type')
					e.player=card.get('player')
					e.minute=card.get('minute')
					e.minute_stoppage=card.get('stoppage')

					events.append(e)

				for sub in result.get('home_subs',[]):
					if isinstance(sub,str):
						nsub = {}
						nsub['out'],nsub['in'],nsub['minute'],nsub['stoppage'], *_ = sub.split("/") + [None,None,None,None]
						sub = nsub
					if INVENT_MINUTE: sub['minute'] = sub.get('minute') or random.randint(1,90)

					if existing_match_events: e = existing_match_events.pop(0) if existing_match_events else MatchEvent(match=m)

					e.home_team=True
					e.event_type=EventType.SUBSTITUTION_OFF
					e.player=sub.get('out')
					e.minute=sub.get('minute')
					e.minute_stoppage=sub.get('stoppage')

					events.append(e)

					e = existing_match_events.pop(0) if existing_match_events else MatchEvent(match=m)

					e.home_team=True
					e.event_type=EventType.SUBSTITUTION_ON
					e.player=sub.get('in')
					e.minute=sub.get('minute')
					e.minute_stoppage=sub.get('stoppage')

					events.append(e)


				for sub in result.get('away_subs',[]):
					if isinstance(sub,str):
						nsub = {}
						nsub['out'],nsub['in'],nsub['minute'],nsub['stoppage'], *_ = sub.split("/") + [None,None,None,None]
						sub = nsub
					if INVENT_MINUTE: sub['minute'] = sub.get('minute') or random.randint(1,90)

					e = existing_match_events.pop(0) if existing_match_events else MatchEvent(match=m)

					e.home_team=False
					e.event_type=EventType.SUBSTITUTION_OFF
					e.player=sub.get('out')
					e.minute=sub.get('minute')
					e.minute_stoppage=sub.get('stoppage')

					events.append(e)

					e = existing_match_events.pop(0) if existing_match_events else MatchEvent(match=m)

					e.home_team=False
					e.event_type=EventType.SUBSTITUTION_ON
					e.player=sub.get('in')
					e.minute=sub.get('minute')
					e.minute_stoppage=sub.get('stoppage')

					events.append(e)

				session.add_all(events)
				# remove events that weren't matched by anything
				session.query(MatchEvent).where(MatchEvent.id.in_(ev.id for ev in existing_match_events)).delete()

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



def add_data_and_repeat(files={}):
	for f in get_all_import_files():
		mtime = os.stat(f).st_mtime
		if files.get(f) != mtime:
			files[f] = mtime
			add_data_from_file(f)

	tim = Timer(30,add_data_and_repeat)
	tim.daemon = True
	tim.start()





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
