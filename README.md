# OctoPrint-Filamentstorage

Connects to RepBox or any [Filament Storage Box](https://github.com/waltmoorhouse/FilamentBox)
supporting the below serial communications:
1) sends periodic updates in the following format: 
    H:xx.xx% T:xx.xxC S1:x.xxkg S2:x.xxkg S3:x.xxkg S4:x.xxkg L1:x.xxmm L2:x.xxmm L3:x.xxmm L4:x.xxmm P:\[ON|OFF\]
1) accepts the following commands:
    1) SET H=xx (sets maxHumidity to xx)
    1) SET T=xx (sets maxTemperature to xx)
    1) TARE y (Tares scale y, 0<y<5)
    1) ZERO z (Zeros length z, 0<z<5)
    1) CALI y=xx (Calibrates scale y, 0<y<5, with a known weight xx)

## Setup

Install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:

    https://github.com/waltmoorhouse/OctoPrint-Filamentstorage/archive/master.zip

## Configuration

Default Max Temp: Max Temp will be set to this value on startup.  
Default Max Humidity: Max Temp will be set to this value on startup.  
Pause on Extrusion Mismatch: Pauses the print if the extrusion mismatch is greater than the below value.  
Maximum Extrusion Mismatch: If the Gcode extrusion value minus the filament box extrusion value 
is greater than this value, the print will be paused. 

Max Temp: If the temp goes above this, the dehydrator will be turned off.  
Max Humidity: If the humidity goes above this, the dehydrator will be turned on, unless currentTemp > maxTemp.

## Device Compatibility

Any USB device that operates similarly to this Open Source project:
[https://github.com/waltmoorhouse/FilamentBox](https://github.com/waltmoorhouse/FilamentBox)
    
