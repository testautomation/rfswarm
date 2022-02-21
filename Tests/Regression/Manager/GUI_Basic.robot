*** Settings ***
Library 	OperatingSystem
Library 	Process
Library 	SikuliLibrary

Suite Setup			Sikili Setup
Suite Teardown		Sikili Teardown


*** Variables ***
${IMAGE_DIR} 	${CURDIR}/../../Screenshots-doc/img

*** Test Cases ***
GUI Runs and Closes
	[Tags]	macos-latest
	Start Process 	python3 	${EXECDIR}${/}rfswarm_manager${/}rfswarm.py    alias=Manager 	stdout=${OUTPUT DIR}${/}stdout.txt 	stderr=${OUTPUT DIR}${/}stderr.txt
	Wait Until Screen Contain 	rfwasrm_mac_Window_Controls.png 	120
	Make rfswarm Active
	Type With Modifiers 	q 	CMD
	${result}= 	Wait For Process 	Manager
	Should Be Equal As Integers 	${result.rc} 	0


*** Keywords ***
Sikili Setup
	Add Image Path    ${IMAGE_DIR}
	# cleanup previous output
	Log To Console    ${OUTPUT DIR}
	Remove File    ${OUTPUT DIR}${/}*.txt
	Remove File    ${OUTPUT DIR}${/}sikuli_captured${/}*.*

Sikili Teardown
	${running}= 	Is Process Running 	Manager
	IF 	${running}
		${result}= 	Terminate Process 	Manager
		Log    ${result}
		${stdout}= 	Get File 	${OUTPUT DIR}${/}stdout.txt
		Log    ${stdout}
		${stderr}= 	Get File 	${OUTPUT DIR}${/}stderr.txt
		Log    ${stderr}
	END

Make rfswarm Active
	Click 	rfwasrm_mac_title_bg.png
	Run Keyword And Ignore Error	Click Plan

Click Plan
	Click	rfwasrm_mac_Plan.png
	Wait until screen contain 	rfwasrm_mac_Play.png	10
