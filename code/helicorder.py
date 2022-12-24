import scipy.signal as sig
import sys
import numpy as np
import csv
import datetime

import urllib.request, json 

from datetime import timedelta
import tkinter as tk
from tkinter import messagebox
 
import tkinter.ttk as ttk
from tkinter.filedialog import askopenfilename
#import serial.tools.list_ports

import scipy.fftpack as fft
import scipy.signal as signal

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.figure import Figure

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

samplerate = 30

def bin_to_str(b):
    return to_bytearray(b).decode("ascii")        
        
        
class PlotLogGui:
    def __init__(self):

        self.master = tk.Tk()
        
        self.style = ttk.Style()     
        self.style.configure('TButton', anchor='center')
        self.style.configure('TLabel', anchor='center')
        self.style.configure('TNotebook.Tab', foreground='blue')
        self.style.configure('TLabelframe.Label', foreground='blue')
  
        # create main window
        self.master.title("Helicorder Application - Version 0.0")
        self.master.geometry('1024x768')
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
        self.plotbutton = ttk.Button(self.controlFrame, text="Plot", command=self.plotit)
        self.lpbutton = ttk.Button(self.controlFrame, text="LP", command=self.plot_lp)
        self.bpbutton = ttk.Button(self.controlFrame, text="BP", command=self.plot_bp)
        self.hpbutton = ttk.Button(self.controlFrame, text="HP", command=self.plot_hp)
        self.getbutton = ttk.Button(self.controlFrame, text="Get EQ times", command=self.get_eq)
        self.specbutton = ttk.Button(self.controlFrame, text="Plot Spectrogram", command=self.plot_spec)
        self.fftbutton = ttk.Button(self.controlFrame, text="Plot fft", command=self.plot_fft)


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
        self.plotbutton.grid(row=1, column=0)
        self.lpbutton.grid(row=2, column=0)
        self.hpbutton.grid(row=3, column=0)
        self.bpbutton.grid(row=4, column=0)
        self.getbutton.grid(row=5, column=0)
        self.specbutton.grid(row=6, column=0)
        self.fftbutton.grid(row=7, column=0)


        self.filter = None
        self.axs = None

        self.strip_time = 3600.0 
        self.sample_rate = 30.0
        self.strip_samples = int(self.strip_time * self.sample_rate)
      
        sys.stdout = StdoutRedirector(self.text)

        self.master.mainloop()

    def plotit(self):
        self.filter = None
        self.plot()
        
    def plot_lp(self):
        self.filter = "LP"
        self.plot()
        
    def plot_hp(self):
        self.filter = "HP"
        self.plot()
        
    def plot_bp(self):
        self.filter = "BP"
        self.plot()

    def readcsv(self):
