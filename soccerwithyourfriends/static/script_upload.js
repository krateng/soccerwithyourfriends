// written by ChatGPT

document.addEventListener('DOMContentLoaded', function() {
    var form = document.getElementById('upload-form');
    var fileInput = document.getElementById('file-input');
    var dropZone = document.getElementById('drop-zone');

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false)
    });

    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false)
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false)
    });

    // Handle dropped files
    dropZone.addEventListener('drop', handleDrop, false);

    form.addEventListener('submit', function(e) {
        e.preventDefault();

        var files = fileInput.files;
        var formData = new FormData();

        for (var i = 0; i < files.length; i++) {
            var file = files[i];
            formData.append('files', file, file.name);
        }

        fetch('/upload', {
            method: 'POST',
            body: formData
        }).then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            } else {
                alert('Files uploaded successfully!');
            }
        }).catch(e => {
            console.log('There was a problem with the file upload.');
        });
    });

    function preventDefaults (e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        dropZone.classList.add('highlight');
    }

    function unhighlight(e) {
        dropZone.classList.remove('highlight');
    }

    function handleDrop(e) {
        var dt = e.dataTransfer;
        var files = dt.files;

        fileInput.files = files;
    }
});
