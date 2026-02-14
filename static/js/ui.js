document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const browseLink = document.getElementById('browse-link');
    const jobList = document.getElementById('job-list');
    const template = document.getElementById('job-template');
    const mainContent = document.getElementById('main-content');
    const termsModal = document.getElementById('terms-modal');
    const hwpNotInstalled = document.getElementById('hwp-not-installed');
    const termsAcceptBtn = document.getElementById('terms-accept-btn');
    const termsDeclineBtn = document.getElementById('terms-decline-btn');

    const jobManager = new JobManager();

    const STATUS_LABELS = {
        pending: '?湲곗쨷',
        processing: '蹂?섏쨷',
        completed: '?꾨즺',
        failed: '?ㅽ뙣'
    };

    function waitForApi() {
        return new Promise((resolve) => {
            if (window.pywebview && window.pywebview.api) {
                resolve();
                return;
            }
            window.addEventListener('pywebviewready', resolve, { once: true });
        });
    }

    async function initApp() {
        await waitForApi();
        const api = window.pywebview.api;

        const accepted = await api.get_terms_accepted();
        if (!accepted) {
            showTermsModal();
            return;
        }

        const installed = await api.check_hwp_installed();
        if (!installed) {
            showHwpNotInstalled();
            return;
        }

        showMainContent();
    }

    function showTermsModal() {
        termsModal.classList.remove('hidden');
        mainContent.classList.add('hidden');
        hwpNotInstalled.classList.add('hidden');
    }

    function showHwpNotInstalled() {
        termsModal.classList.add('hidden');
        mainContent.classList.add('hidden');
        hwpNotInstalled.classList.remove('hidden');
    }

    function showMainContent() {
        termsModal.classList.add('hidden');
        hwpNotInstalled.classList.add('hidden');
        mainContent.classList.remove('hidden');
    }

    termsAcceptBtn.addEventListener('click', async () => {
        await window.pywebview.api.accept_terms();

        const installed = await window.pywebview.api.check_hwp_installed();
        if (!installed) {
            showHwpNotInstalled();
            return;
        }
        showMainContent();
    });

    termsDeclineBtn.addEventListener('click', () => {
        window.close();
    });

    browseLink.addEventListener('click', async (e) => {
        e.stopPropagation();
        const files = await window.pywebview.api.select_files();
        if (files && files.length > 0) {
            processFiles(files);
        }
    });

    dropZone.addEventListener('click', async () => {
        const files = await window.pywebview.api.select_files();
        if (files && files.length > 0) {
            processFiles(files);
        }
    });

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

    dropZone.addEventListener('drop', async (e) => {
        const droppedPaths = [];

        if (e.dataTransfer && e.dataTransfer.files) {
            for (const f of Array.from(e.dataTransfer.files)) {
                if (f && f.path) {
                    droppedPaths.push(f.path);
                }
            }
        }

        if (droppedPaths.length > 0) {
            processFiles(droppedPaths);
            return;
        }

        const files = await window.pywebview.api.select_files();
        if (files && files.length > 0) {
            processFiles(files);
        }
    });

    function processFiles(filePaths) {
        filePaths.forEach(filePath => processFile(filePath));
    }

    async function processFile(filePath) {
        const filename = filePath.split('\\').pop().split('/').pop();
        const ext = filename.split('.').pop().toLowerCase();

        if (!['hwp', 'hwpx'].includes(ext)) {
            alert(`"${filename}" ?뚯씪? 吏?먰븯吏 ?딅뒗 ?뺤떇?낅땲??\nHWP, HWPX ?뚯씪留?蹂?섑븷 ???덉뒿?덈떎.`);
            return;
        }

        const job = jobManager.addJob(filename);
        const jobEl = createJobElement(job);
        jobList.appendChild(jobEl);
        jobList.classList.remove('hidden');

        jobManager.updateJobStatus(job.id, 'processing', 30);
        updateJobElement(jobManager.getJob(job.id));

        try {
            const result = await window.pywebview.api.convert_file(filePath);

            if (result.success) {
                job.pdf_path = result.pdf_path;
                job.pdf_filename = result.filename;
                jobManager.updateJobStatus(job.id, 'completed', 100);
            } else {
                job.error = result.error;
                jobManager.updateJobStatus(job.id, 'failed', 0);
            }
        } catch (error) {
            job.error = error.message || '蹂??以??ㅻ쪟媛 諛쒖깮?덉뒿?덈떎.';
            jobManager.updateJobStatus(job.id, 'failed', 0);
        }

        updateJobElement(jobManager.getJob(job.id));
    }

    function createJobElement(job) {
        const clone = template.content.cloneNode(true);
        const el = clone.querySelector('.job-item');
        el.dataset.id = job.id;

        el.querySelector('.filename').textContent = job.filename;
        el.querySelector('.status-badge').textContent = STATUS_LABELS.pending;
        el.querySelector('.spinner').classList.remove('hidden');

        const downloadBtn = el.querySelector('.download-btn');
        downloadBtn.addEventListener('click', async () => {
            if (job.pdf_path) {
                try {
                    const result = await window.pywebview.api.save_file(
                        job.pdf_path,
                        job.pdf_filename || job.filename.replace(/\.\w+$/, '.pdf')
                    );
                    if (result.success) {
                        console.log('????꾨즺:', result.path);
                    } else if (result.error !== 'cancelled') {
                        alert('????ㅽ뙣: ' + result.error);
                    }
                } catch (err) {
                    console.error('????ㅻ쪟:', err);
                    alert('?뚯씪 ???以??ㅻ쪟媛 諛쒖깮?덉뒿?덈떎.');
                }
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

        badge.textContent = STATUS_LABELS[job.status] || job.status;
        badge.className = 'status-badge ' + job.status;

        progressBar.style.width = `${Math.min(job.progress, 100)}%`;

        if (job.status === 'completed') {
            spinner.classList.add('hidden');
            downloadBtn.classList.remove('hidden');
            errorIcon.classList.add('hidden');
        } else if (job.status === 'failed') {
            spinner.classList.add('hidden');
            downloadBtn.classList.add('hidden');
            errorIcon.classList.remove('hidden');
            errorIcon.title = job.error || '蹂???ㅽ뙣';
        } else {
            spinner.classList.remove('hidden');
            downloadBtn.classList.add('hidden');
            errorIcon.classList.add('hidden');
        }
    }

    initApp();
});
