---
layout: plugin

id: filamentstorage  
title: OctoPrint-Filamentstorage  
description: Plugin for OpenSource Filament Storage Containers that report Temp, Humidity, and scale values over USB.  
author: Walt Moorhouse  
license: AGPLv3  
date: 2019-10-23

homepage: https://github.com/waltmoorhouse/OctoPrint-Filamentstorage  
source: https://github.com/waltmoorhouse/OctoPrint-Filamentstorage  
archive: https://github.com/waltmoorhouse/OctoPrint-Filamentstorage/archive/master.zip

tags:
- filament
- usb

screenshots:
- url: url of a screenshot, /assets/img/...
  alt: alt-text of a screenshot
  caption: caption of a screenshot
- url: url of another screenshot, /assets/img/...
  alt: alt-text of another screenshot
  caption: caption of another screenshot
- ...

# TODO
featuredimage: url of a featured image for your plugin, /assets/img/...

# TODO
# You only need the following if your plugin requires specific OctoPrint versions or
# specific operating systems to function - you can safely remove the whole
# "compatibility" block if this is not the case.

compatibility:

  # List of compatible versions
  #
  # A single version number will be interpretated as a minimum version requirement,
  # e.g. "1.3.1" will show the plugin as compatible to OctoPrint versions 1.3.1 and up.
  # More sophisticated version requirements can be modelled too by using PEP440
  # compatible version specifiers.
  #
  # You can also remove the whole "octoprint" block. Removing it will default to all
  # OctoPrint versions being supported.

  octoprint:
  - 1.2.0

  # List of compatible operating systems
  #
  # Valid values:
  #
  # - windows
  # - linux
  # - macos
  # - freebsd
  #
  # There are also two OS groups defined that get expanded on usage:
  #
  # - posix: linux, macos and freebsd
  # - nix: linux and freebsd
  #
  # You can also remove the whole "os" block. Removing it will default to all
  # operating systems being supported.

  os:
  - linux
  - windows
  - macos
  - freebsd

---

**TODO**: Longer description of your plugin, configuration examples etc. This part will be visible on the page at
http://plugins.octoprint.org/plugin/filamentstorage/
