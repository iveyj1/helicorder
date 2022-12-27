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
The A/D box comprises one or more A/D converter chips interfaced to an Arduino Pro Mini.  The Arduino UART port is connected to an the host computer. Any device that can accept a UART signal can receive the data.  Usually, a small board that interfaces UART to USB is the most convenient route for PC or Raspberry Pi. 

The A/D converter has a differential input, meaning that the connected device must be floating (not grounded at either terminal).  This is the usual arrangement for moving-coil seismometers and geophones, but other types of device might require hardware modifications to work.  The typical bias voltage for teach analog input pin is 1.5VDC with respect to ground with a 5k input impedance.

Shielded cables should be used between the seismometer and the A/D box.  The best arrangement is to connect the cable shield to the metal case of the A/D box and the case of the seismometer.  This provides shielding throughout the signal path.  Shielded twisted-pair wire or one pair of a shielded Cat 5 Ethernet cable can be used.  If RJ45 connectors are used, ensure that the shield path is continuous to both boxes through whatever connections are used.  A few inches of exposed wire outside the shield at either end is usually not harmful as long as there is shield continuity.

## Hardware setup
Set up the seismometer and connect the two seismometer signal wires to the analog connections of the A/D box.  Connect the A/D box UART port to the USB-UART interface.  Plug the USB-UART interface into the host computer.

# Scripts

## Overview
Three main scripts are provided along with several utility and helper scripts.  The main scripts are:

seislog.py - reads data from the USB port and logs a csv file to the local disk.  Files rotate at 0 hours UTC. Also attempts to save a file containing the USGS list of relevant earthquake parameters for quakes that happen during the recording.  Acts as a server for monitor.py. Only seislog is required in order to log data.

monitor.py - displays live data on a graph mostly for setup and debug.  This may be run locally or on a remote machine.

helicorder.py displays the content of a data file and displays a graph and spectrum info and USGS quake info.

Seislog.conf is read by seislog and/or monitor for setup purposes.  Depending on the setup, there may be two copies of this on different machines.  Needs to be edited.  For the hardware you have the sample rate is 10

There is an example launch script and crontab to automate startup and recovery.

There is also a configuration file `seislog.conf` that is used by seislog and monitor.py

# Script Setup
The seislog script nees to run continuously.  Select a user to run this script, and in the appropriate home directory, clone the git repository using the command

`git clone https://github.com/iveyj1/helicorder`

cd to the helicorder/code directory, and if needed, check out the main branch of the repo.

`git checkout main`

