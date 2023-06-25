
from sqlalchemy import create_engine, Table, Column, Integer, String, Boolean, MetaData, ForeignKey, exc
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum

import re


# this is basically an enum, but we don't make it an actual enum
# it's just named integer values so we can pass them directly into the DB
class EventType:
	BOOKING = 1
	SECOND_BOOKING = 2
	STRAIGHT_RED = 3
	GOAL = 4
	OWN_GOAL = 5
	SUBSTITUTION = 6
	SUBSTITUTION_OFF = 7
	SUBSTITUTION_ON = 8
	PENALTY_GOAL = 9
	PENALTY_MISS = 10
class MatchResult(str,Enum):
	LOSS = 'L'
	DRAW = 'D'
	WIN = 'W'
class MatchStatus:
	UNPLAYED = 0
	LIVE = 1
	FINISHED = 2
	CANCELLED = 3
	CANCELLED_WIN_HOME = 4
	CANCELLED_WIN_AWAY = 5
	CANCELLED_DRAW = 6





Base = declarative_base()


class Root:
	def deep_json(self):
		with Session() as session:
			return {
				'entities':{
					**{
						player.uid() : player.deep_json()
						for player in session.scalars(session.query(Player)).all()
					},
					**{
						season.uid() : season.deep_json()
						for season in session.scalars(session.query(Season)).all()
					},
					**{
						team.uid() : team.deep_json()
						for team in session.scalars(session.query(TeamSeason)).all()
					},
					**{
						match.uid() : match.deep_json()
						for match in session.scalars(session.query(Match)).all()
					},
					**{
						matchevent.uid() : matchevent.deep_json()
						for matchevent in session.scalars(session.query(MatchEvent)).all()
					},
					**{
						story.uid() : story.deep_json()
						for story in session.scalars(session.query(NewsStory)).all()
					}
				},
				'seasons':[
					{'ref':season.uid()}
					for season in sorted([season for season in session.scalars(session.query(Season)).all()],key=lambda x:x.start_date)
				],
				'all_time_table':[
					{'ref':player.uid()}
					for player in sorted(session.scalars(session.query(Player)).all(),key=lambda player: (player.points(),player.goals()['difference']),reverse=True)
				],
				'news':[
					{'ref':story.uid()}
					for story in sorted(session.scalars(session.query(NewsStory)).all(),key=lambda x: x.date,reverse=True)
				]
			}

class Player(Base):
	__tablename__ = 'players'
	id = Column(Integer, primary_key=True)
	name = Column(String)

	def uid(self):
		return "p" + str(self.id)

	def played(self):
		return sum(t.played() for t in self.teams)
	def points(self):
		return sum(t.points() for t in self.teams)
	def goals(self):
		allgoals = [t.goals() for t in self.teams]
		result =  {
			'for': sum(e['for'] for e in allgoals),
			'against': sum(e['against'] for e in allgoals)
		}
		result['difference'] = result['for'] - result['against']
		return result
	def results(self):
		allresults = [t.results() for t in self.teams]
		return {
			'won': sum(e['won'] for e in allresults),
			'drawn': sum(e['drawn'] for e in allresults),
			'lost': sum(e['lost'] for e in allresults)
		}

	def deep_json(self):
		return {
			'uid': self.uid(),
			'name': self.name,
			#
			'teams':[
				{'ref':team.uid()}
				for team in sorted(self.teams,key=lambda team:team.season.start_date)
			],
			'all_time_stats':{
				'played': self.played(),
				'points': self.points(),
				'goals': self.goals(),
				'results': self.results()
			}
		}

class Season(Base):
	__tablename__ = 'seasons'
	id = Column(Integer, primary_key=True)
	name = Column(String)
	start_date = Column(Integer)
	points_win = Column(Integer,default=3)
	points_draw = Column(Integer,default=1)

	def uid(self):
		return "s" + str(self.id)


	def deep_json(self):
		return {
			'uid': self.uid(),
			'name': self.name,
			'start_date': date_display(self.start_date),
			#
			'table': [
				{'ref':team.uid()}
				for team in sorted(self.teams,key=lambda team:(team.points(),team.goals()['difference']),reverse=True)
			],
			'games': [
				{'ref':match.uid()}
				for match in sorted(self.matches,key=lambda match:match.date or 0)
			],
			'scorers': sorted([
				{'team': {'ref':team.uid()}, 'player': scorer, 'goals': goals}
				for team in self.teams
				for scorer,goals in team.scorers().items()
			],key=lambda x: x['goals'],reverse=True)
		}

