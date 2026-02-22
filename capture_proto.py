#!/usr/bin/env python3
"""Capture actual protobuf request from cursor-agent."""

import subprocess
import sys
import os
import tempfile

# Create a script that will intercept the request
interceptor_code = '''
const http = require('http');
const https = require('https');

// Store original request function
const originalRequest = https.request;

// Intercept
https.request = function(options, callback) {
    const req = originalRequest.call(this, options, callback);

    const originalWrite = req.write.bind(req);
    req.write = function(chunk, encoding, callback) {
        if (options.path && options.path.includes('StreamChat')) {
            // Log the request
            process.stderr.write(`\\n=== INTERCEPTED REQUEST ===\\n`);
            process.stderr.write(`Path: ${options.path}\\n`);
            process.stderr.write(`Headers: ${JSON.stringify(options.headers)}\\n`);
            process.stderr.write(`Body (hex): ${chunk.toString('hex')}\\n`);
            process.stderr.write(`Body (base64): ${chunk.toString('base64')}\\n`);
            process.stderr.write(`=== END INTERCEPTED ===\\n`);
        }
        return originalWrite(chunk, encoding, callback);
    };

    return req;
};
'''

def main():
    print("Capturing protobuf request from cursor-agent...")

    # Create interceptor script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write(interceptor_code)
        interceptor_path = f.name

    # Run cursor-agent with NODE_OPTIONS to preload interceptor
    env = os.environ.copy()
    env['NODE_OPTIONS'] = f'--require {interceptor_path}'

    result = subprocess.run(
        ['cursor-agent', '--print', '--model', 'gpt-5.2', 'say hello'],
        capture_output=True,
        text=True,
        env=env,
        timeout=60
    )

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    # Clean up
    os.unlink(interceptor_path)

if __name__ == "__main__":
    main()
