const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const htmlPath = path.join(__dirname, '../static/index.html');

try {
    if (!fs.existsSync(htmlPath)) {
        console.error("FAIL: static/index.html does not exist");
        process.exit(1);
    }

    const html = fs.readFileSync(htmlPath, 'utf8');
    const dom = new JSDOM(html);
    const doc = dom.window.document;

    const requiredIds = [
        'drop-zone',
        'file-input',
        'file-info',
        'filename',
        'progress-container',
        'progress-bar',
        'status-text',
        'result-area',
        'download-btn',
        'reset-btn'
    ];

    let missing = [];
    requiredIds.forEach(id => {
        if (!doc.getElementById(id)) {
            missing.push(id);
        }
    });

    if (missing.length > 0) {
        console.error(`FAIL: Missing required IDs: ${missing.join(', ')}`);
        process.exit(1);
    }

    console.log("PASS: All required UI elements are present.");

} catch (e) {
    console.error(`ERROR: ${e.message}`);
    process.exit(1);
}
