// Intercept ALL network requests from cursor-agent
const fs = require('fs');
const http = require('http');
const https = require('https');

// Intercept https.request
const origHttpsRequest = https.request;
https.request = function(...args) {
    const req = origHttpsRequest.apply(this, args);
    const options = args[0];

    if (typeof options === 'object') {
        console.error(`[HTTPS] ${options.method || 'GET'} ${options.hostname}${options.path}`);
    }

    const origWrite = req.write.bind(req);
    req.write = function(data, ...rest) {
        if (data && data.length > 0) {
            const buf = Buffer.from(data);
            console.error(`[HTTPS WRITE] ${buf.length} bytes`);
            if (options.path && (options.path.includes('Chat') || options.path.includes('chat'))) {
                console.error('[BODY HEX]', buf.toString('hex').substring(0, 500));
                fs.writeFileSync('/tmp/cursor_req_' + Date.now() + '.bin', buf);
            }
        }
        return origWrite(data, ...rest);
    };

    return req;
};

// Intercept http.request
const origHttpRequest = http.request;
http.request = function(...args) {
    const req = origHttpRequest.apply(this, args);
    const options = args[0];

    if (typeof options === 'object') {
        console.error(`[HTTP] ${options.method || 'GET'} ${options.hostname}${options.path}`);
    }

    return req;
};

// Intercept fetch if available
if (typeof globalThis.fetch !== 'undefined') {
    const origFetch = globalThis.fetch;
    globalThis.fetch = async function(url, options = {}) {
        console.error(`[FETCH] ${options.method || 'GET'} ${url}`);
        if (options.body) {
            console.error(`[FETCH BODY] ${options.body.length || 'unknown'} bytes`);
            if (url.includes('Chat') || url.includes('chat')) {
                const buf = Buffer.from(options.body);
                console.error('[FETCH BODY HEX]', buf.toString('hex').substring(0, 500));
                fs.writeFileSync('/tmp/cursor_fetch_' + Date.now() + '.bin', buf);
            }
        }
        return origFetch.apply(this, arguments);
    };
}

console.error('[INTERCEPTOR] Network interceptor loaded');
