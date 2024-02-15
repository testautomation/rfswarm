*** Settings ***
Library 	OperatingSystem
Library 	Process
Library 	DatabaseLibrary
Library 	String

*** Variables ***

${pyfile_agent} 		${EXECDIR}${/}rfswarm_agent${/}rfswarm_agent.py
${pyfile_manager} 	${EXECDIR}${/}rfswarm_manager${/}rfswarm.py
${process_agent} 		None
${process_manager} 	None

# datapath: /home/runner/work/rfswarm/rfswarm/rfswarm_manager/results/PreRun
${results_dir} 			${EXECDIR}${/}rfswarm_manager${/}results

*** Keywords ***

Show Log
	[Arguments]		${filename}
	Log to console 	${\n}-----${filename}-----
	${filedata}= 	Get File 	${filename}
	Log to console 	${filedata}
	Log to console 	-----${filename}-----${\n}

Run Agent
	[Arguments]		${options}=None
	IF  ${options} == None
		${options}= 	Create List
	END
	Log to console 	\${options}: ${options}
	${process}= 	Start Process 	python3 	${pyfile_agent}  @{options}  alias=Agent 	stdout=${OUTPUT DIR}${/}stdout_agent.txt 	stderr=${OUTPUT DIR}${/}stderr_agent.txt
	Set Test Variable 	$process_agent 	${process}

Run Manager CLI
	[Arguments]		${options}=None
	IF  ${options} == None
		${options}= 	Create List
	END
	Log to console 	\${options}: ${options}
	${process}= 	Start Process 	python3 	${pyfile_manager}  @{options}  alias=Agent 	stdout=${OUTPUT DIR}${/}stdout_manager.txt 	stderr=${OUTPUT DIR}${/}stderr_manager.txt
	Set Test Variable 	$process_manager 	${process}

Wait For Manager
	[Arguments]		${timeout}=10min
	${result}= 	Wait For Process		${process_manager} 	timeout=${timeout} 	on_timeout=kill
	# Should Be Equal As Integers 	${result.rc} 	0
	Log to console 	${result.rc}

Stop Manager
	${result}= 	Terminate Process		${process_manager}
	# Should Be Equal As Integers 	${result.rc} 	0
	Log to console 	${result.rc}

Stop Agent
	${result}= 	Terminate Process		${process_agent}
	# Should Be Equal As Integers 	${result.rc} 	0
	Log to console 	${result.rc}

Find Result DB
	${fols}= 	List Directory 	${results_dir}
	Log to console 	${fols}
	${fols}= 	List Directory 	${results_dir} 	*_* 	absolute=True
	# Log to console 	${fols}
	${files}= 	List Directory 	${fols[0]}
	Log to console 	${files}
	${file}= 	List Directory 	${fols[0]} 	*.db 	absolute=True
	Log to console 	${file[0]}
	RETURN 	${file[0]}

Query Result DB
	[Arguments]		${dbfile} 	${sql}
	Log to console 	\${dbfile}: ${dbfile}
	${dbfile}= 	Replace String 	${dbfile} 	${/} 	/
	# Log to console 	\${dbfile}: ${dbfile}
	Connect To Database Using Custom Params 	sqlite3 	database="${dbfile}", isolation_level=None
	Log to console 	\${sql}: ${sql}
	${result}= 	Query 	${sql}
	Log to console 	\${result}: ${result}
	Disconnect From Database
	RETURN 	${result}


#
