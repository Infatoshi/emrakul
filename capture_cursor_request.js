// Intercept cursor-agent HTTP requests to capture protobuf format
// Run: NODE_OPTIONS="--require ./capture_cursor_request.js" cursor-agent --print "test"

const https = require('https');
const fs = require('fs');

const originalRequest = https.request;

https.request = function(options, callback) {
    const req = originalRequest.call(this, options, callback);

    if (options.hostname && options.hostname.includes('cursor')) {
        const chunks = [];
        const originalWrite = req.write.bind(req);

        req.write = function(chunk) {
            chunks.push(Buffer.from(chunk));

            // Log to stderr so it doesn't mix with stdout
            const combined = Buffer.concat(chunks);
            console.error('\n=== CAPTURED REQUEST ===');
            console.error('Path:', options.path);
            console.error('Content-Type:', options.headers['content-type']);
            console.error('Body length:', combined.length);
            console.error('Body (hex):', combined.toString('hex'));
            console.error('Body (base64):', combined.toString('base64'));

            // Save to file
            fs.writeFileSync('/tmp/cursor_request.bin', combined);
            fs.writeFileSync('/tmp/cursor_request.hex', combined.toString('hex'));
            console.error('Saved to /tmp/cursor_request.bin');
            console.error('=== END CAPTURED ===\n');

            return originalWrite(chunk);
        };
    }

    return req;
};

console.error('Cursor request interceptor loaded');
