"""mitmproxy addon to capture Cursor API requests."""
import os
from mitmproxy import http

class CursorCapture:
    def request(self, flow: http.HTTPFlow) -> None:
        if "cursor" in flow.request.host:
            print(f"\n{'='*60}")
            print(f"[REQUEST] {flow.request.method} {flow.request.url}")
            print(f"Headers: {dict(flow.request.headers)}")

            if flow.request.content:
                content = flow.request.content
                print(f"Body length: {len(content)}")
                print(f"Body (hex first 500): {content[:500].hex()}")

                # Save to file
                fname = f"/tmp/cursor_mitm_{flow.request.path.replace('/', '_')}.bin"
                with open(fname, 'wb') as f:
                    f.write(content)
                print(f"Saved to: {fname}")
            print('='*60)

    def response(self, flow: http.HTTPFlow) -> None:
        if "cursor" in flow.request.host and "Chat" in flow.request.path:
            print(f"\n[RESPONSE] {flow.response.status_code}")
            if flow.response.content:
                print(f"Response length: {len(flow.response.content)}")

addons = [CursorCapture()]
