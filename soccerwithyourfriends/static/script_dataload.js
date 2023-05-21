
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
		});


	fetch("/api/config")
		.then(data=>data.json())
		.then(result=>{
			fill_page(result);

		});

});

function refresh(uid) {
	updateEntity(uid)
		.then(result=>{
			render_page(data);
		});
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
