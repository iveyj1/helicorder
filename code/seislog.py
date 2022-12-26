import time
import csv
import datetime
import serial
import json
import urllib.request 
import os
import configparser
import queue
import threading
import getconfig
import socket

class ReadData:
    def __init__(self):
        self.config = getconfig.getconfig('seislog.conf')
        self.com_port = self.config['DEFAULT']["com_port"]
        self.baud_rate = self.config['DEFAULT']["baud_rate"]
        self.out_file_base_name = self.config['DEFAULT']['out_file_base_name']
        self.out_file_name = self.out_file_base_name + time.strftime("%Y-%m-%dT%H%M", time.gmtime()) +'.csv' 
        self.server_port = self.config['DEFAULT']['server_port']
        self.get_quakes = (self.config['DEFAULT']['get_quakes'].upper() == 'TRUE')
        self.quake_url = self.config['DEFAULT']['quake_url']

        self.out_file = None
        print("opening: %s" % os.path.realpath(self.out_file_name))
        self.out_file = open(self.out_file_name, "w")

        self.ser = None
        self.ser = serial.Serial(self.com_port, self.baud_rate, timeout = 0)
        while(self.ser.read(1000) == 1000):
            pass
        self.remainder = ""
        self.queue = None
        if self.server_port != 0:
            self.socket_out_queue = queue.Queue()
            self.socket_connected_event = threading.Event()
            self.socket_thread = threading.Thread(target = socket_worker, args = (self.server_port, self.socket_out_queue, self.socket_connected_event))
            self.socket_thread.daemon = True
            self.socket_thread.start()
        self.rollover = False

    def read_data(self):
        str = self.ser.read(1000).decode("utf-8")
        # if str == '':
        #     print('early')
        # else:
        #     print(str)
        if len(str) > 0:
            list, self.remainder = getlines(self.remainder + str)
            for data in list:
                if self.out_file != None:
                    self.out_file.write(data + "\n") 
                if self.socket_connected_event.is_set():
                    self.socket_out_queue.put(data.encode('utf-8') + b'\n')            
            self.out_file.close()
            time_hour_minute = datetime.datetime.utcnow().replace(year=1900, month=1, day=1, second=0, microsecond=0)
            midnight = datetime.datetime(1900,1,1,0,0,0,0)
            if time_hour_minute == midnight:
                if not self.rollover:
                    #print(time_hour_minute.strftime("%Y-%m-%dT%H%M"), midnight.strftime("%Y-%m-%dT%H%M"))
                    self.out_file_name = self.out_file_base_name + time.strftime("%Y-%m-%dT%H%M", time.gmtime()) +'.csv' 
                    self.get_quakes_from_USGS('')
                    self.rollover = True
            else:
                self.rollover = False
            self.out_file = open(self.out_file_name, "a")

    def get_quakes_from_USGS(self, filename_adder):
        if self.get_quakes:
            try:
                print('\ndownloading quakes')
                quakefilename = reader.out_file_name.replace('.csv', '') + '_quakes' + filename_adder +'.json'
                with urllib.request.urlopen(self.quake_url,timeout = 10) as url:
                    data = json.loads(url.read().decode())
                    print('download complete')
                with open(quakefilename, 'w') as qfile:
                    qfile.write(json.dumps(data))
                    print('quake file {} written'.format(quakefilename))
            except urllib.error.URLError:
                pass
            print('done with quakes')

def socket_worker(server_port, out_queue, connected_event):
#    try:
        while 1:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                while 1:
                    try:
                        s.bind(('', int(server_port)))
                        break
                    except:
                        print(f'bind to {server_port} failed')
                        time.sleep(15)
                        pass
                print("listening on", (socket.gethostname(), int(server_port)))  # how do I get numeric host address? - gethostbyname() returns 127.0.1.1
                s.listen(1)
                conn, addr = s.accept()
                print('remote connection from:', addr)
                connected_event.set()
                while 1:
                    data = out_queue.get(block = True)
                    #print("transmitting data:", data)
                    out_queue.task_done()
                    try:
                        conn.send(data)
                    except (ConnectionAbortedError, ConnectionResetError, TimeoutError):
                        print('remote disconnected')
                        connected_event.clear()
                        break
#    finally:
#        s.shutdown()
#        s.close()


linecount = 0
def getlines(str):
    global linecount
    list = []
    partial = ""
    #print("in getlines", str)
    for i in range(len(str)):
        if(str[i] == '\r' or str[i] == '\n'):
            if(len(partial) > 0):
                #print("partial", partial)
                list.append(partial)
                partial = ""
                #print(linecount, list, partial)
                linecount += 1
            
            #
        else:
            #print(str[i])
            partial = partial + str[i]
    #print(linecount, list, partial)
    return(list, partial)        


try:
    i = 0               
    reader = ReadData()
    reader.get_quakes_from_USGS('_prev')

    try:
        while True:
            time.sleep(0.02) 
            reader.read_data()
    except KeyboardInterrupt:
        pass

    reader.get_quakes_from_USGS('')

except KeyboardInterrupt:
    pass

finally:

    if reader.ser != None:
        reader.ser.close()

    if reader.out_file != None:
        reader.out_file.close()
    
