from __future__ import absolute_import
from Sender import ControllerGeneric, GPAT, STATUSPAT, POSPAT, TLOPAT, DOLLARPAT, FEEDPAT, SPLITPAT, VARPAT
from CNC import CNC
import time

class Controller(ControllerGeneric):
	def __init__(self, master):
		self.gcode_case = 1
		self.has_override = False
		self.master = master
		#print("smoothie loaded")

	def executeCommand(self, oline, line, cmd):
		if line[0] in ( "help", "version", "mem", "ls",
				"cd", "pwd", "cat", "rm", "mv",
				"remount", "play", "progress", "abort",
				"reset", "dfu", "break", "config-get",
				"config-set", "get", "set_temp", "get",
				"get", "net", "load", "save", "upload",
				"calc_thermistor", "thermistors", "md5sum"):
			self.master.serial.write(oline+"\n")
			return True
		return False

	def hardResetPre(self):
		self.master.serial.write(b"reset\n")

	def hardResetAfter(self):
		time.sleep(6)

	def viewSettings(self):
		pass

	def viewBuild(self):
		self.master.serial.write(b"version\n")
		self.master.sendGCode("$I")

	def viewStartup(self):
		pass

	def checkGcode(self):
		pass

	def grblHelp(self):
		self.master.serial.write(b"help\n")

	def grblRestoreSettings(self):
		pass

	def grblRestoreWCS(self):
		pass

	def grblRestoreAll(self):
		pass

	def purgeController(self):
		pass

	def overrideSet(self):
		pass

	def parseBracketAngle(self, line, cline):
		# <Idle|MPos:68.9980,-49.9240,40.0000,12.3456|WPos:68.9980,-49.9240,40.0000|F:12345.12|S:1.2>
		ln= line[1:-1] # strip off < .. >

		# split fields
		l= ln.split('|')

		# strip off status
		CNC.vars["state"]= l[0]

		# strip of rest into a dict of name: [values,...,]
		d= { a: [float(y) for y in b.split(',')] for a, b in [x.split(':') for x in l[1:]] }
		CNC.vars["mx"] = float(d['MPos'][0])
		CNC.vars["my"] = float(d['MPos'][1])
		CNC.vars["mz"] = float(d['MPos'][2])
		CNC.vars["wx"] = float(d['WPos'][0])
		CNC.vars["wy"] = float(d['WPos'][1])
		CNC.vars["wz"] = float(d['WPos'][2])
		CNC.vars["wcox"] = CNC.vars["mx"] - CNC.vars["wx"]
		CNC.vars["wcoy"] = CNC.vars["my"] - CNC.vars["wy"]
		CNC.vars["wcoz"] = CNC.vars["mz"] - CNC.vars["wz"]
		if 'F' in d:
		        CNC.vars["curfeed"] = float(d['F'][0])
		self.master._posUpdate = True

		# Machine is Idle buffer is empty
		# stop waiting and go on
		if self.master.sio_wait and not cline and l[0] in ("Idle","Check"):
		        self.master.sio_wait = False
		        self.master._gcount += 1

	def parseBracketSquare(self, line):
		pat = POSPAT.match(line)
		if pat:
			if pat.group(1) == "PRB":
				CNC.vars["prbx"] = float(pat.group(2))
				CNC.vars["prby"] = float(pat.group(3))
				CNC.vars["prbz"] = float(pat.group(4))
				#if self.running:
				self.master.gcode.probe.add(
					 CNC.vars["prbx"]
					+CNC.vars["wx"]
					-CNC.vars["mx"],
					 CNC.vars["prby"]
					+CNC.vars["wy"]
					-CNC.vars["my"],
					 CNC.vars["prbz"]
					+CNC.vars["wz"]
					-CNC.vars["mz"])
				self.master._probeUpdate = True
			CNC.vars[pat.group(1)] = \
				[float(pat.group(2)),
				 float(pat.group(3)),
				 float(pat.group(4))]
		else:
			pat = TLOPAT.match(line)
			if pat:
				CNC.vars[pat.group(1)] = pat.group(2)
				self.master._probeUpdate = True
			elif DOLLARPAT.match(line):
				CNC.vars["G"] = line[1:-1].split()
				CNC.updateG()
				self.master._gUpdate = True
