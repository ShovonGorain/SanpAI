// Video Management
const videoFilter = document.getElementById('video-filter');
const videoTableBody = document.getElementById('video-table-body');
const videoPageInfo = document.getElementById('video-page-info');
const prevVideoPage = document.getElementById('prev-video-page');
const nextVideoPage = document.getElementById('next-video-page');

let videoCurrentPage = 1;
const videoRowsPerPage = 10;

function fetchVideos(page = 1, filterBy = 'all') {
    const url = `/admin/get_videos?page=${page}&per_page=${videoRowsPerPage}&filter=${filterBy}`;
    fetch(url)
        .then(handleResponse)
        .then(data => {
            renderVideoTable(data);
        })
        .catch(error => console.error('Error fetching videos:', error));
}

function renderVideoTable(data) {
    videoTableBody.innerHTML = '';
    data.videos.forEach(video => {
        videoTableBody.innerHTML += `
            <tr>
                <td>${video.title || 'Untitled'}</td>
                <td>${video.user_name}</td>
                <td>${new Date(video.created_at).toLocaleDateString()}</td>
                <td>${video.duration ? video.duration.toFixed(2) + 's' : 'N/A'}</td>
                <td>${video.music_style || 'N/A'}</td>
                <td>
                    <button class="btn btn-primary btn-sm view-video" data-id="${video.id}" data-url="${video.full_video_url}">View</button>
                    <button class="btn btn-danger btn-sm delete-video" data-id="${video.id}">Delete</button>
                </td>
            </tr>
        `;
    });

    const totalPages = Math.ceil(data.total / videoRowsPerPage);
    videoPageInfo.textContent = `Page ${data.page} of ${totalPages}`;
    prevVideoPage.disabled = data.page === 1;
    nextVideoPage.disabled = data.page === totalPages;
    videoCurrentPage = data.page;
}

videoFilter.addEventListener('change', () => {
    fetchVideos(1, videoFilter.value);
});
prevVideoPage.addEventListener('click', () => {
    if (videoCurrentPage > 1) {
        fetchVideos(videoCurrentPage - 1, videoFilter.value);
    }
});
nextVideoPage.addEventListener('click', () => {
    fetchVideos(videoCurrentPage + 1, videoFilter.value);
});

fetchVideos();

// View video buttons using event delegation
videoTableBody.addEventListener('click', function(e) {
    if (e.target.classList.contains('view-video')) {
        const videoId = e.target.getAttribute('data-id');
        const videoUrl = `/videos/${videoId}/view`;
        document.querySelector('.video-detail-content').innerHTML = `
            <div class="video-preview">
                <video controls width="100%">
                    <source src="${videoUrl}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            </div>
        `;
        openModal('video-detail-modal');
        document.getElementById('download-video-btn').setAttribute('data-videoid', videoId);
    }
});

document.getElementById('download-video-btn').addEventListener('click', function() {
    const videoId = this.getAttribute('data-videoid');
    const a = document.createElement('a');
    a.href = `/videos/${videoId}/view`;
    a.download = `video-${videoId}.mp4`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
});

// Delete Video
videoTableBody.addEventListener('click', function(e) {
    if (e.target.classList.contains('delete-video')) {
        const videoId = e.target.getAttribute('data-id');
        showConfirmationModal('Delete Video', `Are you sure you want to delete video ${videoId}?`, () => {
            fetch(`/admin/videos/${videoId}`, { method: 'DELETE' })
            .then(handleResponse)
            .then(data => {
                fetchVideos(); // Refresh the table
                showInfoModal('Success', 'Video deleted successfully.');
            })
            .catch(error => {
                showInfoModal('Error', `Error: ${error.message}`);
                console.error('Error deleting video:', error);
            });
        });
    }
});
