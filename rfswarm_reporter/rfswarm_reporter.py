#!/usr/bin/python
#
#	Robot Framework Swarm
#		Reporter
#    Version 0.9.0
#

import sys
import platform
import os
import signal


import sqlite3

import time
from datetime import datetime, timezone
import threading

import inspect

import argparse
import configparser
import tempfile


import tkinter as tk				#python3
import tkinter.ttk as ttk			#python3
import tkinter.filedialog as tkf	#python3
import tkinter.messagebox as tkm	#python3
import tkinter.simpledialog as tksd

# required for matplot graphs
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
# required for matplot graphs

class ReporterBase():
	version="0.9.0"
	debuglvl = 0

	save_ini = True
	running = True
	displaygui = True
	gui = None
	darkmode = False

	template = None
	save_template = True

	dir_path = os.path.dirname(os.path.realpath(__file__))

	run_dbthread = True
	dbthread = None
	# datapath = ""
	# dbfile = ""
	datadb = None
	dbqueue = {"Write": [], "Read": [], "ReadResult": {}, "Results": [], "Metric": [], "Metrics": []}


	settings = {}

	def debugmsg(self, lvl, *msg):
		msglst = []
		prefix = ""
		if self.debuglvl >= lvl:
			try:
				suffix = ""
				if self.debuglvl >= 4:
					stack = inspect.stack()
					the_class = stack[1][0].f_locals["self"].__class__.__name__
					the_method = stack[1][0].f_code.co_name
					the_line = stack[1][0].f_lineno
					# print("RFSwarmBase: debugmsg: I was called by {}.{}()".format(str(the_class), the_method))
					prefix = "{}: {}({}): [{}:{}]	".format(str(the_class), the_method, the_line, self.debuglvl, lvl)
					# <36 + 1 tab
					# if len(prefix.strip())<36:
					# 	prefix = "{}	".format(prefix)
					# <32 + 1 tab
					if len(prefix.strip())<32:
						prefix = "{}	".format(prefix)
					# <28 + 1 tab
					# if len(prefix.strip())<28:
					# 	prefix = "{}	".format(prefix)
					# <24 + 1 tab
					if len(prefix.strip())<24:
						prefix = "{}	".format(prefix)

					msglst.append(str(prefix))

					# suffix = "	[{} @{}]".format(self.version, str(datetime.now().replace(microsecond=0).isoformat(sep=' ')))
					suffix = "	[{} @{}]".format(self.version, str(datetime.now().isoformat(sep=' ', timespec='seconds')))
					# suffix = "	[{} @{}]".format(self.version, "HH:mm:SS")

				for itm in msg:
					msglst.append(str(itm))
				msglst.append(str(suffix))
				print(" ".join(msglst))
			except:
				pass

	def findiniloctaion(self):

		if self.args.ini:
			self.debugmsg(1, "self.args.ini: ", self.args.ini)
			return self.args.ini

		inilocations = []

		srcdir = os.path.join(os.path.dirname(__file__))
		self.debugmsg(7, "srcdir[-2]: ", srcdir[-2:])
		if srcdir[-2:] == "/.":
			srcdir = srcdir[0:-2]
		self.debugmsg(7, "srcdir: ", srcdir)

		inifilename = "RFSwarmReporter.ini"
		# default location for all previous versions
		inilocations.append(os.path.join(srcdir, inifilename))
		# probably best location
		inilocations.append(os.path.join(os.path.expanduser("~"), ".rfswarm", inifilename))
		# last resort location
		inilocations.append(os.path.join(tempfile.gettempdir(), inifilename))

		self.debugmsg(6, "inilocations: ", inilocations)


		for iniloc in inilocations:
			self.debugmsg(7, "iniloc: ", iniloc)
			if os.path.isfile(iniloc):
				self.debugmsg(7, "iniloc exists")
				return iniloc
			else:
				# can we write to this location?
				# 	if anything in the try statement fails then we can't so progress to next location
				self.debugmsg(7, "iniloc can be created?")
				try:
					loc = os.path.dirname(iniloc)
					self.debugmsg(7, "loc: ", loc)
					self.debugmsg(7, "loc isdir:", os.path.isdir(loc))
					if not os.path.isdir(loc):
						self.debugmsg(7, "creating loc")
						os.makedirs(loc)
						self.debugmsg(7, "loc created")

					self.debugmsg(7, "os.access(loc): ", os.access(loc, os.X_OK | os.W_OK))
					if os.access(loc, os.X_OK | os.W_OK):
						self.debugmsg(7, "iniloc can be created!")
						return iniloc
				except:
					pass
		# This should cause saveini to fail?
		return None

	def saveini(self):
		self.debugmsg(6, "save_ini:", self.save_ini)
		if self.save_ini:
			with open(base.reporter_ini, 'w') as configfile:    # save
				base.config.write(configfile)
				self.debugmsg(6, "File Saved:", self.reporter_ini)

	def template_create(self):
		# base.template_create()
		base.template = configparser.ConfigParser()
		base.config['Reporter']['Template'] = ""
		if "Template" not in base.template:
			base.template["Template"] = {}
		base.template["Template"]["Order"] = ""
		# base.debugmsg(5, "template order:", base.template["Template"]["Order"])
		base.debugmsg(5, "base.template: ", base.template._sections)

		self.template_new_section("TOP", "Executive Summary")
		self.template_new_section("TOP", "Test Result Summary")


	def template_get_order(self, parent):
		if parent == "TOP":
			base.debugmsg(5, "template order:", base.template["Template"]["Order"])
			if len(base.template["Template"]["Order"])>0:
				return base.template["Template"]["Order"].split(',')
			else:
				return []
		else:
			base.debugmsg(5, "parent order:", base.template[parent])
			if "Order" in base.template[parent]:
				return base.template[parent]["Order"].split(',')
			else:
				return []

	def template_set_order(self, parent, orderlst):
		base.debugmsg(5, "parent:", parent, "	orderlst: ", orderlst)
		if parent == "TOP":
			base.template["Template"]["Order"] = ",".join(orderlst)
		else:
			base.template[parent]["Order"] = ",".join(orderlst)

	def template_new_section(self, parent, name):
		id = "{:02X}".format(int(time.time()*10000))
		# id = "{:02X}".format(int(time.time()*1000000))
		# id = "{:02X}".format(time.time()) # cannot convert float
		base.debugmsg(5, "id:", id)
		self.template_add_section(parent, id, name)
		return id

	def template_add_section(self, parent, id, name):
		base.debugmsg(5, "parent: ", parent)
		if id not in base.template:
			base.template[id] = {}
		base.template[id]['Name'] = name
		base.template[id]['Parent'] = parent
		order = self.template_get_order(parent)
		base.debugmsg(5, "order: ", order)
		order.append(id)
		self.template_set_order(parent, order)
		base.debugmsg(5, "base.template: ", base.template._sections)


	def template_item_parent(self, id):
		if id in base.template and 'Parent' in base.template[id]:
			return base.template[id]['Parent']
		else:
			return "TOP"

	def template_remove_section(self, id):
		parent = self.template_item_parent(id)
		order = self.template_get_order(parent)
		base.debugmsg(5, "order: ", order)
		pos = order.index(id)
		base.debugmsg(5, "pos: ", pos)
		order.pop(pos)
		base.debugmsg(5, "order: ", order)
		self.template_set_order(parent, order)
		base.debugmsg(5, "base.template: ", base.template._sections)
		subitems = self.template_get_order(id)
		for item in subitems:
			self.template_remove_section(item)
		del base.template[id]
		base.debugmsg(5, "base.template: ", base.template._sections)

	def template_move_section_up(self, id):
		parent = self.template_item_parent(id)
		order = self.template_get_order(parent)
		base.debugmsg(5, "order: ", order)
		pos = order.index(id)
		base.debugmsg(5, "pos: ", pos)
		order.pop(pos)
		order.insert(pos -1, id)
		base.debugmsg(5, "order: ", order)
		self.template_set_order(parent, order)

	def template_move_section_down(self, id):
		parent = self.template_item_parent(id)
		order = self.template_get_order(parent)
		base.debugmsg(5, "order: ", order)
		pos = order.index(id)
		base.debugmsg(5, "pos: ", pos)
		order.pop(pos)
		order.insert(pos +1, id)
		base.debugmsg(5, "order: ", order)
		self.template_set_order(parent, order)

		# base.template["Template"]["Order"].index('ED299C2969A') # get index from list
		# base.template["Template"]["Order"].insert(1, base.template["Template"]["Order"].pop(2)) # move item in list



	def template_save(self, filename):
		saved = False
		if filename is None or len(filename)<1:
			filename = base.config['Reporter']['Template']
		with open(filename, 'w') as templatefile:    # save
			base.template.write(templatefile)
			self.debugmsg(6, "Template Saved:", filename)
			saved = True
		if saved:
			base.config['Reporter']['Template'] = filename
			path, file= os.path.split(base.config['Reporter']['Template'])
			base.config['Reporter']['TemplateDir'] = path
			base.saveini()


	def template_open(self, filename):
		if len(filename)>0 and os.path.isfile(filename):
			base.debugmsg(7, "filename: ", filename)

			base.config['Reporter']['Template'] = filename
			path, file= os.path.split(base.config['Reporter']['Template'])
			base.config['Reporter']['TemplateDir'] = path
			base.saveini()

			base.template = configparser.ConfigParser()
			base.template.read(filename)
		else:
			base.template_create()


	def open_results_db(self, dbpath):
		self.close_results_db()
		if self.datadb is None:
			base.debugmsg(5, "Connect to DB")
			self.datadb = sqlite3.connect(dbpath)

	def close_results_db(self):
		# base.config['Reporter']['Results']
		if self.datadb is not None:
			base.run_dbthread = False
			base.debugmsg(5, "Disconnect and close DB")
			self.datadb.commit()
			self.datadb.close()
			self.datadb = None

	def run_db_thread(self):
		while base.run_dbthread:
			if (self.datadb is None):
				base.debugmsg(9, "open results database")
				# self.ensure_db()
				# base.config['Reporter']['Results']
				if len(base.config['Reporter']['Results'])>0:
					self.open_results_db(base.config['Reporter']['Results'])
				else:
					base.run_dbthread = False

			if self.datadb is not None:

				# process db queues

				# General Write
				if len(base.dbqueue["Write"])>0:
					base.debugmsg(9, "run_db_thread: dbqueue: Write")
					tmpq = list(base.dbqueue["Write"])
					base.dbqueue["Write"] = []
					base.debugmsg(9, "run_db_thread: dbqueue: Write: tmpq:", tmpq)
					for item in tmpq:
						if item["SQL"] and item["VALUES"]:
							try:
								base.debugmsg(9, "run_db_thread: dbqueue: Write: SQL:", item["SQL"], " 	VALUES:", item["VALUES"])
								cur = self.datadb.cursor()
								cur.execute(item["SQL"], item["VALUES"])
								cur.close()
								self.datadb.commit()
							except Exception as e:
								base.debugmsg(1, "run_db_thread: dbqueue: Write: Exception:", e)
								base.debugmsg(1, "run_db_thread: dbqueue: Write: Item:", item)
						else:
							base.debugmsg(1, "run_db_thread: dbqueue: Write: Item not written, missing key SQL or VALUES")
							base.debugmsg(1, "run_db_thread: dbqueue: Write: Item:", item)

				# General Read
				if len(base.dbqueue["Read"])>0:
					base.debugmsg(7, "run_db_thread: dbqueue: Read")
					tmpq = list(base.dbqueue["Read"])
					base.dbqueue["Read"] = []
					base.debugmsg(7, "run_db_thread: dbqueue: Read: tmpq:", tmpq)
					for item in tmpq:
						if "SQL" in item: # and item["VALUES"]:
							try:
								base.debugmsg(7, "run_db_thread: dbqueue: Read: SQL:", item["SQL"])
								self.datadb.row_factory = self.dict_factory
								cur = self.datadb.cursor()
								cur.execute(item["SQL"])
								result = cur.fetchall()
								base.debugmsg(7, "run_db_thread: dbqueue: Read: result:", result)
								cur.close()
								self.datadb.commit()

								base.debugmsg(7, "run_db_thread: dbqueue: Read: result:", result)
								if "KEY" in item:
									base.dbqueue["ReadResult"][item["KEY"]] = result

							except Exception as e:
								base.debugmsg(1, "run_db_thread: dbqueue: Read: Exception:", e)
								base.debugmsg(1, "run_db_thread: dbqueue: Read: Item:", item)
						else:
							base.debugmsg(1, "run_db_thread: dbqueue: Read: Item not written, missing key SQL or VALUES")
							base.debugmsg(1, "run_db_thread: dbqueue: Read: Item:", item)



			time.sleep(0.1)
			# end of while base.run_dbthread

		if self.datadb is not None:
			# self.datadb.close()
			# self.datadb = None
			self.close_results_db()

	def dict_factory(self, cursor, row):
		d = {}
		for idx, col in enumerate(cursor.description):
			d[col[0]] = row[idx]
		return d

	def start_db(self):
		base.run_dbthread = True
		base.dbthread = threading.Thread(target=base.run_db_thread)
		base.dbthread.start()

	def stop_db(self):
		base.run_dbthread = False
		base.dbthread.join()
		base.dbthread = None


