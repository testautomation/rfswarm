*** Settings ***
Resource 	ºCommon.robot

*** Test Cases ***
Issue #171
	[Tags]	ubuntu-latest		windows-latest		macos-latest
	@{agnt_options}= 	Create List 	-g 	1 	-m 	http://localhost:8138
	Run Agent 	${agnt_options}
	Log to console 	${CURDIR}
	# ${scenariofile}= 	Normalize Path 	${CURDIR}${/}..${/}..${/}Demo${/}demo.rfs
	${scenariofile}= 	Normalize Path 	${CURDIR}${/}testdata${/}Issue-#171${/}Issue171.rfs
	Log to console 	${scenariofile}
	@{mngr_options}= 	Create List 	-g 	1 	-s 	${scenariofile} 	-n
	Run Manager CLI 	${mngr_options}
	Wait For Manager
	Show Log 	stdout_manager.txt
	Show Log 	stderr_manager.txt
	Show Log 	stdout_agent.txt
	Show Log 	stderr_agent.txt

	${dbfile}= 	Find Result DB
	# Query Result DB 	${dbfile} 	Select * from Results
	${result}= 	Query Result DB 	${dbfile} 	Select * from ResultSummary;
	${result}= 	Query Result DB 	${dbfile} 	Select Name from ResultSummary;
	${result}= 	Query Result DB 	${dbfile} 	Select count(*) from ResultSummary;
	Should Be True	${result} > 0

	Stop Agent
