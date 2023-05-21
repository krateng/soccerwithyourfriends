
var data = {};

document.addEventListener('DOMContentLoaded',function(){
	fetch("/api/root_data")
		.then(data=>data.json())
		.then(result=>{
			data = result;
			return data;
		})
		.then(resolve_references)
		.then(result=>{
			console.log(data);
			render_page(data);
		})
		.then(result=>{
			for (var key of Object.keys(data.entities)) {
				if (key.startsWith('m')) {
					var game = data.entities[key];
					if (game.match_status == 1) {
						refreshGameInfo(game.uid);
					}
				}
			}
		});


	fetch("/api/config")
		.then(data=>data.json())
		.then(result=>{
			fill_page(result);

		});

});



async function refreshGameInfo(uid) {
	var game = data.entities[uid];
	var ids_to_update = [uid,game.home_team.uid,game.away_team.uid,game.season.uid];
	for (var ev of game.events) {
		ids_to_update.push(ev.uid);
	}
	console.log(ids_to_update);
	for (var id of ids_to_update) {
		await updateEntity(id);
	}
	render_page(data);

	if (data.entities[uid].match_status == 1) {
		setTimeout(refreshGameInfo.bind(null,uid),8000);
	}
}


// Are you f***ing kidding me
// I messed around for an hour with this async await then nonsense
// then I ask ChatGPT what's wrong and it just fixes it instantly
// why even do any work
// let's just let the AI overlords handle it all and permanently move into Skyrim VR
// Serana here I come

// calls the api, then resolves reference, then returns
async function updateEntity(uid) {
	r1 = await fetch("/api/entity/" + uid);
	result = await r1.json();
	if (!(uid in data.entities)) { data.entities[uid] = {} }
	Object.assign(data.entities[uid],result);
	await resolve_references(data.entities[uid]);
}

// tries to resolves reference, updates missing entities, then returns
async function resolve_references(obj) {

		for (var key of Object.keys(obj)) {
			if (typeof obj[key] === 'object' && obj[key] !== null) {
							if (obj[key].hasOwnProperty("ref")) {
								var refid = obj[key]['ref'];
								if (!data.entities.hasOwnProperty(refid)) {
									r = await updateEntity(refid);
								}
								obj[key] = data.entities[refid];
							}
							else {
								await resolve_references(obj[key]);
							}
			}
		}
}
