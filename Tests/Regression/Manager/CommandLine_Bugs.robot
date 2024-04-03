# *** Settings ***
# Resource 	CommandLine_Common.robot

# *** Test Cases ***
# Robbot files with same name but different folders
# 	[Tags]	ubuntu-latest		windows-latest		macos-latest 	Issue #184
# 	Log To Console 	${\n}TAGS: ${TEST TAGS}
# 	@{agnt_options}= 	Create List 	-g 	1 	-m 	http://localhost:8138
# 	Run Agent 	${agnt_options}
# 	Sleep    1s
# 	Check Agent Is Running
# 	Log to console 	${CURDIR}
# 	${scenariofile}= 	Normalize Path 	${CURDIR}${/}testdata${/}Issue-#184${/}Issue-#184.rfs
# 	Log to console 	${scenariofile}
# 	@{mngr_options}= 	Create List 	-g 	1 	-s 	${scenariofile} 	-n
# 	Run Manager CLI 	${mngr_options}
# 	Wait For Manager
# 	Stop Agent
# 	Show Log 	${OUTPUT DIR}${/}stdout_manager.txt
# 	Show Log 	${OUTPUT DIR}${/}stderr_manager.txt
# 	Show Log 	${OUTPUT DIR}${/}stdout_agent.txt
# 	Show Log 	${OUTPUT DIR}${/}stderr_agent.txt

# 	Should Not Contain 	${OUTPUT DIR}${/}stdout_agent.txt 		Robot returned an error
# 	Should Not Contain 	${OUTPUT DIR}${/}stdout_agent.txt 		please check the log file

# 	${dbfile}= 	Find Result DB
# 	${result}= 	Query Result DB 	${dbfile} 	Select count(*) from Summary;
# 	Should Be True	${result[0][0]} > 0
# 	Should Be Equal As Numbers	${result[0][0]} 	4
# 	${result}= 	Query Result DB 	${dbfile} 	Select count(*) from Summary where _pass > 0;
# 	Should Be True	${result[0][0]} > 0
# 	Should Be Equal As Numbers	${result[0][0]} 	4
# 	${result}= 	Query Result DB 	${dbfile} 	Select result_name from Summary;
# 	Should Contain 	${result} 	${{ ('Folder A Log Variables AAA',) }}
# 	Should Contain 	${result} 	${{ ('Folder B Log Variables BBB',) }}
# 	${result}= 	Query Result DB 	${dbfile} 	Select result_name from Summary where _pass > 0;
# 	Should Contain 	${result} 	${{ ('Folder A Log Variables AAA',) }}
# 	Should Contain 	${result} 	${{ ('Folder B Log Variables BBB',) }}
