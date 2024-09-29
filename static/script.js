document.addEventListener('DOMContentLoaded', () => {
    const videoPlayer = document.getElementById('videoPlayer');
    const videoContainer = document.getElementById('videoContainer');
    const videoInput = document.getElementById('videoInput');
    const clearRectanglesBtn = document.getElementById('clearRectanglesBtn');
    const processVideoBtn = document.getElementById('processVideoBtn');
    const downloadCsvBtn = document.getElementById('downloadCsvBtn');
    const dataTable = document.getElementById('dataTable');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const controlButtons = document.getElementById('controlButtons');

    let regions = [];
    let isDrawing = false;
    let startX, startY;

    // Initially hide the video container and control buttons
    videoContainer.style.display = 'none';
    controlButtons.style.display = 'none';

    videoInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            const videoUrl = URL.createObjectURL(file);
            videoPlayer.src = videoUrl;
            // Show the video container and control buttons when a file is uploaded
            videoContainer.style.display = 'block';
            controlButtons.style.display = 'block';
        }
    });

    // Prevent default drag behavior on the video
    videoPlayer.addEventListener('dragstart', (e) => e.preventDefault());

    videoContainer.addEventListener('mousedown', startDrawing);
    videoContainer.addEventListener('mousemove', drawRectangle);
    videoContainer.addEventListener('mouseup', endDrawing);
    videoContainer.addEventListener('mouseleave', endDrawing);

    function getScalingFactor() {
        const videoRect = videoPlayer.getBoundingClientRect();
        return {
            scaleX: videoPlayer.videoWidth / videoRect.width,
            scaleY: videoPlayer.videoHeight / videoRect.height
        };
    }

    function getMousePosition(event) {
        const videoRect = videoPlayer.getBoundingClientRect();
        const scale = getScalingFactor();
        return {
            x: (event.clientX - videoRect.left) * scale.scaleX,
            y: (event.clientY - videoRect.top) * scale.scaleY
        };
    }

    function startDrawing(event) {
        isDrawing = true;
        const pos = getMousePosition(event);
        startX = pos.x;
        startY = pos.y;
    }

    function drawRectangle(event) {
        if (!isDrawing) return;
        const pos = getMousePosition(event);

        // Clear previous rectangles
        drawRectangles();

        // Draw the new rectangle
        const ctx = document.querySelector('#videoOverlay').getContext('2d');
        ctx.strokeStyle = 'red';
        ctx.lineWidth = 2;
        ctx.strokeRect(startX, startY, pos.x - startX, pos.y - startY);
    }

    function endDrawing(event) {
        if (!isDrawing) return;
        isDrawing = false;
        const pos = getMousePosition(event);

        // Add the new region
        regions.push({
            x: Math.min(startX, pos.x),
            y: Math.min(startY, pos.y),
            width: Math.abs(pos.x - startX),
            height: Math.abs(pos.y - startY)
        });

        // Redraw all rectangles
        drawRectangles();
    }

    function drawRectangles() {
        const canvas = document.createElement('canvas');
        canvas.width = videoPlayer.videoWidth;
        canvas.height = videoPlayer.videoHeight;
        const ctx = canvas.getContext('2d');

        ctx.drawImage(videoPlayer, 0, 0, canvas.width, canvas.height);

        regions.forEach((region) => {
            ctx.strokeStyle = 'red';
            ctx.lineWidth = 2;
            ctx.strokeRect(region.x, region.y, region.width, region.height);
        });

        if (document.querySelector('#videoOverlay')) {
            document.querySelector('#videoOverlay').remove();
        }
        const img = document.createElement('img');
        img.src = canvas.toDataURL();
        img.id = 'videoOverlay';
        img.style.position = 'absolute';
        img.style.top = '0';
        img.style.left = '0';
        img.style.width = '100%';
        img.style.height = '100%';
        img.style.pointerEvents = 'none'; // Ensure the overlay doesn't interfere with mouse events
        videoContainer.appendChild(img);
    }

    clearRectanglesBtn.addEventListener('click', () => {
        regions = [];
        if (document.querySelector('#videoOverlay')) {
            document.querySelector('#videoOverlay').remove();
        }
    });

    processVideoBtn.addEventListener('click', async () => {
        loadingIndicator.style.display = 'block';

        const formData = new FormData();
        formData.append('file', videoInput.files[0]);

        try {
            const uploadResponse = await fetch('/upload', {
                method: 'POST',
                body: formData,
            });

            if (!uploadResponse.ok) {
                throw new Error('File upload failed');
            }

            const uploadData = await uploadResponse.json();

            const processResponse = await fetch('/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filepath: uploadData.filepath,
                    regions: regions,
                }),
            });

            if (!processResponse.ok) {
                throw new Error('Video processing failed');
            }

            const processData = await processResponse.json();
            displayResults(processData);
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred during processing. Please try again.');
        } finally {
            loadingIndicator.style.display = 'none';
        }
    });

    function displayResults(data) {
        const table = document.createElement('table');
        const headerRow = table.insertRow();
        
        Object.keys(data[0]).forEach(key => {
            const th = document.createElement('th');
            th.textContent = key;
            headerRow.appendChild(th);
        });

        data.forEach(row => {
            const tr = table.insertRow();
            Object.values(row).forEach(value => {
                const td = tr.insertCell();
                td.textContent = value;
            });
        });

        dataTable.innerHTML = '';
        dataTable.appendChild(table);
        document.getElementById('dataControls').style.display = 'block';
    }

    downloadCsvBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(Array.from(dataTable.querySelector('table').rows).slice(1).map(row => {
                    return Array.from(row.cells).reduce((obj, cell, index) => {
                        obj[dataTable.querySelector('table').rows[0].cells[index].textContent] = cell.textContent;
                        return obj;
                    }, {});
                })),
            });

            if (!response.ok) {
                throw new Error('CSV download failed');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'numbers_by_time.csv';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred during CSV download. Please try again.');
        }
    });
});