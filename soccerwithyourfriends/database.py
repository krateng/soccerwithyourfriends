
from sqlalchemy import create_engine, Table, Column, Integer, String, Boolean, MetaData, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum



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

class Player(Base):
	__tablename__ = 'players'
	id = Column(Integer, primary_key=True)
	name = Column(String)

	def json(self):
		return {
			'name': self.name,
			'teams':sorted([
				team.json(full=False)
				for team in self.teams
			],key=lambda x:x['season']),
			'uid': 'p' + str(self.id)
		}

class Season(Base):
	__tablename__ = 'seasons'
	id = Column(Integer, primary_key=True)
	name = Column(String)
	points_win = Column(Integer,default=3)
	points_draw = Column(Integer,default=1)

	def json(self):
		return {
			'name': self.name,
			'table': sorted([
				{
					k:v for k,v in team.json().items()
					#if k not in ['matches']
					#'team': team.name,
					#'team_coat': team.coat,
					#'player': team.player.name,
					#'played': team.played(),
					#'points': team.points(),
					#'goals': team.goals(),
					#'results': team.results(),
					#'uid': 't' + str(team.id)
				}
				for team in self.teams
			],key=lambda x:(x['points'],x['goals']['difference']),reverse=True),
			'games': [
				match.json()
				for match in sorted(self.matches,key=lambda x:x.date or 0)
			],
			'uid': 's' + str(self.id)
		}
	def json_short(self):
		return {
			'name': self.name,
			'uid': 's' + str(self.id)
		}

class TeamSeason(Base):
	__tablename__ = 'team_seasons'
	id = Column(Integer, primary_key=True)
	player_id = Column(Integer, ForeignKey('players.id'))
	season_id = Column(Integer, ForeignKey('seasons.id'))
	name = Column(String)
	coat = Column(String)

	player = relationship('Player',backref='teams')
	season = relationship('Season',backref='teams')

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
		print(carded)

	def json(self,full=True):
		result = {
			'name': self.name,
			'coat': self.coat,
			#'player': self.player.name,
			'season': self.season.name,
			'played': self.played(),
			'points': self.points(),
			'goals': self.goals(),
			'matches': [match.json_perspective(team=self) for match in self.matches()],
			'results': self.results(),
			'scorers': self.scorers(),
			'carded': self.cards(),
			'uid': 't' + str(self.id)
		}
		if full:
			result['player'] = self.player.json()
		return result

class Match(Base):
	__tablename__ = 'matches'
	id = Column(Integer, primary_key=True)
	season_id = Column(Integer, ForeignKey('seasons.id'))
	team1_id = Column(Integer, ForeignKey('team_seasons.id'))
	team2_id = Column(Integer, ForeignKey('team_seasons.id'))
	date = Column(Integer)
	live = Column(Boolean,default=False)
	match_status = Column(Integer,default=MatchStatus.FINISHED)

	season = relationship('Season', backref='matches')
	team1 = relationship('TeamSeason', foreign_keys=[team1_id], backref='home_matches')
	team2 = relationship('TeamSeason', foreign_keys=[team2_id], backref='away_matches')

	def scoreline(self):
		return (
		len([ev for ev in self.match_events if ev.event_type in (EventType.GOAL, EventType.OWN_GOAL) and ev.home_team]),
		len([ev for ev in self.match_events if ev.event_type in (EventType.GOAL, EventType.OWN_GOAL) and not ev.home_team])
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
		return [me.player for me in self.team_events(team) if me.event_type == EventType.GOAL]
	def carded(self,team):
		return {
			'y':[me.player for me in self.team_events(team) if me.event_type == EventType.BOOKING],
			'yr':[me.player for me in self.team_events(team) if me.event_type == EventType.SECOND_BOOKING],
			'r':[me.player for me in self.team_events(team) if me.event_type == EventType.STRAIGHT_RED]
		}

	def json(self):
		return {
			'season': self.season.name,
			'date': date_display(self.date),
			'home':{
				'player': self.team1.player.name,
				'team': self.team1.name,
				'coat': self.team1.coat,
				'uid': 't' + str(self.team1.id)
			},
			'away':{
				'player': self.team2.player.name,
				'team': self.team2.name,
				'coat': self.team2.coat,
				'uid': 't' + str(self.team2.id)
			},
			'result': self.scoreline(),
			'events':sorted([e.json() for e in self.match_events],key=lambda x:x['minute']),
			'live': self.live,
			'status': self.match_status,
			'uid': 'm' + str(self.id)
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

	def json(self):
		return {
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

	def json(self):
		return {
			'title': self.title,
			'text': self.text,
			'author': self.author,
			'image': self.image,
			'date': date_display(self.date),
			'uid': 'n' + str(self.id)
		}

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




engine = create_engine('sqlite:///soccer_league.db')

# ONLY TESTING
#Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)







### OLD DATA

from .importdata import add_data

add_data()
