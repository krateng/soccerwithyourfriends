// select stuff

function showStory(uid){
	var mainarea = document.getElementById("main_area");
	mainarea.innerHTML = env_unsafe.render('detail_news.html',{story:data.entities[uid]});
}
function selectStory(element) {
	var story_id = element.dataset.storyid;
	addQueryArg('select',story_id);
	showStory(story_id);
}

function showGame(uid){
	var mainarea = document.getElementById("main_area");
	mainarea.innerHTML = env.render('detail_game.html',{game:data.entities[uid]});
}
function selectGame(element) {
	var game_id = element.dataset.gameid;
	addQueryArg('select',game_id);
	showGame(game_id);
}

function showTeam(uid){
	var mainarea = document.getElementById("main_area");
	mainarea.innerHTML = env.render('detail_team.html',{team:data.entities[uid]});
}
function selectTeam(element) {
	var team_id = element.dataset.teamid;
	addQueryArg('select',team_id);
	showTeam(team_id);
}


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

	document.getElementById('table_body').innerHTML = env.render('table.html',seasoninfo);
	document.getElementById('topscorers_body').innerHTML = env.render('scorers.html',seasoninfo);
	document.getElementById('season_matrix').innerHTML = env.render('matrix.html',seasoninfo);
	document.getElementById('games').innerHTML = env.render('list_games.html',seasoninfo);
	document.getElementById('team_list').innerHTML = env.render('list_teams.html',seasoninfo);

	addQueryArg('season',season_id)

}


// general functionality


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

document.addEventListener('DOMContentLoaded',function(){
	for (node of document.getElementsByClassName('horizontal_scrollable')) {
		node.addEventListener('mousewheel', scroll, false);
	}
	for (node of document.getElementsByClassName('vertical_scrollable')) {
		node.addEventListener('mousewheel', scroll, false);
	}
});


// navigation

function showFromQuery() {
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

window.addEventListener('popstate',showFromQuery);

function addQueryArg(key,val) {
	url = new URL(window.location.href);
	url.searchParams.set(key,val);
	window.history.pushState({},null,url.href);
}
function getQueryArg(key) {
	url = new URL(window.location.href);
	return url.searchParams.get(key);
}
