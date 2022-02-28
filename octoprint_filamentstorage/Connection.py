import os
import re
import sys
import glob
import threading
import serial
import serial.tools.list_ports

HUMIDITY_EXPRESSION = "^H:+([\\-0-9]+[.]*[0-9]*)%.*"
L1_EXPRESSION = ".*L1:+([\\-0-9]+[.]*[0-9]*)mm.*"
L2_EXPRESSION = ".*L2:+([\\-0-9]+[.]*[0-9]*)mm.*"
L3_EXPRESSION = ".*L3:+([\\-0-9]+[.]*[0-9]*)mm.*"
L4_EXPRESSION = ".*L4:+([\\-0-9]+[.]*[0-9]*)mm.*"
humidityPattern = re.compile(HUMIDITY_EXPRESSION)
l1Pattern = re.compile(L1_EXPRESSION)
l2Pattern = re.compile(L2_EXPRESSION)
l3Pattern = re.compile(L3_EXPRESSION)
l4Pattern = re.compile(L4_EXPRESSION)


class Connection():
	def __init__(self, plugin):
		self._logger = plugin._logger
		self._printer = plugin._printer
		self._printer_profile_manager = plugin._printer_profile_manager
		self._plugin_manager = plugin._plugin_manager
		self._identifier = plugin._identifier
		self._settings = plugin._settings

		self.ports = []

		self.readThread = None
		self.readThreadStop = False
		self._connected = False
		self.serialConn = None
		self.gCodeExtrusion = 0
		self.boxExtrusion = 0
		self.boxExtrusionOffset = 0
		self.connect()

	def connect(self):
		self._logger.info("Connecting...")

		self.ports = self.getAllPorts()
		self._logger.info("Potential ports: {}".format(self.ports))
		if len(self.ports) > 0:
			for port in self.ports:
				if not self._connected:
					if self.isPrinterPort(port):
						self._logger.info("Skipping Printer Port:{}".format(port))
					else:
						try:
							self.serialConn = serial.Serial(port, 115200, timeout=0.5)
							self._logger.info("Starting read thread...")
							self.startReadThread()
							self._connected = True
						except serial.SerialException:
							self.update_ui_error("Connection failed!")
			if not self._connected:
				self.update_ui_error("Couldn't connect on any port.")
		else:
			msg = "NO SERIAL PORTS FOUND!"
			self.update_ui_error(msg)

	def update_ui_control(self, data):
		self._plugin_manager.send_plugin_message(self._identifier, {"type": "control", "data": data})

	def update_ui_status(self, data):
		self._plugin_manager.send_plugin_message(self._identifier, {"type": "status", "data": data})

	def update_ui_prompt(self, prompt):
		self._plugin_manager.send_plugin_message(self._identifier, {"type": "prompt", "data": prompt})

	def update_ui_error(self, error):
		self._plugin_manager.send_plugin_message(self._identifier, {"type": "error", "data": error})

	def set(self, name, value):
		value_str = "SET " + name + "={}".format(value)
		self._logger.info(value_str)
		self.serialConn.write(value_str.encode())

	def send(self, data):
		self._logger.info("Sending: {}".format(data))
		self.serialConn.write(data.encode())

	def calibrate(self, spoolNum):
		self._logger.info("Calibrating spool: {}".format(spoolNum))
		self.serialConn.write(("CALI {}".format(spoolNum)).encode())

	def tare(self, spoolNum):
		self._logger.info("Taring spool: {}".format(spoolNum))
		self.serialConn.write(("TARE {}".format(spoolNum)).encode())

	def zero(self, spoolNum):
		self._logger.info("Zeroing spool: {}".format(spoolNum))
		self.serialConn.write(("ZERO {}".format(spoolNum)).encode())

	def reset_extrusion(self):
		self.gCodeExtrusion = 0
		self.boxExtrusionOffset = self.boxExtrusion
		self.boxExtrusion = 0

	def monitor_humidity(self, status):
		if self._settings.get(["humidityPause"]):
			match = humidityPattern.match(status)
			if match:
				if float(self._settings.get(["humidityPausePercentage"])) < float(match.group(1)):
					self._printer.pause_print()
				else:
					if not self.is_extrusion_mismatch_triggered:
						self._printer.resume_print()

	def monitor_box_extrusion(self, status):
		amount = 0
		match = l1Pattern.match(status)
		if match:
			amount += float(match.group(1))

		match = l2Pattern.match(status)
		if match:
			amount += float(match.group(1))

		match = l3Pattern.match(status)
		if match:
			amount += float(match.group(1))

		match = l4Pattern.match(status)
		if match:
			amount += float(match.group(1))

		self.boxExtrusion = (amount - self.boxExtrusionOffset)
		self._plugin_manager.send_plugin_message(self._identifier,
												 dict(type="extrusion", data="box={}".format(self.boxExtrusion)))

	def monitor_gcode_extrusion(self, amount):
		self.gCodeExtrusion += float(amount)
		if self.is_extrusion_mismatch_triggered:
			self._printer.pause_print()
			self.update_ui_error("Extrusion Mismatch detected, pausing print!")
		self._plugin_manager.send_plugin_message(
			self._identifier, dict(type="extrusion", data="gcode={}".format(self.gCodeExtrusion)))

	def is_extrusion_mismatch_triggered(self):
		return self._settings.get(["extrusionMismatchPause"]) & float(self.gCodeExtrusion) - float(
			self.boxExtrusion) > float(self._settings.get(["extrusionMismatchMax"], merged=True))

	def arduino_read_thread(self, serialConnection):
		self._logger.info("Read Thread: Starting thread")
		while self.readThreadStop is False:
			try:
				line = serialConnection.readline()
				if line:
					line = line.strip()
					if line[:5] == "ERROR":
						self.update_ui_error(line)
					elif line[:6] == "PROMPT":
						self.update_ui_prompt(line)
					elif line[:11] == "CALIBRATION":
						self.update_ui_control(line)
					else:
						self.monitor_humidity(line)
						self.monitor_box_extrusion(line)
						self.update_ui_status(line)
			except serial.SerialException:
				self._connected = False
				self._logger.error("error reading from USB")
				self.update_ui_control("disconnected")
				self.stopReadThread()
		self._logger.info("Read Thread: Thread stopped.")

	# below code "stolen" from https://gitlab.com/mosaic-mfg/palette-2-plugin/blob/master/octoprint_palette2/Omega.py
	def getAllPorts(self):
		baselist = []

		if 'win32' in sys.platform:
			# use windows com stuff
			self._logger.info("Using a windows machine")
			for port in serial.tools.list_ports.grep('.*0403:6015.*'):
				self._logger.info("got port {}".format(port.device))
				baselist.append(port.device)

		baselist = baselist + glob.glob('/dev/serial/by-id/*FTDI*') + glob.glob('/dev/*usbserial*') + glob.glob(
			'/dev/*usbmodem*') + glob.glob('/dev/*ttyUSB*')
		baselist = self.getRealPaths(baselist)
		# get unique values only
		baselist = list(set(baselist))
		return baselist

	def getRealPaths(self, ports):
		self._logger.info("Paths: {}".format(ports))
		for index, port in enumerate(ports):
			port = os.path.realpath(port)
			ports[index] = port
		return ports

	def isPrinterPort(self, selected_port):
		selected_port = os.path.realpath(selected_port)
		printer_port = self._printer.get_current_connection()[1]
		self._logger.info("Trying port: {}".format(selected_port))
		self._logger.info("Printer port: {}".format(printer_port))
		# because ports usually have a second available one (.tty or .cu)
		printer_port_alt = ""
		if printer_port is None:
			return False
		else:
			if "tty." in printer_port:
				printer_port_alt = printer_port.replace("tty.", "cu.", 1)
			elif "cu." in printer_port:
				printer_port_alt = printer_port.replace("cu.", "tty.", 1)
			self._logger.info("Printer port alt: {}".format(printer_port_alt))
			if selected_port == printer_port or selected_port == printer_port_alt:
				return True
			else:
				return False

	def startReadThread(self):
		if self.readThread is None:
			self.readThreadStop = False
			self.readThread = threading.Thread(
				target=self.arduino_read_thread,
				args=(self.serialConn,)
			)
			self.readThread.daemon = True
			self.readThread.start()

	def stopReadThread(self):
		self.readThreadStop = True
		if self.readThread and threading.current_thread() != self.readThread:
			self.readThread.join()
		self.readThread = None

	def is_connected(self):
		return self._connected
