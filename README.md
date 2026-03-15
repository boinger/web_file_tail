# web_file_tail

Watch a file `tail -F` in real time in a web browser using AJAX long-polling and jQuery.

> **Warning**: This exposes system log files over HTTP. **Never** run this on a publicly-facing server. At minimum, put it behind a VPN and password-protect it. You have been warned.

## How It Works

The browser makes a POST request to the server with the last known line count (or 0 on first load). The server checks the file:

- **New lines available** → returns them immediately as JSON along with the updated line count.
- **No new lines** → polls the file's mtime once per second for up to 50 seconds. If the file changes, returns the new lines. If 50 seconds pass with no change, returns `count: -1` and the client retries.

The browser renders each line into a `<div>`, auto-scrolls to the bottom, and immediately makes the next request. This loop continues indefinitely.

The server-side poll timeout (50s) is intentionally shorter than the client AJAX timeout (60s) to prevent overlapping requests.

## Setup

### Requirements

- Python 3 (no third-party packages)
- A WSGI server (Apache + mod_wsgi, gunicorn, etc.)
- `sudo` access for the web server user to run `logtail.py`

### 1. Deploy the files

Place the Python scripts somewhere the WSGI server can reach. The default path in the code is `/usr/local/sbin/logtail.py` — edit `longpoller.py` line 36 (`logtail_py`) if yours differs.

The HTML/JS/CSS files go wherever your web server serves static content.

### 2. Configure WSGI

For Apache with mod_wsgi, add to your site config:

```apache
WSGIScriptAlias /admin/logtail /var/www/sbin/longpoller.py
WSGIScriptAlias /admin/tailoptions /var/www/sbin/tailoptions.py
```

### 3. Configure sudo

The web server user needs passwordless sudo for `logtail.py` only:

```
apache ALL=(ALL) NOPASSWD:/usr/local/sbin/logtail.py
```

Replace `apache` with your web server user (`www-data`, etc.).

### 4. Configure log files

Edit `logpaths.txt` (must be in the same directory as `longpoller.py` and `tailoptions.py`). Each line maps a codename to a file path:

```
mycodename    /var/log/messages
anothercode   /var/log/httpd/error_log
```

- Codenames are what the browser sends — actual file paths never leave the server.
- Use `#DAY#` in a path to substitute the abbreviated weekday (e.g., `Mon`, `Tue`), useful for day-rotated logs like PostgreSQL.
- Blank lines and lines starting with `#` are ignored.

### 5. Open in browser

- **Simple view** (single file via query param): `http://yourserver/path/to/index.html?tailfile=mycodename`
- **Form-based view** (dropdown selector + pause/resume): `http://yourserver/path/to/form-based.html`

The form-based view supports spacebar to toggle pause.

## File Overview

| File | Purpose |
|------|---------|
| `longpoller.py` | WSGI app — receives tail requests, delegates file I/O to `logtail.py` via sudo, returns JSON |
| `logtail.py` | CLI tool — provides `linecount`, `mtime`, `isreadable`, and `tail` operations on files. Runs under sudo so only this one script needs elevated privileges. |
| `tailoptions.py` | WSGI app — returns `logpaths.txt` contents as a JS-consumable map for the form-based UI dropdown |
| `logpaths.txt` | Codename → file path mapping (space-delimited, one per line) |
| `index.html` | Minimal frontend — tails a single file specified via `?tailfile=` query param |
| `form-based.html` | Full-featured frontend — dropdown file selector, pause/resume, auto-scroll |
| `assets/js/AjaxLongPoller.js` | Client-side long-polling, DOM rendering, pause/unpause, `$_GET` helper |
| `assets/css/filetail.css` | Styles for the tail window and pause overlay |
| `assets/js/jquery-3.7.1.min.js` | Vendored jQuery |
| `deprecated/LongPoller.php` | Original PHP implementation from upstream — not maintained |

## Configuration Reference

| Setting | File | Default | Description |
|---------|------|---------|-------------|
| `logtail_py` | `longpoller.py:36` | `/usr/local/sbin/logtail.py` | Path to the logtail CLI script |
| `safety_max` | `longpoller.py:32` | `50` | Max seconds to poll for file changes before returning -1 |
| `initial_tail` | `longpoller.py:34` | `25` | Number of lines to return on first request |
| `timeout` | `AjaxLongPoller.js:12` | `60000` | Client AJAX timeout in milliseconds (must be > safety_max) |
| `maxLines` | `AjaxLongPoller.js:37` | `5000` | Max DOM nodes before oldest lines are pruned |
| Log level | `longpoller.py:38` | `ERROR` | Change to `INFO` or `DEBUG` for troubleshooting (logs to stderr) |

## Acknowledgments

Based on [richardvk/web_file_tail](https://github.com/richardvk/web_file_tail). Python rewrite by [@boinger](https://github.com/boinger).
