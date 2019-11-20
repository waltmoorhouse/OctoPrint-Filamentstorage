import os
import sys
import glob
import threading
import serial
import serial.tools.list_ports


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
		self.connect()

	def connect(self):
		self._logger.info("Connecting...")

		self.ports = self.getAllPorts()
		self._logger.info("Potential ports: %s" % self.ports)
		if len(self.ports) > 0:
			for port in self.ports:
				if not self._connected:
					if self.isPrinterPort(port):
						self._logger.info("Skipping Printer Port:" + port)
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
		value_str = "SET " + name + "=%s" % value
		self._logger.info(value_str)
		self.serialConn.write(value_str.encode())

	def send(self, data):
		self._logger.info("Sending: %s" % data)
		self.serialConn.write(data.encode())

	def calibrate(self, spoolNum, mass):
		self._logger.info("Calibrating spool: %s with mass %s" % spoolNum % mass)
		self.serialConn.write(("CALI %s=%s" % spoolNum % mass).encode())

	def tare(self, spoolNum):
		self._logger.info("Taring spool: %s" % spoolNum)
		self.serialConn.write(("TARE %s" % spoolNum).encode())

	def zero(self, spoolNum):
		self._logger.info("Zeroing spool: %s" % spoolNum)
		self.serialConn.write(("ZERO %s" % spoolNum).encode())

	def arduinoReadThread(self, serialConnection):
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
				self._logger.info("got port %s" % port.device)
				baselist.append(port.device)

		baselist = baselist + glob.glob('/dev/serial/by-id/*FTDI*') + glob.glob('/dev/*usbserial*') + glob.glob('/dev/*usbmodem*')
		baselist = self.getRealPaths(baselist)
		# get unique values only
		baselist = list(set(baselist))
		return baselist

	def getRealPaths(self, ports):
		self._logger.info("Paths: %s" % ports)
		for index, port in enumerate(ports):
			port = os.path.realpath(port)
			ports[index] = port
		return ports

	def isPrinterPort(self, selected_port):
		selected_port = os.path.realpath(selected_port)
		printer_port = self._printer.get_current_connection()[1]
		self._logger.info("Trying port: %s" % selected_port)
		self._logger.info("Printer port: %s" % printer_port)
		# because ports usually have a second available one (.tty or .cu)
		printer_port_alt = ""
		if printer_port is None:
			return False
		else:
			if "tty." in printer_port:
				printer_port_alt = printer_port.replace("tty.", "cu.", 1)
			elif "cu." in printer_port:
				printer_port_alt = printer_port.replace("cu.", "tty.", 1)
			self._logger.info("Printer port alt: %s" % printer_port_alt)
			if selected_port == printer_port or selected_port == printer_port_alt:
				return True
			else:
				return False

	def startReadThread(self):
		if self.readThread is None:
			self.readThreadStop = False
			self.readThread = threading.Thread(
				target=self.arduinoReadThread,
				args=(self.serialConn,)
			)
			self.readThread.daemon = True
			self.readThread.start()

	def stopReadThread(self):
		self.readThreadStop = True
		if self.readThread and threading.current_thread() != self.readThread:
			self.readThread.join()
		self.readThread = None

