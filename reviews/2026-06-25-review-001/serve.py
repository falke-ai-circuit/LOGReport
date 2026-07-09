#!/usr/bin/env python3
"""Serve the review folder as a browsable HTML site on port 8000."""
import http.server
import os
import markdown
import html

PORT = 8642
DIR = "/opt/data/LOGReport/reviews/2026-06-25-review-001"

class ReviewHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def do_GET(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            # Directory listing
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            items = sorted(os.listdir(path))
            html_out = ['<!DOCTYPE html><html><head><meta charset="utf-8">',
                       '<title>LOGReport Review 2026-06-25-001</title>',
                       '<style>body{font-family:system-ui,max-width:900px,margin:2rem auto,padding:0 1rem}',
                       'a{color:#0366d6}h1{border-bottom:1px solid #eee}',
                       'li{padding:0.3rem 0}pre{background:#f6f8fa;padding:1rem;overflow-x:auto;border-radius:6px}',
                       'code{background:#f6f8fa;padding:0.2rem 0.4rem;border-radius:3px}',
                       'table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:0.5rem}',
                       'th{background:#f6f8fa}</style></head><body>']
            # If there's an index.md or REVIEW.md, show it rendered
            review_md = os.path.join(path, "REVIEW.md")
            if os.path.exists(review_md) and self.path.rstrip("/").endswith(("001", "001/")):
                with open(review_md) as f:
                    md_content = f.read()
                html_out.append(markdown.markdown(md_content, extensions=["tables", "fenced_code"]))
            else:
                html_out.append("<h1>Directory listing</h1><ul>")
                for item in items:
                    full = os.path.join(path, item)
                    if os.path.isdir(full):
                        html_out.append(f'<li><a href="{item}/">{item}/</a></li>')
                    else:
                        html_out.append(f'<li><a href="{item}">{item}</a></li>')
                html_out.append("</ul>")
            html_out.append("</body></html>")
            self.wfile.write("".join(html_out).encode())
            return
        if path.endswith(".md"):
            with open(path) as f:
                md_content = f.read()
            html_body = markdown.markdown(md_content, extensions=["tables", "fenced_code"])
            html_out = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>{os.path.basename(path)}</title>
<style>
body{{font-family:system-ui;max-width:900px;margin:2rem auto;padding:0 1rem;line-height:1.6;color:#24292e}}
a{{color:#0366d6}}h1,h2,h3{{border-bottom:1px solid #eee;padding-bottom:0.3rem}}
pre{{background:#f6f8fa;padding:1rem;overflow-x:auto;border-radius:6px}}
code{{background:#f6f8fa;padding:0.2rem 0.4rem;border-radius:3px;font-size:0.9em}}
pre code{{background:none;padding:0}}
table{{border-collapse:collapse;width:100%;margin:1rem 0}}
td,th{{border:1px solid #ddd;padding:0.5rem;text-align:left}}
th{{background:#f6f8fa}}
hr{{border:none;border-top:2px solid #eee;margin:2rem 0}}
blockquote{{border-left:4px solid #dfe2e5;padding:0 1rem;color:#6a737d}}
</style></head><body>{html_body}</body></html>"""
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_out.encode())
            return
        super().do_GET()

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), ReviewHandler)
    print(f"Serving review on http://0.0.0.0:{PORT}")
    server.serve_forever()