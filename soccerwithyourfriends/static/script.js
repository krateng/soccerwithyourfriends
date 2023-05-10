nunjucks.configure('templates', {autoescape: true})

document.addEventListener('DOMContentLoaded',function(){

	fetch("/api/config")
		.then(data=>data.json())
		.then(result=>{
			console.log(result);
			for (var element of document.getElementsByClassName("league_title")) {
				element.innerHTML = result.branding.league_name;
			}


		});

	fetch("/api/seasons")
		.then(data=>data.json())
		.then(result=>{
			document.getElementById('season_list').innerHTML = nunjucks.render('seasonlist.html',result);

			var show = getQueryArg('season');
			if (show) {
				var seasonelement = document.getElementById("season_" + show);
			}
			else {
				var seasonelement = document.getElementById('season_list').lastElementChild;
			}

			seasonelement.onclick();

		})
		.then(showmain);


	fetch("/api/news")
		.then(data=>data.json())
		.then(result=>{
			document.getElementById('news_stories').innerHTML = nunjucks.render('news_row.html',result);
		})
		.then(showmain);

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
	console.log(show);
	if (show) {
		var showelement = document.getElementById(show);
		console.log(showelement);
	}
	else {
		var showelement = document.getElementById('news_stories').firstElementChild;
	}

	showelement.onclick();
}


function selectSeason(element) {
	for (var e of element.parentNode.children) {
		e.classList.remove('selected');
	}
	element.classList.add('selected');

	var season_id = element.dataset.seasonid;

	fetch("/api/season/" + season_id)
		.then(data=>data.json())
		.then(result=>{
			document.getElementById('table_body').innerHTML = nunjucks.render('table.html',result);
			document.getElementById('games').innerHTML = nunjucks.render('games.html',result);
			document.getElementById('team_list').innerHTML = nunjucks.render('teamlist.html',result);

			addQueryArg('season',season_id)

		})
		.then(showmain);
}

function selectStory(element) {
	var story_id = element.dataset.storyid;

	var mainarea = document.getElementById("main_area");
	var bigarticle = element.cloneNode(true);
	bigarticle.removeAttribute('onclick');
	mainarea.replaceChildren(bigarticle);

		addQueryArg('select','story_' + story_id)
}

function selectGame(element) {
	var game_id = element.dataset.gameid;

	var mainarea = document.getElementById("main_area");
	var biggame = element.cloneNode(true);
	biggame.removeAttribute('onclick');
	mainarea.replaceChildren(biggame);

	addQueryArg('select','game_' + game_id)
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
	window.history.pushState(null,null,url.href);
}
function getQueryArg(key) {
	url = new URL(window.location.href);
	return url.searchParams.get(key);
}
