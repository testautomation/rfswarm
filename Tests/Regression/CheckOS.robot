
*** Test Cases ***

Check OS
	${uname}= 	Evaluate 	os.uname()		os
	Log 	${uname}
	Log to console 	${uname}
