# Hardware Description
A/D type: 24-bit differential input

Sample rate: 10 or 30 samples per second

Link type: UART

Signal level: 5V

Baud rate: 9600

Data type: 32-bit signed integer

Value format: Printable ASCII text in base 10 with leading negative sign

Value range: -(2<sup>31</sup>) to 2<sup>31</sup>-1 

Sample delimiter: Lines are terminated with a carriage return

Value delimeter: One value per line (single channel system) or CSV (multiple channel system)  

### Single channel example:

-2836509\<cr\>

4588328\<cr\>

...

## Hardware Notes:
The A/D box comprises one or more A/D converter chips interfaced to an Arduino Pro Mini.  The Arduino UART port is connected to the host computer. Any device that can accept a UART signal can receive the data.  Usually, a small board that interfaces UART to USB is the most convenient route for PC or Raspberry Pi. 

The A/D converter has a differential input, meaning that the connected device must be floating (not grounded at either terminal).  This is the usual arrangement for moving-coil seismometers and geophones, but other types of device might require hardware modifications to work.  The typical bias voltage for teach analog input pin is 1.5VDC with respect to ground with a 5k input impedance.

Shielded cables should be used between the seismometer and the A/D box.  The best arrangement is to connect the cable shield to the metal case of the A/D box and the case of the seismometer.  This provides shielding throughout the signal path.  Shielded twisted-pair wire or one pair of a shielded Cat 5 Ethernet cable can be used.  If RJ45 connectors are used, ensure that the shield path is continuous to both boxes through whatever connections are used.  A few inches of exposed wire outside the shield at either end is usually not harmful as long as there is shield continuity.

## Hardware setup
Set up the seismometer and connect the two seismometer signal wires to the analog connections of the A/D box.  Connect the A/D box UART port to the USB-UART interface.  Plug the USB-UART interface into the host computer.

# Scripts

## Overview
Three main scripts are provided along with several utility and helper scripts.  The main scripts are:

`seislog.py` - reads data from the USB port and logs a csv file to the local disk.  Files rotate at 0 hours UTC. Also attempts to save a file containing the USGS list of relevant earthquake parameters for quakes that happen during the recording.  Acts as a server for monitor.py. Only seislog is required in order to log data.

`monitor.py` - displays live data on a graph mostly for setup and debug.  This may be run locally or on a remote machine.

`helicorder.py` displays the content of a data file and displays a graph and spectrum info and USGS quake info.

`seislog.conf` is read by seislog and/or monitor for setup purposes.  Depending on the setup, there may be two copies of this on different machines.  This file needs to be edited .

There is also an example launch script and crontab to automate startup and recovery.

## Script Setup
The seislog script needs to run continuously.  Select a user to run this script, and in the appropriate home directory, clone the git repository using the command

`git clone https://github.com/iveyj1/helicorder`

cd to the helicorder/code directory, and if needed, pull, and check out the main branch of the repo.

`git pull`

`git checkout main`

## seislog.conf Setup

The seislog.conf file is used by both seislog.py and monitor.py.  If monitor.py is used on a remote computer, a copy of this file will need to be in both locations.  The server_port entry must match in both copies, and the server_address of the monitor.py copy of the configuration file must contain the ip address or host name of the server that runs seislog.py.

### Section [GENERAL]

### sample_rate =

This depends on the A/D hardware.  Older hardware should use `sample_rate = 10`

### com_port = 

Linux

The USB UART adapter appears in Linux as a device in `/dev/`. It will usually be an entry of the form /dev/ttyUSBx.  This path should be entered in `seislog.conf` as follows:

`com_port = /dev/ttyUSB0`

If there is only one device listed of the form /dev/ttyUSB*, this should be all that is necessary.

Notes:

If there is more than one ttyUSB device, you may need to note which ttyUSB entry appears when the USB UART adapter is first plugged in.  This can be done by running 
`ls /dev/ttyUSB*` before and after plugging in the adapter.

On some systems, the /dev/ttyUSBx path may change unexpectedly, e.g., from ttyUSB0 to ttyUSB1 on reboot or addition of another USB device.  If this happens, a workaround is to use the paths in /dev/serial/by-path instead of /dev, for example:

```
pi@meshlog-house:/dev/serial/by-path $ ll
total 0
drwxr-xr-x 2 root root 80 Dec 26 23:37 .
drwxr-xr-x 4 root root 80 Dec 26 23:37 ..
lrwxrwxrwx 1 root root 13 Dec 26 23:37 platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.2:1.0-port0 -> ../../ttyUSB0
lrwxrwxrwx 1 root root 13 Dec 26 23:37 platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.3:1.0-port0 -> ../../ttyUSB1
```

In this case instead of /dev/ttyUSB0 you would use: 

`com_port = /dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.2:1.0-port0`

If this path is used, the path will need to be updated if the USB UART adapter is moved to a different USB socket on the computer.  Note that both paths above end in 'port0' - this is not the distinguishing part of the path.


