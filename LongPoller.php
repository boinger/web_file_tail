<?php

$logfile = '/var/log/syslog';
$wc = "/usr/bin/wc";
$sudo = "/usr/bin/sudo";
$tail = "/usr/bin/tail";
$cut = "/usr/bin/cut";
$tr = "/usr/bin/tr";

//error_log("Running LongPolling2.php");

$num = (isset($_GET['num'])) ? $_GET['num'] : 0;

if (!$num) {
	$cmd = "$sudo $wc -l $logfile | $cut -d \" \" -f 1 | $tr -d '\n' 2>/dev/null";
	$file_len = shell_exec($cmd);
        //error_log("INITLEN = $file_len");
 	$cmd = "$sudo $tail -10 $logfile";
	$logfile_lines = shell_exec($cmd);
	$logfile_lines_arr = preg_split('/\n/', trim($logfile_lines));
	$ret_arr = array('count'=>$file_len,'loglines'=>$logfile_lines_arr);
	//echo json_encode($logfile_lines_arr);
	echo json_encode($ret_arr);

}
else {
	//error_log("Num passed!");
	$nextline = $num+1;
	$safety_max = 130; // this is a number of seconds, it should be longer than the ajax timeout
	sleep(2);
	$cmd = "$sudo $wc -l $logfile | $cut -d \" \" -f 1 | $tr -d '\n' 2>/dev/null";
        $curr_len = shell_exec($cmd);
	if ($curr_len==$num) {
		clearstatcache(); // NB NB!!!
		$ft = filectime($logfile);
	        //error_log("CURRLEN = $curr_len (Filetime: $ft)");
		$cft = $ft;
		$safety = 0;
		while ($cft==$ft  && $safety < $safety_max) {
			clearstatcache(); // goes only with the log message below
			//error_log("$logfile was last modified: " . date ("F d Y H:i:s.", filemtime($logfile)));
			//error_log("file is STILL THE SAME SIZE, sleep.....zzzzzzz");
			//error_log("$safety) file STILL HAS THE SAME MTIME ($cft), sleep.....zzzzzzz");
			sleep(1);
			//$cmd = "$sudo $wc -l $logfile | $cut -d \" \" -f 1 | $tr -d '\n' 2>/dev/null";
	        	//$curr_len = shell_exec($cmd);
	        	//error_log("CURRLEN = $curr_len");
			clearstatcache();
			$cft = filectime($logfile);
			$safety++;
	 	} // end while

		if ($safety >= $safety_max){
			//error_log("SAFETY EXCEEDED, return for re-request");
			$ret_arr = array('count'=>-1);
			echo json_encode($ret_arr);
			exit;
		}

		//error_log("file has FINALLY UPDATED! ($cft)" );
		get_last_log_lines_from_pos($nextline);
		exit;

	} // end if	
	//error_log("file has ALREADY UPDATED (was $num, now $curr_len)");

	get_last_log_lines_from_pos($nextline);
	//$cmd = "$sudo $tail -n +$nextline $logfile";
	//error_log($cmd);
        //$logfile_lines = shell_exec($cmd);
        //$logfile_lines_arr = preg_split('/\n/', trim($logfile_lines));

	//$ret_arr = array('count'=>$curr_len,'loglines'=>$logfile_lines_arr);
	//echo json_encode($ret_arr);
	
} // end else

function get_last_log_lines_from_pos($pos) {
	global $sudo, $tail, $logfile, $wc, $cut, $tr;

	$cmd = "$sudo $tail -n +$pos $logfile";
        //error_log($cmd);
        $logfile_lines = shell_exec($cmd);
        $logfile_lines_arr = preg_split('/\n/', trim($logfile_lines));

	$cmd = "$sudo $wc -l $logfile | $cut -d \" \" -f 1 | $tr -d '\n' 2>/dev/null";
	$curr_len = shell_exec($cmd);
	//error_log("CURRLEN = $curr_len");

        $ret_arr = array('count'=>$curr_len,'loglines'=>$logfile_lines_arr);
        echo json_encode($ret_arr);
} // end function get_last_log_lines_from_pos
?>
