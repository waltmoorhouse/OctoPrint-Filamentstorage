# coding=utf-8
from __future__ import absolute_import

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.

import octoprint.plugin
import flask
from . import Connection


class FilamentstoragePlugin(octoprint.plugin.StartupPlugin,
							octoprint.plugin.SettingsPlugin,
							octoprint.plugin.AssetPlugin,
							octoprint.plugin.SimpleApiPlugin,
							octoprint.plugin.TemplatePlugin):

	# ~~ StartupPlugin mixin

	def on_after_startup(self):
		self._logger.info("Connecting to Filament Storage Container...")
		self.conn = Connection.Connection(self)
		self._logger.info("Connected to Filament Storage Container!")

	# ~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return dict(
			maxT=80,
			maxH=5,
			warnH=15
		)

	# ~~ AssetPlugin mixin

	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/filamentstorage.js"],
			css=["css/filamentstorage.css"]
		)

	# ~~ SimpleApiPlugin mixin

	def get_api_commands(self):
		return dict(
			connect=[],
			set=["name", "value"],
			tare=["id"]
		)

	def on_api_command(self, command, payload):
		try:
			data = None
			if command == "connect":
				self.conn.connect()
			elif command == "set":
				self.conn.set(payload["name"], payload["value"])
			elif command == "tare":
				self.conn.tare(payload["id"])
			response = "POST request (%s) successful" % command
			return flask.jsonify(response=response, data=data, status=200), 200
		except Exception as e:
			error = str(e)
			self._logger.info("Exception message: %s" % str(e))
			return flask.jsonify(error=error, status=500), 500

	# ~~ SoftwareUpdate hook

	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
		# for details.
		return dict(
			filamentstorage=dict(
				displayName="Filament Storage Plugin",
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
			dict(type="navbar", custom_bindings=False),
			dict(type="settings", custom_bindings=False)
		]


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Filament Storage Plugin"


def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = FilamentstoragePlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}
