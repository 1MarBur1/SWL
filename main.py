from PyQt6.QtWidgets import QApplication, QPushButton, QMainWindow, QVBoxLayout, QWidget, QLabel, QColorDialog, QHBoxLayout
from PyQt6.QtCore import QTimer
import sys
import glob
from time import sleep
import serial
import threading

def setInterval(func,time):
    e = threading.Event()
    while not e.wait(time):
        func()

def serial_ports():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

ser = serial.Serial(serial_ports()[0], 115200)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.currentData = []
        ser.write(bytearray([0xFF]))
        self.currentData = self.get_data()

        self.temp = QLabel("Температура воздуха: " + str(self.currentData[3]) + "°C")
        self.humidity = QLabel("Влажность воздуха: " + str(self.currentData[4]) + "%")

        self.airLayout = QHBoxLayout()
        self.airLayout.addWidget(self.temp)
        self.airLayout.addWidget(self.humidity)

        self.soilhumidity = QLabel("Влажость почвы: " + str(self.currentData[8]) + "%")
        self.soiltemp = QLabel("Температура почвы: " + str(self.currentData[7]) + "°C")

        self.soilLayout = QHBoxLayout()
        self.soilLayout.addWidget(self.soilhumidity)
        self.soilLayout.addWidget(self.soiltemp)

        self.pressure = QLabel("Давление воздуха: " + str(self.currentData[5]) + "hPa")
        self.light = QLabel("Интенсивность света: " + str(self.currentData[6]) + "Люкс")

        self.otherLayout = QHBoxLayout()
        self.otherLayout.addWidget(self.pressure)
        self.otherLayout.addWidget(self.light)
        
        self.color = QColorDialog()

        self.submitColor = QPushButton("Задать цвет")
        self.submitColor.clicked.connect(self.onSubmitColor)

        self.pumpButton = QPushButton("Включить помпу" if self.currentData[-6] == 0 else "Выключить помпу")
        self.pumpButton.clicked.connect(self.onPumpButtonClick)

        self.windButton = QPushButton("Включить вентилятор" if self.currentData[-5] == 0 else "Выключить вентилятор")
        self.windButton.clicked.connect(self.onWindButtonClick)

        self.windowButton = QPushButton("Открыть окно" if self.currentData[-4] == 15 else "Закрыть окно")
        self.windowButton.clicked.connect(self.onWindowButtonClick)
        
        layout = QVBoxLayout()
        layout.addLayout(self.airLayout)
        layout.addLayout(self.soilLayout)
        layout.addLayout(self.otherLayout)
        layout.addWidget(self.color)
        layout.addWidget(self.submitColor)
        layout.addWidget(self.pumpButton)
        layout.addWidget(self.windButton)
        layout.addWidget(self.windowButton)

        container = QWidget()
        container.setLayout(layout)

        self.setWindowTitle("Умная теплица")

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.updateData)
        self.timer.start()

        self.setCentralWidget(container)

    def updateData(self):
        ser.write(bytearray([0xFF]))
        self.currentData = self.get_data()
        self.reloadSensors()

    def reloadSensors(self):
        self.temp.setText("Температура воздуха: " + str(self.currentData[3]) + "°C")
        self.humidity.setText("Влажность воздуха: " + str(self.currentData[4]) + "%")
        self.pressure.setText("Давление воздуха: " + str(self.currentData[5]) + "hPa")
        self.soiltemp.setText("Температура почвы: " + str(self.currentData[7]) + "°C")
        self.soilhumidity.setText("Влажость почвы: " + str(self.currentData[8]) + "%")
        self.light.setText("Интенсивность света: " + str(self.currentData[6]) + "Люкс")

    def onSubmitColor(self):
        _currentColor = self.color.currentColor()
        _writeRGB = bytearray([0xA3])
        self.reloadSensors()

        _writeRGB.append(_currentColor.red())
        _writeRGB.append(_currentColor.green())
        _writeRGB.append(_currentColor.blue())

        ser.write(_writeRGB)
        self.currentData = self.get_data()
        self.color.show()
        
    def onPumpButtonClick(self):
        ser.write(bytearray([0xA0, 0x1]))
        self.reloadSensors()
        self.currentData = self.get_data()
        self.pumpButton.setText("Включить помпу" if self.currentData[-6] == 0 else "Выключить помпу")

    def onWindButtonClick(self):
        ser.write(bytearray([0xA1, 0x1]))
        self.currentData = self.get_data()
        self.reloadSensors()
        self.windButton.setText("Включить вентилятор" if self.currentData[-5] == 0 else "Выключить вентилятор")

    def onWindowButtonClick(self):
        if (self.currentData[-4] == 15):
            ser.write(bytearray([0xA2, 0xAA]))
            self.windowButton.setText("Закрыть окно")
        else:
            ser.write(bytearray([0xA2, 0xF]))
            self.windowButton.setText("Открыть окно")

        self.currentData = self.get_data()

    def get_data (self):
        sleep(0.1)
        _currentData = str(ser.read_all())[2:-5]
        currentDataList = list(map(float, _currentData.split('|')))
        print(currentDataList)
        return currentDataList


app = QApplication(sys.argv)
window = MainWindow()

window.show()
sys.exit(app.exec())
