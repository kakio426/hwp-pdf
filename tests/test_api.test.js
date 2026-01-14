/**
 * @jest-environment jsdom
 */

// Mock fetch globally
global.fetch = jest.fn();

// Import the api module (we'll implement this next)
// Since we are using vanilla JS without modules for the browser, 
// we'll load the file content and eval it or use a commonJS wrapper pattern.
// For TDD simplicity, let's assume we can require it. 
// Note: In real setup, we might need to handle the lack of module.exports in browser-side JS
// or write the code in a format that works in both (UMD) or use a build step.
// For this exercise, I will structure api.js as a CommonJS module that also attaches to window if present.

const API = require('../static/js/api.js');

describe('API Wrapper', () => {
    beforeEach(() => {
        fetch.mockClear();
    });

    test('uploadFile sends correct POST request', async () => {
        const mockFile = new File(['content'], 'test.hwp', { type: 'application/x-hwp' });
        fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ job_id: 'job-123', status: 'pending' })
        });

        const result = await API.uploadFile(mockFile);

        expect(fetch).toHaveBeenCalledTimes(1);
        expect(fetch).toHaveBeenCalledWith('/api/upload', expect.objectContaining({
            method: 'POST',
            body: expect.any(FormData)
        }));
        expect(result).toEqual({ job_id: 'job-123', status: 'pending' });
    });

    test('uploadFile throws error on failure', async () => {
        const mockFile = new File(['content'], 'test.hwp');
        fetch.mockResolvedValueOnce({
            ok: false,
            json: async () => ({ detail: 'Upload failed' })
        });

        await expect(API.uploadFile(mockFile)).rejects.toThrow('Upload failed');
    });

    test('checkStatus calls correct endpoint', async () => {
        fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ status: 'processing', progress: 50 })
        });

        const status = await API.checkStatus('job-123');
        expect(fetch).toHaveBeenCalledWith('/api/status/job-123');
        expect(status.status).toBe('processing');
    });
});
