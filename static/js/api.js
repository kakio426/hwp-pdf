const API = {
    /**
     * Uploads a file to the conversion server
     * @param {File} file - The file object to upload
     * @returns {Promise<Object>} - The JSON response containing job_id
     */
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                // Check if detail is an array (Pydantic validation error) or string
                const errorMsg = typeof data.detail === 'string'
                    ? data.detail
                    : JSON.stringify(data.detail);
                throw new Error(errorMsg || 'Upload failed');
            }

            return data;
        } catch (error) {
            console.error('Upload Error:', error);
            throw error;
        }
    },

    /**
     * Checks the status of a conversion job
     * @param {string} jobId - The job ID
     * @returns {Promise<Object>} - The status object
     */
    async checkStatus(jobId) {
        try {
            const response = await fetch(`/api/status/${jobId}`);
            if (!response.ok) {
                throw new Error('Failed to check status');
            }
            return await response.json();
        } catch (error) {
            console.error('Status Check Error:', error);
            throw error;
        }
    }
};

// Export for both CommonJS (Tests) and Browser
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API;
} else {
    window.API = API;
}
