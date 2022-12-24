import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import serial
#import serial.tools.list_ports as list_ports
import tkinter as tk
from tkinter import messagebox

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.figure import Figure
import configparser
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

        self.config = getconfig.getconfig('seislog.conf')
        self.server_address = self.config['DEFAULT']['server_address']
        self.server_port = self.config['DEFAULT']['server_port']
        self.sample_rate = float(self.config['DEFAULT']['sample_rate'])

        self.display_y_offset = float(self.config['MONITOR']['display_y_offset'])
        self.display_y_max = float(self.config['MONITOR']['display_y_max'])
        self.display_y_min = float(self.config['MONITOR']['display_y_min'])
        self.trace_duration = float(self.config['MONITOR']['trace_duration'])

        self.display_samples = int(self.trace_duration * self.sample_rate)

        self.master = tk.Tk()
        
        # create main window
        self.master.title("monitor - Version 0.1")
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
        self.readbutton = tk.Button(self.controlFrame, text="Don't push this button", command=self.read_data)

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
        self.trace = {"t" : np.linspace(self.trace_duration - 1 / self.sample_rate, 0, self.display_samples), "y" : np.zeros(self.display_samples)}
        self.lines = []
        self.i = 0
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.server_address, int(self.server_port)))
        self.s.setblocking(0)

        self.remainder = ""
        self.rollover = False

    def read_data(self):
        str = ''
        try:
            str = b""
            str = self.s.recv(100).decode("utf-8")
        except BlockingIOError:
            pass

        if len(str) > 0:
            list, self.remainder = getlines(self.remainder + str)
            for data in list:
                self.trace["y"] = shift(self.trace['y'], -1)
                self.trace["y"][-1] = int(data) + self.display_y_offset
            self.plot()
   
    def plot(self):
        if len(self.lines) == 0:
            self.axs.set_ylim(self.display_y_max, self.display_y_min)
            self.axs.set_xlim(self.trace_duration, 0)
            self.lines = self.axs.plot(self.trace['t'], self.trace['y'], color = 'b', linewidth = 1)
        else:
            #ylimits = self.axs.get_ylim()
            #if max(self.trace['y']) > ylimits[0] or min(self.trace['y']) < ylimits[1]:
            #    self.axs.set_ylim(ylimits[0] * 10, ylimits[1] * 10)
            self.lines[0].set_data(self.trace['t'], self.trace['y'])
        self.fig.canvas.draw_idle()
linecount = 0
def getlines(str):
    global linecount
    list = []
    partial = ""
    for i in range(len(str)):
        if(str[i] == '\r' or str[i] == '\n'):
            if(len(partial) > 0):
                list.append(partial)
                partial = ""
            linecount += 1
        else:
            partial = partial + str[i]
    return(list, partial)     

def update(a):
    global gui
    gui.read_data()

i = 0               
gui = PlotLogGui()

anim = animation.FuncAnimation(gui.fig, update, interval = 20)
gui.master.mainloop()

