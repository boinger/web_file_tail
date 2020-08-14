$(function() {
    tailfile = 'httpdaccesslog';
    connectToServer(tailfile,0);
});

function connectToServer(file_to_tail = 'httpdaccesslog', linenum) {
    $.ajax({
        dataType: "json",
        url: "/admin/logtail",
        data: { num: linenum, tailfile: file_to_tail },
        type: 'POST',
        timeout: 120000, // in milliseconds
        success: function(data) {
            if (data == null) {
                //console.log("Got back junk");
                console.log('ajax failed. reloading...');
                connectToServer(file_to_tail,0);
                $("#tail_window").html("Error, reloading...");
            } else {
                //console.log("Got back good data");
                var items = [];
                var count = parseInt(data.count);
                if (count < 0) {
                    console.log('ajax failed. reloading...');
                    connectToServer(file_to_tail,linenum);
                }
                //console.log("Count "+count);
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
                $('#tail_window').each(function(){
                    maxlength = 50000;
                    thislength = $(this).html().length;
                    if (thislength > maxlength) {
                        lengthdelta = thislength - maxlength;
                        var truncated = $(this).html().substr(lengthdelta);
                        $(this).html('[...] ' + truncated);
                    }
                });

                connectToServer(file_to_tail,count);
            } // end else
        }, // end success
        error: function(request, status, err) {
            if (status == "timeout") {
                console.log('ajax failed. reloading...');
                connectToServer(file_to_tail,0);
                $("#tail_window").html("Local timeout, reloading...");
            } // end if
        } // end error
    }); // end ajax
} // end function connectToServer
