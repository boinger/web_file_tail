$(function() {
    connectToServer(0);
});

function connectToServer(linenum) {
    $.ajax({
        dataType: "json",
        url: "LongPoller.php",
        data: { num: linenum },
        timeout: 120000, // in milliseconds
        success: function(data) {
            if (data == null) {
                //console.log("Got back junk");
                console.log('ajax failed. reloading...');
                connectToServer(0);
                $("#tail_window").html("Error, reloading...");
            } else {
                //console.log("Got back good data");
                var items = [];
                var count = parseInt(data.count);
                if (count < 0) {
                    console.log('ajax failed. reloading...');
                    connectToServer(linenum);
                }
                //console.log("Count "+count);
                var loglines = data.loglines;
                loglines.reverse();
                var l = 0;
                $.each(loglines, function(key, val) {
                    l = l + 1;
                    //console.log("Val "+val.toString());
                    $("#tail_window").prepend("<br />");
                    items.push(val.toString());
                    var newlines = items.join("");
                    // Let's sanitize output
                    $("#tail_window").prepend(document.createTextNode(newlines));

                    items = [];
                }); // end each

                connectToServer(count);




            } // end else
        }, // end success
        error: function(request, status, err) {
            if (status == "timeout") {
                console.log('ajax failed. reloading...');
                connectToServer(0);
                $("#tail_window").html("Local timeout, reloading...");
            } // end if
        } // end error
    }); // end ajax
} // end function connectToServer