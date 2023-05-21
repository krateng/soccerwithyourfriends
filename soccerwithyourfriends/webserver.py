from bottle import Bottle, run, template, static_file, response
from waitress import serve
import jinja2
from importlib import resources
import toml

from .database import Session, Match, TeamSeason, Season, NewsStory, Root
from .config import config


PORT = 8080
THREADS = 16
# the actual image and font files etc should rarely change
# if configuration is changed, it will likely just change which file
# is being referred to
CACHE_HOURS_USERCONTENT = 7 * 24
CACHE_HOURS_USERCONFIG = 6
# when the the application is updated, we want to avoid inconsistencies in css
# and scripts and stuff 
CACHE_HOURS_STATIC = 6


app = Bottle()
env = jinja2.Environment(
    loader=jinja2.PackageLoader("soccerwithyourfriends", package_path='dynamic'),
    autoescape=jinja2.select_autoescape()
)


@app.get('/api/seasons')
def season_list():
	with Session() as session:
		select = session.query(Season)
		seasons = session.scalars(select).all()
		return {'seasons':sorted([season.json() for season in seasons],key=lambda x:x['name'])}

@app.get('/api/root')
def root_info():
	with Session() as session:
		return Root().json()

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
	response = static_file(config['branding']['logo'],root="branding")
	response.set_header("Cache-Control", f"public, max-age={CACHE_HOURS_USERCONTENT*3600}")
	return response

# restrict which user data folders are accessible via web
@app.get('/content/newsimages/<path:path>')
def custom_content(path):
	response = static_file(path,root="newsimages")
	response.set_header("Cache-Control", f"public, max-age={CACHE_HOURS_USERCONTENT*3600}")
	return response
@app.get('/content/teams/<path:path>')
def custom_content(path):
	response = static_file(path,root="teams")
	response.set_header("Cache-Control", f"public, max-age={CACHE_HOURS_USERCONTENT*3600}")
	return response
@app.get('/content/branding/<path:path>')
def custom_content(path):
	response = static_file(path,root="branding")
	response.set_header("Cache-Control", f"public, max-age={CACHE_HOURS_USERCONTENT*3600}")
	return response

@app.get('/custom_style.css')
def custom_style():
	response = static_file("custom_style.css",root="branding")
	response.set_header("Cache-Control", f"public, max-age={CACHE_HOURS_USERCONFIG*3600}")
	return response



###

@app.get('/configured_style.css')
def configured_style():
	response.set_header("Cache-Control", f"public, max-age={CACHE_HOURS_USERCONFIG*3600}")
	response.set_header("Content-Type","text/css")

	return env.get_template('configured_style.css.jinja').render(config=config)

@app.get('/')
def main():
	return static('index.html')

@app.get('/<path:path>')
def static(path):
	with resources.files('soccerwithyourfriends') / 'static' as staticfolder:
		response = static_file(path,root=staticfolder)
		response.set_header("Cache-Control", f"public, max-age={CACHE_HOURS_STATIC*3600}")
		return response



def run():
	serve(app, host='*', port=PORT, threads=THREADS)