class ReporterCore:


	def __init__(self, master=None):
		base.debugmsg(0, "Robot Framework Swarm: Reporter")
		base.debugmsg(0, "	Version", base.version)
		signal.signal(signal.SIGINT, self.on_closing)

		base.debugmsg(9, "ArgumentParser")
		# Check for command line args
		parser = argparse.ArgumentParser()
		parser.add_argument('-g', '--debug', help='Set debug level, default level is 0')
		parser.add_argument('-v', '--version', help='Display the version and exit', action='store_true')
		parser.add_argument('-i', '--ini', help='path to alternate ini file') # nargs='?',
		parser.add_argument('-n', '--nogui', help='Don\'t display the GUI', action='store_true')
		parser.add_argument('-d', '--dir', help='Results directory')
		parser.add_argument('-t', '--template', help='Specify the template')
		base.args = parser.parse_args()


		base.debugmsg(6, "base.args: ", base.args)

		if base.args.debug:
			base.debuglvl = int(base.args.debug)

		if base.args.version:
			exit()


		base.debugmsg(6, "ConfigParser")
		base.config = configparser.ConfigParser()

		#
		# 	ensure ini file
		#
		base.reporter_ini = base.findiniloctaion()

		if base.args.ini:
			base.save_ini = False
			base.debugmsg(5, "base.args.ini: ", base.args.ini)
			base.reporter_ini = base.args.ini

		if os.path.isfile(base.reporter_ini):
			base.debugmsg(7, "reporter_ini: ", base.reporter_ini)
			base.config.read(base.reporter_ini)
		else:
			base.saveini()

		base.debugmsg(0, "	Configuration File: ", base.reporter_ini)

		base.debugmsg(9, "base.config: ", base.config._sections)

		#
		# GUI
		#
		if 'GUI' not in base.config:
			base.config['GUI'] = {}
			base.saveini()

		if 'win_width' not in base.config['GUI']:
			base.config['GUI']['win_width'] = "800"
			base.saveini()

		if 'win_height' not in base.config['GUI']:
			base.config['GUI']['win_height'] = "390"
			base.saveini()

		#
		# Reporter
		#

		if 'Reporter' not in base.config:
			base.config['Reporter'] = {}
			base.saveini()

		if 'ResultDir' not in base.config['Reporter']:
			base.config['Reporter']['ResultDir'] = base.dir_path
			base.saveini()

		if 'Results' not in base.config['Reporter']:
			base.config['Reporter']['Results'] = ""
			base.saveini()

		if 'Template' not in base.config['Reporter']:
			base.config['Reporter']['Template'] = ""
			base.saveini()

		if 'TemplateDir' not in base.config['Reporter']:
			base.config['Reporter']['TemplateDir'] = ""
			base.saveini()

		self.selectResults(base.config['Reporter']['Results'])

		base.template_open(base.config['Reporter']['Template'])


		if base.displaygui:
			base.gui = ReporterGUI()

	def mainloop(self):

		base.debugmsg(5, "mainloop start")

		if base.displaygui:
			base.gui.mainloop()

		# while base.running:
		# 	time.sleep(300)


	def on_closing(self, _event=None, *extras):
		base.running = False
		base.debugmsg(5, "base.running:", base.running)

		base.debugmsg(5, "Close results db")
		# base.close_results_db()
		base.stop_db()

		base.debugmsg(2, "Exit")
		try:
			sys.exit(0)
		except SystemExit:
			try:
				os._exit(0)
			except:
				pass


	def selectResults(self, resultsfile):
		pass
		base.debugmsg(5, "resultsfile:", resultsfile)

		if len(resultsfile)>0:
			base.config['Reporter']['Results'] = resultsfile
			filedir = os.path.dirname(resultsfile)
			base.debugmsg(9, "filedir:", filedir)
			parent = os.path.dirname(filedir)
			base.debugmsg(9, "parent:", parent)
			base.config['Reporter']['ResultDir'] = parent
			base.saveini()
			# base.open_results_db(base.config['Reporter']['Results'])
			base.start_db()



