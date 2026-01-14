const JobManager = require('../static/js/job_manager.js');

describe('JobManager', () => {
    let jobManager;

    beforeEach(() => {
        jobManager = new JobManager();
    });

    test('addJob adds a job to the queue', () => {
        const job = jobManager.addJob('file1.hwp');
        expect(job.filename).toBe('file1.hwp');
        expect(job.status).toBe('pending');
        expect(job.id).toBeDefined();
        expect(jobManager.getAllJobs().length).toBe(1);
    });

    test('updateJobStatus updates the status', () => {
        const job = jobManager.addJob('file1.hwp');
        jobManager.updateJobStatus(job.id, 'processing', 50);

        const updated = jobManager.getJob(job.id);
        expect(updated.status).toBe('processing');
        expect(updated.progress).toBe(50);
    });

    test('getJob returns undefined for non-existent id', () => {
        expect(jobManager.getJob('non-existent')).toBeUndefined();
    });

    test('removeJob removes from queue', () => {
        const job = jobManager.addJob('file1.hwp');
        jobManager.removeJob(job.id);
        expect(jobManager.getAllJobs().length).toBe(0);
    });
});
