from bottle import Bottle, run, template, static_file, response
from waitress import serve
from importlib import resources
import toml

from .database import Session, Match, TeamSeason, Season, NewsStory, Root
from .config import config


PORT = 8080
THREADS = 16


app = Bottle()


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
	response.set_header("Cache-Control", "public, max-age=604800")
	return response

# restrict which user data folders are accessible via web
@app.get('/content/newsimages/<path:path>')
def custom_content(path):
	response = static_file(path,root="newsimages")
	response.set_header("Cache-Control", "public, max-age=604800")
	return response
@app.get('/content/teams/<path:path>')
def custom_content(path):
	response = static_file(path,root="teams")
	response.set_header("Cache-Control", "public, max-age=604800")
	return response
@app.get('/content/branding/<path:path>')
def custom_content(path):
	response = static_file(path,root="branding")
	response.set_header("Cache-Control", "public, max-age=604800")
	return response

@app.get('/custom_style.css')
def custom_style():
	response = static_file("custom_style.css",root="branding")
	response.set_header("Cache-Control", "public, max-age=3600")
	return response


@app.get('/configured_style.css')
def configured_style():
	response.set_header("Cache-Control", "public, max-age=3600")
	response.set_header("Content-Type","text/css")

	css_vars = ""
	css_fontdefs = ""
	for font in ['mainfont','leaguefont']:
		if isinstance(config['branding'][font],str):
			css_vars += f"--{font}: {config['branding'][font]};\n"
		else:
			css_vars += f"--{font}: generated-{font};\n"
			for fontweight in config['branding'][font]:
				css_fontdefs += '''
				@font-face {{
					font-family: generated-{font};
					font-weight: {fontweight};
					src: url(content/branding/{fontfile});
				}}
				'''.format(font=font,fontweight=fontweight,fontfile=config['branding'][font][fontweight])



	css_vars = '''
	:root {{
		{css_vars}
	}}
	'''.format(css_vars=css_vars)

	css_otherbranding = '''

header h1 {{
	background-image: url(\'content/branding/{logo}\');
}}


:root {{
	--primary_color: {primary_color};
	--secondary_color: {secondary_color};
	--tertiary_color: {tertiary_color};
	--tertiary_color_shade: {tertiary_color_shade};
}}


	'''.format(
		logo = config['branding']['logo'],
		primary_color = config['branding']['colors'][0],
		secondary_color = config['branding']['colors'][1],
		tertiary_color = config['branding']['colors'][2],
		tertiary_color_shade = config['branding']['colors'][3]
	)

	return css_vars + css_fontdefs + css_otherbranding





###

@app.get('/')
def main():
	return static('index.html')

@app.get('/<path:path>')
def static(path):
	with resources.files('soccerwithyourfriends') / 'static' as staticfolder:
		response = static_file(path,root=staticfolder)
		return response



def run():
	serve(app, host='*', port=PORT, threads=THREADS)
