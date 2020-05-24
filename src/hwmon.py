import tkinter as tk
import tk_tools
import clr
import ctypes, sys, os, winsound
from enum import IntEnum, auto

class HWMon:

    # https://github.com/openhardwaremonitor/openhardwaremonitor/blob/master/Hardware/IHardware.cs#L15
    class HardwareType(IntEnum):
        Mainboard   = 0
        SuperIO     = auto()
        CPU         = auto()
        RAM         = auto()
        GpuNvidia   = auto()
        GpuAti      = auto()
        TBalancer   = auto()
        Heatmaster  = auto()
        HDD         = auto()

    # https://github.com/openhardwaremonitor/openhardwaremonitor/blob/master/Hardware/ISensor.cs#L17
    class SensorType(IntEnum):
        Voltage     = 0      # V
        Clock       = auto() # MHz
        Temperature = auto() # °C
        Load        = auto() # %
        Fan         = auto() # RPM
        Flow        = auto() # L/h
        Control     = auto() # %
        Level       = auto() # %
        Factor      = auto() # 1
        Power       = auto() # W
        Data        = auto() # GB = 2^30 Bytes    
        SmallData   = auto() # MB = 2^20 Bytes
        Throughput  = auto() # MB/s = 2^20 Bytes/s

    def __init__(self):
        print ("Initializing sensors...")

        clr.AddReference("OpenHardwareMonitorLib")
        from OpenHardwareMonitor import Hardware

        self.handle = Hardware.Computer()
        self.handle.CPUEnabled = True
        self.handle.HDDEnabled = True
        # self.handle.RAMEnabled = True
        # self.handle.GPUEnabled = True
        # self.handle.MainboardEnabled = True
        # self.handle.FanControllerEnabled = True
        self.handle.Open()

        self.sensors = []

    def poll(self):
        self.sensors.clear()

        # cer noi date de la OpenHardwareMonitor
        for i in self.handle.Hardware:
            i.Update()
            for sensor in i.Sensors:
                self.parse_sensor(sensor)
            for j in i.SubHardware:
                j.Update()
                for subsensor in j.Sensors:
                    self.parse_sensor(subsensor)

    def parse_sensor(self, sensor):
        # este posibil ca un senzor sa nu citeasca nimic, iar in acest caz nu iau in calcul senzorul respectiv
        # (ex: daca driverul nu poate fi incarcat, atunci senzorii pentru temperatura si voltaj de la CPU nu pot fi accesati)
        if sensor.Value is not None:
            self.sensors.append(sensor)

    def get_temp(self, hw_type):
        # pentru procesoarele multicore, biblioteca raporteaza n+1 temperaturi astfel:
        #  n temperaturi pentru fiecare core
        #  1 temperatura generala a procesorului (senzorul asociat acestei temperaturi are indexul cel mai mare)

        # pastrez din toti senzorii doar lista cu cei care sunt de temperatura pentru piesa hw de interes
        temp_sensors = filter(lambda x: 
                                x.SensorType == self.SensorType.Temperature and
                                x.Hardware.HardwareType == hw_type,
                            self.sensors)

        # citesc senzorul cu indexul cel mai mare (why? vezi mai sus ^)
        temp_sensors = sorted(temp_sensors, reverse=True, key=lambda x: x.Index)

        try:
            temp = temp_sensors[0].Value
        except:
            temp = -1

        return temp

    def print_sensors(self):
        for s in self.sensors:
            print("{} {} ({}) - {} {} - {}".format(
                self.HardwareType(s.Hardware.HardwareType).name,
                self.SensorType(s.SensorType).name,
                s.Name, 
                s.Hardware.Name, s.Index, s.Value))