class TeamSeason(Base):
	__tablename__ = 'team_seasons'
	id = Column(Integer, primary_key=True)
	player_id = Column(Integer, ForeignKey('players.id'))
	season_id = Column(Integer, ForeignKey('seasons.id'))
	name = Column(String)
	name_short = Column(String)
	coat = Column(String)

	player = relationship('Player',backref='teams')
	season = relationship('Season',backref='teams')

	def uid(self):
		return "t" + str(self.id)


	def matches(self):
		return sorted(self.home_matches + self.away_matches,key=lambda x:x.date or 0)
	def played(self):
		return len([m for m in self.matches() if m.match_status in (MatchStatus.FINISHED,MatchStatus.LIVE)])

	def points(self):
		return sum(match.points(self) for match in self.matches())
	def goals(self):
		result =  {
			'for': sum(match.goals(self)[0] for match in self.matches()),
			'against': sum(match.goals(self)[1] for match in self.matches())
		}
		result['difference'] = result['for'] - result['against']
		return result
	def results(self):
		return {
		'won': len([match for match in self.matches() if match.result(self) == MatchResult.WIN]),
		'drawn': len([match for match in self.matches() if match.result(self) == MatchResult.DRAW]),
		'lost': len([match for match in self.matches() if match.result(self) == MatchResult.LOSS])
	}

	def scorers(self):
		goalscorers = [sc for match in self.matches() for sc in match.scorers(self)]
		scorers = {player:goalscorers.count(player) for player in goalscorers if player}
		scorers = dict(sorted(scorers.items(), key=lambda x: x[1], reverse=True))
		return scorers
	def cards(self):
		cards = {}
		for match in self.matches():
			crds = match.carded(self)
			for k in crds:
				cards[k] = cards.get(k,[]) + crds[k]

		carded = {player:{cardtype: cards[cardtype].count(player) } for cardtype in cards for player in cards[cardtype]}
		scorers = dict(sorted(carded.items(), key=lambda x: (x[1].get('r',0),x[1].get('yr',0),x[1].get('y',0)), reverse=True))
		return carded

	def deep_json(self):
		return {
			'uid': self.uid(),
			'name': self.name,
			'shortname': self.name_short,
			'coat': self.coat,
			#
			'season': {'ref':self.season.uid()},
			'player': {'ref':self.player.uid()},
			'matches': [match.json_perspective(team=self) for match in self.matches()],
			'stats':{
				'played': self.played(),
				'points': self.points(),
				'goals': self.goals(),
				'results': self.results()
			},
			'scorers': self.scorers(),
			'carded': self.cards()
		}

class Match(Base):
	__tablename__ = 'matches'
	id = Column(Integer, primary_key=True)
	season_id = Column(Integer, ForeignKey('seasons.id'))
	team1_id = Column(Integer, ForeignKey('team_seasons.id'))
	team2_id = Column(Integer, ForeignKey('team_seasons.id'))
	team1_coach = Column(String)
	team2_coach = Column(String)
	date = Column(Integer)
	#live = Column(Boolean,default=False)
	match_status = Column(Integer,default=MatchStatus.FINISHED)

	season = relationship('Season', backref='matches')
	team1 = relationship('TeamSeason', foreign_keys=[team1_id], backref='home_matches')
	team2 = relationship('TeamSeason', foreign_keys=[team2_id], backref='away_matches')

	def uid(self):
		return "m" + str(self.id)

	def scoreline(self):
		return (
		len([ev for ev in self.match_events if ev.event_type in (EventType.GOAL, EventType.PENALTY_GOAL, EventType.OWN_GOAL) and ev.home_team]),
		len([ev for ev in self.match_events if ev.event_type in (EventType.GOAL, EventType.PENALTY_GOAL, EventType.OWN_GOAL) and not ev.home_team])
		)
		# own goals are counted for the team they benefit

	def points(self,team):
		if self.result(team) == MatchResult.WIN: return self.season.points_win
		elif self.result(team) == MatchResult.DRAW: return self.season.points_draw
		elif self.result(team) == MatchResult.LOSS: return 0
		elif (self.match_status == MatchStatus.CANCELLED_WIN_HOME) and (self.team1 == team):return self.season.points_win
		elif (self.match_status == MatchStatus.CANCELLED_WIN_AWAY) and (self.team2 == team):return self.season.points_win
		elif (self.match_status == MatchStatus.CANCELLED_DRAW) and (team in (self.team1,self.team2)):return self.season.points_draw
		return 0
	def goals(self,team):
		if team == self.team1: return self.scoreline()
		if team == self.team2: return tuple(reversed(self.scoreline()))
		return (0,0)
	def result(self,team):
		if self.match_status in (MatchStatus.FINISHED,MatchStatus.LIVE):
			h,a = self.scoreline()
			if h>a and team == self.team1: return MatchResult.WIN
			if h>a and team == self.team2: return MatchResult.LOSS
			if h==a and team in (self.team1,self.team2): return MatchResult.DRAW
			if h<a and team == self.team1: return MatchResult.LOSS
			if h<a and team == self.team2: return MatchResult.WIN
		else: return None

	def team_events(self,team):
		return [me for me in self.match_events if (me.home_team and team == self.team1) or (not me.home_team and team == self.team2)]
	def scorers(self,team):
		return [me.player for me in self.team_events(team) if me.event_type in (EventType.GOAL, EventType.PENALTY_GOAL)]
	def carded(self,team):
		return {
			'y':[me.player for me in self.team_events(team) if me.event_type == EventType.BOOKING],
			'yr':[me.player for me in self.team_events(team) if me.event_type == EventType.SECOND_BOOKING],
			'r':[me.player for me in self.team_events(team) if me.event_type == EventType.STRAIGHT_RED]
		}


	def json_perspective(self,team):
		opponent = self.team1 if team == self.team2 else self.team2
		return {
			'date': date_display(self.date),
			'home': (team == self.team1),
			'opponent': {
				'name': opponent.name,
				'coat': opponent.coat
			},
			'result': self.result(team),
			'score': self.goals(team),
			'points': self.points(team),
			'status': self.match_status,
			'uid': 'm' + str(self.id)
		}

	def deep_json(self):
		return {
			'uid':self.uid(),
			'date':date_display(self.date),
			'match_status':self.match_status,
			'result': self.scoreline(),
			'home_coach': self.team1_coach,
			'away_coach': self.team2_coach,
			#
			'home_team': {'ref':self.team1.uid()},
			'away_team': {'ref':self.team2.uid()},
			'season': {'ref': self.season.uid()},
			'events':[
				{'ref': event.uid()}
				for event in sorted(self.match_events,key=lambda event:(event.minute,event.minute_stoppage or 0))
			]
		}

