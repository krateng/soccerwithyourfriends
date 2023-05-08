from bottle import Bottle, run, template, static_file, response
from waitress import serve
from importlib import resources
import toml

from .database import Session, Match, TeamSeason, Season, NewsStory
from .config import config

app = Bottle()


@app.get('/api/seasons')
def season_list():
	with Session() as session:
		select = session.query(Season)
		seasons = session.scalars(select).all()
		return {'seasons':sorted([season.json_short() for season in seasons],key=lambda x:x['name'])}

@app.get('/api/match/<match_id>')
def match_info(match_id):
	with Session() as session:
		select = session.query(Match).where(Match.id==match_id)
		match = session.scalars(select).one()
		return match.json()


@app.get('/api/team/<team_id>')
def team_info(team_id):
	with Session() as session:
		select = session.query(TeamSeason).where(TeamSeason.id==team_id)
		team = session.scalars(select).one()
		return team.json()
		
@app.get('/api/season/<season_id>')
def season_info(season_id):

	if season_id == 'current':
		season_id = config['current']['season']

	with Session() as session:
		select = session.query(Season).where(Season.id==season_id)
		season = session.scalars(select).one()
		return season.json()
		

@app.get('/api/news')
def news():
	with Session() as session:
		select = session.query(NewsStory)
		news = session.scalars(select).all()
		return {'stories':sorted([newsstory.json() for newsstory in news],key=lambda x: x['date'],reverse=True)}
		
@app.get('/api/config')
def getconfig():
	return config


###

@app.get('/favicon.ico')
def favicon():
	return static_file(config['style']['logo'],root="content")

@app.get('/content/<path:path>')
def custom_content(path):
	return static_file(path,root="content")

@app.get('/configured_style.css')
def configured_style():

	response.set_header("Content-Type","text/css")

	return '''
@font-face {
  font-family: titlefont;
  src: url(content/''' + config['style']['league_font'] + ''');
}
@font-face {
  font-family: mainfont;
  src: url(content/''' + config['style']['main_font'] + ''');
}
@font-face {
  font-family: mainfont;
  font-weight: bold;
  src: url(content/''' + config['style']['main_font_bold'] + ''');
}

header h1 {
	background-image: url(\'content/''' + config['style']['logo'] + '''\');
}
	
	
	'''





###

@app.get('/')
def main():
	return static('index.html')

@app.get('/<path:path>')
def static(path):
	with resources.files('server') / 'static' as staticfolder:
		return static_file(path,root=staticfolder)
		
		
def run():
	serve(app, host='localhost', port=8080, threads=16)