class Meter(tk.Frame):
    def __init__(self, master, hw_type, sensor_type, **kwargs):
        tk.Frame.__init__(self, master, **kwargs)

        self.hw_type = hw_type
        self.sensor_type = sensor_type
        self.limit_var = tk.IntVar(self, 100)
        self.meter_name = "{} {}".format(HWMon.HardwareType(hw_type).name, HWMon.SensorType(sensor_type).name)

        self.canvas = tk.Canvas(self, width=400, height=220,
                                borderwidth=2, relief="sunken",
                                bg="white")
        self.canvas.pack(fill="both")

        # afisaj ac-indicator - hardcodat sa afiseze in grade Celsius, desi clasa Meter este scrisa in asa fel
        # incat sa suporte afisarea oricarui tip de senzor pentru orice piesa hardware suportata de biblioteca
        # totusi, aplicatia se bazeaza doar pe temperaturi, deci e ok si asa
        self.gauge = tk_tools.Gauge(self.canvas, width=400, height=200,
                                    max_value=100.0, divisions=10,
                                    yellow=70, red=90,
                                    label=self.meter_name, unit="°C")
        self.gauge.pack()


        # slider de stabilire a valorii maxime admise
        # daca senzorul citeste o valoare mai mare decat ce indica acest slider, atunci se va lua o actiune
        # vezi App::check_sensors_limits
        self.label = tk.Label(self, text="Adjust " + self.meter_name + " limit")
        self.label.pack()
        
        self.scale = tk.Scale(self, orient="horizontal", from_=0, to=100, variable=self.limit_var, length=200)
        self.scale.pack()


class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        # initializare afisaje (ac indicator + slider de limitare)
        cpu_meter = Meter(self, HWMon.HardwareType.CPU, HWMon.SensorType.Temperature)
        hdd_meter = Meter(self, HWMon.HardwareType.HDD, HWMon.SensorType.Temperature)
        cpu_meter.pack(side="left")
        hdd_meter.pack(side="left")
        
        # initializare senzori - biblioteca
        self.hwmon  = HWMon()
        self.meters = [cpu_meter, hdd_meter]
        self.title("Hardware Monitor")
        self.resizable(False, False)
        self.loop()
        # self.hwmon.print_sensors()

    def update_gauges(self):
        # actualizeaza grafica pe baza datelor de la senzori

        for m in self.meters:
            temp = self.hwmon.get_temp(m.hw_type)
            m.gauge.set_value(temp)

            if temp == -1:
                print ("Can't read {}. Are you admin?".format(m.meter_name))

    def check_sensors_limits(self):
        # verifica depasirea limitelor impuse de utilizator

        for m in self.meters:
            meter_value = self.hwmon.get_temp(m.hw_type)
            meter_limit = m.limit_var.get()

            if meter_value > meter_limit:
                # Actiune daca se trece peste limita:

                # Ex: shutdown fortat:
                # os.system("shutdown /s /t 1")

                # sau mai putin drastic, doar printez un warning in consola si dau un sunet de eroare :)
                print ("Exceeded {} ({} > {})".format(m.meter_name, meter_value, meter_limit))

                try:
                    winsound.PlaySound("SystemHand", winsound.SND_ALIAS | winsound.SND_NOSTOP | winsound.SND_ASYNC)
                except RuntimeError:
                    pass


    def loop(self):
        self.hwmon.poll()
        self.update_gauges()
        self.check_sensors_limits()

        # 20 de actualizari pe secunda = overkill
        # insa cum tk-tools nu interpoleaza acul de la afisare, arata mult mai bine cu un loop cu frecventa mare :)
        self.after(50, self.loop)



# !! IMPORTANT !!
# ---------------

# OpenHardwareMonitor citeste datele de la hardware printr-un driver
# Incarcarea unui driver necesita drepturi de administrator

# Codul de mai jos verifica daca scriptul ruleaza ca admin;
# Daca nu, se incearca repornirea acestuia cu drepturi de admin

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    if is_admin():
        print ("App running with admin rights.")
        app = App()
        app.mainloop()
    else:
        print ("Certain sensors require elevated privileges.")
        print ("Restarting app as admin...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
