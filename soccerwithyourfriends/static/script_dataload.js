
var data = {};

document.addEventListener('DOMContentLoaded',function(){
	fetch("/api/root_data")
		.then(data=>data.json())
		.then(result=>{
			data = result;
			resolve_references(data);
			console.log(data);

			render_page(data);
		});


		fetch("/api/config")
			.then(data=>data.json())
			.then(result=>{
				fill_page(result);

			});

});



function resolve_references(obj) {
    Object.keys(obj).forEach(key => {


		    if (typeof obj[key] === 'object' && obj[key] !== null) {
								if (obj[key].hasOwnProperty("ref")) {
									var refid = obj[key]['ref'];
									obj[key] = data.entities[refid];
								}
								else {
									resolve_references(obj[key]);
								}

		    }
    })
}