class ReporterGUI(tk.Frame):

	style_text_colour = "#000"
	imgdata = {}
	b64 = {}

	titleprefix = "rfswarm Reporter"


	def __init__(self, master=None):

		self.root = tk.Tk()
		self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
		tk.Frame.__init__(self, self.root)
		self.grid(sticky="news", ipadx=0, pady=0)
		self.root.columnconfigure(0, weight=1)
		self.root.rowconfigure(0, weight=1)

		self.root.geometry(base.config['GUI']['win_width'] + "x" + base.config['GUI']['win_height'])

		self.root.resizable(True, True)

		base.debugmsg(6, "updateTitle")
		self.updateTitle()

		base.debugmsg(5, "self.root", self.root)
		base.debugmsg(5, "self.root[background]", self.root["background"])
		self.rootBackground = self.root["background"]

		self.load_icons()


		base.debugmsg(5, "BuildUI")
		self.BuildUI()
		self.BuildMenu()


	def load_icons(self):
		#	"New Report Template"	page_add.png
		self.imgdata["New Report Template"] = self.get_icon("page_add.gif")
		# 	"Open Report Template"	folder_page.png
		self.imgdata["Open Report Template"] = self.get_icon("folder_page.gif")
		# 	"Save Report Template"	page_save.png
		self.imgdata["Save Report Template"] = self.get_icon("page_save.gif")
		# 	"Open Scenario Results"	folder_table.png
		self.imgdata["Open Scenario Results"] = self.get_icon("folder_table.gif")
		# 	"Apply Report Template"	page_go.png
		self.imgdata["Apply Report Template"] = self.get_icon("page_go.gif")

		# "New Section"	add.gif
		self.imgdata["New Section"] = self.get_icon("add.gif")
		# Remove Section	 delete.gif
		self.imgdata["Remove Section"] = self.get_icon("delete.gif")
		# Move Section Up	 resultset_up.gif
		self.imgdata["Section Up"] = self.get_icon("resultset_up.gif")
		# Move Section Down	 resultset_down.gif
		self.imgdata["Section Down"] = self.get_icon("resultset_down.gif")



	def get_icon(self, imagefile):
		if len(self.b64) < 1:
			self.load_b64()

		# files["New"] = "famfamfam_silk_icons/icons/page_white.edt.gif"

		if imagefile not in self.b64:
			base.debugmsg(6, "imagefile:", imagefile)
			scrdir = os.path.dirname(__file__)
			base.debugmsg(6, "scrdir:", scrdir)
			imgfile = os.path.join(scrdir, "../famfamfam_silk_icons/icons", imagefile)
			base.debugmsg(6, "imgfile:", imgfile)
			if os.path.isfile(imgfile):
				base.debugmsg(0, "isfile: imgfile:", imgfile)
				with open(imgfile,"rb") as f:
					img_raw = f.read()
				base.debugmsg(0, "img_raw", imagefile, ":", img_raw)
				# b64 = base64.encodestring(img_raw)
				# img_text = 'img_b64 = \\\n"""{}"""'.format(b64)

				self.b64[imagefile] = img_raw  # tk.PhotoImage(file=imgfile)
				# base.debugmsg(0, "self.b64[",imagefile,"]:", self.imgdata[icontext])

			else:
				base.debugmsg(6, "File not found imgfile:", imgfile)

		if imagefile in self.b64:
			return tk.PhotoImage(data=self.b64[imagefile])
		else:
			base.debugmsg(6, "File not found imagefile:", imagefile)


	def load_b64(self):

		# gif's
		self.b64["page_add.gif"] =  b'GIF87a\x10\x00\x10\x00\xe6\x00\x00\x00\x00\x00+U\xaa*d\xbb.ga1h>.i\xbe0i\xba3j\x124l\x1aIm\xb64q\xc18v\xc3?y\xbe;z\xc4AzzJ{,B~\xc3?\x80\xc7D\x83\xc6F\x88\xc7\\\x88HI\x89\xc7M\x8c\xc9Q\x8c"c\x8cKU\x8f(d\x93\xdcs\x99_\x81\xac`\x8e\xae\x86}\xb2\xe3R\xb4\xf8R\xb5\xf7\x84\xb7\xe3\x9c\xb9\xa7\x87\xbb_\x8d\xbcd\x8f\xbci\xa0\xbd\xaec\xbf\xfcg\xc0\xfdm\xc3\xfd\xb3\xd4\x94\xb5\xd4\xf2\xb7\xd5\x9d\x97\xd7\xff\x9c\xd7\xff\xbb\xd7\xf5\x9c\xd8\xff\xa1\xd9\xff\xb5\xd9\xf6\xbd\xda\xf6\xc3\xdd\xf8\xc7\xe0\xfa\xcb\xe3\xfb\xd1\xe6\xbb\xd4\xe6\xfd\xd8\xe6\xf2\xd8\xe7\xfe\xd7\xe8\xfe\xd9\xe8\xfe\xde\xea\xf6\xe1\xeb\xf6\xe9\xef\xf5\xe6\xf0\xf7\xec\xf2\xf7\xec\xf3\xf9\xf1\xf5\xf9\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\t\x00\x00E\x00,\x00\x00\x00\x00\x10\x00\x10\x00\x00\x07\xb9\x80E\x10\x16\x84\x85\x84\x15\x0bE\x8a\x8a\x12AB\x8f\x90A9\x1e\x1a\x8bE\x15C6\x9a654/D2\x94\x8b\x98\x9b\x9a\x9eD\x9a!\x0c\x8a\x988\xae\xa63>AC?\x10\xacC\xae\xaf6\x9e++C\x12\xacB:\xb98\xb03B\xc0E\x13B<\xcd\xb9\xa64\xc8\x8cB;<\xc4\xc5\x9cB\x11\xd3\xd7\xae&\x1b\x18\x18\x0e\x8a\x11B\xdd"\x1c*7%\x19\x07E\r@\x1f  \x1f\xf2\x14**D$$\xee\r>)1`\xb8\x80\xd1\xe2\x01\x0b"\x08U\xb8S\xe0\x03\xc5\x89\x87\x0f\x11\x90\x18Ad\x04\xbf"\x05\x84\xf8\xe8\xc1\xb1\x87\x90\x0e\x17H\xa8 q\xc1\x9d\x01\x01(S\xa2\x1c\x80\xe0\x00\x02\x02E\x02\x01\x00;'

		self.b64["folder_page.gif"] =  b"GIF87a\x10\x00\x10\x00\xe6\x00\x00\x00\x00\x00@j\xaa9q\xaaAu\xc6C{\xc3Q\x7f\xcbS\x84\xccS\x84\xd0\xd9\x86'\xd9\x87(\xd9\x89)\xdb\x941^\x97\xcd\xdb\x9b2l\x9f\xd1k\xa1\xd2\xdb\xa53\xe1\xa6K\xe3\xabS\xdb\xac2\xdb\xb22\xda\xb5/\x88\xbc\xea\x93\xbc\xe5\xe7\xbdp\xe9\xbdc\x97\xc0\xe6\x93\xc2\xec\xc7\xc2\x86\x9e\xc4\xea\xe3\xc4^\xd0\xc9\x8c\xeb\xca\x91\xd8\xcf\x90\xf2\xd2=\xb3\xd3\xf4\xdd\xd3\x93\xf3\xd5r\xf3\xd6L\xe4\xd8\x93\xf3\xd8z\xbd\xd9\xf7\xd7\xd9\xca\xf4\xda\\\xf4\xdb\x83\xe9\xdc\x93\xf5\xdcf\xf6\xddk\xc4\xde\xfa\xf5\xde\x8c\xf5\xde\x93\xf6\xdft\xf6\xe1\x94\xf7\xe1}\xcc\xe2\xfc\xf6\xe2\xad\xc5\xe3\xfa\xf5\xe3\xa0\xf7\xe3\x84\xf6\xe5\x9c\xf8\xe5\x8c\xf8\xe5\x93\xd4\xe6\xfd\xd8\xe7\xff\xdb\xe9\xff\xde\xe9\xf5\xf8\xea\xc3\xe5\xef\xfa\xe7\xf2\xfc\xe8\xf2\xef\xf9\xf2\xdc\xfb\xf2\xcc\xeb\xf4\xfc\xfb\xf6\xe8\xf1\xf7\xff\xf3\xf9\xfd\xfe\xfa\xef\xfe\xfc\xf4\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\t\x00\x00O\x00,\x00\x00\x00\x00\x10\x00\x10\x00\x00\x07\xbe\x80O\x82\x83\x1d\x1a\x17\x17\x0f\x0e\x0c\x04\x83\x8dO\x17NH\x92CD\x16\x07\x8e\x82\x17H060#K8\x1b\x8c\x8e\x17J6\xa7)AHK\x06\x98\xa5>>\x9d)#C\x06\x15\x1e\xb8\xb8\xaf\xb0\xb2D\x06\x14N\xc1\xc1\xbb\xbc0H\xbfM<297\x06J@\xd0?\xb1J\x06\x13M22\x19\x0b\xdb\xdc\xdc\xc7\x13I\x18\x12\x11 H\xc2\xc2\x0bE\x06\x10\xc1M\xee;\xf0\xf09F\x0b\xc7\x10M=\xf9=-'$!\x1f\x1cT,\x18P\xa0\x01\xbe|<t\xd4\x98\xf1b\x85\x89#\x0b\x04-`\xd2\x83G\xc2\x85.\x1c\x8a\x80(H\x81\x91\x1d4h\xc4\x88\xc1\x82\x05\x8a\x12%\x84D|\x82@A\x02\x050c\xc2|\x89@P \x00;"

		self.b64["page_save.gif"] =  b'GIF87a\x10\x00\x10\x00\xe6\x00\x00\x00\x00\x00+U\xaa\x1cZ\xaf)^\xa7+d\xbb6h\xab/i\xbc0i\xba;i\xacAl\xacIm\xb6Ap\xb14q\xc18v\xc3?y\xbe;z\xc4B~\xc3U~\xbcO\x7f\xc4Q\x7f\xc2D\x83\xc6T\x83\xc5\\\x84\xc0Z\x86\xc8F\x88\xc7I\x89\xc7^\x89\xcag\x8b\xd4k\x8b\xcel\x8b\xdbM\x8c\xc9c\x8c\xcbp\x8f\xe2k\x92\xced\x93\xdcm\x98\xd5s\x9a\xd2z\x9e\xd6z\x9e\xdcw\x9f\xda{\xa2\xdc\x82\xa5\xd7\x83\xa5\xde\x81\xa8\xe3\x85\xa9\xde\x8c\xb0\xe5}\xb2\xe3R\xb4\xf8R\xb6\xf7\x92\xb6\xe6\x84\xb7\xe3\x9a\xb7\xed\x9a\xb9\xeac\xbf\xfcg\xc0\xfd\x84\xc0O\x84\xc0R\xa2\xc0\xed\x9f\xc1\xefm\xc3\xfd\xb4\xc8\xe4\x99\xcao\x9a\xcaq\xb1\xce\xf3\xbb\xcf\xef\xb5\xd4\xf2\x9c\xd7\xff\xbb\xd7\xf5\x9c\xd8\xff\xb5\xd9\xf6\xbd\xda\xf6\xc3\xdd\xf8\xc6\xe0\xf9\xcb\xe3\xfb\xd5\xe6\xfd\xd8\xe6\xf2\xd8\xe7\xfe\xd7\xe8\xfe\xd9\xe8\xfe\xde\xea\xf6\xe1\xeb\xf6\xc8\xee\x87\xc8\xee\x8c\xe9\xef\xf5\xe6\xf0\xf7\xe6\xf1\xee\xe8\xf3\xea\xec\xf3\xf5\xed\xf3\xf8\xe9\xf4\xe5\xd8\xf5\xa3\xf1\xf5\xf9\xf4\xfa\xff\xff\xff\xde\xff\xff\xe1\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\t\x00\x00`\x00,\x00\x00\x00\x00\x10\x00\x10\x00\x00\x07\xcd\x80\x10\x1e\x83\x84\x1e\x19\r`\x89\x8a\x14WX\x8e\x8eWK."\x8a\x89\x19[I\x99HGC_E\x93\x95\x97\x99\x99\x9c_\x992\x0e\x8a\x97JJ\xa4FPW[S\x10\xaa[\xac\xadI\x9cAA[\x14\xaaXL\xb7#%$)\x1f!$$\x1f`\x18XNN\xac\x1f?_<_\xd6_9\x1a\x14XM\xb7\x17:_!\xd6\\\\-\x1f\xdb\xb7J\x1a9\xd7\xd7,\x13\x0fT/0//\x1f4(*(\xfb(&\x16\x0fPv\x10\x11B\xe4C\x8c\x15+\xf8\x9d \x11\x81\x01\x14\x1b5"V\x98q\xa5\x8a\xc5*WJ,0\x80\x05\xca\x93\x8f\x12fX\xb9\xd1\xc3\x07\x8e,&\n\x1c \xc0\x92e\x05 ]\xa2h\xd1"\xc5\x8b\n\x04\x95\x12\x19\xa8\xb0\x01D\x87\x9f\x1c\x12\x0c\x08\x04\x00;'

		self.b64["folder_table.gif"] =  b'GIF87a\x10\x00\x10\x00\xe6\x00\x00\x00\x00\x00@w\xbcR\x85\xc5\xda\x86\'\xd9\x87(\xd9\x89)W\x8a\xc9\\\x8a\xc6^\x8f\xccc\x93\xcf\xdb\x941l\x9a\xd4\xdb\x9b2t\xa1\xd8|\xa5\xdc\xdb\xa53\xe2\xa9O\x80\xaa\xde\x98\xaa\xc1\xdb\xac2\x84\xad\xe1\xe0\xae`\xe4\xafZ\xdb\xb22\x8c\xb3\xe4\xda\xb5/\x94\xb8\xe7\xb3\xb9\x92\x9c\xbd\xea\xb6\xbd\x9c|\xbfv\x9f\xc0\xec\xe5\xc2\x91\x82\xc3|\xa6\xc3\xeb\xbe\xc4\xa5\xe3\xc4_\xc1\xc6\xa7\xea\xc6~\x89\xc7\x82\xac\xc7\xe9\xad\xc8\xe8\xb3\xcb\xe8\xc6\xcb\xae\x93\xcc\x8b\xb8\xcc\xe2\xf0\xcc \xf1\xce)\xf1\xd1j\xf2\xd15\xf1\xd3r\xf3\xd4D\xa4\xd5\x9b\xf2\xd5|\xf2\xd6\x81\xf3\xd7R\xf3\xd8\x86\xf4\xd8T\xf3\xd9\x8e\xf5\xdba\xd2\xdc\xdf\xf4\xdc\x9f\xf4\xde\x94\xf4\xde\xa8\xf6\xden\xf6\xdfr\xf5\xe1\xa0\xf7\xe1z\xf7\xe2\x82\xdb\xe5\xf1\xf8\xe5\x8c\xf8\xe6\x94\xf9\xe9\xa4\xf8\xea\xc3\xed\xeb\xe5\xfa\xec\xad\xfa\xed\xb4\xf3\xef\xe7\xfb\xef\xba\xfa\xf0\xdd\xeb\xf1\xf7\xfc\xf2\xca\xef\xf3\xf8\xf7\xf6\xed\xfb\xf6\xe8\xf4\xf7\xfb\xfd\xf8\xe7\xfe\xfa\xec\xfe\xfc\xf5\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\t\x00\x00Z\x00,\x00\x00\x00\x00\x10\x00\x10\x00\x00\x07\xc6\x80Z\x82\x82"\x85\x1c\x1a\x18\x18\x14\x11\x0e\x0e\x83\x84U\x91\x92\x92\r\x8fZ\x1fU44,\'!!\x1eU\x0b\x96\x1cUY\xa6\xa7Y\xa1\xa3U\x85\xad\x85U\t\x19$\xb3$\x1a\xacY)\xa8P\x08\x17\xa8\x18U(())*\xc5E\x06\x17XF>B\xbf\xb9\xb9\xa7E\x02\x13X>>6\x12 \n\xdb\xdc\n\xd2\x13T&\x16\x10\x15SSMJ\xe9R\xde\x07\x0f\xa6XX<+%#\x1d\x1d\x1b-\n\x02\x01\x0fXQNK\x8c\x18!2\x04\xc8\x8e\x1cV\x14\x08b\x80\x85\t\x92#D\x08\x1a\xbc1\xe3\x8aB-\n\xae<$\x12\xe4\xe0\x8c\x18/\\D\xb9X\xe0\xc9\x8f\x1e>t\xe0\xa8QC\x06\x0c\x18I\n\x08\x1aP\x80@\x81\x9b8o\xda\x1c (\x10\x00;'

		self.b64["page_go.gif"] = b'GIF87a\x10\x00\x10\x00\xe6\x00\x00\x00\x00\x00+U\xaa$_\xb8)b\xb7\'d\xb4*d\xbb.i\xbe0i\xbaIm\xb6\x1cq\x004q\xc18v\xc3?y\xbe\x1dz\x16\x17{\x02\x1b{\x0b;{\xc4B~\xc3\x1f\x7f\x00?\x80\xc7D\x83\xc61\x87\x08F\x88\xc7I\x89\xc77\x8b\r6\x8c\x10M\x8c\xc9@\x8f\x11F\x91\x15d\x93\xdcC\x94)H\x94.O\x98\x1dU\x99"Z\x9c#b\x9f.]\xa06c\xa0,[\xa18^\xa2@k\xa44d\xa5Dm\xa6<r\xa9Ct\xacM|\xb0S}\xb2\xe3\x81\xb4YS\xb5\xf8S\xb6\xf7\x82\xb6d\x84\xb7\xe3\x85\xb7i\x8c\xbam\x90\xbdte\xbf\xfcg\xc0\xfd\x97\xc2\x80m\xc3\xfd\x99\xc3\x83\x9f\xc6\x88\xa2\xc7\x8a\xa4\xc9\x8c\xac\xcd\x92\xb1\xcf\x97\xb5\xd4\xf2\xbb\xd7\xf5\x9f\xd8\xff\xa1\xd9\xff\xb5\xd9\xf6\xbd\xda\xf6\xc3\xdd\xf8\xc6\xe0\xf9\xcc\xe3\xfb\xd4\xe6\xfd\xd8\xe6\xf2\xd8\xe7\xfe\xd7\xe8\xfe\xd9\xe8\xfe\xde\xea\xf6\xe1\xeb\xf6\xe9\xef\xf5\xe6\xf0\xf7\xec\xf2\xf7\xec\xf3\xf9\xf1\xf5\xf9\x00\xff\x00\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\t\x00\x00X\x00,\x00\x00\x00\x00\x10\x00\x10\x00\x00\x07\xc5\x80X\x11\x1a\x84\x85\x84\x17\x0bX\x8a\x8a\x14ST\x8f\x90SK.\x1d\x8bX\x17UI\x9aIHGBWE\x94\x8b\x98\x9b\x9a\x9eW\x9a3\x0c\x8a\x98J\xae\xa6FPSUQ\x11\xacU\xae\xafI\x9eAAU\x14\xacTL\xb9J\xb0FT\xc0X\x16TN\xcd\xb9I+%G\xc8\x8cTMN\xc4J*/!T\x13\xd5\xb9*((#-?,\x1c\x10\x8a\x13T\xb9(@?\xf16>)\x15\x8a\x10R011%?552\x02\xee0!\x01\x0b\x04(:\x88\x0c\x11\xf1\xc3G\x0f\x1e4v\xa4h\xa0H\x01\x14\x1c7n\x80\xe0\xb0\x01\x03\x89\x1c)<\x10Pd\x80\n\x94\'(\x9f<\xcap\xe2\xc3\x15\x01\x8a\x0e\x14\x98Is\xe6\x03\x07\x05\x06\x0c\xc0\x12\x08\x00;'

		self.b64["add.gif"] = b'GIF87a\x10\x00\x10\x00\xe6\x00\x00\x00\x00\x00,|\x1d+~"&\x80\x1e/\x81)0\x81\'3\x83)8\x87.=\x8a2A\x8e5E\x8f9K\x92?Q\x95CN\x9a>U\x9bE]\x9dLb\xa0Me\xa2Ri\xa5Zh\xa6Vj\xabVl\xab[f\xacRu\xacat\xad_z\xb2d~\xb3h\x83\xb5kn\xb6V\x88\xb8op\xb9W\x87\xbaqt\xbb\\}\xbbk\x8a\xbcr}\xbde\x8b\xbfzp\xc2by\xc2c\x8d\xc3{|\xc4i\x92\xc6\x80~\xc8o\x89\xc9\x7f\x86\xcbz\x99\xcc\x86\x81\xcdu\x8d\xcd\x83\x99\xcd\x8a\x93\xce\x88\xa5\xcf\x94\x8a\xd0}\xa7\xd1\x97\x8e\xd3\x83\x99\xd4\x8b\x96\xd5\x8a\xac\xd5\x9e\x9e\xd9\x92\xa1\xda\x97\xb5\xda\xa6\xb8\xdb\xab\xa6\xdc\x9c\xb5\xdd\xaa\xbb\xde\xb0\xb0\xe0\xa7\xb6\xe0\xad\xbc\xe3\xb5\xcc\xe6\xc4\xc6\xe8\xc1\xcf\xe9\xca\xd5\xeb\xd0\xd8\xee\xd3\xdd\xf1\xd9\xe1\xf2\xdd\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\t\x00\x00K\x00,\x00\x00\x00\x00\x10\x00\x10\x00\x00\x07\xb1\x80K\x82\x83\x84\x85\x86"\x1b\x1b\x19\x17\x17\x86\x82"\x1f2CFE?!\x13\x11\x85\x90?IB=:@D\'\x0f\x0f\x84\x1f<H91/775B!\x0e\x83\x1d-G:7+JJ,(*A\x0e\x0b\x82\x1b>@/,!\xba\x15  6)\n\x82\x1aB6,\xba\xd5J\x1e(8\x08\x82\x19>3.\xd6\xba\x1e#\xda\x82\x1807(%\x16\xe2\x1e -$\x06\x82\x15\x16>&\xcb\xe2\x1c ;\t\xf2\x82\x11!|,\xf3\xc0A\xdf\x8e\n\xfe\x04Ax\xd0\xad\xc5\x88\x11-vP( \xa0\x90\x03\x06\rN\xd0\xa0A\x02\x01EGK\x14$@p\xc0\x00\x01\x90(\t\x05\x02\x00;'

		self.b64["delete.gif"] =  b'GIF87a\x10\x00\x10\x00\xe6\x00\x00\x00\x00\x00\xb9F$\xb5G"\xb9I&\xb5J\x1e\xbcK+\xc2K.\xd1M;\xbfN2\xc5N3\xcdP8\xbfR4\xc1R6\xc2S=\xc5TB\xdcTI\xe6UL\xcaVD\xceVJ\xe9WK\xce[L\xe7[T\xea[N\xd8\\O\xd5^T\xec^R\xd1aS\xdac]\xddcb\xf0cT\xd6d\\\xe1d[\xead[\xeeeP\xe3gg\xddie\xeei]\xe1jj\xe3kb\xe3pe\xf3s\\\xf2wb\xf3yb\xe4zs\xe9{s\xe9\x7fx\xf6\x82g\xf0\x83{\xed\x84}\xf6\x84k\xf0\x85p\xf8\x86p\xee\x8au\xee\x8c\x81\xf0\x8cw\xf8\x8cv\xf1\x8ez\xf4\x8e\x81\xee\x92\x8f\xf5\x92~\xf9\x93\x7f\xfa\x9b\x87\xf1\x9e\x97\xfa\x9e\x8b\xf4\xa2\x9f\xfa\xa4\x91\xf5\xa6\xa1\xf5\xab\xa3\xfb\xab\x9e\xf2\xae\xab\xf5\xb0\xa6\xf8\xb0\xa5\xf4\xb5\xab\xf8\xb7\xa9\xf9\xba\xb0\xfa\xbb\xaf\xf8\xc4\xbf\xfc\xc8\xbb\xf9\xcc\xc5\xfb\xd5\xce\xfd\xdc\xd5\xfd\xdd\xd9\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\t\x00\x00S\x00,\x00\x00\x00\x00\x10\x00\x10\x00\x00\x07\xaf\x80S\x82\x83\x84\x85\x86%#\x1c\x1b\x1b\x1e\x86\x82%%:LONH\'\x18\x14\x85\x90EQKA?DM,\x14\x11\x84%CP=;8<<7I&\xa5\x82"0O?;41\xba1*G\x07\r\x82&FD6\x19\xc6\xc7)9-\x0c\x82#J<2R\xd2\xd3\x13$>\x08\x82\x1bC3.\xd3\xd4 >\x05\xd95;(\x13\xe7\xe8\x16/+\xe2S\x18\x0fC\x1d!\xe8\x13\x10\x15B\t\x03\x83\x1a&C\x19\x16\xf5 @\x00\x82!\x00!\t\x11>\x08\x81\x01\xa2\x02\x0c \x17\x06\x08(\x14\xc1\x81\x02\x16:t\xac0 \xd1\xd1\x94\x04\x0b\x10\x14(\xa0\xcf\xa3\xc9A\x81\x00\x00;'

		self.b64["resultset_up.gif"] =  b'GIF89a\x10\x00\x10\x00\xa5\x00\x00\x00\x00\x00\x14A\xb7\x15E\xb9\x16J\xbd\x16N\xc0\x17P\xbd\x18S\xc0\x19Y\xc5\x1ab\xc6\x1ab\xc9#n\xcd,r\xcd<s\xce5w\xd2=w\xd0?z\xd0C\x7f\xd3E\x84\xd6K\x88\xd6S\x8e\xdba\x96\xddb\x97\xe1n\xa0\xe2t\xa2\xdfu\xa3\xe1y\xa7\xe3}\xa9\xe1}\xa9\xe8\x80\xab\xe9\x82\xac\xe3\x87\xb0\xe8\x8a\xb1\xe4\x90\xb5\xe7\x92\xb7\xe8\x99\xbb\xea\xa2\xc2\xed\xa8\xc7\xee\xad\xc8\xef\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x01\n\x00?\x00,\x00\x00\x00\x00\x10\x00\x10\x00\x00\x06G\xc0\x9fpH,\x1a\x8f\xc8\xa4r\xc9L"\x0e\xcd\x85\x04bXF(\x9f\xce\xa3\x90\xa4`D\x1d\x8c\xc618b<\xa3P\xf8\x92a\x08\x8a\x9bM\x894\x12\x81:\x9a\x0b#@\xe4p2\x16\x15\x13\x11\r\n\t\x07\x04M\x8a\x8b\x8cHA\x00;'

		self.b64["resultset_down.gif"] =  b'GIF89a\x10\x00\x10\x00\xa5\x00\x00\x00\x00\x00\x14A\xb7\x15E\xb9\x16J\xbd\x16N\xc0\x17P\xbd\x18S\xc0\x19Y\xc5\x1ab\xc6\x1ab\xc9#n\xcd,r\xcd<s\xce5w\xd2=w\xd0?z\xd0C\x7f\xd3E\x84\xd6K\x88\xd6S\x8e\xdba\x96\xddb\x97\xe1n\xa0\xe2t\xa2\xdfu\xa3\xe1y\xa7\xe3}\xa9\xe1}\xa9\xe8\x80\xab\xe9\x82\xac\xe3\x87\xb0\xe8\x8a\xb1\xe4\x90\xb5\xe7\x92\xb7\xe8\x99\xbb\xea\xa2\xc2\xed\xa8\xc7\xee\xad\xc8\xef\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00!\xfe\x11Created with GIMP\x00!\xf9\x04\x01\n\x00?\x00,\x00\x00\x00\x00\x10\x00\x10\x00\x00\x06G\xc0\x9fpH,\x1a\x8f\xc8\xa4rI8$\x14\x8d\xc8\xa4b\xc9p8\xc4\x00\xe3\xa2\xe9\x80D#Ri\xb3)\n\x18\x99\x0b\xa6\x13\x1ay0\xc7\x81C\xb3\x16a(\xc9\xc2\xa3\xf3\xa1D\x96\x06\x10\x12\x0bKB\x07\x08\x85\x89\x8a\x8b\x8c\x8dA\x00;'

	def updateTitle(self):
		titletext = "{} v{} - {}".format(self.titleprefix, base.version, "Please Select")
		# ['Reporter']['ResultDir']
		if 'Reporter' in base.config and 'Results' in base.config['Reporter']:
			if len(base.config['Reporter']['Results'])>0:
				path, filename= os.path.split(base.config['Reporter']['Results'])
				basepath, dirname= os.path.split(path)
				titletext = "{} v{} - {}".format(self.titleprefix, base.version, dirname)

		self.master.title(titletext)

	def updateStatus(self, newstatus):
		# newstatus = "Template: Untitled"
		self.statusmsg.set(newstatus)

	def updateResults(self):
		# self.stsResults.set(base.config['Reporter']['Results'])
		if base.config['Reporter']['Results']:
			sres = "Results: {}".format(base.config['Reporter']['Results'])
			self.stsResults.set(sres)
		else:
			sres = "Results: Please select a result file"
			self.stsResults.set(sres)

	def updateTemplate(self):
		# self.stsTemplate.set(base.config['Reporter']['Results'])
		if base.config['Reporter']['Template']:
			stem = "Template: {}".format(base.config['Reporter']['Template'])
			self.stsTemplate.set(stem)
		else:
			stem = "Template: Untitled"
			self.stsTemplate.set(stem)



	def BuildMenu(self):
		window = self.master
		self.root.option_add('*tearOff', False)
		root_menu = tk.Menu(window)

		if sys.platform.startswith('darwin'):
			appmenu = tk.Menu(root_menu, name='apple')
			root_menu.add_cascade(menu=appmenu)
			appmenu.add_command(label='About rfswarm Reporter')
			appmenu.add_separator()
			base.debugmsg(5, "appmenu:", appmenu)

		window.config(menu = root_menu)
		results_menu = tk.Menu(root_menu) # it intializes a new su menu in the root menu
		root_menu.add_cascade(label = "Results", menu = results_menu) # it creates the name of the sub menu

		accelkey = "Ctrl"
		if sys.platform.startswith('darwin'):
			accelkey = "Command"

		results_menu.add_command(label = "Open", command = self.mnu_results_Open, accelerator="{}-o".format(accelkey))
		window.bind('o', self.mnu_results_Open)
		results_menu.add_separator() # it adds a line after the 'Open files' option

		if sys.platform.startswith('darwin'):
			# https://tkdocs.com/tutorial/menus.html
			# root.createcommand('tk::mac::ShowPreferences', showMyPreferencesDialog)
			self.root.createcommand('tk::mac::Quit', self.on_closing)
		else:
			results_menu.add_command(label = "Exit", command = self.on_closing, accelerator="{}-x".format(accelkey))
			window.bind('x', self.on_closing)

		self.template_menu = tk.Menu(root_menu)
		root_menu.add_cascade(label = "Template", menu = self.template_menu)

		self.template_menu.add_command(label = "New", command = self.mnu_template_New, accelerator="{}-n".format(accelkey)) # it adds a option to the sub menu 'command' parameter is used to do some action
		window.bind('n', self.mnu_template_New)
		self.template_menu.add_command(label = "Open", command = self.mnu_template_Open, accelerator="{}-t".format(accelkey))
		window.bind('o', self.mnu_template_Open)
		self.template_menu.add_command(label = "Save", command = self.mnu_template_Save, accelerator="{}-s".format(accelkey))
		window.bind('s', self.mnu_template_Save)
		self.template_menu.add_command(label = "Save As", command = self.mnu_template_SaveAs, accelerator="{}-a".format(accelkey))
		window.bind('a', self.mnu_template_SaveAs)



	def BuildUI(self):

		self.ConfigureStyle()

		self.bbar = tk.Frame(self)
		self.bbar.grid(column=0, row=0, sticky="nsew")
		self.bbar.config(bg="red")

		self.mainframe = tk.Frame(self)
		self.mainframe.grid(column=0, row=1, sticky="nsew")
		self.mainframe.config(bg="green")

		self.stsbar = tk.Frame(self)
		self.stsbar.grid(column=0, row=9, sticky="nsew")
		self.stsbar.config(bg="pink")

		# statusmsg
		self.stsTemplate = tk.StringVar()
		self.stsResults = tk.StringVar()
		self.statusmsg = tk.StringVar()

		self.ststmpl = ttk.Label(self.stsbar, textvariable=self.stsTemplate)
		self.ststmpl.grid(column=0, row=0, sticky="nsew")
		self.stsres = ttk.Label(self.stsbar, textvariable=self.stsResults)
		self.stsres.grid(column=0, row=1, sticky="nsew")
		self.stslbl = ttk.Label(self.stsbar, textvariable=self.statusmsg)
		self.stslbl.grid(column=0, row=3, sticky="nsew")

		self.stsbar.columnconfigure(0, weight=1)
		self.stsbar.rowconfigure(0, weight=1)
		self.updateStatus("")
		self.updateResults()
		self.updateTemplate()


		self.columnconfigure(0, weight=1)
		self.rowconfigure(1, weight=1)

		self.mainframe.rowconfigure(1, weight=1)


		self.sbbar = tk.Frame(self.mainframe)
		self.sbbar.grid(column=0, row=0, sticky="nsew")
		self.sbbar.config(bg="blue")

		self.sections = tk.Frame(self.mainframe, relief=tk.SUNKEN, bd=3)
		self.sections.grid(column=0, row=1, sticky="nsew")
		# self.sections.config(bg="cyan")
		self.mainframe.columnconfigure(0, weight=1)
		self.sections.columnconfigure(0, weight=1)
		self.sections.rowconfigure(0, weight=1)

		# self.btnShowHide = tk.StringVar()
		# btnShowHide = tk.Button(self.mainframe, textvariable=self.btnShowHide, command=self.sections_show_hide, width=1, padx=0, pady=0, bd=0, relief=tk.FLAT, fg=self.style_text_colour)
		# self.btnShowHide.set("<")
		# btnShowHide.grid(column=1, row=1, sticky="nsew")
		# btnShowHide.rowconfigure(1, weight=1)


		self.content = tk.Frame(self.mainframe)
		self.content.grid(column=2, row=1, columnspan=2, sticky="nsew")
		# self.content.config(bg="lightblue")

		self.mainframe.columnconfigure(2, weight=1)
		self.mainframe.columnconfigure(3, weight=1)

		self.BuildToolBar()
		self.BuildSections()



	def BuildToolBar(self):
		btnno = 0

		# Open Scenario Results
		# 	"Open Scenario Results"	folder_table.png
		icontext = "Open Scenario Results"
		bnew = ttk.Button(self.bbar, image=self.imgdata[icontext], padding='3 3 3 3', text=icontext, command=self.mnu_results_Open)
		bnew.grid(column=btnno, row=0, sticky="nsew")


		btnno += 1
		# New Report Template
		#	"New Report Template"	page_add.png
		icontext = "New Report Template"
		bnew = ttk.Button(self.bbar, image=self.imgdata[icontext], padding='3 3 3 3', text=icontext, command=self.mnu_template_New)
		bnew.grid(column=btnno, row=0, sticky="nsew")


		# Open Report Template
		# 	self.imgdata["Open Report Template"] = folder_page.png
		btnno += 1
		icontext = "Open Report Template"
		bnew = ttk.Button(self.bbar, image=self.imgdata[icontext], padding='3 3 3 3', text=icontext, command=self.mnu_template_Open)
		bnew.grid(column=btnno, row=0, sticky="nsew")

		# Save Report Template
		# 	"Save Report Template"	page_save.png
		btnno += 1
		icontext = "Save Report Template"
		bnew = ttk.Button(self.bbar, image=self.imgdata[icontext], padding='3 3 3 3', text=icontext, command=self.mnu_template_Save)
		bnew.grid(column=btnno, row=0, sticky="nsew")

		# # Apply Report Template
		# # 	"Apply Report Template"	page_go.png
		# btnno += 1
		# icontext = "Apply Report Template"
		# bnew = ttk.Button(self.bbar, image=self.imgdata[icontext], padding='3 3 3 3', text=icontext, command=self.mnu_do_nothing)
		# bnew.grid(column=btnno, row=0, sticky="nsew")

		# page_excel.png
		# page_word.png
		# page_white_acrobat.png





	def BuildSections(self):

		# self.sbbar
		btnno = 0
		# New Section
		#	"New Section"	add.gif
		icontext = "New Section"
		bnew = ttk.Button(self.sbbar, image=self.imgdata[icontext], padding='3 3 3 3', text=icontext, command=self.mnu_new_rpt_sect)
		bnew.grid(column=btnno, row=0, sticky="nsew")

		# Remove Section
		# delete.gif
		btnno += 1
		icontext = "Remove Section"
		brem = ttk.Button(self.sbbar, image=self.imgdata[icontext], padding='3 3 3 3', text=icontext, command=self.mnu_rem_rpt_sect)
		brem.grid(column=btnno, row=0, sticky="nsew")

		# Move Section Up
		# resultset_up.gif
		btnno += 1
		icontext = "Section Up"
		bup = ttk.Button(self.sbbar, image=self.imgdata[icontext], padding='3 3 3 3', text=icontext, command=self.mnu_rpt_sect_up)
		bup.grid(column=btnno, row=0, sticky="nsew")

		# Move Section Down
		# resultset_down.gif
		btnno += 1
		icontext = "Section Down"
		bdwn = ttk.Button(self.sbbar, image=self.imgdata[icontext], padding='3 3 3 3', text=icontext, command=self.mnu_rpt_sect_down)
		bdwn.grid(column=btnno, row=0, sticky="nsew")


		#	https://pythonguides.com/python-tkinter-treeview/
		self.sectionstree = ttk.Treeview(self.sections, selectmode='browse', show='tree')
		# self.sectionstree = ttk.Treeview(self.sections, selectmode='extended', show='tree')

		self.sectionstree.grid(column=0, row=0, sticky="nsew")
		# ttk.Style().configure("Treeview", background="pink")
		# ttk.Style().configure("Treeview", fieldbackground="orange")

		# vsb = ttk.Scrollbar(self.sections, orient=tk.VERTICAL,command=self.sectionstree.yview)
		vsb = ttk.Scrollbar(self.sections, orient="vertical", command=self.sectionstree.yview)
		self.sectionstree.configure(yscrollcommand=vsb.set)
		vsb.grid(column=1, row=0, sticky="nsew")

		# hsb = ttk.Scrollbar(self.sections, orient=tk.HORIZONTAL,command=self.sectionstree.xview)
		hsb = ttk.Scrollbar(self.sections, orient="horizontal", command=self.sectionstree.xview)
		self.sectionstree.configure(xscrollcommand=hsb.set)
		hsb.grid(column=0, row=1, sticky="nsew")

		# self.sectionstree.bind("<Button-1>", self.sect_click_sect)

		# if len(base.config['Reporter']['Template']) <1:
		# 	self.mnu_template_New()
		# else:
		# 	self.mnu_template_New()
		self.LoadSections("TOP")

	def LoadSections(self, ParentID):
		if ParentID == "TOP":
			items = self.sectionstree.get_children("")
			base.debugmsg(5, "items:", items)
			if len(items)>0:
				# self.sectionstree.delete(items)
				for itm in items:
					self.sectionstree.delete(itm)
			self.sectionstree.insert("", "end", ParentID, text="Report", open=True, tags=ParentID)
		else:
			items = self.sectionstree.get_children(ParentID)
			base.debugmsg(5, "items:", items)
			if len(items)>0:
				# self.sectionstree.delete(items)
				for itm in items:
					self.sectionstree.delete(itm)


		sections = base.template_get_order(ParentID)
		base.debugmsg(5, "sections:", sections)
		for sect in sections:
			self.LoadSection(ParentID, sect)
		# self.sectionstree.see("RS")

		# self.sectionstree.tag_bind("TOP", sequence=None, callback=self.sect_click_top)
		# self.sectionstree.tag_bind("Sect", sequence=None, callback=self.sect_click_sect)
		self.sectionstree.tag_bind(ParentID, callback=self.sect_click_top)
		self.sectionstree.tag_bind("Sect", callback=self.sect_click_sect)

	def LoadSection(self, ParentID, sectionID):
		sect_name = "{}".format(base.template[sectionID]["Name"])
		self.sectionstree.insert(ParentID, "end", sectionID, text=sect_name, tags="Sect")
		if "Order" in base.template[sectionID]:
			self.LoadSections(sectionID)
		# self.sectionstree.see(sectionID)

	def on_closing(self, _event=None, *extras):
		try:
			base.debugmsg(5, "close window")
			self.destroy()
		except:
			# were closing the application anyway, ignore any error
			pass
		base.debugmsg(5, "core.on_closing")
		core.on_closing()

	def ConfigureStyle(self):

		# we really only seem to need this for MacOS 11 and up for now
		# base.debugmsg(5, "sys.platform", sys.platform)
		# base.debugmsg(5, "platform.system", platform.system())
		# base.debugmsg(5, "platform.release", platform.release())
		# base.debugmsg(5, "platform.mac_ver", platform.mac_ver())

		if sys.platform.startswith('darwin'):
			release, _, machine = platform.mac_ver()
			split_ver = release.split('.')
			if int(split_ver[0]) > 10:
				# Theme settings for ttk
				style = ttk.Style()
				# https://tkdocs.com/tutorial/styles.html#usetheme

				# style.theme_use()
				# base.debugmsg(5, "style.theme_use():	", style.theme_use(), "	available:", style.theme_names())
				# style.theme_use('default')
				# https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/ttk-style-layer.html
				# base.debugmsg(5, "style.layout", style.layout)
				# # list = style.layout()
				# # base.debugmsg(5, "list", list)
				# base.debugmsg(5, "style.element_names", style.element_names)
				# list = style.element_names()
				# base.debugmsg(5, "list", list)
				# base.debugmsg(5, "style.theme_names", style.theme_names)
				# list = style.theme_names()
				# base.debugmsg(5, "list", list)


				# style.layout("rfsinput", style.layout('TEntry'))
				# style.configure("rfsinput", **style.configure('TEntry'))
				# style.map("rfsinput", **style.map('TEntry'))
				# style.map("rfsinput",
				#     fieldbackground=[(['!invalid','!disabled'], '#fff'),
				#                      (['!invalid','disabled'], '#aaa')]
				# )
				# style.map("rfsinput",
				#     fieldbackground=[(['!invalid','!disabled'], '#fff'),
				#                      (['!invalid','disabled'], '#aaa'),
				#                      (['invalid','!disabled'], '#ff4040'),
				#                      (['invalid','disabled'], '#ffc0c0')]
				# )
				# style.configure("rfs.Entry", foreground="black")
				# style.configure("rfs.Entry", foreground="systemControlTextColor")
				# style.configure("rfs.Entry", foreground=self.rootBackground)	# systemWindowBackgroundColor
				# base.debugmsg(5, "self.rootBackground", self.rootBackground)
				# style.configure("rfs.Entry", foreground=self.rootBackground)	# systemControlTextColor

				# style.configure("rfs.Entry", foreground="systemControlAccentColor")
				# style.configure("rfs.Entry", foreground="systemControlTextColor")
				# style.configure("rfs.Entry", foreground="systemDisabledControlTextColor")
				# style.configure("rfs.Entry", foreground="systemLabelColor")
				# style.configure("rfs.Entry", foreground="systemLinkColor")
				# style.configure("rfsinput", foreground="systemPlaceholderTextColor")
				# style.configure("rfs.Entry", foreground="systemSelectedTextBackgroundColor")
				# style.configure("rfs.Entry", foreground="systemSelectedTextColor")
				# style.configure("rfs.Entry", foreground="systemSeparatorColor")
				# style.configure("rfs.Entry", foreground="systemTextBackgroundColor")
				# style.configure("rfs.Entry", foreground="systemTextColor")

				# style.layout("rfsinput", style.layout('TLabel'))
				# style.configure("rfsinput", **style.configure('TLabel'))
				# style.map("rfsinput", **style.map('TLabel'))
				# style.configure("TLabel", foreground="systemPlaceholderTextColor")
				style.configure("TLabel", foreground=self.style_text_colour)
				style.configure("TEntry", foreground="systemPlaceholderTextColor")
				# style.configure("TButton", foreground="systemPlaceholderTextColor")
				style.configure("TButton", foreground=self.style_text_colour)
				# style.configure("TCombobox", foreground="systemPlaceholderTextColor")
				# style.configure("TCombobox", foreground=self.style_text_colour)
				# style.configure("TComboBox", foreground=self.style_text_colour)
				# style.configure("Combobox", foreground=self.style_text_colour)
				# style.configure("ComboBox", foreground=self.style_text_colour)
				#
				# style.configure("OptionMenu", foreground=self.style_text_colour)
				# style.configure("TOptionMenu", foreground=self.style_text_colour)
				# style.configure("Optionmenu", foreground=self.style_text_colour)
				# style.configure("TOptionmenu", foreground=self.style_text_colour)

				# style.configure("Menubutton", foreground=self.style_text_colour)
				style.configure("TMenubutton", foreground=self.style_text_colour)

				# self.rfstheme["default"] = "systemPlaceholderTextColor"
				# self.rfstheme["default"] = self.style_text_colour

				# style.configure("Canvas", foreground=self.style_text_colour)
				style.configure("Canvas", fill=self.style_text_colour)
				style.configure("Canvas", activefill=self.style_text_colour)

				# style.configure("Spinbox", foreground=self.style_text_colour)
				style.configure("TSpinbox", foreground=self.style_text_colour)

				style.configure("TRadiobutton", foreground=self.style_text_colour)

				style.configure("Treeview", foreground=self.style_text_colour)
				style.configure("Treeview", background=self.rootBackground)
				style.configure("Treeview", fieldbackground=self.rootBackground)
				# style.configure("Treeview", padding=self.rootBackground)

				# style.layout('Treeview')
				# base.debugmsg(5, "Treeview Options:	", style.layout('Treeview'))
				# base.debugmsg(5, "Treeview.field:	", style.element_options('Treeview.field'))
				# base.debugmsg(5, "Treeview.padding:	", style.element_options('Treeview.padding'))
				# base.debugmsg(5, "Treeview.treearea:	", style.element_options('Treeview.treearea'))



				base.debugmsg(5, "self.style_text_colour:	", self.style_text_colour)
				base.debugmsg(5, "self.rootBackground:		", self.rootBackground)


	def sections_show_hide(self):
		state = self.btnShowHide.get()
		base.debugmsg(5, "state:", state)
		if state == ">":
			self.btnShowHide.set("<")
			self.sections.grid(column=0, row=1, sticky="nsew")
			self.mainframe.columnconfigure(0, weight=1)

		else:
			self.btnShowHide.set(">")
			self.sections.grid_forget()
			self.mainframe.columnconfigure(0, weight=0)


	def sect_click_top(self, *args):
		selected = self.sectionstree.focus()
		base.debugmsg(5, "selected:", selected)

	def sect_click_sect(self, *args):
		selected = self.sectionstree.focus()
		base.debugmsg(5, "selected:", selected)
		base.debugmsg(5, "args:", args, args[0].x)
		xmin = 0
		xmax = 0
		bbox = self.sectionstree.bbox(selected)
		base.debugmsg(5, "bbox:", bbox)
		if bbox:
			xmin = bbox[1]
			xmax = bbox[1]+bbox[3]

		if xmin > args[0].x < xmax:
			# unfocus
			# self.sectionstree.selection_set(selected)
			# self.sectionstree.selection_toggle(selected)
			self.sectionstree.selection_remove(selected)
			self.sectionstree.focus("")
			pass

	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	#
	# menu functions
	#
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

	def mnu_do_nothing(self):
		base.debugmsg(5, "Not implimented yet.....")


	def mnu_results_Open(self, _event=None):
		base.debugmsg(9, "mnu_file_Open: _event:", _event, "	Type:", type(_event))

		if type(_event) is not type(""):
			# self.mnu_file_Close()	# ensure any previous scenario is closed and saved if required
			ResultsFile = str(tkf.askopenfilename(initialdir=base.config['Reporter']['ResultDir'], title = "Select RFSwarm Results File", filetypes = (("RFSwarm Results","*.db"),("all files","*.*"))))
		else:
			ResultsFile = _event

		base.debugmsg(5, "ResultsFile:", ResultsFile)

		# ['Reporter']['Results']
		if len(ResultsFile)>0:

			core.selectResults(ResultsFile)
			self.updateTitle()
			self.updateResults()


	def mnu_template_New(self, _event=None):
		base.debugmsg(5, "New Report Template")

		base.template_create()
		# self.reportsections = self.sectionstree.insert("", "end", "R", text="Report")

		# self.sectionstree.insert(self.reportsections, "end", "0", text="Title Page")
		# self.sectionstree.insert(self.reportsections, "end", "1", text="Executive Summary")
		# self.sectionstree.insert("", "end", "RS", text="Report Settings")
		# self.sectionstree.insert("", "end", "TC", text="Table of Contents")
		# self.sectionstree.insert("", "end", "1", text="1. Executive Summary")
		# self.new_rpt_sect("Executive Summary")
		# self.sectionstree.insert("", "end", "2", text="2. Test Result Summary")
		# self.new_rpt_sect("Test Result Summary")
		self.LoadSections("TOP")

		# sql = "SELECT * FROM Results"
		# base.debugmsg(7, "sql:", sql)
		# base.dbqueue["Read"].append({"SQL": sql, "KEY": "Results"})



		# base.debugmsg(5, "New Report Template loaded")

		self.updateTemplate()


	def mnu_template_Open(self, _event=None):
		base.debugmsg(5, "Not implimented yet.....")
		TemplateFile = str(tkf.askopenfilename(initialdir=base.config['Reporter']['TemplateDir'], title = "Select RFSwarm Reporter Template", filetypes = (("RFSwarm Reporter Template","*.template"),("all files","*.*"))))
		base.debugmsg(5, "TemplateFile:", TemplateFile)

		# ['Reporter']['Results']
		if len(TemplateFile)>0:
			base.template_open(TemplateFile)
			self.LoadSections("TOP")
			self.updateTemplate()

	def mnu_template_Save(self, _event=None):
		# base.debugmsg(5, "Not implimented yet.....")
		base.debugmsg(5, "Filename:", base.config['Reporter']['Template'])
		if len(base.config['Reporter']['Template'])>0:
			base.template_save(base.config['Reporter']['Template'])
			self.updateTemplate()
		else:
			self.mnu_template_SaveAs()

	def mnu_template_SaveAs(self, _event=None):
		base.debugmsg(5, "Prompt for filename")
		templatefile = str(tkf.asksaveasfilename(\
						initialdir=base.config['Reporter']['TemplateDir'], \
						title = "Save RFSwarm Reporter Template", \
						filetypes = (("Template","*.template"),("all files","*.*"))\
						))
		base.debugmsg(5, "templatefile", templatefile)
		base.template_save(templatefile)
		self.updateTemplate()




	def mnu_new_rpt_sect(self):
		selected = self.sectionstree.focus()
		base.debugmsg(5, "selected:", selected)
		name = tksd.askstring(title="New Section", prompt="Section Name:")
		if name is not None and len(name)>0:
			if selected is None or len(selected)<1:
				selected = "TOP"
			id = base.template_new_section(selected, name)
			self.LoadSection(selected, id)


	def mnu_rem_rpt_sect(self):
		selected = self.sectionstree.focus()
		base.debugmsg(5, "selected:", selected)
		if selected:
			base.debugmsg(5, "Removing:", base.template[selected]["Name"])
			base.template_remove_section(selected)
			parent = base.template_item_parent(selected)
			self.LoadSections(parent)


	def mnu_rpt_sect_up(self):
		selected = self.sectionstree.focus()
		base.debugmsg(5, "selected:", selected)
		if selected:
			base.debugmsg(5, "Moving", base.template[selected]["Name"], "up")
			base.template_move_section_up(selected)
			parent = base.template_item_parent(selected)
			self.LoadSections(parent)
			self.sectionstree.selection_set(selected)
			self.sectionstree.focus(selected)

	def mnu_rpt_sect_down(self):
		selected = self.sectionstree.focus()
		base.debugmsg(5, "selected:", selected)
		if selected:
			base.debugmsg(5, "Moving", base.template[selected]["Name"], "down")
			base.template_move_section_down(selected)
			parent = base.template_item_parent(selected)
			self.LoadSections(parent)
			self.sectionstree.selection_set(selected)
			self.sectionstree.focus(selected)




class RFSwarm_Reporter():

	running = True

	def __init__(self):
		while base.running:
			# time.sleep(300)
			time.sleep(1)


base = ReporterBase()

core = ReporterCore()

core.mainloop()

# r = RFSwarm_Reporter()