#        filename = "c:\\users\\user\\Google Drive\\seismo\\geotech_sl-210-192_2019-03-07T0247.csv"
#        filename = "x:\\seismo\\geotech_sl-210-192_2019-03-12T0215.csv"
        filename = self.filename #"x:\\seismo\\geotech_sl-210-192_2019-03-10T0303.csv"
        with open(filename) as csv_file:
            filetime = filename[-19:-4]
            self.start_time_exact = datetime.datetime.strptime(filetime, "%Y-%m-%dT%H%M")
            print(self.start_time_exact.strftime("%Y-%m-%d %H:%M:%S"))
            #start_strip = start_time_exact - timedelta(microseconds=start_time_exact.microsecond, seconds=start_time_exact.second, minutes=start_time_exact.minute % self.strip_time)
            csv_reader = csv.reader(csv_file, delimiter=',')
            self.trace = []
            
            i = 0
            for row in csv_reader:
                try:
                    self.trace.append(int(row[0]))
                    i = i + 1
                except(ValueError):
                    pass
            self.trace = np.array(self.trace)
            if(self.filter == "LP"):
                coeffs = sig.firls(1023, bands=(0, 1, 1.1, self.sample_rate/2.0), desired = (1, 1, 0, 0), fs = self.sample_rate)
                self.trace = sig.filtfilt(coeffs, 1, self.trace)
            elif(self.filter == "HP"):
                coeffs = sig.firls(1023, bands=(0, 1, 1.1, self.sample_rate/2.0), desired = (0, 0, 1, 1), fs = self.sample_rate)
                self.trace = sig.filtfilt(coeffs, 1, self.trace)
            elif(self.filter == "BP"):
                coeffs = sig.firls(1023, bands=(0, .1, .15, 1, 1.05, self.sample_rate/2.0), desired = (0, 0, 1, 1, 0, 0), fs = self.sample_rate)
                self.trace = sig.filtfilt(coeffs, 1, self.trace)

    def lasthour(self, time):
        return(time.replace(second=0, minute=0, hour=time.hour))
        
        
    def read_data(self):
        self.filter = None
        self.filename = askopenfilename()
        self.readcsv()
        return

    
    def plot(self):

        self.readcsv()
        if self.axs != None:
            self.axs.remove()
        self.axs = self.fig.add_subplot(111)
        start_strip_second = self.start_time_exact.minute * 60 + self.start_time_exact.second
        start_strip_hour_time = self.start_time_exact.replace(minute = 0, second = 0, microsecond = 0)
        end_strip_time = (self.start_time_exact + datetime.timedelta(seconds = len(self.trace) // self.sample_rate))
        end_strip_hour_time = end_strip_time.replace(minute = 0, second = 0, microsecond = 0) + datetime.timedelta(hours = 1)
        strips_duration = end_strip_hour_time - start_strip_hour_time
        numstrips = int(strips_duration.total_seconds()) // 3600
        print("calculate strips:", self.start_time_exact, start_strip_hour_time,end_strip_hour_time, numstrips, strips_duration.total_seconds())
        self.maxs = np.std(self.trace) * 5
        print("maximum counts:", self.maxs)
        self.strips = []
        for j in range(numstrips):
            if j == 0:
                # calculate how many seconds into the strip period first strip starts
                # Make range for strip time
                t = np.arange(start_strip_second, self.strip_time, 1/self.sample_rate)

                start_sample = 0
                # calculate sample number (in trace array) of end of strip
                if(len(self.trace) > self.strip_samples - int(start_strip_second * self.sample_rate)):
                    end_first_strip_sample = self.strip_samples - int(start_strip_second * self.sample_rate)
                    t = np.arange(start_strip_second, self.strip_time, 1/self.sample_rate)
                else:
                    end_first_strip_sample = len(self.trace)
                    t = np.arange(start_strip_second, start_strip_second + len(self.trace) / self.sample_rate, 1/self.sample_rate)
                    
                end_sample = end_first_strip_sample
                
            elif j == numstrips - 1:
                # last strip - make time range from 0 to end of trace
                t = np.arange(0, (len(self.trace) - self.strip_samples * j + start_strip_second * self.sample_rate) / self.sample_rate, 1/self.sample_rate)
                start_sample = end_first_strip_sample + self.strip_samples * (j - 1)
                end_sample = len(self.trace)

            else:
                t = np.arange(0, self.strip_time, 1.0/30.0)
                start_sample = end_first_strip_sample + self.strip_samples * (j - 1)
                end_sample = end_first_strip_sample + self.strip_samples * j

            start_time = self.lasthour(self.start_time_exact) + timedelta(hours = j)
            end_time = self.lasthour(self.start_time_exact) + timedelta(hours = j + 1)
            #print(start_time, end_time)

            #print(j, t, start_sample, end_sample, start_time, end_time)
            y = self.trace[start_sample:end_sample] / (self.maxs * 1.5) + self.start_time_exact.hour
            self.strips.append({'start_time':start_time, 'end_time':end_time,  'start_sample': start_sample, 'end_sample': end_sample, 't':t, 'y':y})

            #print(self.strips)                

            self.axs.set_ylim(self.start_time_exact.hour + 25.5, self.start_time_exact.hour - 0.5)
            self.axs.set_yticks(np.arange(self.start_time_exact.hour, self.start_time_exact.hour + 25, 1))
            self.axs.plot(t, y + j, color = 'b', linewidth = 1)

        self.get_eq()
        self.fig.canvas.draw_idle()

    def plot_spec(self):
        if self.axs != None:
            self.axs.remove()
        self.axs = self.fig.add_subplot(111)
        #t,f,sxx = sig.spectrogram(self.trace, self.sample_rate)
        #self.axs.imshow(sxx)
        self.axs.specgram(self.trace, NFFT=2048, Fs=self.sample_rate, cmap='inferno')
        self.fig.canvas.draw_idle()
        return    
        
    def plot_fft(self):
        if self.axs != None:
            self.axs.remove()
        self.axs = self.fig.add_subplot(111)
        #t,f,sxx = sig.spectrogram(self.trace, self.sample_rate)
        #self.axs.imshow(sxx)
        N = len(self.trace)
        f, Pxx_den = signal.welch(self.trace, fs = self.sample_rate, window = 'blackman', nperseg = 8192, nfft = 8192, detrend = 'linear', scaling = 'spectrum')
        self.axs.semilogy(f, Pxx_den)
        self.fig.canvas.draw_idle()
        return

    def xyfromtime(self, time):
        for strip in self.strips:
            #print(time, strip['start_time'], strip['end_time'])
            if (time > strip['start_time'] and time < strip['end_time']):
                x = (time - strip['start_time']).seconds
                time_since_start_of_graph = strip['start_time'] - self.start_time_exact.replace(hour=0, microsecond=0, second=0, minute=0)
                hours_since_plot_start = time_since_start_of_graph.seconds // 3600 + time_since_start_of_graph.days * 24 
                y = hours_since_plot_start
                #print("found:", strip["start_time"], self.start_time_exact.replace(hour=0, microsecond=0, second=0, minute=0), hours_since_plot_start)
                return(x, y)
        return None
        
    def get_eq(self):
        offs = .2
        print("getting eq")
        with urllib.request.urlopen("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson") as url:
            data = json.loads(url.read().decode())
            #print(data)
            first = True
            for quake in data["features"]:
                #print(quake['properties']['place'])
                t = datetime.datetime.utcfromtimestamp(int(quake["properties"]["time"])/1000)
                #print("Is quake in graph? %d", len(self.strips))
                a = self.xyfromtime(t)
                if a != None and quake['properties']['mag'] >= 4.8:
                    if (first):
                        print("%-3s %-40s %-6s %-6s %-25s %-5s %-5s, %-6s" % ("Mag", "Location", "  Lon", " Lat", "Time", " Dist", " Depth", "Sec"))
                        first = False
                    #print("annotate quake %s %s" % (quake['properties']['mag'],quake['properties']['place']))
                    #self.axs.annotate("%4.1f %s" % (quake['properties']['mag'],quake['properties']['place'],), xy=a, xytext=(a[0]-5,a[1]-0.5+offs), arrowprops=dict(arrowstyle = '->'))
                    offs = -offs
                    q_lat = np.pi*quake['geometry']['coordinates'][1]/180
                    q_lon = np.pi*quake['geometry']['coordinates'][0]/180
                    s_lat = np.pi*42.52/180
                    s_lon = np.pi*-83.36/180
                    seconds_from_data_start = (t - self.start_time_exact).seconds + (t - self.start_time_exact).days * 24 * 3600
                    dist = np.arccos(np.sin(q_lat)*np.sin(s_lat) + np.cos(q_lat)*np.cos(s_lat)*np.cos(q_lon - s_lon))*360/(2*np.pi)
                    #print("%3.1f %15s %4.1f $4.1f %s %4.1f"%(quake['properties']['mag'], quake["properties"]["place"], quake["geometry"]["coordinates"][1],  quake["geometry"]["coordinates"][0], self.xyfromtime(t), dist))
                    print("%3.1f %-40s %6.1f %6.1f %25s %5.1f %5.1f %6s"%(quake['properties']['mag'], quake["properties"]["place"], quake["geometry"]["coordinates"][1],  quake["geometry"]["coordinates"][0], t, dist, quake['geometry']['coordinates'][2], seconds_from_data_start))
                    vs = 180/4400
                    #print("Get surface wave position")
                    s = self.xyfromtime(t + datetime.timedelta(seconds=dist/vs))
                    #print(s)
                    #print(offs)
                    #print(vs,s,t,quake["properties"]["time"])
                    if(s != None):
                        self.axs.annotate("%4.1f %s surface" % (quake['properties']['mag'],quake['properties']['place'],), xy=s, xytext=(s[0]-10,s[1]-0.4+offs), arrowprops=dict(arrowstyle = '->'))                    
                
                
#def update():
#    global gui
#    gui.

    
gui = PlotLogGui()
