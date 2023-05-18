from .fileload import observe_file

import toml

config = {
	'branding':{
		'league_name': "Cool League",
		'main_font': "font-thin.otf",
		'main_font_bold': "font-regular.otf",
		'league_font': "coolfont.ttf",
		'logo': "league.png",
		'colors': ["red","white","darkgrey","grey"]
	}
}


def set_default_config(srcfile):
	try:
		loadedconfig = toml.load(srcfile)
	except FileNotFoundError:
		loadedconfig = {}

	for k in config:
		config[k].update(loadedconfig.get(k,{}))
	if config != loadedconfig:
		with open(srcfile,'w') as fd:
			toml.dump(config,fd)

def load_config(srcfile):

	global config
	config.update(toml.load(srcfile))

set_default_config('config.toml')
observe_file('config.toml',load_config)
