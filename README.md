# SuckControl
## Description
Automatic control of any fan (*which is supported by your motherboard or graphics card*) depending on any temperature sensor.  
Built on [LibreHardwareMonitorLib](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor). Check it, to see what is possible with your hardware.

## Usage
* Run `SuckControl.exe` and follow the instructions of the first time setup
  * Windows will complain about it, read [here](https://stackoverflow.com/questions/54733909/windows-defender-alert-users-from-my-pyinstaller-exe)
  * You need to (*identify and*) name all the sensors you want to use
    * Or just keep the default name
    * Don't name two sensors of the same type exactly the same
    * [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor) could help identifying
* Directly after, the setup for the first rule (*temperature curve*) starts 
  * Select a temperature sensor
  * Select a control sensor
  * Enter the first point of the curve. Temperature is Celsius, speed is in %: `<temp>,<speed>`. Like: `35,20`
    * 100 is the highest value for `<temp>` and `<speed>`
    * Repeat for every point
  * If you are done, just press enter 
* The config is now saved for the first time and you should see the menu
* Close SuckControl and run it again with the parameter `--daemon`
  * This doesn't let you configure anything, but runs in the background and sets the fan speeds according to the temperatures
  * If SuckControl isn't able to control a fan, it will say so (*like in the first time setup*)

### Important Notes
* `CTRL + C` is catched and reverts the fans to default (letting the motherboard control them again). But any other method of killing the process, does not.
  * But that's needed, since it would make only sense to run this tool from taskscheduler.
* You can make this autostart with the task scheduler of Windows.

## Building
* After cloning, `pip -r requirements.txt`
* Get `LibreHardwareMonitorLib.dll` and `HidSharp.dll` from LibreHardwareMonitor
  * You can run `ui.py` in this state
* Install PyInstaller `pip install PyInstaller`
* Run PyInstaller with: `-F --uac-admin --noupx --add-data LibreHardwareMonitorLib.dll;. --add-data HidSharp.dll;. --hidden-import pkg_resources.py2_warn suckcontrol.py`
