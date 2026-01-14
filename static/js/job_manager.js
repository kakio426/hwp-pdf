class JobManager {
    constructor() {
        this.jobs = [];
    }

    addJob(filename) {
        // Simple distinct ID for frontend tracking before server job_id is assigned
        const id = 'temp_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        const job = {
            id: id,
            job_id: null, // Server assigned ID
            filename: filename,
            status: 'pending',
            progress: 0,
            created_at: new Date()
        };
        this.jobs.push(job);
        return job;
    }

    updateJobStatus(id, status, progress, serverJobId = null) {
        const job = this.getJob(id);
        if (job) {
            if (status) job.status = status;
            if (progress !== undefined) job.progress = progress;
            if (serverJobId) job.job_id = serverJobId;
            return job;
        }
        return null;
    }

    getJob(id) {
        return this.jobs.find(j => j.id === id);
    }

    getJobByServerId(serverJobId) {
        return this.jobs.find(j => j.job_id === serverJobId);
    }

    getAllJobs() {
        return this.jobs;
    }

    removeJob(id) {
        this.jobs = this.jobs.filter(j => j.id !== id);
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = JobManager;
} else {
    window.JobManager = JobManager;
}