class MatchEvent(Base):
	__tablename__ = 'match_events'
	id = Column(Integer, primary_key=True)
	match_id = Column(Integer, ForeignKey('matches.id'))
	home_team = Column(Boolean)
	event_type = Column(Integer)
	player = Column(String)
	player_secondary = Column(String)
	minute = Column(Integer)
	minute_stoppage = Column(Integer,default=0)

	match = relationship('Match',backref='match_events')

	def uid(self):
		return "e" + str(self.id)


	def deep_json(self):
		return {
			'uid':self.uid(),
			'home': self.home_team,
			'event_type': self.event_type,
			'player': self.player,
			'player_secondary': self.player_secondary,
			'minute': (self.minute,self.minute_stoppage),
			'minute_display': minute_display(self.minute,self.minute_stoppage)
		}




class NewsStory(Base):
	__tablename__ = 'news'
	id = Column(Integer, primary_key=True)
	title = Column(String)
	text = Column(String)
	author = Column(String)
	image = Column(String)
	date = Column(Integer)
	importfile = Column(String)

	def uid(self):
		return "n" + str(self.id)

	def deep_json(self):
		return {
			'uid': self.uid(),
			'title': self.title,
			'text': resolve_news_links(self.text),
			'author': self.author,
			'image': self.image,
			'date': date_display(self.date)
		}



uid_codes = {
	't':TeamSeason,
	'p':Player,
	's':Season,
	'm':Match,
	'e':MatchEvent,
	'n':NewsStory
}

def get_entity_info(uid):
	with Session() as session:
		objtype = uid_codes[uid[0]]
		id = int(uid[1:])
		try:
			info = session.scalars(session.query(objtype).where(objtype.id==id)).one().deep_json()
		except exc.NoResultFound:
			info = {}
		return info



def date_display(raw):
	if raw is None:
		return "Unknown Date"
	return str(raw)[:4] + '-' + str(raw)[4:6] + '-' + str(raw)[6:8]
def minute_display(minute,stoppage):
	if minute is None: return "?"
	res = str(minute) + "'"
	if stoppage:
		res += "+" + str(stoppage)
	return res
def resolve_news_links(raw):
	step1 = re.sub(r"{{([\w\.\- ]+?)\|([\w\.\- ]+?)\|([0-9\-]+?)}}",replace_link,raw)
	return re.sub(r"{{([\w\.\- ]+?)\|([0-9\-]+?)}}",replace_link,step1)

def replace_link(match):
	with Session() as session:
		groups = match.groups()
		# works for both 2 groups and 3 groups
		teamname, seasonname = groups[-2:]
		string = groups[0]

		select = session.query(Season).where(Season.name==seasonname)
		season = session.scalars(select).one()
		select = session.query(TeamSeason).where((TeamSeason.name == teamname) & (TeamSeason.season_id == season.id))
		team = session.scalars(select).one()
		return f"<span class='team_link clickable' data-teamid=t{team.id} onclick='selectTeam(this)''>{string}</span>"



engine = create_engine('sqlite:///soccer_league.db')

# ONLY TESTING
#Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)







### OLD DATA

from .importdata import add_data_continuously

add_data_continuously()
