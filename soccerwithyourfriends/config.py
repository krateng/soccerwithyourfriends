import toml


defaultconfig = """[branding]

# These are all relative to the 'branding' folder
league_name = "Cool League"
main_font = "font-thin.otf"
main_font_bold = "font-regular.otf"
league_font = "coolfont.ttf"
logo = "league.png"
colors = ["red","white","darkgray"]

[current]

season = 1

# You also need the following folders in your data folder:
teams		For badges / logos
newsimages	Story images
import		Data that is added to the DB at launch
"""

try:
	config = toml.load('config.toml')
except FileNotFoundError:
	with open('config.toml','w') as tomlfile:
		tomlfile.write(defaultconfig)
	config = toml.load('config.toml')
