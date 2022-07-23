import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
import scipy.signal as sig
import sys
import csv
import datetime
import serial
import serial.tools.list_ports as list_ports
import tkinter.dialog as dialog
import json
import urllib
import urllib.request, json 
import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk
from tkinter.filedialog import askopenfilename

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.figure import Figure
import os
import configparser
import queue
import threading
import socket
import getconfig

def mb(s):
    tk.messagebox.showinfo(" ", s)

class StdoutRedirector(object):
    def __init__(self,text_widget):
        self.text_space = text_widget

    def write(self,string):
        self.text_space.insert('end', string)
        self.text_space.see('end')
        
    def flush(self):
    	pass
    
#shift a numpy array right, dropping last n (or shift left and drop first n if n negative) and fill with NaN
def shift(xs, n):
    e = np.empty_like(xs)
    if n >= 0:
        e[:n] = np.nan
        e[n:] = xs[:-n]
    else:
        e[n:] = np.nan
        e[:n] = xs[-n:]
    return e

class PlotLogGui:
    def __init__(self):

        self.master = tk.Tk()
        
        self.style = ttk.Style()     
        self.style.configure('TButton', anchor='center')
        self.style.configure('TLabel', anchor='center')
        self.style.configure('TNotebook.Tab', foreground='blue')
        self.style.configure('TLabelframe.Label', foreground='blue')
  
        # create main window
        self.master.title("Record - Version 0.0")
        self.master.geometry('800x600')
        self.master.rowconfigure(0,weight=1)
        self.master.columnconfigure(0, weight=1)

        # create outermost frame (surrounds everything)
        self.frame = tk.Frame(self.master)
        self.frame.config(borderwidth=2, relief="sunken")
        self.frame.grid(column=0, row=0, sticky='NSEW')

        # create frame for bottom text widget
        self.textFrame = tk.Frame(self.frame)
        # create text widget and scrollbar
        self.text = tk.Text(self.textFrame, borderwidth=2, relief="sunken", width=100, height=12, )
        self.text.config(font=("consolas",8))
        self.scroll = tk.Scrollbar(self.textFrame, command=self.text.yview)
        self.text['yscrollcommand'] = self.scroll.set   

        # create plot widget
        self.fig = Figure()
        self.fig.set_tight_layout(True)
        
        # create canvas for figure to draw in using Agg backend
        self.plotcanvas = FigureCanvasTkAgg(self.fig, master=self.frame)  
        self.toolbarFrame = tk.Frame(self.frame)

        # create frame for left-side controls
        self.controlFrame = tk.Frame(self.frame)
        self.controlFrame.config(borderwidth=2, relief="sunken")
        
        # create label
        self.readbutton = ttk.Button(self.controlFrame, text="Read data", command=self.read_data)

        # configure frame grid
        colwt = [0,1]
        for i in range(0,len(colwt)):
            self.frame.columnconfigure(i, weight=colwt[i])
        rowwt = [1,0]
        for i in range(0,len(rowwt)):
             self.frame.rowconfigure(i, weight=rowwt[i])

        # configure textFrame grid
        self.textFrame.grid_rowconfigure(0, weight=1)
        self.textFrame.grid_columnconfigure(0, weight=1)
        
        # lay out items
        self.toolbarFrame.grid(row=1, column=1,sticky=('W'))
        # textFrame in frame
        self.textFrame.grid(row=2, column=1,  sticky=('SEW'))
        # text and scroll in textFrame
        self.text.grid(row=0,column=0,sticky="nsew",padx=2,pady=2)
        self.scroll.grid(row=0,column=1,sticky="nsew")
        
        # canvas in frame
        self.plotcanvas.get_tk_widget().grid(row=0, column=1,  sticky=('NSEW'))
        toolbar = NavigationToolbar2Tk(self.plotcanvas, self.toolbarFrame)
        toolbar.update()
        
        # controlframe in frame
        self.controlFrame.grid(row=0, column=0, rowspan=2)

        # label in controlframe
        self.readbutton.grid(row=0, column=0)

        self.filter = None
        self.axs = self.fig.add_subplot(111)
        

        self.strip_time = 3600.0 
        self.sample_rate = 10.0
        self.strip_samples = int(self.strip_time * self.sample_rate)

        self.trace = {"t" : np.linspace(899.9, 0, 9000), "y" : np.zeros(9000)}
        self.lines = []
        self.i = 0
        self.config = getconfig.getconfig('seislog.conf')
        # self.config = configparser.ConfigParser()
        # config_file_name = 'seislog.conf'
        # try:
        #     with open(config_file_name, 'r') as configfile:
        #         self.config.read_file(configfile)
        # except IOError:
        #     self.config["DEFAULT"] = {'com_port' : 'COM1', 'baud_rate' : '9600', 'out_file_base_name' : "unknown", 'server_port' : '0', 'server_address' : '127.0.0.1'}
        #     with open(config_file_name, 'w') as configfile:
        #         print('configuration file not found - default {} written'.format(config_file_name))
        #         self.config.write(configfile)
        self.com_port = self.config["DEFAULT"]["com_port"]
        self.baud_rate = self.config["DEFAULT"]["baud_rate"]
        self.out_file_base_name = self.config["DEFAULT"]["out_file_base_name"]
        self.out_file_name = self.out_file_base_name + time.strftime("%Y-%m-%dT%H%M", time.gmtime()) +'.csv' 
        self.out_file = open(self.out_file_name, "w")
        self.server_address = self.config['DEFAULT']['server_address']
        self.server_port = self.config['DEFAULT']['server_port']
        
        print(type(self.out_file))
        print("opening: %s" % os.path.realpath(self.out_file.name))
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.server_address, int(self.server_port)))
        self.s.setblocking(0)

        self.sampcount = 0
        self.remainder = ""
        self.queue = None
        self.rollover = False

    def read_data(self):
        str = ''
        try:
            str = self.s.recv(1).decode("utf-8")
        except BlockingIOError:
            pass

        if len(str) > 0:
            list, self.remainder = getlines(self.remainder + str)
            for data in list:
                self.sampcount = self.sampcount + 1
                self.trace["y"] = shift(self.trace['y'], -1)
                self.trace["y"][-1] = int(data)
                if self.out_file != None:
                    self.out_file.write(data + "\n") 
            self.out_file.close()
            time_hour_minute = datetime.datetime.utcnow().replace(year=1900, month=1, day=1, second=0, microsecond=0)
            midnight = datetime.datetime(1900,1,1,0,0,0,0)
            if time_hour_minute == midnight:
                if not self.rollover:
                    #print(time_hour_minute.strftime("%Y-%m-%dT%H%M"), midnight.strftime("%Y-%m-%dT%H%M"))
                    self.out_file_name = self.out_file_base_name + time.strftime("%Y-%m-%dT%H%M", time.gmtime()) +'.csv' 
                    with urllib.request.urlopen("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson") as url:
                        data = json.loads(url.read().decode())
                    with open(gui.out_file_name.replace(".csv", "")+'_quakes.json', 'w') as qfile:
                        qfile.write(json.dumps(data))                    
                    self.rollover = True
            else:
                self.rollover = False
            self.out_file = open(self.out_file_name, "a")
            self.plot()
   
    def plot(self):
        if len(self.lines) == 0:
            self.axs.set_ylim(100000,-100000)
            self.axs.set_xlim(900,0)
            self.lines = self.axs.plot(self.trace['t'], self.trace['y'], color = 'b', linewidth = 1)
        else:
            #ylimits = self.axs.get_ylim()
            #if max(self.trace['y']) > ylimits[0] or min(self.trace['y']) < ylimits[1]:
            #    self.axs.set_ylim(ylimits[0] * 10, ylimits[1] * 10)
            self.lines[0].set_data(self.trace['t'], self.trace['y'])
        self.fig.canvas.draw_idle()

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

def update(a):
    global gui
    gui.read_data()

i = 0               
gui = PlotLogGui()

anim = animation.FuncAnimation(gui.fig, update, interval=100)
gui.master.mainloop()

if gui.out_file != None:
    gui.out_file.close()

