var loglinecount;
var debug = false;
function connectToServer(file_to_tail, linenum, callback=false) {
    if(cts) cts.abort();
    debug && console.log("connectToServer requested with args: "+ file_to_tail +", "+ linenum +", "+ callback)
    cts = $.ajax({
        dataType: "json",
        url: "/admin/logtail", // Python option
        //url: "LongPoller.php", // original PHP option
        data: { num: linenum, tailfile: file_to_tail },
        type: 'POST',
        timeout: 60000, // in milliseconds
        success: function(data) {
            if (data == null) {
                console.log('ajax returned junk. reloading...');
                connectToServer(file_to_tail, 0);
                $("#tail_window").html("Error, reloading...");
            } else {
                var items = [];
                loglinecount = parseInt(data.count);
                debug && console.log("Got back "+ loglinecount +" lines of data.");
                $("#logname").text('Tailing file: ' + data.filename);
                if (loglinecount < 0) {
                    console.log('Server timeout. Retrying from line '+ linenum +'...');
                    connectToServer(file_to_tail, linenum);
                    if(callback) callback(false);
                    return; // break out so we don't overlap self-calls
                } else if (loglinecount === 0) {
                    $("#tail_window").text('[Empty file]');
                } else {
                    $.each(data.loglines, function(key, val) {
                        //debug && console.log("Val "+val.toString());
                        items.push(val.toString());
                        var newlines = items.join("");
                        var div = document.createElement('div');
                        clean_line = document.createTextNode(newlines);
                        div.appendChild(clean_line);
                        $("#tail_window").append(div);
                        items = [];
                    }); // end each
                    // truncate the output if it starts to get long....
                    $('#tail_window').each(function() {
                        maxlength = 50000;
                        thislength = $(this).html().length;
                        if (thislength > maxlength) {
                            lengthdelta = thislength - maxlength;
                            var truncated = $(this).html().substr(lengthdelta);
                            $(this).html('[...] ' + truncated);
                        }
                    });
                }
                connectToServer(file_to_tail, loglinecount);
            } // end else
            if(callback) callback(true);
        }, // end success
        error: function(request, status, err) {
            if (status == "timeout") {
                console.log('ajax failed. retrying...');
                $('#tail_window').text(''); // blank out existing logfile tail lines
                connectToServer(file_to_tail, 0);
            } // end if
            if(callback) callback(false);
        } // end error
    }); // end ajax
} // end function connectToServer

function pause() {
    if(cts) cts.abort();
    $( "#pause" ).hide();
    $( "#resume" ).show();
    $("#tail_window").css("background-color", "rgba(0,0,0,0.05)");
    $('#tail_window').css("scroll-snap-type", "none");
    $('#pauseoverlay').fadeIn(50);
    paused = 1;
}

function unpause() {
    connectToServer(tailfile, loglinecount);
    $( "#resume" ).hide();
    $( "#pause" ).show();
    $("#tail_window").css("background-color", "white");
    $('#tail_window').css("scroll-snap-type", 'y');
    $('#pauseoverlay').fadeOut(50);
    paused = 0;
}

function $_GET(variable) {
    var query = window.location.search.substring(1);
    var vars = query.split("&");
    for (var i = 0; i < vars.length; i++) {
        var pair = vars[i].split("=");
        if (pair[0] == variable) {
            return unescape(pair[1]);
        }
    }
    return false;
}