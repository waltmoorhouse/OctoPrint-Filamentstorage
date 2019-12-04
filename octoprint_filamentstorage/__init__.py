# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import re
import flask
from . import Connection

EXTRUSION_EXPRESSION = ".*G[0|1] .*E[+]*([\\-0-9]+[.]*[0-9]*).*"
extrusionPattern = re.compile(EXTRUSION_EXPRESSION)


class FilamentstoragePlugin(octoprint.plugin.StartupPlugin,
							octoprint.plugin.SettingsPlugin,
							octoprint.plugin.AssetPlugin,
							octoprint.plugin.SimpleApiPlugin,
							octoprint.plugin.TemplatePlugin):

	# ~~ StartupPlugin mixin

	def on_after_startup(self):
		self._logger.info("Attempting to connect to Filament Storage Container...")
		self.conn = Connection.Connection(self)
		if self.conn.is_connected():
			self._logger.info("Connected to Filament Storage Container!")
		else:
			self._logger.error("Could not connect to Filament Storage Container!")

	# ~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return dict(
			maxT=80,
			maxH=5,
			extrusionMismatchPause=False,
			extrusionMismatchMax=25,
			humidityPause=False,
			humidityWarnPercentage=25,
			humidityPausePercentage=30,
		)

	# ~~ AssetPlugin mixin

	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/filamentstorage.js"],
			css=["css/filamentstorage.css"],
		)

	# ~~ SimpleApiPlugin mixin

	def get_api_commands(self):
		return dict(
			connect=[],
			response=["data"],
			calibrate=["id"],
			set=["name", "value"],
			tare=["id"],
			zero=["id"],
			reset=[],
		)

	def on_api_command(self, command, payload):
		try:
			data = None
			if command == "connect":
				self.conn.connect()
			if command == "reset":
				self.conn.reset_extrusion()
			elif command == "response":
				self.conn.send(payload["data"])
			elif command == "set":
				self.conn.set(payload["name"], payload["value"])
			elif command == "calibrate":
				self.conn.calibrate(payload["id"])
			elif command == "tare":
				self.conn.tare(payload["id"])
			elif command == "zero":
				self.conn.zero(payload["id"])
			response = "POST request (%s) successful" % command
			return flask.jsonify(response=response, data=data, status=200), 200
		except Exception as e:
			error = str(e)
			self._logger.info("Exception message: %s" % str(e))
			return flask.jsonify(error=error, status=500), 500

	# ~~ Gcode Processor hook

	def process_line(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
		match = extrusionPattern.match(cmd)
		if match:
			self.conn.monitor_gcode_extrusion(match.group(1))

	# ~~ SoftwareUpdate hook

	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
		# for details.
		return dict(
			filamentstorage=dict(
				displayName="Filament Storage",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="waltmoorhouse",
				repo="OctoPrint-Filamentstorage",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/waltmoorhouse/OctoPrint-Filamentstorage/archive/{target_version}.zip"
			)
		)

	def get_template_configs(self):
		return [
			dict(type="settings", custom_bindings=False),
		]


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Filament Storage"


def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = FilamentstoragePlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.comm.protocol.gcode.sent": __plugin_implementation__.process_line
	}
