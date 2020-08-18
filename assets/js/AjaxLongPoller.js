var loglinecount;
function connectToServer(file_to_tail, linenum, callback=false) {
    cts = $.ajax({
        dataType: "json",
        url: "/admin/logtail", // Python option
        //url: "LongPoller.php", // original PHP option
        data: { num: linenum, tailfile: file_to_tail },
        type: 'POST',
        timeout: 120000, // in milliseconds
        success: function(data) {
            if (data == null) {
                //console.log("Got back junk");
                console.log('ajax failed. reloading...');
                connectToServer(file_to_tail, 0);
                $("#tail_window").html("Error, reloading...");
            } else {
                //console.log("Got back good data");
                var items = [];
                loglinecount = parseInt(data.count);
                $("#logname").text('Tailing file: ' + data.filename);
                if (loglinecount < 0) {
                    console.log('ajax failed. reloading...');
                    connectToServer(file_to_tail, linenum);
                } else if (loglinecount === 0) {
                    $("#tail_window").text('[Empty file]');
                } else {
                    //console.log("Count "+loglinecount);
                    $.each(data.loglines, function(key, val) {
                        //console.log("Val "+val.toString());
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
                console.log('ajax failed. reloading...');
                connectToServer(file_to_tail, 0);
                $("#tail_window").html("Local timeout, reloading...");
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