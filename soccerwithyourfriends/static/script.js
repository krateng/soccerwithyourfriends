nunjucks.configure('templates', {autoescape: true, web: {useCache: true}});


var data = {entities:{}};

document.addEventListener('DOMContentLoaded',function(){

	fetch("/api/config")
		.then(data=>data.json())
		.then(result=>{
			console.log(result);
			for (var element of document.getElementsByClassName("league_title")) {
				element.innerHTML = result.branding.league_name;
			}


		});

	var seasonfetch = fetch("/api/seasons")
		.then(data=>data.json())
		.then(result=>{
			data.seasons = result.seasons;
			for (var season of data.seasons) {
				data.entities[season.uid] = season;
				for (var game of season.games) {
					data.entities[game.uid] = game;
				}
				for (var team of season.table) {
					data.entities[team.uid] = team;
				}
			}


			document.getElementById('season_list').innerHTML = nunjucks.render('list_seasons.html',result);

			var show = getQueryArg('season');
			if (show) {
				var seasonelement = document.getElementById("entity_" + show);
			}
			else {
				var seasonelement = document.getElementById('season_list').lastElementChild;
			}

			seasonelement.onclick();

		});


	var newsfetch = fetch("/api/news")
		.then(data=>data.json())
		.then(result=>{
			data.stories = result.stories;
			for (var story of data.stories) {
				data.entities[story.uid] = story;
			}
			document.getElementById('news_stories').innerHTML = nunjucks.render('list_news.html',result);
		});

		Promise.all([seasonfetch,newsfetch]).then(showmain)

	for (node of document.getElementsByClassName('horizontal_scrollable')) {
		node.addEventListener('mousewheel', scroll, false);
	}
	for (node of document.getElementsByClassName('vertical_scrollable')) {
		node.addEventListener('mousewheel', scroll, false);
	}

});

function showmain() {
	// show something in the main area
	var show = getQueryArg('select');
	if (show) {
		if (show[0]== 'n') {
			showStory(show);
		}
		else if (show[0] == 'm') {
			showGame(show);
		}
		else if (show[0] == 't') {
			showTeam(show);
		}
	}
	else {
		var showelement = document.getElementById('news_stories').firstElementChild;
		showelement.onclick();
	}


}
window.addEventListener('popstate',showmain);

function selectSeason(element) {
	if (element.classList.contains('selected')) {
		return;
	}
	for (var e of element.parentNode.children) {
		e.classList.remove('selected');
	}
	element.classList.add('selected');

	var season_id = element.dataset.seasonid;

	var seasoninfo = data.entities[season_id];

	document.getElementById('table_body').innerHTML = nunjucks.render('table.html',seasoninfo);
	document.getElementById('games').innerHTML = nunjucks.render('list_games.html',seasoninfo);
	document.getElementById('team_list').innerHTML = nunjucks.render('list_teams.html',seasoninfo);

	addQueryArg('season',season_id)

}


function showStory(uid){
	var mainarea = document.getElementById("main_area");
	mainarea.innerHTML = nunjucks.render('detail_news.html',{story:data.entities[uid]});
}
function selectStory(element) {
	var story_id = element.dataset.storyid;
	addQueryArg('select',story_id);
	showStory(story_id);
}

function showGame(uid){
	var mainarea = document.getElementById("main_area");
	mainarea.innerHTML = nunjucks.render('detail_game.html',{game:data.entities[uid]});
}
function selectGame(element) {
	var game_id = element.dataset.gameid;
	addQueryArg('select',game_id);
	showGame(game_id);
}

function showTeam(uid){
	var mainarea = document.getElementById("main_area");
	mainarea.innerHTML = nunjucks.render('detail_team.html',{team:data.entities[uid]});
}
function selectTeam(element) {
	var team_id = element.dataset.teamid;
	addQueryArg('select',team_id);
	showTeam(team_id);
}


function scroll(e) {
        e = window.event || e;
        var delta = Math.max(-1, Math.min(1, (e.wheelDelta || -e.detail)));
        if (this.classList.contains('horizontal_scrollable')) {
        	this.scrollLeft -= (delta * this.dataset.scrollspeed);
        }
        else if (this.classList.contains('vertical_scrollable')) {
        	this.scrollTop -= (delta * this.dataset.scrollspeed);
        }
        e.preventDefault();
}

function addQueryArg(key,val) {
	url = new URL(window.location.href);
	url.searchParams.set(key,val);
	window.history.pushState({},null,url.href);
}
function getQueryArg(key) {
	url = new URL(window.location.href);
	return url.searchParams.get(key);
}
