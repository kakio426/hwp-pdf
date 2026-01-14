document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const jobList = document.getElementById('job-list');
    const template = document.getElementById('job-template');
    const browseLink = document.querySelector('.browse-link');

    // Logic Components
    const jobManager = new JobManager();
    const POLL_INTERVAL = 1500;
    const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

    // --- Template Helpers ---
    function createJobElement(job) {
        const clone = template.content.cloneNode(true);
        const el = clone.querySelector('.job-item');
        el.dataset.id = job.id;

        // Initial state
        el.querySelector('.filename').textContent = job.filename;
        el.querySelector('.status-badge').textContent = 'Pending';
        el.querySelector('.spinner').classList.remove('hidden');

        // Add Download Event
        const downloadBtn = el.querySelector('.download-btn');
        downloadBtn.addEventListener('click', () => {
            if (job.job_id) {
                window.location.href = `/api/download/${job.job_id}`;
            }
        });

        return el;
    }

    function updateJobElement(job) {
        const el = jobList.querySelector(`.job-item[data-id="${job.id}"]`);
        if (!el) return;

        const badge = el.querySelector('.status-badge');
        const progressBar = el.querySelector('.progress-bar');
        const spinner = el.querySelector('.spinner');
        const downloadBtn = el.querySelector('.download-btn');
        const errorIcon = el.querySelector('.error-icon');

        // Update Badge Color & Text
        badge.textContent = job.status.charAt(0).toUpperCase() + job.status.slice(1);
        badge.className = 'status-badge ' + job.status;

        // Update Progress
        progressBar.style.width = `${Math.min(job.progress, 100)}%`;

        // Update Actions
        if (job.status === 'completed') {
            spinner.classList.add('hidden');
            downloadBtn.classList.remove('hidden');
            errorIcon.classList.add('hidden');
        } else if (job.status === 'failed') {
            spinner.classList.add('hidden');
            downloadBtn.classList.add('hidden');
            errorIcon.classList.remove('hidden');
            errorIcon.title = job.error || 'Conversion failed';
        } else {
            // Pending or Processing
            spinner.classList.remove('hidden');
            downloadBtn.classList.add('hidden');
            errorIcon.classList.add('hidden');
        }
    }

    // --- Core Logic ---

    // Drag & Drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(evt => {
        dropZone.addEventListener(evt, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    ['dragenter', 'dragover'].forEach(evt => {
        dropZone.addEventListener(evt, () => dropZone.classList.add('drag-over'));
    });

    ['dragleave', 'drop'].forEach(evt => {
        dropZone.addEventListener(evt, () => dropZone.classList.remove('drag-over'));
    });

    dropZone.addEventListener('drop', handleDrop);
    dropZone.addEventListener('click', () => fileInput.click()); // Click to browse

    if (browseLink) {
        browseLink.addEventListener('click', (e) => {
            e.stopPropagation();
            fileInput.click();
        });
    }

    fileInput.addEventListener('change', handleFiles);

    function handleDrop(e) {
        handleFiles({ target: { files: e.dataTransfer.files } });
    }

    function handleFiles(e) {
        const files = Array.from(e.target.files);
        if (!files.length) return;

        files.forEach(processFile);

        // Reset input for same file selection
        fileInput.value = '';
    }

    async function processFile(file) {
        // Validation
        const ext = file.name.split('.').pop().toLowerCase();
        if (!['hwp', 'hwpx', 'odt', 'docx'].includes(ext)) {
            // Using toast or alert for now, ideally strictly typed
            alert(`Skipped ${file.name}: Unsupported file type.`);
            return;
        }

        if (file.size > MAX_FILE_SIZE) {
            alert(`Skipped ${file.name}: File too large.`);
            return;
        }

        // Add to Manager & UI
        const job = jobManager.addJob(file.name);
        const jobEl = createJobElement(job);
        jobList.appendChild(jobEl);
        jobList.classList.remove('hidden');

        // Start Upload
        try {
            jobManager.updateJobStatus(job.id, 'uploading', 10);
            updateJobElement(jobManager.getJob(job.id));

            const data = await API.uploadFile(file);

            // Server accepted
            jobManager.updateJobStatus(job.id, 'processing', 30, data.job_id);
            updateJobElement(jobManager.getJob(job.id));

            // Start Polling
            pollStatus(job.id, data.job_id);

        } catch (error) {
            console.error(error);
            jobManager.updateJobStatus(job.id, 'failed', 0);
            const failedJob = jobManager.getJob(job.id);
            failedJob.error = error.message;
            updateJobElement(failedJob);
        }
    }

    async function pollStatus(localId, serverJobId) {
        try {
            const data = await API.checkStatus(serverJobId);
            const job = jobManager.getJob(localId);
            if (!job) return; // Removed?

            if (data.status === 'completed') {
                jobManager.updateJobStatus(localId, 'completed', 100);
                updateJobElement(job);
            } else if (data.status === 'failed') {
                job.error = data.error || 'Failed on server';
                jobManager.updateJobStatus(localId, 'failed', 0);
                updateJobElement(job);
            } else {
                // Fake progress update for UX
                let newProgress = job.progress;
                if (newProgress < 90) {
                    newProgress += (Math.random() * 5);
                }
                jobManager.updateJobStatus(localId, 'processing', newProgress);
                updateJobElement(job);

                setTimeout(() => pollStatus(localId, serverJobId), POLL_INTERVAL);
            }
        } catch (error) {
            const job = jobManager.getJob(localId);
            job.error = 'Network error during polling';
            jobManager.updateJobStatus(localId, 'failed', 0);
            updateJobElement(job);
        }
    }
});
