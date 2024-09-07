*** Settings ***
Resource 	CommandLine_Common.robot

Suite Setup 	Set Platform

*** Test Cases ***
Install Application Icon or Desktop Shortcut
	[Tags]	ubuntu-latest		windows-latest		macos-latest 	Issue #145

	@{agent_options}= 	Create List 	-c 	ICON
	Run Agent 	${agent_options}

	Check Icon Install
