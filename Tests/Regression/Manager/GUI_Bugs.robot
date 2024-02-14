*** Settings ***
Resource 	GUI_Common.robot

Suite Setup 	Set Platform

*** Test Cases ***
Issue #171
	[Tags]	ubuntu-latest		windows-latest		macos-latest
	Open Agent
	Open Manager GUI
	Resize Window 	100 	10
	Take A Screenshot

	Wait Agent Ready
	Click Tab 	 Run

	# manager_macos_button_runsettings
	Click Button 	runsettings
	Take A Screenshot

	Run Keyword 	Close Manager GUI ${platform}
	Stop Agent
