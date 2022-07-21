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

class ReadData:
    def __init__(self):

        self.config = configparser.ConfigParser()
        try:
            with open('read_config.ini', 'r') as configfile:
                self.config.read_file(configfile)
        except IOError:
            self.config["DEFAULT"] = {'com_port' : 'COM1', 
                                        'baudrate' : '9600', 
                                        'out_file_base_name' : "seismo_", 
                                        'socket_port' : '5067', 
                                        'get_quakes':'False',
                                        'quake_url':'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojson'
                                        }
            with open('read_config.ini', 'w') as configfile:
                self.config.write(configfile)
        self.com_port = self.config["DEFAULT"]["com_port"]
        self.baud_rate = self.config["DEFAULT"]["baud_rate"]

        self.out_file_name = self.config["DEFAULT"]["out_file_base_name"] + time.strftime("%Y-%m-%dT%H%M", time.gmtime()) +'.csv' 
        self.out_file = open(self.out_file_name, "w")
        self.get_quakes = (self.config['DEFAULT']['get_quakes'].upper() == 'TRUE')
        self.quake_url = self.config['DEFAULT']['quake_url']
        print(type(self.out_file))
        print("opening: %s" % os.path.realpath(self.out_file.name))

        self.ser = serial.Serial(self.com_port, self.baud_rate, timeout = 0)
        while(self.ser.read(1000) == 1000):
            pass
        self.sampcount = 0
        self.remainder = ""
        self.queue = None
        if self.config['DEFAULT']['socket_port'] != 0:
            self.socket_out_queue = queue.Queue()
            self.socket_connected_event = threading.Event()
            self.socket_thread = threading.Thread(target = socket_worker, args = (self.config['DEFAULT']['socket_port'], self.socket_out_queue, self.socket_connected_event))
            self.socket_thread.daemon = True
            self.socket_thread.start()
        self.rollover = False

    def read_data(self):
        str = self.ser.read(1000).decode("utf-8")
        if len(str) > 0:
            list, self.remainder = getlines(self.remainder + str)
            for data in list:
                self.sampcount = self.sampcount + 1
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
                    self.out_file_name = self.config["DEFAULT"]["out_file_base_name"] + time.strftime("%Y-%m-%dT%H%M", time.gmtime()) +'.csv' 
                    with urllib.request.urlopen(self.config.quakeurl) as url:
                        data = json.loads(url.read().decode())
                    with open(reader.out_file_name.replace(".csv", "")+'_quakes.json', 'w') as qfile:
                        qfile.write(json.dumps(data))                    
                    self.rollover = True
            else:
                self.rollover = False
            self.out_file = open(self.out_file_name, "a")
   

import socket
def socket_worker(socket_port, out_queue, connected_event):
    while 1:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((socket.gethostname(), int(socket_port)))
            print("listening on", ("10.0.0.7", int(socket_port)))
            s.listen(1)
            conn, addr = s.accept()
            print('Connection address:', addr)
            connected_event.set()
            while 1:
                #data = conn.recv(BUFFER_SIZE)
                data = out_queue.get(block = True)
                print("transmitting data:", data)
                out_queue.task_done()
                try:
                    conn.send(data)
                except ConnectionAbortedError:
                    connected_event.clear()
                    break

def getlines(str):
    list = []
    partial = ""
    #print("in getlines", str)
    for i in range(len(str)):
        if(str[i] == '\r' or str[i] == '\n'):
            if(len(partial) > 0):
                #print("partial", partial)
                list.append(partial)
                partial = ""
        else:
            #print(str[i])
            partial = partial + str[i]
    #print("result", list, partial)
    return(list, partial)        

i = 0               
reader = ReadData()
if reader.get_quakes:
    with urllib.request.urlopen(reader.quake_url) as url:
        data = json.loads(url.read().decode())
    with open(reader.out_file_name.replace(".csv", "")+'_quakes_prev.json', 'w') as qfile:
        qfile.write(json.dumps(data))

try:
    while True:
        time.sleep(0.1)
        reader.read_data()
except KeyboardInterrupt:
    pass

if reader.get_quakes:
    with urllib.request.urlopen(reader.quake_url) as url:
        data = json.loads(url.read().decode())
    with open(reader.out_file_name.replace(".csv", "")+'_quakes.json', 'w') as qfile:
        qfile.write(json.dumps(data))

reader.ser.close()
if reader.out_file != None:
    reader.out_file.close()

