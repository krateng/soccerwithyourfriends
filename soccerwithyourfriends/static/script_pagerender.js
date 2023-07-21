var env = nunjucks.configure('/templates', {autoescape: true, web: {useCache: true}});
var env_unsafe = nunjucks.configure('/templates', {autoescape: false, web: {useCache: true}});

function render_page(data) {
	document.getElementById('season_list').innerHTML = env.render('list_seasons.html',data);
	//document.getElementById('eternal_table_body').innerHTML = env.render('table_eternal.html',data);

	document.getElementById('news_stories').innerHTML = env.render('list_news.html',data);

	showFromQuery();

	var show = getQueryArg('season');
	if (show) {
		var seasonelement = document.getElementById("entity_" + show);
	}
	else {
		var seasonelement = document.getElementById('season_list').lastElementChild;
	}

	seasonelement.onclick();

}


function fill_page(data) {
	for (var element of document.getElementsByClassName("league_title")) {
		element.innerHTML = data.branding.league_name;
	}
}
