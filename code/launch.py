
import os
import subprocess

# find if a process with the given string is running
def findProcess(str):
    pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]

    for pid in pids:
        try:
            procpath = os.path.join('/proc', pid, 'cmdline')
            cmdline_f = open(procpath, 'rb')
            cmdline = cmdline_f.read()
            a = cmdline.split(b'\0')
            #print(a)
            if(str.encode(encoding="utf-8") in a):
                return(True)
        except IOError:
            continue
    return False

# main app
basepath = 'helicorder/code'

os.chdir(basepath)

command = "nohup /usr/bin/python3 seislog.py -t" + "> con_out.txt 2>&1 &"
if not findProcess("seislog.py"):
    print("launching logger: " + command) 
    os.system(command)
    touch_command = "touch " + "sl_starting"
else:
    print("not launching: " +command )
    touch_command = "touch " + "sl__running"
os.system(touch_command)    

