# web_file_tail
Watch a file tail in real time on a web browser using longpolling and jquery.

This is really sample code that can be modified to suit almost any realtime 'push to the browser' requirement.

- When called for the first time, the script requests some content from the server with 0 (zero) as the current line count.
- It then waits for the server, which should initially return the first 10 lines of the log file back to the browser,
  as well as the current max line number of the file.
- The browser then absorbs the returned json data, puts it in a DIV and then immediately makes an identical call to the server
  again. However this time the returned last line number is included in the ajax call so the server knows what the last line was
  that the client received.
- The server checks the current file length (number of lines) to determine if any new lines were written since the last call; if
  so it returns them immediately and the same process as above is followed.
- If no new lines have yet been added since the last call, then the server script looks at the current file ctime to note when it
  was last updated.
- It then goes into a loop, where every second it checks the file's ctime and compare it to the ctime when the client made the
  call to the browser.
- When the ctime is updated, the script retreives whichever lines have been written and returns them to the client, who once
  again processes them, adds them to the current DIV content and then makes a new call to the server... and so the process
  continues!

Notes:
- The javascript uses the '.ajax' jquery method since this allows for a timeout to be set. Currently an arbitrary timeout of 120s
  is used since the test log we are using returns data at least every minute, so in theory the timeout should never be reached.
- The server will also NOT sit in its one second check loop indefinately. To prevent this invocation of the script from living
  forever if the client dies, it will exit the loop after 115 iterations. That is, it should terminate after 115 seconds, which
  is longer than the clients timeout, ie the script should always time out before the client, or, the only time the client should
  time out is if the script dies. This is because if both client and server are still running, and the client time out first, the
  client will make a new request while the original is still running. There might not be any real implication though.
- This sample code was tested by tailing the syslog on an Ubuntu server. This required read rights for the www-data user to the
  /var/log/syslog file. This was achieved by making system calls as 'sudo' user and adding privileges specifically to the
  required script with the following sudoers config:

  %www-data ALL=(ALL) NOPASSWD: /usr/bin/wc, /usr/bin/tail

TODO:
- keep a track in the browser of the total number of lines so far and truncate some of the old data after a certain interval
  or line count do that the DIV content does not grow indefinately.
- get rid of the hard coded references to fully qualified path names of system commands, make it system independant
- add jquery as a CDN reference
