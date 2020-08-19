# web_file_tail
Watch a file `tail -F` in real time on a web browser using longpolling and jquery.

This is really sample code that can be modified to suit almost any realtime 'push to the browser' requirement.

**_Important_**: You should basically never run this on a publicly-facing web server.  You are introducing a **MASSIVE SECURITY HOLE** by allowing visibility to system logs.  At the _very, very least_ this should be password-protected.  Really, though, you should have significant, real security around this thing (like, behind a VPN at least).

**Don't say I didn't warn you.**

# Functionality notes:
## Basics:
 * When called for the first time, the script sends a request for a file from the server with 0 (zero) as the current line count.

 * It then waits for the server, which should initially return the last 25 (default) lines of the log file back to the browser as a JSON bundle, as well as the current total line count of the file.

 * The browser then processes the returned JSON data, putting each line in a div and then immediately makes an new call to the server again, however but with previous line count is included in the ajax call (instead of 0) so the server knows what the last line was that the client received.

 * The server checks the current file line count to determine if any new lines were written since the last request; if so it returns them and the new file line count and the process repeats in a loop.

 * If no new lines have yet been added since the last call, then the server script looks at the current file ctime to note when it was last updated, and then goes into a one second loop, checking the file's ctime and comparing it to when the client made the request.

 * Once the ctime is updated, the script retreives the new lines and returns them to the client (in a JSON bundle), who once again processes them, adds them to the div and then makes a new request to the server... and so the process continues!

## Behind-the-scenes details:
 * The javascript uses jquery's .ajax() method since this allows for a timeout to be set. Currently an arbitrary timeout of 60 seconds is used since the test log we are using returns data at least every minute, so in theory the timeout should never be reached.

 * The server will also NOT sit in its one second check loop indefinately. It prevents this by exiting the loop after 50 iterations. That is, it should terminate after 50 seconds, which is shorter than the client's timeout. This is because if both client and server are still running and the client times out first, the client will make a new request while the original is still running. This doesn't cause any issues other than some overlapping requests, but it still is handled more gracefully if the script tells the browser it failed to return fresh data.  There may be better way to deal with this overall that I'm missing, perhaps.

 * This code defaults to tailing /var/log/messages (standard system log path on an Linux system). This requires read rights for the web server user (www-data, but this may differ on your system) to the file, which was achieved by making system calls as root using 'sudo', which necessitated adding privileges to the sudoers config:

  `%www-data ALL=(ALL) NOPASSWD: /usr/bin/wc, /usr/bin/tail`

# TODO:
* breakout system-level access to a dedicated script so as to simplify sudo requirements, as well as increase security slightly.
