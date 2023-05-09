
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
					'team': team.name,
					'team_coat': team.coat,
					'player': team.player.name,
					'played': team.played(),
					'points': team.points(),
					'goals': team.goals(),
					'results': team.results()
				}
				for team in self.teams
			],key=lambda x:(x['points'],x['goals']['difference']),reverse=True),
			'games': sorted([
				match.json()
				for match in self.matches
			],key=lambda x:x['date'])
		}
	def json_short(self):
		return {
			'name': self.name,
			'id': self.id
		}

class TeamSeason(Base):
	__tablename__ = 'team_seasons'
	id = Column(Integer, primary_key=True)
	player_id = Column(Integer, ForeignKey('players.id'))
	season_id = Column(Integer, ForeignKey('seasons.id'))
	name = Column(String)
	coat = Column(String)

	player = relationship('Player')
	season = relationship('Season',backref='teams')

	def matches(self):
		return self.home_matches + self.away_matches
	def played(self):
		return len(self.matches())

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

	def json(self):
		return {
			'name': self.name,
			'coat': self.coat,
			'player': self.player.name,
			'season': self.season.name,
			'played': self.played(),
			'points': self.points(),
			'goals': self.goals(),
			'matches': [match.json_perspective(team=self) for match in self.matches()],
			'results': self.results()
		}

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
		if self.result(team) == MatchResult.DRAW: return self.season.points_draw
		if self.result(team) == MatchResult.LOSS: return 0
		return 0
	def goals(self,team):
		if team == self.team1: return self.scoreline()
		if team == self.team2: return tuple(reversed(self.scoreline()))
		return (0,0)
	def result(self,team):
		h,a = self.scoreline()
		if h>a and team == self.team1: return MatchResult.WIN
		if h>a and team == self.team2: return MatchResult.LOSS
		if h==a and team in (self.team1,self.team2): return MatchResult.DRAW
		if h<a and team == self.team1: return MatchResult.LOSS
		if h<a and team == self.team2: return MatchResult.WIN

	def json(self):
		return {
			'season': self.season.name,
			'date': date_display(self.date),
			'home':{
				'player': self.team1.player.name,
				'team': self.team1.name,
				'coat': self.team1.coat
			},
			'away':{
				'player': self.team2.player.name,
				'team': self.team2.name,
				'coat': self.team2.coat
			},
			'result': self.scoreline(),
			'events':sorted([e.json() for e in self.match_events],key=lambda x:x['minute']),
			'live': self.live,
			'status': self.match_status
		}
	def json_perspective(self,team):
		return {
			'date': date_display(self.date),
			'home': (team == self.team1),
			'opponent': self.team1.name if team == self.team2 else self.team2.name,
			'result': self.result(team),
			'score': self.goals(team),
			'points': self.points(team),
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

	def json(self):
		return {
			'title': self.title,
			'text': self.text,
			'author': self.author,
			'image': self.image,
			'date': date_display(self.date)
		}

def date_display(raw):
	if raw is None:
		return "Unknown"
	return str(raw)[:4] + '-' + str(raw)[4:6] + '-' + str(raw)[6:8]
def minute_display(minute,stoppage):
	if minute is None: return "?"
	res = str(minute) + "'"
	if stoppage:
		res += "+" + str(stoppage)
	return res




engine = create_engine('sqlite:///soccer_league.db')

# ONLY TESTING
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)







### OLD DATA

from .importdata import add_data

add_data()
