nunjucks.configure('templates', {autoescape: true})

document.addEventListener('DOMContentLoaded',function(){

	fetch("/api/config")
		.then(data=>data.json())
		.then(result=>{
			console.log(result);
			for (var element of document.getElementsByClassName("league_title")) {
				element.innerHTML = result.info.league_name;
			}
					
			
		});

	fetch("/api/seasons")
		.then(data=>data.json())
		.then(result=>{
			document.getElementById('season_list').innerHTML = nunjucks.render('seasonlist.html',result);
			var current = document.getElementById('season_list').lastElementChild;
			current.onclick();			
			
		});

		
	fetch("/api/news")
		.then(data=>data.json())
		.then(result=>{
			document.getElementById('news_stories').innerHTML = nunjucks.render('news_row.html',result);
			var latest = document.getElementById('news_stories').firstElementChild;
			latest.onclick();
			
		});

	for (node of document.getElementsByClassName('horizontal_scrollable')) {
		node.addEventListener('mousewheel', scroll, false);
	}
	for (node of document.getElementsByClassName('vertical_scrollable')) {
		node.addEventListener('mousewheel', scroll, false);
	}
});


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
			
		});
}

function selectStory(element) {
	var mainarea = document.getElementById("main_area");
	//for (var e of element.parentNode.children) {
	//	e.classList.remove('selected');
	//}
	//element.parentNode.classList.add('selected');
	//element.classList.add('selected');
	var bigarticle = element.cloneNode(true);
	bigarticle.removeAttribute('onclick');
	mainarea.replaceChildren(bigarticle);
}

function selectGame(element) {
	var mainarea = document.getElementById("main_area");
	var biggame = element.cloneNode(true);
	biggame.removeAttribute('onclick');
	mainarea.replaceChildren(biggame);
}


function scroll(e) {
        e = window.event || e;
        var delta = Math.max(-1, Math.min(1, (e.wheelDelta || -e.detail)));
        if (this.classList.contains('horizontal_scrollable')) {
        	this.scrollLeft -= (delta * 70);
        }
        else if (this.classList.contains('vertical_scrollable')) {
        	this.scrollTop -= (delta * 70);
        }
        e.preventDefault();
}

