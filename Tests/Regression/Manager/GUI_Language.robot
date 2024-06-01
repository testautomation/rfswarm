*** Settings ***
Resource 	GUI_Common.robot

Suite Setup 	Set Platform
Test Setup 	Language Test Init
Test Teardown 	Language Test End
Test Tags 	windows-latest	ubuntu-latest	macos-latest	Issue #238
Test Template 	Add Test In Language

*** Test Cases ***
# Issue #238
Bulgarian		bg
Bosnian		bs
Czech		cs
German		de
English		en
# Spanish		es
# Finnish		fi
# French		fr
# Hindi		hi
# Italian		it
# Dutch		nl
# Polish		pl
# Portuguese		pt
# Brazilian Portuguese		pt_br
# Romanian		ro
# Russian		ru
# Swedish		sv
# Thai		th
# Turkish		tr
# Ukrainian		uk
# Vietnamese		vi
# Chinese Simplified		zh_cn
# Chinese Traditional		zh_tw



*** Keywords ***
Add Test In Language
	[Arguments] 	${langcode}
	Log 	${langcode} 	console=True
	Open Manager GUI
	Start New Scenario
	Check If The Agent Is Ready
	Click Tab 	Plan
	Select ${langcode} Language Test Script
	Select 1 Robot Test Case
	Take A Screenshot
	Check Agent Downloaded ${langcode} Language Test Files


Language Test Init
	${mgrini}= 	Get Manager INI Location
	Set INI Window Size 	1200 	600
	# ${options}= 	Create List 	 	-d 	${agent_dir}
	Open Agent

Language Test End
	Run Keyword		Close Manager GUI ${platform}
	Stop Agent

#
