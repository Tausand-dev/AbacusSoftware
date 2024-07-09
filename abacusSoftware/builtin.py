import abacusSoftware.constants as constants
import abacusSoftware.common as common
# from abacusSoftware.supportWidgets import SamplingWidget
from abacusSoftware.files import File, G2_file
import pyAbacus as abacus
import datetime
import os
import time
import numpy as np
import pyqtgraph as pg
import pyqtgraph.exporters
from threading import Thread
from abacusSoftware.supportWidgets import ClickableLineEdit
from random import choice
import re
try:
    from PyQt5 import QtCore, QtGui, QtWidgets
    from PyQt5.QtWidgets import QLabel, QSpinBox, QComboBox, QSizePolicy, \
                            QVBoxLayout, QHBoxLayout, QFrame, \
                            QPushButton, QDialog, QGroupBox, QFormLayout, QMessageBox,\
                            QFileDialog
    from PyQt5.QtCore import QEvent
    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QTextBrowser
    from PyQt5.QtWidgets import QWhatsThis
    from PyQt5.QtGui import QPixmap
    from PyQt5.QtGui import QImage, QColor
    from PyQt5.QtGui import QPainter
    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QDialogButtonBox, QLabel

except ModuleNotFoundError:
    from PyQt4.QtGui import QLabel, QSpinBox, QComboBox, QSizePolicy


class SweepDialogBase(QDialog):
    def __init__(self, parent):
        super(SweepDialogBase, self).__init__(parent)
        self.resize(400, 500)

        self.parent = parent

        self.left_frame = QFrame()
        self.right_frame = QFrame()

        self.verticalLayout = QVBoxLayout(self.left_frame)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setSpacing(6)

        self.frame = QFrame()

        self.horizontalLayout = QHBoxLayout(self.frame)
        self.horizontalLayout.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout.setSpacing(6)

        

        
        #self.verticalLayout.addWidget(self.frame)

        self.groupBox = QGroupBox("Settings")

        self.formLayout = QFormLayout(self.groupBox)

        samplingLabel = QLabel("Sampling time:")
        coincidenceLabel = QLabel("Coincidence Window:")

        startLabel = QLabel("Start time (ns):")
        stopLabel = QLabel("Stop time (ns):")
        stepLabel = QLabel("Step size (ns):")
        nLabel = QLabel("Number of measurements per step:")

        self.samplingLabel = QLabel("")
        self.setSampling(0)
        self.coincidenceLabel = QLabel("")
        self.setCoincidence(self.parent.coincidence_spinBox.value())
        self.startSpin = QSpinBox()
        self.stopSpin = QSpinBox()
        self.stepSpin = QSpinBox()
        self.nSpin = QSpinBox()
        self.nSpin.setMinimum(1)

        self.startSpin.lineEdit().setReadOnly(True)
        self.stopSpin.lineEdit().setReadOnly(True)
        self.stepSpin.lineEdit().setReadOnly(True)

        self.samplingLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.coincidenceLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.startSpin.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.stopSpin.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.stepSpin.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.nSpin.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.startSpin.valueChanged.connect(self.handleStart)

        self.formLayout.addRow(samplingLabel, self.samplingLabel)
        self.formLayout.addRow(coincidenceLabel, self.coincidenceLabel)
        self.rowIndexOfCoincidenceLabel = self.formLayout.rowCount()
        self.formLayout.addRow(startLabel, self.startSpin)
        self.formLayout.addRow(stopLabel, self.stopSpin)
        self.formLayout.addRow(stepLabel, self.stepSpin)
        self.formLayout.addRow(nLabel, self.nSpin)

        self.verticalLayout.addWidget(self.groupBox)
        self.buttonsFrame = QFrame()
        self.verticalLayout.addWidget(self.buttonsFrame)
        
        self.HorLayout = QHBoxLayout(self.buttonsFrame)

        self.startStopButton = QPushButton("Start")
        self.saveButton = QPushButton("Save")
        self.savePlotsButton = QPushButton("Save Plots")
        self.startStopButton.setMaximumSize(QtCore.QSize(140, 60))
        self.saveButton.setMaximumSize(QtCore.QSize(140, 60))
        self.savePlotsButton.setMaximumSize(QtCore.QSize(140, 60))
        self.HorLayout.addWidget(self.saveButton)
        self.HorLayout.addWidget(self.savePlotsButton)
        self.HorLayout.addWidget(self.startStopButton)
        

        self.plot_win = pg.GraphicsLayoutWidget()
        self.plot = self.plot_win.addPlot(row=2, col=0)

        self.sideBySideFrame = QFrame()
        self.sideBySideLayout = QHBoxLayout(self.sideBySideFrame)
        self.sideBySideLayout.addWidget(self.left_frame)
        self.sideBySideLayout.addWidget(self.right_frame)

        self.verticalRightLayout = QVBoxLayout(self.right_frame)
        self.verticalRightLayout.addWidget(self.plot_win)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.frame)
        self.layout.addWidget(self.sideBySideFrame)

        symbolSize = 8
        self.plot_line = self.plot.plot(pen = "r", symbol='o', symbolPen = "r", symbolBrush="r", symbolSize=symbolSize)

        self.fileName = ""

        self.startStopButton.clicked.connect(self.startStop)

        self.x_data = []
        self.y_data = []

        self.completed = False

        self.timer = QtCore.QTimer()
        self.timer.setInterval(constants.CHECK_RATE)
        self.timer.timeout.connect(self.updatePlot)

        self.header = None

        self.error = None

        self.right_frame.setMinimumWidth(int(self.left_frame.width()*0.75)) #v1.6.0: cast to int

    def handleStart(self, value):
        self.stopSpin.setMinimum(value + abacus.constants.DELAY_STEP_VALUE)

    def warning(self, error):
        error_text = str(error)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(error_text)
        msg.setWindowTitle("Warning")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        return msg.exec_()

    def enableWidgets(self, enable):
        self.startSpin.setEnabled(enable)
        self.stopSpin.setEnabled(enable)
        self.stepSpin.setEnabled(enable)
        self.nSpin.setEnabled(enable)
        try:
            self.comboBox.setEnabled(enable)
        except:
            pass

    def updatePlot(self):
        self.plot_line.setData(self.x_data, self.y_data)
        if self.error != None:
            self.parent.errorWindow(self.error)
            self.error = None

        if self.completed:
            if self.fileName != "":
                file = File(self.fileName, self.header)
                data = np.vstack((self.x_data, self.y_data)).T
                file.npwrite(data, "%d" + constants.DELIMITER + "%d")

            self.x_data = []
            self.y_data = []
            self.timer.stop()
            self.completed = False
            self.startStopButton.setText("Start")
            self.startStopButton.setStyleSheet("background-color: none")
            self.enableWidgets(True)
            self.parent.check_timer.start()

    def cleanPlot(self):
        self.x_data = []
        self.y_data = []
        self.plot_line.setData(self.x_data, self.y_data)

#To do: Delete this block of code
    # def chooseFile(self):
    #     try:
    #         directory = constants.directory_lineEdit
    #     except:
    #         directory = os.path.expanduser("~")

    #     dlg = QFileDialog(directory = directory)
    #     dlg.setAcceptMode(QFileDialog.AcceptSave)
    #     dlg.setFileMode(QFileDialog.AnyFile)
    #     nameFilters = [constants.SUPPORTED_EXTENSIONS[extension] for extension in constants.SUPPORTED_EXTENSIONS]
    #     dlg.setNameFilters(nameFilters)
    #     dlg.selectNameFilter(constants.SUPPORTED_EXTENSIONS[constants.EXTENSION_DATA])
    #     if dlg.exec_():
    #         name = dlg.selectedFiles()[0]
    #         self.fileName = common.unicodePath(name)
    #         self.lineEdit.setText(self.fileName)

    def stopAcquisition(self):
        e = Exception("Data acquisition is active, in order to make the sweep it will be turned off.")
        ans = self.warning(e)
        if ans == QMessageBox.Ok:
            ans = True
        else: ans = False
        if ans: self.parent.startAcquisition()
        return ans

    def setSampling(self, val):
        self.samplingLabel.setText("%d (ms)"%val)

    def setCoincidence(self, val):
        self.coincidenceLabel.setText("%d ns"%val)

    def setDarkTheme(self):
        self.plot_win.setBackground((42, 42, 42))
        whitePen = pg.mkPen(color=(255, 255, 255))
        self.plot.getAxis('bottom').setPen(whitePen)
        self.plot.getAxis('left').setPen(whitePen)
        self.plot.getAxis('bottom').setTextPen(whitePen)
        self.plot.getAxis('left').setTextPen(whitePen)

    def setLightTheme(self):
        self.plot_win.setBackground(None)
        blackPen = pg.mkPen(color=(0, 0, 0))
        self.plot.getAxis('bottom').setPen(blackPen)
        self.plot.getAxis('left').setPen(blackPen)
        self.plot.getAxis('bottom').setTextPen(blackPen)
        self.plot.getAxis('left').setTextPen(blackPen)



class DelayDialog(SweepDialogBase):
    def __init__(self, parent):
        super(DelayDialog, self).__init__(parent)
        self.setWindowTitle("Delay time sweep")
        self.g2constant=True
        self.comboBox1 = QComboBox()
        self.comboBox2 = QComboBox()
        self.savePlotsButton.clicked.connect(self.save_plotDelay)
        self.number_channels = 0

        self.comboBox1.setEditable(True)
        self.comboBox2.setEditable(True)
        self.comboBox1.lineEdit().setReadOnly(True)
        self.comboBox2.lineEdit().setReadOnly(True)
        self.comboBox1.lineEdit().setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.comboBox2.lineEdit().setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.comboBox1.currentIndexChanged.connect(self.channelsChange)
        self.comboBox2.currentIndexChanged.connect(self.channelsChange)

        self.formLayout.insertRow(0, QLabel("Channel 2:"), self.comboBox2)
        self.formLayout.insertRow(0, QLabel("Channel 1:"), self.comboBox1)
        self.rowIndexOfCoincidenceLabel += 2 

        self.startSpin.setMinimum(-abacus.constants.DELAY_MAXIMUM_VALUE)
        self.startSpin.setMaximum(abacus.constants.DELAY_MAXIMUM_VALUE - abacus.constants.DELAY_STEP_VALUE)
        self.startSpin.setSingleStep(abacus.constants.DELAY_STEP_VALUE)
        self.startSpin.setValue(-abacus.constants.DELAY_MAXIMUM_VALUE)

        self.stopSpin.setMinimum(-abacus.constants.DELAY_MAXIMUM_VALUE)
        self.stopSpin.setMaximum(abacus.constants.DELAY_MAXIMUM_VALUE)
        self.stopSpin.setSingleStep(abacus.constants.DELAY_STEP_VALUE)
        self.stopSpin.setValue(abacus.constants.DELAY_MAXIMUM_VALUE)
        self.saveButton.clicked.connect(self.save_file)
        self.saveButton.setEnabled(False)
        self.savePlotsButton.setEnabled(False)
        self.aftermeasure=False
        
        
        self.stepSpin.setMinimum(abacus.constants.DELAY_STEP_VALUE)
        self.stepSpin.setMaximum(((abacus.constants.DELAY_MAXIMUM_VALUE - abacus.constants.DELAY_MINIMUM_VALUE) // abacus.constants.DELAY_STEP_VALUE) * abacus.constants.DELAY_STEP_VALUE)
        self.stepSpin.setSingleStep(abacus.constants.DELAY_STEP_VALUE)
        self.stepSpin.setValue(abacus.constants.DELAY_STEP_VALUE) #new on v1.4.0 (2020-06-30)

        self.y_datach1 = []
        self.y_datach2 = []
        
        self.plot_singles = self.plot_win.addPlot(row=0, col=0)
        self.plot_channel2 = self.plot_win.addPlot(row=1, col=0)
        symbolSize = 5
        self.plot_line1 = self.plot_singles.plot(pen = "r", symbol='o', symbolPen = "r", symbolBrush="r", symbolSize=symbolSize)
        self.plot_line2 = self.plot_channel2.plot(pen = "r", symbol='o', symbolPen = "r", symbolBrush="r", symbolSize=symbolSize)

        self.setNumberChannels(4)

        self.setTabOrder(self.comboBox1, self.comboBox2)
        self.setTabOrder(self.comboBox2, self.startSpin)
        self.setTabOrder(self.startSpin, self.stopSpin)
        self.setTabOrder(self.stopSpin, self.stepSpin)
        self.setTabOrder(self.stepSpin, self.nSpin)
        self.setTabOrder(self.nSpin, self.startStopButton)
        #self.setTabOrder(self.startStopButton, self.lineEdit)

    def channelsChange(self, index):
        i1 = self.comboBox1.currentIndex()
        i2 = self.comboBox2.currentIndex()
        if(i1 == i2):
            self.comboBox2.setCurrentIndex((i1 + 1) % self.number_channels)
        if not self.aftermeasure:

            channel1 = self.comboBox1.currentText()
            channel2 = self.comboBox2.currentText()

            self.plot_singles.setLabel('left', "Counts " + channel1)
            self.plot_singles.setLabel('bottom', "Delay time", units='ns')

            self.plot_channel2.setLabel('left', "Counts " + channel2)
            self.plot_channel2.setLabel('bottom', 'Delay time', units='ns')

            if channel2 > channel1:
                channel12 = channel1+channel2
            else:
                channel12 = channel2+channel1

            self.plot.setLabel('left', "Coincidences " + channel12)
            self.plot.setLabel('bottom', "Delay time", units='ns')

    def createComboBox(self):
        self.comboBox2 = QComboBox()
        self.comboBox2.setEditable(True)
        self.comboBox2.lineEdit().setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.comboBox2.lineEdit().setReadOnly(True)

        self.comboBox1.currentIndexChanged.connect(self.channelsChange)

    def startStop(self):
        if self.startStopButton.text() == "Stop":
            self.comboBox1.setEnabled(True)
            self.comboBox2.setEnabled(True)
            self.aftermeasure=True
            self.timer.stop()
            self.completed = True
            self.updatePlot()
            self.completed = True
            self.saveButton.setEnabled(True)
            self.savePlotsButton.setEnabled(True)

        else:
            self.aftermeasure=False
            self.channelsChange(0)
            self.comboBox1.setEnabled(False)
            self.comboBox2.setEnabled(False)
            self.saveButton.setEnabled(False)
            self.savePlotsButton.setEnabled(False)
            self.x_data = []
            self.y_data = []
            self.y_datach1 = []
            self.y_datach2= []
            step = self.stepSpin.value()
            n = self.nSpin.value()
            range_ = np.arange(self.startSpin.value(), self.stopSpin.value() + 1, step)
            range_ = range_[range_ <= abacus.constants.DELAY_MAXIMUM_VALUE]

            if self.parent.port_name != None:
                if self.parent.streaming:
                    if self.stopAcquisition():
                        self.run(n, range_)
                else:
                    self.run(n, range_)
            else:
                self.parent.connect()
                if self.parent.port_name != None:
                    if self.parent.streaming:
                        if self.stopAcquisition():
                            self.run(n, range_)
                    else:
                        self.run(n, range_)

    def updatePlot(self):
        if constants.IS_LIGHT_THEME: 
            colors_symbols = self.parent.light_colors_in_use
            predefined_colors = constants.COLORS
            nColors = len(constants.COLORS)
        else: 
            colors_symbols = self.parent.dark_colors_in_use
            predefined_colors = constants.DARK_COLORS
            nColors = len(constants.DARK_COLORS)

        nSymbols = len(constants.SYMBOLS)

        channel1 = self.comboBox1.currentText()
        channel2 = self.comboBox2.currentText()
        if channel2 > channel1:
            channel12 = channel1+channel2
        else:
            channel12 = channel2+channel1

        color1, symbol1 = self.parent.chooseChannelColorAndSymbol(channel1, predefined_colors, colors_symbols, constants.SYMBOLS)
        color2, symbol2 = self.parent.chooseChannelColorAndSymbol(channel2, predefined_colors, colors_symbols, constants.SYMBOLS)
        color, symbol = self.parent.chooseChannelColorAndSymbol(channel12, predefined_colors, colors_symbols, constants.SYMBOLS)

        symbolSize = self.parent.symbolSize
        linewidth = self.parent.linewidth
        
        self.plot_line1.opts['pen'] = pg.mkPen(color1, width=linewidth)
        self.plot_line1.opts['symbol'] = symbol1
        self.plot_line1.opts['symbolPen'] = color1
        self.plot_line1.opts['symbolBrush'] = color1
        self.plot_line1.opts['symbolSize'] = symbolSize

        self.plot_line2.opts['pen'] = pg.mkPen(color2, width=linewidth)
        self.plot_line2.opts['symbol'] = symbol2
        self.plot_line2.opts['symbolPen'] = color2
        self.plot_line2.opts['symbolBrush'] = color2
        self.plot_line2.opts['symbolSize'] = symbolSize

        self.plot_line.opts['pen'] = pg.mkPen(color, width=linewidth)
        self.plot_line.opts['symbol'] = symbol
        self.plot_line.opts['symbolPen'] = color
        self.plot_line.opts['symbolBrush'] = color
        self.plot_line.opts['symbolSize'] = symbolSize

        self.plot_line.setData(self.x_data, self.y_data)
        
        self.plot_line1.setData(self.x_data, self.y_datach1)
        self.plot_line2.setData(self.x_data, self.y_datach2)

        if self.error != None:
            self.parent.errorWindow(self.error)
            self.error = None

        if self.completed:
            self.saveButton.setEnabled(True)
            self.savePlotsButton.setEnabled(True)
            self.timer.stop()
            self.completed = False
            self.startStopButton.setText("Start")
            self.startStopButton.setStyleSheet("background-color: none")
            self.enableWidgets(True)
            self.parent.check_timer.start()
    def save_plotDelay(self):
        try:
        
            try:
                directory = constants.directory_lineEdit
            except:
                directory = os.path.expanduser("~")
            dlg = QFileDialog(directory=directory)
            dlg.setAcceptMode(QFileDialog.AcceptSave)
            dlg.setFileMode(QFileDialog.AnyFile)
            nameFilters = ['JPEG Image (*.jpg)', 'PNG Image (*.png)']
            dlg.setNameFilters(nameFilters)
            if dlg.exec_():
                name = dlg.selectedFiles()[0]
                fileName = common.unicodePath(name)
                exporter1 = pg.exporters.ImageExporter(self.plot_win.scene())
                exporter1.parameters()['width'] = 1000
                exporter1.parameters()['height'] = 800
                temp_image = exporter1.export(toBytes=True)
                width, height = 1000, 800
                white_background = QImage(width, height, QImage.Format_RGB32)
                white_background.fill(QColor('white'))
                painter = QPainter(white_background)
                painter.drawImage(0, 0, temp_image)
                painter.end()
                white_background.save(fileName)
                message_box = QMessageBox(self)
                message_box.setIcon(QMessageBox.Information)
                textmessage="The plot have been saved successfully in "+"\n\n"+ fileName
                message_box.setText(textmessage)
                message_box.setWindowTitle("Successful save")
                message_box.setStandardButtons(QMessageBox.Ok)
                message_box.exec_()
                    
        except:
            message_box = QMessageBox(self.parent)
            message_box.setIcon(QMessageBox.Critical)
            message_box.setText("The plots could not be saved.")
            message_box.setWindowTitle("Error saving")
            message_box.setStandardButtons(QMessageBox.Ok)
            message_box.exec_()
    
    def save_file(self):
        # if self.saveg2sentinel==0:
        
        try:
            try:
                directory = constants.directory_lineEdit
            except:
                directory = os.path.expanduser("~")

            dlg = QFileDialog(directory=directory)
            dlg.setAcceptMode(QFileDialog.AcceptSave)
            dlg.setFileMode(QFileDialog.AnyFile)
            nameFilters = ['Data Files (*.dat)','CSV Files (*.csv)','Text Files (*.txt)','All Files (*)']
            dlg.setNameFilters(nameFilters)
            if dlg.exec_():
                name = dlg.selectedFiles()[0]
                fileName = common.unicodePath(name)
                new_header=self.header.split(',')
                sampling_time="Sampling time: "+str(self.parent.sampling_widget.getValue())+"ms"
                coincidence="Coincidence window: "+str(self.parent.coincidence_spinBox.value())+"ns"
                StartInit= "Min delay: "+str(self.startSpin.value())+"ns"
                StopInit= "Max delay: "+str(self.stopSpin.value())+"ns"
                parameters_list=[sampling_time,coincidence,StartInit,StopInit]
                self.x_data = [ int(x) for x in self.x_data ]
                self.y_datach1 = [ int(x) for x in self.y_datach1 ]
                self.y_datach2 = [ int(x) for x in self.y_datach2 ]
                self.y_data = [ int(x) for x in self.y_data ]
                data = np.vstack((self.x_data, self.y_datach1, self.y_datach2, self.y_data)).T
                g2fileclass=G2_file(fileName,data,new_header,parameters_list)
                g2fileclass.writefile()
                message_box = QMessageBox(self)
                message_box.setIcon(QMessageBox.Information)
                textmessage="The data has been saved successfully in "+"\n\n"+ fileName
                message_box.setText(textmessage)
                message_box.setWindowTitle("Successful save")
                message_box.setStandardButtons(QMessageBox.Ok)
                message_box.exec_()
                self.saveg2sentinel=1
                self.saveg2route=fileName
        except:
            message_box = QMessageBox(self.parent)
            message_box.setIcon(QMessageBox.Critical)
            message_box.setText("The data could not be saved.")
            message_box.setWindowTitle("Error saving")
            message_box.setStandardButtons(QMessageBox.Ok)
            message_box.exec_()
    
    
    
    

    def cleanPlot(self):
        self.x_data = []
        self.y_data = []
        self.y_datach1 = []
        self.y_datach2= []
        self.plot_line.setData(self.x_data, self.y_data)
        
        self.plot_line1.setData(self.x_data, self.y_datach1)
        self.plot_line2.setData(self.x_data, self.y_datach2)

    def run(self, n, range_):
        self.cleanPlot()
        self.completed = False
        self.startStopButton.setText("Stop")
        self.startStopButton.setStyleSheet("background-color: green")
        self.enableWidgets(False)

        channel1 = self.comboBox1.currentText()
        channel2 = self.comboBox2.currentText()
        if channel2 > channel1:
            channel12 = channel1+channel2
        else:
            channel12 = channel2+channel1

        self.header = "Delay time (ns)" + constants.DELIMITER + "Counts " + channel1 + constants.DELIMITER \
           + "Counts " + channel2 + constants.DELIMITER + "Coincidences " + channel12

        self.parent.check_timer.stop()
        thread = Thread(target = self.heavyDuty, args = (n, range_))
        thread.daemon = True
        self.timer.start()
        thread.start()

    def heavyDuty(self, n, range_):
        port = self.parent.port_name
        channel1 = self.comboBox1.currentText()
        channel2 = self.comboBox2.currentText()
        if channel2 > channel1:
            channel12 = channel1+channel2
        else:
            channel12 = channel2+channel1
        if port != None:
            try:
                for delay in range_:
                    value = 0
                    valuech1 = 0 #(new sept-15-2021)
                    valuech2 = 0 #(new sept-15-2021)
                    last_id = 0
                    if delay > 0:
                        delay1 = 0
                        delay2 = delay
                    else:
                        delay1 = abs(delay)
                        delay2 = 0
                    delay1_ = -1
                    delay2_ = -1
                    for j in range(constants.NUMBER_OF_TRIES):
                        abacus.setSetting(port, "delay_%s" % channel1, delay1)
                        abacus.setSetting(port, "delay_%s" % channel2, delay2)
                        time.sleep(1e-3)
                        try:
                            delay1_ = abacus.getSetting(port, "delay_%s" % channel1)
                            delay2_ = abacus.getSetting(port, "delay_%s" % channel2)
                            if ((delay1 != delay1_) and (delay2 != delay2_)): break
                        except abacus.BaseError as e:
                            time.sleep(1e-2)
                            if j == (constants.NUMBER_OF_TRIES - 1): raise(e)

                    time.sleep(self.parent.sampling_widget.getValue() / 1000)

                    for i in range(n):
                        for j in range(constants.NUMBER_OF_TRIES):
                            if self.completed: return
                            try:
                                counters, id = abacus.getFollowingCounters(port, [channel12, channel1, channel2])
                                if (id != last_id) and (id != 0):
                                    value += counters.getValue(channel12)
                                    valuech1 += counters.getValue(channel1) #(new sept-15-2021)
                                    valuech2 += counters.getValue(channel2) #(new sept-15-2021)
                                    last_id = id
                                    break
                                else:
                                    time_left = abacus.getTimeLeft(port) / 1000 # seconds
                                    time.sleep(time_left)

                            except abacus.BaseError as e:
                                if j == (constants.NUMBER_OF_TRIES - 1): raise(e)

                    self.x_data.append(delay)
                    self.y_data.append(value / n)
                    self.y_datach1.append(valuech1 / n) #(new sept-15-2021)
                    self.y_datach2.append(valuech2 / n) #(new sept-15-2021)
                self.completed = True
            except Exception as e:
                self.completed = True
                self.error = e

    def setNumberChannels(self, number_channels):
        self.number_channels = number_channels
        self.comboBox1.blockSignals(True)
        self.comboBox2.blockSignals(True)
        self.comboBox1.clear()
        self.comboBox2.clear()
        self.comboBox1.addItems([chr(i + ord('A')) for i in range(number_channels)])
        self.comboBox2.addItems([chr(i + ord('A')) for i in range(number_channels)])

        self.comboBox2.setCurrentIndex(1)

        self.comboBox1.blockSignals(False)
        self.comboBox2.blockSignals(False)

        channel1 = self.comboBox1.currentText()
        channel2 = self.comboBox2.currentText()
        
        

        self.plot_singles.setLabel('left', "Counts " + channel1)
        self.plot_singles.setLabel('bottom', "Delay time", units='ns')

        self.plot_channel2.setLabel('left', "Counts " + channel2)
        self.plot_channel2.setLabel('bottom', 'Delay time', units='ns')

        if channel2 > channel1:
            channel12 = channel1+channel2
        else:
            channel12 = channel2+channel1
        self.plot.setLabel('left', "Coincidences " + channel12)
        self.plot.setLabel('bottom', "Delay time", units='ns')

    def updateConstants(self): #new on v1.4.0 (2020-06-30)
        try:
            self.startSpin.setMinimum(-abacus.constants.DELAY_MAXIMUM_VALUE)
            self.startSpin.setMaximum(abacus.constants.DELAY_MAXIMUM_VALUE - abacus.constants.DELAY_STEP_VALUE)
            self.startSpin.setSingleStep(abacus.constants.DELAY_STEP_VALUE)
            self.startSpin.setValue(-abacus.constants.DELAY_MAXIMUM_VALUE)

            self.stopSpin.setMinimum(-abacus.constants.DELAY_MAXIMUM_VALUE)
            self.stopSpin.setMaximum(abacus.constants.DELAY_MAXIMUM_VALUE)
            self.stopSpin.setSingleStep(abacus.constants.DELAY_STEP_VALUE)
            self.stopSpin.setValue(abacus.constants.DELAY_MAXIMUM_VALUE)

            self.stepSpin.setMinimum(abacus.constants.DELAY_STEP_VALUE)
            self.stepSpin.setMaximum(((abacus.constants.DELAY_MAXIMUM_VALUE - abacus.constants.DELAY_MINIMUM_VALUE) // abacus.constants.DELAY_STEP_VALUE) * abacus.constants.DELAY_STEP_VALUE)
            self.stepSpin.setSingleStep(abacus.constants.DELAY_STEP_VALUE)
            self.stepSpin.setValue(abacus.constants.DELAY_STEP_VALUE)
        except AttributeError as e:
            if abacus.constants.DEBUG: print(e)

    def setDarkTheme(self):
        self.plot_win.setBackground((42, 42, 42))
        whitePen = pg.mkPen(color=(255, 255, 255))
        self.plot.getAxis('bottom').setPen(whitePen)
        self.plot.getAxis('left').setPen(whitePen)
        self.plot.getAxis('bottom').setTextPen(whitePen)
        self.plot.getAxis('left').setTextPen(whitePen)
        

        self.plot_singles.getAxis('bottom').setPen(whitePen)
        self.plot_singles.getAxis('left').setPen(whitePen)
        self.plot_singles.getAxis('bottom').setTextPen(whitePen)
        self.plot_singles.getAxis('left').setTextPen(whitePen)

        self.plot_channel2.getAxis('bottom').setPen(whitePen)
        self.plot_channel2.getAxis('left').setPen(whitePen)
        self.plot_channel2.getAxis('bottom').setTextPen(whitePen)
        self.plot_channel2.getAxis('left').setTextPen(whitePen)

    def setLightTheme(self):
        self.plot_win.setBackground(None)
        blackPen = pg.mkPen(color=(0, 0, 0))
        self.plot.getAxis('bottom').setPen(blackPen)
        self.plot.getAxis('left').setPen(blackPen)
        self.plot.getAxis('bottom').setTextPen(blackPen)
        self.plot.getAxis('left').setTextPen(blackPen)
        

        self.plot_singles.getAxis('bottom').setPen(blackPen)
        self.plot_singles.getAxis('left').setPen(blackPen)
        self.plot_singles.getAxis('bottom').setTextPen(blackPen)
        self.plot_singles.getAxis('left').setTextPen(blackPen)

        self.plot_channel2.getAxis('bottom').setPen(blackPen)
        self.plot_channel2.getAxis('left').setPen(blackPen)
        self.plot_channel2.getAxis('bottom').setTextPen(blackPen)
        self.plot_channel2.getAxis('left').setTextPen(blackPen)
        
#g2 function calculate


class G2Dialog(SweepDialogBase):
    def __init__(self, parent):
        super(G2Dialog, self).__init__(parent)
        self.setWindowTitle("g(2) Function")
        self.oldValuesSentinel=0
        self.g2constant=True
        self.comboBox1 = QComboBox()
        self.comboBox2 = QComboBox()
        self.saveg2sentinel=0
        self.saveg2route=""

        self.number_channels = 0

        self.comboBox1.setEditable(True)
        self.comboBox2.setEditable(True)
        self.comboBox1.lineEdit().setReadOnly(True)
        self.comboBox2.lineEdit().setReadOnly(True)
        self.comboBox1.lineEdit().setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.comboBox2.lineEdit().setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.comboBox1.currentIndexChanged.connect(self.channelsChange)
        self.comboBox2.currentIndexChanged.connect(self.channelsChange)

        self.formLayout.insertRow(0, QLabel("Channel 2:"), self.comboBox2)
        self.formLayout.insertRow(0, QLabel("Channel 1:"), self.comboBox1)
        self.rowIndexOfCoincidenceLabel += 2 

        self.startSpin.setMinimum(-abacus.constants.DELAY_MAXIMUM_VALUE)
        self.startSpin.setMaximum(abacus.constants.DELAY_MAXIMUM_VALUE - abacus.constants.DELAY_STEP_VALUE)
        self.startSpin.setSingleStep(abacus.constants.DELAY_STEP_VALUE)
        self.startSpin.setValue(-abacus.constants.DELAY_MAXIMUM_VALUE)
        
        

        self.stopSpin.setMinimum(-abacus.constants.DELAY_MAXIMUM_VALUE)
        self.stopSpin.setMaximum(abacus.constants.DELAY_MAXIMUM_VALUE)
        self.stopSpin.setSingleStep(abacus.constants.DELAY_STEP_VALUE)
        self.stopSpin.setValue(abacus.constants.DELAY_MAXIMUM_VALUE)
        

        self.stepSpin.setMinimum(abacus.constants.DELAY_STEP_VALUE)
        self.stepSpin.setMaximum(((abacus.constants.DELAY_MAXIMUM_VALUE - abacus.constants.DELAY_MINIMUM_VALUE) // abacus.constants.DELAY_STEP_VALUE) * abacus.constants.DELAY_STEP_VALUE)
        self.stepSpin.setSingleStep(abacus.constants.DELAY_STEP_VALUE)
        self.stepSpin.setValue(abacus.constants.DELAY_STEP_VALUE) #new on v1.4.0 (2020-06-30)
        self.stepSpin.lineEdit().setReadOnly(True)
        self.savePlotsButton.clicked.connect(self.save_plotg2)
        self.saveButton.setEnabled(False)
        self.savePlotsButton.setEnabled(False)
        self.aftermeasure=False
        
        #defined the total integration time to calculate the g(2)
        #set default value in 0
        self.totalTime=0
        self.dt_w=0
        self.mulConst=0
        # set the coincide time in ns
        self.coincideWindow=self.parent.coincidence_spinBox.value()

        self.y_datach1 = []
        self.y_datach2 = []
        self.g2data = []
        self.saveButton.clicked.connect(self.save_file)
        
        # self.plot_singles = self.plot_win.addPlot(row=0, col=0)
        # self.plot_channel2 = self.plot_win.addPlot(row=1, col=0)
        # symbolSize = 5
        # self.plot_line1 = self.plot_singles.plot(pen = "r", symbol='o', symbolPen = "r", symbolBrush="r", symbolSize=symbolSize)
        # self.plot_line2 = self.plot_channel2.plot(pen = "r", symbol='o', symbolPen = "r", symbolBrush="r", symbolSize=symbolSize)

        self.setNumberChannels(4)

        self.setTabOrder(self.comboBox1, self.comboBox2)
        self.setTabOrder(self.comboBox2, self.startSpin)
        self.setTabOrder(self.startSpin, self.stopSpin)
        self.setTabOrder(self.stopSpin, self.stepSpin)
        self.setTabOrder(self.stepSpin, self.nSpin)
        self.setTabOrder(self.nSpin, self.startStopButton)
        #self.setTabOrder(self.startStopButton, self.lineEdit)

    def channelsChange(self, index):
        i1 = self.comboBox1.currentIndex()
        i2 = self.comboBox2.currentIndex()
        if(i1 == i2):
                self.comboBox2.setCurrentIndex((i1 + 1) % self.number_channels)
        if not self.aftermeasure:
            channel1 = self.comboBox1.currentText()
            channel2 = self.comboBox2.currentText()

            # self.plot_singles.setLabel('left', "Counts " + channel1)
            # self.plot_singles.setLabel('bottom', "Delay time", units='ns')

            # self.plot_channel2.setLabel('left', "Counts " + channel2)
            # self.plot_channel2.setLabel('bottom', 'Delay time', units='ns')

            if channel2 > channel1:
                channel12 = channel1+channel2
            else:
                channel12 = channel2+channel1

            self.plot.setLabel('left', "g(2) " + channel12)
            self.plot.setLabel('bottom', "Delay time ", units='ns')
    def save_file(self):
        # if self.saveg2sentinel==0:
        
        try:
            try:
                directory = constants.directory_lineEdit
            except:
                directory = os.path.expanduser("~")

            dlg = QFileDialog(directory=directory)
            dlg.setAcceptMode(QFileDialog.AcceptSave)
            dlg.setFileMode(QFileDialog.AnyFile)
            nameFilters = ['Data Files (*.dat)','CSV Files (*.csv)','Text Files (*.txt)','All Files (*)']
            dlg.setNameFilters(nameFilters)
            if dlg.exec_():
                name = dlg.selectedFiles()[0]
                fileName = common.unicodePath(name)
                new_header=self.header.split(',')
                new_header.append("g2 Data")
                sampling_time="Sampling time: "+str(self.parent.sampling_widget.getValue())+"ms"
                coincidence="Coincidence window: "+str(self.parent.coincidence_spinBox.value())+"ns"
                StartInit= "Min delay: "+str(self.startSpin.value())+"ns"
                StopInit= "Max delay: "+str(self.stopSpin.value())+"ns"
                parameters_list=[sampling_time,coincidence,StartInit,StopInit]
                self.x_data = [ int(x) for x in self.x_data ]
                self.y_datach1 = [ int(x) for x in self.y_datach1 ]
                self.y_datach2 = [ int(x) for x in self.y_datach2 ]
                self.y_data = [ int(x) for x in self.y_data ]
                data = np.vstack((self.x_data, self.y_datach1, self.y_datach2, self.y_data,self.g2data)).T
                g2fileclass=G2_file(fileName,data,new_header,parameters_list)
                g2fileclass.writefile()
                message_box = QMessageBox(self)
                message_box.setIcon(QMessageBox.Information)
                textmessage="The data has been saved successfully in "+"\n\n"+ fileName
                message_box.setText(textmessage)
                message_box.setWindowTitle("Successful save")
                message_box.setStandardButtons(QMessageBox.Ok)
                message_box.exec_()
                self.saveg2sentinel=1
                self.saveg2route=fileName
        except:
            message_box = QMessageBox(self.parent)
            message_box.setIcon(QMessageBox.Critical)
            message_box.setText("The data could not be saved.")
            message_box.setWindowTitle("Error saving")
            message_box.setStandardButtons(QMessageBox.Ok)
            message_box.exec_()
        # else:
        #     message_box = QMessageBox(self)
        #     message_box.setIcon(QMessageBox.Information)
        #     textmessage="The data has already been saved successfully in "+"\n\n"+ self.saveg2route
        #     message_box.setText(textmessage)
        #     message_box.setWindowTitle("Successful save")
        #     message_box.setStandardButtons(QMessageBox.Ok)
        #     message_box.exec_()
            
        
    
    def save_plotg2(self):
        # try:
        try:
            directory = constants.directory_lineEdit
        except:
            directory = os.path.expanduser("~")

        dlg = QFileDialog(directory=directory)
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        dlg.setFileMode(QFileDialog.AnyFile)
        nameFilters = ['JPEG Image (*.jpg)', 'PNG Image (*.png)']
        dlg.setNameFilters(nameFilters)
        if dlg.exec_():
            name = dlg.selectedFiles()[0]
            fileName = common.unicodePath(name)
            exporter1 = pg.exporters.ImageExporter(self.plot_win.scene())
            exporter1.parameters()['width'] = 780
            exporter1.parameters()['height'] = 700
            temp_image = exporter1.export(toBytes=True)
            width, height = 780, 700
            white_background = QImage(width, height, QImage.Format_RGB32)
            white_background.fill(QColor('white'))
            painter = QPainter(white_background)
            painter.drawImage(0, 0, temp_image)
            painter.end()
            white_background.save(fileName)
            message_box = QMessageBox(self)
            message_box.setIcon(QMessageBox.Information)
            textmessage="The plot have been saved successfully in "+"\n\n"+ fileName
            message_box.setText(textmessage)
            message_box.setWindowTitle("Successful save")
            message_box.setStandardButtons(QMessageBox.Ok)
            message_box.exec_()
        # except:
        #     message_box = QMessageBox(self.parent)
        #     message_box.setIcon(QMessageBox.Critical)
        #     message_box.setText("The plots could not be saved.")
        #     message_box.setWindowTitle("Error saving")
        #     message_box.setStandardButtons(QMessageBox.Ok)
        #     message_box.exec_()
            
        
        
        
        

    def createComboBox(self):
        self.comboBox2 = QComboBox()
        self.comboBox2.setEditable(True)
        self.comboBox2.lineEdit().setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.comboBox2.lineEdit().setReadOnly(True)

        self.comboBox1.currentIndexChanged.connect(self.channelsChange)

    def startStop(self):
        if self.startStopButton.text() == "Stop":
            self.comboBox1.setEnabled(True)
            self.comboBox2.setEnabled(True)
            self.saveButton.setEnabled(True)
            self.savePlotsButton.setEnabled(True)
            self.timer.stop()
            self.aftermeasure=True
            self.completed = True
            self.updatePlot()
            self.completed = True
            self.stopSpin.setEnabled(False)
            self.startSpin.setEnabled(False)
            self.stepSpin.setEnabled(False)
            self.nSpin.setEnabled(False)

        else:
            self.comboBox1.setEnabled(False)
            self.comboBox2.setEnabled(False)
            self.aftermeasure=False
            self.channelsChange(0)
            self.saveButton.setEnabled(False)
            self.savePlotsButton.setEnabled(False)
            self.x_data = []
            self.y_data = []
            self.y_datach1 = []
            self.y_datach2= []
            self.g2data = []
            self.saveg2sentinel=0
            self.saveg2route=""
            self.default_values()
            step = self.stepSpin.value()
            n = self.nSpin.value()
            range_ = np.arange(self.startSpin.value(), self.stopSpin.value() + 1, step)
            range_= self.reorder_array(range_)
            range_ = range_[range_ <= abacus.constants.DELAY_MAXIMUM_VALUE]
            

            #the value is given in ms
            self.totalTime=self.parent.sampling_widget.getValue()
            #the value in s
            self.totalTime=self.totalTime/1000
            #Coincidence window in ns                        
            coincidence_res=self.coincideWindow/(10**9)
            self.dt_w=2*(coincidence_res+(coincidence_res/2))
            self.mulConst=self.totalTime/self.dt_w

            if self.parent.port_name != None:
                if self.parent.streaming:
                    if self.stopAcquisition():
                        self.run(n, range_)
                else:
                    self.run(n, range_)
            else:
                self.parent.connect()
                if self.parent.port_name != None:
                    if self.parent.streaming:
                        if self.stopAcquisition():
                            self.run(n, range_)
                    else:
                        self.run(n, range_)

    def updatePlot(self):
        if constants.IS_LIGHT_THEME: 
            colors_symbols = self.parent.light_colors_in_use
            predefined_colors = constants.COLORS
            nColors = len(constants.COLORS)
        else: 
            colors_symbols = self.parent.dark_colors_in_use
            predefined_colors = constants.DARK_COLORS
            nColors = len(constants.DARK_COLORS)

        nSymbols = len(constants.SYMBOLS)

        channel1 = self.comboBox1.currentText()
        channel2 = self.comboBox2.currentText()
        if channel2 > channel1:
            channel12 = channel1+channel2
        else:
            channel12 = channel2+channel1

        color1, symbol1 = self.parent.chooseChannelColorAndSymbol(channel1, predefined_colors, colors_symbols, constants.SYMBOLS)
        color2, symbol2 = self.parent.chooseChannelColorAndSymbol(channel2, predefined_colors, colors_symbols, constants.SYMBOLS)
        color, symbol = self.parent.chooseChannelColorAndSymbol(channel12, predefined_colors, colors_symbols, constants.SYMBOLS)

        symbolSize = self.parent.symbolSize
        linewidth = self.parent.linewidth
        

        self.plot_line.opts['pen'] = pg.mkPen(color, width=linewidth)
        self.plot_line.opts['symbol'] = symbol
        self.plot_line.opts['symbolPen'] = color
        self.plot_line.opts['symbolBrush'] = color
        self.plot_line.opts['symbolSize'] = symbolSize

        
        if len(self.y_data)>0:
            paired = list(zip(self.x_data, self.y_data))
            paired_sorted = sorted(paired)
            x_sorted, y_sorted = zip(*paired_sorted)
            self.y_data = list(y_sorted)
        
        
        if len(self.x_data)>0:
            pairedg2 = list(zip(self.x_data, self.g2data))
            paired_sortedg2 = sorted(pairedg2)
            x_sortedg2, y_sortedg2 = zip(*paired_sortedg2)
            self.x_data = list(x_sortedg2)
            self.g2data = list(y_sortedg2)
        pairednewg2 = list(zip(self.x_data, self.g2data))
        new_x_data=[]
        new_g2_data=[]
        for i in pairednewg2:
            if i[1]!=-1:
                new_x_data.append(i[0])
                new_g2_data.append(i[1])
        
        self.plot_line.setData(new_x_data, new_g2_data)
        
        # self.plot_line1.setData(self.x_data, self.y_datach1)
        # self.plot_line2.setData(self.x_data, self.y_datach2)

        if self.error != None:
            self.parent.errorWindow(self.error)
            self.error = None
        if self.completed:
            self.saveButton.setEnabled(True)
            self.savePlotsButton.setEnabled(True)
            self.comboBox1.setEnabled(True)
            self.comboBox2.setEnabled(True)
            self.timer.stop()
            self.completed = False
            self.startStopButton.setText("Start")
            self.startStopButton.setStyleSheet("background-color: none")
            self.enableWidgets(True)
            self.stopSpin.setEnabled(False)
            self.startSpin.setEnabled(False)
            self.stepSpin.setEnabled(False)
            self.nSpin.setEnabled(False)
            self.parent.check_timer.start()

        
                


    
    def reorder_array(self, array):
        # Separar positivos y negativos
        positive = array[array >= 0]
        negative = array[array <= 0]
        negative=np.sort(negative)
        negative=np.flip(negative)
        
        

        # Intercalar 0, 1, -1, 2, -2, ...
        ordered = [0]
        for i in range(1, len(positive)):
            ordered.append(positive[i])
            if i < len(negative):
                ordered.append(negative[i])
        
        # Convertir a array de numpy
        return np.array(ordered)

    def cleanPlot(self):
        self.x_data = []
        self.y_data = []
        self.y_datach1 = []
        self.y_datach2= []
        self.g2data = []
        self.plot_line.setData(self.x_data, self.g2data)
        
        # self.plot_line1.setData(self.x_data, self.y_datach1)
        # self.plot_line2.setData(self.x_data, self.y_datach2)

    def run(self, n, range_):
        self.cleanPlot()
        self.completed = False
        self.startStopButton.setText("Stop")
        self.startStopButton.setStyleSheet("background-color: green")
        self.enableWidgets(False)

        channel1 = self.comboBox1.currentText()
        channel2 = self.comboBox2.currentText()
        if channel2 > channel1:
            channel12 = channel1+channel2
        else:
            channel12 = channel2+channel1

        self.header = "Delay time (ns)" + constants.DELIMITER + "Counts " + channel1 + constants.DELIMITER \
           + "Counts " + channel2 + constants.DELIMITER + "Coincidences " + channel12

        self.parent.check_timer.stop()
        thread = Thread(target = self.heavyDuty, args = (n, range_))
        thread.daemon = True
        self.timer.start()
        thread.start()

    def heavyDuty(self, n, range_):
        port = self.parent.port_name
        channel1 = self.comboBox1.currentText()
        channel2 = self.comboBox2.currentText()
        if channel2 > channel1:
            channel12 = channel1+channel2
        else:
            channel12 = channel2+channel1
        if port != None:
            try:
                for delay in range_:
                    value = 0
                    valuech1 = 0 #(new sept-15-2021)
                    valuech2 = 0 #(new sept-15-2021)
                    last_id = 0
                    if delay > 0:
                        delay1 = 0
                        delay2 = delay
                    else:
                        delay1 = abs(delay)
                        delay2 = 0
                    delay1_ = -1
                    delay2_ = -1
                    for j in range(constants.NUMBER_OF_TRIES):
                        abacus.setSetting(port, "delay_%s" % channel1, delay1)
                        abacus.setSetting(port, "delay_%s" % channel2, delay2)
                        time.sleep(1e-3)
                        try:
                            delay1_ = abacus.getSetting(port, "delay_%s" % channel1)
                            delay2_ = abacus.getSetting(port, "delay_%s" % channel2)
                            if ((delay1 != delay1_) and (delay2 != delay2_)): break
                        except abacus.BaseError as e:
                            time.sleep(1e-2)
                            if j == (constants.NUMBER_OF_TRIES - 1): raise(e)

                    time.sleep(self.parent.sampling_widget.getValue() / 1000)

                    for i in range(n):
                        for j in range(constants.NUMBER_OF_TRIES):
                            if self.completed: return
                            try:
                                counters, id = abacus.getFollowingCounters(port, [channel12, channel1, channel2])
                                if (id != last_id) and (id != 0):
                                    value += counters.getValue(channel12)
                                    valuech1 += counters.getValue(channel1) #(new sept-15-2021)
                                    valuech2 += counters.getValue(channel2) #(new sept-15-2021)
                                    last_id = id
                                    break
                                else:
                                    time_left = abacus.getTimeLeft(port) / 1000 # seconds
                                    time.sleep(time_left)

                            except abacus.BaseError as e:
                                if j == (constants.NUMBER_OF_TRIES - 1): raise(e)

                    self.x_data.append(delay)
                    self.y_data.append(value / n)
                    self.y_datach1.append(valuech1 / n) #(new sept-15-2021)
                    self.y_datach2.append(valuech2 / n) #(new sept-15-2021)
                    self.totalCounts1=valuech1 / n
                    self.totalCounts2=valuech2 / n
                    #get the point of coincidences for g(2)
                    coincidences=value/n
                    counts12=self.totalCounts1*self.totalCounts2
                    if counts12!=0:
                        g2value=(coincidences/counts12)*self.mulConst
                    else:
                        #Define 0 if there is no counts
                        g2value=-1
                        
                    self.g2data.append(g2value)
                    
                self.completed = True
            except Exception as e:
                self.completed = True
                self.error = e

    def setNumberChannels(self, number_channels):
        self.number_channels = number_channels
        self.comboBox1.blockSignals(True)
        self.comboBox2.blockSignals(True)
        self.comboBox1.clear()
        self.comboBox2.clear()
        self.comboBox1.addItems([chr(i + ord('A')) for i in range(number_channels)])
        self.comboBox2.addItems([chr(i + ord('A')) for i in range(number_channels)])

        self.comboBox2.setCurrentIndex(1)

        self.comboBox1.blockSignals(False)
        self.comboBox2.blockSignals(False)

        channel1 = self.comboBox1.currentText()
        channel2 = self.comboBox2.currentText()
    

        if channel2 > channel1:
            channel12 = channel1+channel2
        else:
            channel12 = channel2+channel1
        self.plot.setLabel('left', "g(2) " + channel12)
        self.plot.setLabel('bottom', "Delay time ", units='ns')

    def updateConstants(self): #new on v1.4.0 (2020-06-30)
        try:
            self.startSpin.setMinimum(-abacus.constants.DELAY_MAXIMUM_VALUE)
            self.startSpin.setMaximum(abacus.constants.DELAY_MAXIMUM_VALUE - abacus.constants.DELAY_STEP_VALUE)
            self.startSpin.setSingleStep(abacus.constants.DELAY_STEP_VALUE)
            self.startSpin.setValue(-abacus.constants.DELAY_MAXIMUM_VALUE)

            self.stopSpin.setMinimum(-abacus.constants.DELAY_MAXIMUM_VALUE)
            self.stopSpin.setMaximum(abacus.constants.DELAY_MAXIMUM_VALUE)
            self.stopSpin.setSingleStep(abacus.constants.DELAY_STEP_VALUE)
            self.stopSpin.setValue(abacus.constants.DELAY_MAXIMUM_VALUE)

            self.stepSpin.setMinimum(abacus.constants.DELAY_STEP_VALUE)
            self.stepSpin.setMaximum(((abacus.constants.DELAY_MAXIMUM_VALUE - abacus.constants.DELAY_MINIMUM_VALUE) // abacus.constants.DELAY_STEP_VALUE) * abacus.constants.DELAY_STEP_VALUE)
            self.stepSpin.setSingleStep(abacus.constants.DELAY_STEP_VALUE)
            self.stepSpin.setValue(abacus.constants.DELAY_STEP_VALUE)
        except AttributeError as e:
            if abacus.constants.DEBUG: print(e)

    def setDarkTheme(self):
        self.plot_win.setBackground((42, 42, 42))
        whitePen = pg.mkPen(color=(255, 255, 255))
        self.plot.getAxis('bottom').setPen(whitePen)
        self.plot.getAxis('left').setPen(whitePen)
        self.plot.getAxis('bottom').setTextPen(whitePen)
        self.plot.getAxis('left').setTextPen(whitePen)
        


    def setLightTheme(self):
        self.plot_win.setBackground(None)
        blackPen = pg.mkPen(color=(0, 0, 0))
        self.plot.getAxis('bottom').setPen(blackPen)
        self.plot.getAxis('left').setPen(blackPen)
        self.plot.getAxis('bottom').setTextPen(blackPen)
        self.plot.getAxis('left').setTextPen(blackPen)
        


    def default_values(self):
        if self.oldValuesSentinel==0:
            self.oldsampling=self.parent.sampling_widget.getValue()
            self.oldcoincidence=self.parent.coincidence_spinBox.value()
            self.oldValuesSentinel=1
        
        resolution=self.parent.deviceresolution
        self.parent.coincidence_spinBox.setValue(resolution)
        self.stepSpin.setValue(resolution)    
        self.parent.sampling_widget.setValue(100)
        self.stopSpin.setValue(100)
        self.stopSpin.setButtonSymbols(QSpinBox.NoButtons)
        self.startSpin.setValue(-100)
        self.startSpin.setButtonSymbols(QSpinBox.NoButtons)
        self.stopSpin.setEnabled(False)
        self.startSpin.setEnabled(False)
        self.stepSpin.setEnabled(False)
        self.stepSpin.setButtonSymbols(QSpinBox.NoButtons)
        self.nSpin.setEnabled(False)
        self.nSpin.setButtonSymbols(QSpinBox.NoButtons)
        self.coincideWindow=self.parent.coincidence_spinBox.value()
        
        
    def closeEvent(self, event):
        self.parent.sampling_widget.setValue(self.oldsampling)
        self.parent.coincidence_spinBox.setValue(self.oldcoincidence)
        
        event.accept()
        
    def event(self, event): 
        if event.type() == QEvent.EnterWhatsThisMode: #Event called when ? is clicked                
            QWhatsThis.leaveWhatsThisMode() #To change mouse cursor back to arrow
            self.showHelp()
            return True
        return QDialog.event(self, event)
    

    def showHelp(self):
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("Help")
        if constants.IS_LIGHT_THEME:
            pixmap = QPixmap("abacusSoftware/source/EquationG2.png")
        else:
            pixmap = QPixmap("abacusSoftware/source/EquationDark.png")
                
        msgBox.setIconPixmap(pixmap)
        msgBox.exec_()
        
            



class SleepDialog(SweepDialogBase):
    def __init__(self, parent):
        super(SleepDialog, self).__init__(parent)

        self.formLayout.removeRow(self.rowIndexOfCoincidenceLabel-1)
        self.parent = parent

        self.setWindowTitle("Sleep time sweep")

        label = QLabel("Channel:")
        self.comboBox = QComboBox()
        self.comboBox.setEditable(True)
        self.comboBox.lineEdit().setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.comboBox.lineEdit().setReadOnly(True)
        self.comboBox.currentIndexChanged.connect(self.channelsChange)

        self.formLayout.insertRow(0, label, self.comboBox)

        self.startSpin.setMinimum(abacus.constants.SLEEP_MINIMUM_VALUE)
        self.startSpin.setMaximum(abacus.constants.SLEEP_MAXIMUM_VALUE - abacus.constants.SLEEP_STEP_VALUE)
        self.startSpin.setSingleStep(abacus.constants.SLEEP_STEP_VALUE)
        self.startSpin.setValue(abacus.constants.SLEEP_MINIMUM_VALUE)
        self.savePlotsButton.clicked.connect(self.save_plotSleep)
        self.saveButton.clicked.connect(self.save_file)
        self.savePlotsButton.setEnabled(False)
        self.saveButton.setEnabled(False)
        self.aftermeasure=False

        self.stopSpin.setMinimum(abacus.constants.SLEEP_MINIMUM_VALUE)
        self.stopSpin.setMaximum(abacus.constants.SLEEP_MAXIMUM_VALUE)
        self.stopSpin.setSingleStep(abacus.constants.SLEEP_STEP_VALUE)
        self.stopSpin.setValue(abacus.constants.SLEEP_MAXIMUM_VALUE)

        self.stepSpin.setMinimum(abacus.constants.SLEEP_STEP_VALUE)
        self.stepSpin.setMaximum(((abacus.constants.SLEEP_MAXIMUM_VALUE - abacus.constants.SLEEP_MINIMUM_VALUE) // abacus.constants.SLEEP_STEP_VALUE) * abacus.constants.SLEEP_STEP_VALUE)
        self.stepSpin.setSingleStep(abacus.constants.SLEEP_STEP_VALUE)
        self.stepSpin.setValue(abacus.constants.SLEEP_STEP_VALUE) #new on v1.4.0 (2020-06-30)

        self.plot.setLabel('left', "Counts")
        self.plot.setLabel('bottom', "Sleep time", units='ns')

        self.setTabOrder(self.comboBox, self.startSpin)
        self.setTabOrder(self.startSpin, self.stopSpin)
        self.setTabOrder(self.stopSpin, self.stepSpin)
        self.setTabOrder(self.stepSpin, self.nSpin)
        self.setTabOrder(self.nSpin, self.startStopButton)
        #self.setTabOrder(self.startStopButton, self.lineEdit)

    def channelsChange(self, index):
        if not self.aftermeasure:
            channel = self.comboBox.currentText()

            self.plot.setLabel('left', "Counts " + channel)
            self.plot.setLabel('bottom', "Sleep time", units='ns')
    
    def save_file(self):
        # if self.saveg2sentinel==0:
        
        try:
            try:
                directory = constants.directory_lineEdit
            except:
                directory = os.path.expanduser("~")
            dlg = QFileDialog(directory=directory)
            dlg.setAcceptMode(QFileDialog.AcceptSave)
            dlg.setFileMode(QFileDialog.AnyFile)
            nameFilters = ['Data Files (*.dat)','CSV Files (*.csv)','Text Files (*.txt)','All Files (*)']
            dlg.setNameFilters(nameFilters)
            if dlg.exec_():
                name = dlg.selectedFiles()[0]
                fileName = common.unicodePath(name)
                new_header=self.header.split(',')
                sampling_time="Sampling time: "+str(self.parent.sampling_widget.getValue())+"ms"
                coincidence="Coincidence window: "+str(self.parent.coincidence_spinBox.value())+"ns"
                StartInit= "Min delay: "+str(self.startSpin.value())+"ns"
                StopInit= "Max delay: "+str(self.stopSpin.value())+"ns"
                parameters_list=[sampling_time,coincidence,StartInit,StopInit]
                self.x_data = [ int(x) for x in self.x_data ]
                self.y_data = [ int(x) for x in self.y_data ]
                data = np.vstack((self.x_data,self.y_data)).T
                g2fileclass=G2_file(fileName,data,new_header,parameters_list)
                g2fileclass.writefile()
                message_box = QMessageBox(self)
                message_box.setIcon(QMessageBox.Information)
                textmessage="The data has been saved successfully in "+"\n\n"+ fileName
                message_box.setText(textmessage)
                message_box.setWindowTitle("Successful save")
                message_box.setStandardButtons(QMessageBox.Ok)
                message_box.exec_()
                self.saveg2sentinel=1
                self.saveg2route=fileName
        except:
            message_box = QMessageBox(self.parent)
            message_box.setIcon(QMessageBox.Critical)
            message_box.setText("The data could not be saved.")
            message_box.setWindowTitle("Error saving")
            message_box.setStandardButtons(QMessageBox.Ok)
            message_box.exec_()
        
    def save_plotSleep(self):
        try:
            try:
                directory = constants.directory_lineEdit
            except:
                directory = os.path.expanduser("~")

            dlg = QFileDialog(directory=directory)
            dlg.setAcceptMode(QFileDialog.AcceptSave)
            dlg.setFileMode(QFileDialog.AnyFile)
            nameFilters = ['JPEG Image (*.jpg)', 'PNG Image (*.png)']
            dlg.setNameFilters(nameFilters)
            if dlg.exec_():
                name = dlg.selectedFiles()[0]
                fileName = common.unicodePath(name)
                exporter1 = pg.exporters.ImageExporter(self.plot_win.scene())
                exporter1.parameters()['width'] = 800
                exporter1.parameters()['height'] = 700
                temp_image = exporter1.export(toBytes=True)
                width, height = 800, 700
                white_background = QImage(width, height, QImage.Format_RGB32)
                white_background.fill(QColor('white'))
                painter = QPainter(white_background)
                painter.drawImage(0, 0, temp_image)
                painter.end()
                white_background.save(fileName)
                message_box = QMessageBox(self)
                message_box.setIcon(QMessageBox.Information)
                textmessage="The plot have been saved successfully in "+"\n\n"+ fileName
                message_box.setText(textmessage)
                message_box.setWindowTitle("Successful save")
                message_box.setStandardButtons(QMessageBox.Ok)
                message_box.exec_()
        except:
            message_box = QMessageBox(self.parent)
            message_box.setIcon(QMessageBox.Critical)
            message_box.setText("The plots could not be saved.")
            message_box.setWindowTitle("Error saving")
            message_box.setStandardButtons(QMessageBox.Ok)
            message_box.exec_()

    def startStop(self):
        if self.startStopButton.text() == "Stop":
            self.timer.stop()
            self.completed = True
            self.updatePlot()
            self.completed = True
            self.savePlotsButton.setEnabled(True)
            self.saveButton.setEnabled(True)
            self.comboBox.setEnabled(True)

        else:
            self.aftermeasure=True
            self.comboBox.setEnabled(False)
            self.savePlotsButton.setEnabled(False)
            self.saveButton.setEnabled(False)
            self.x_data = []
            self.y_data = []
            step = self.stepSpin.value()
            n = self.nSpin.value()
            range_ = np.arange(self.startSpin.value(), self.stopSpin.value() + 1, step)
            range_ = range_[range_ <= abacus.constants.SLEEP_MAXIMUM_VALUE]
            channel = self.comboBox.currentText()

            if self.parent.port_name != None:
                if self.parent.streaming:
                    if self.stopAcquisition():
                        self.run(channel, n, range_)
                else:
                    self.run(channel, n, range_)
            else:
                self.parent.connect()
                if self.parent.port_name!= None:
                    if self.parent.streaming:
                        if self.stopAcquisition():
                            self.run(channel, n, range_)
                    else:
                        self.run(channel, n, range_)

    def run(self, channel, n, range_):
        self.cleanPlot()
        self.completed = False
        self.startStopButton.setText("Stop")
        self.startStopButton.setStyleSheet("background-color: green")
        self.enableWidgets(False)

        self.header = "Sleep time (ns)"  + constants.DELIMITER +  "Counts %s"%channel

        self.parent.check_timer.stop()
        thread = Thread(target = self.heavyDuty, args = (channel, n, range_))
        thread.daemon = True
        self.timer.start()
        thread.start()

    def heavyDuty(self, channel, n, range_):
        port = self.parent.port_name
        if port != None:
            try:
                for sleep in range_:
                    value = 0
                    last_id = 0
                    sleep_ = -1
                    for j in range(constants.NUMBER_OF_TRIES):
                        try:
                            abacus.setSetting(port, 'sleep_%s' % channel, sleep)
                            time.sleep(1e-3)
                            sleep_ = abacus.getSetting(port, "sleep_%s" % channel)
                            if (sleep != sleep_): break
                        except abacus.BaseError as e:
                            time.sleep(1e-2)
                            if j == (constants.NUMBER_OF_TRIES - 1): raise(e)

                    time.sleep(self.parent.sampling_widget.getValue() / 1000)

                    for i in range(n): # number of points
                        for j in range(constants.NUMBER_OF_TRIES): # tries
                            if self.completed: return
                            try:
                                counters, id = abacus.getFollowingCounters(port, [channel])
                                if (id != last_id) and (id != 0):
                                    last_id = id
                                    value += counters.getValue(channel)
                                    break
                                else:
                                    time_left = abacus.getTimeLeft(port) / 1000 # seconds
                                    time.sleep(time_left)

                            except abacus.BaseError as e:
                                if j == (constants.NUMBER_OF_TRIES - 1): raise(e)

                    self.x_data.append(sleep)
                    self.y_data.append(value / n)
                self.completed = True

            except Exception as e:
                self.completed = True
                self.error = e

    def setNumberChannels(self, number_channels):
        self.comboBox.clear()
        self.comboBox.addItems([chr(i + ord('A')) for i in range(number_channels)])

    def updateConstants(self): #new on v1.4.0 (2020-06-30)
        try:
            self.startSpin.setMinimum(abacus.constants.SLEEP_MINIMUM_VALUE)
            self.startSpin.setMaximum(abacus.constants.SLEEP_MAXIMUM_VALUE - abacus.constants.SLEEP_STEP_VALUE)
            self.startSpin.setSingleStep(abacus.constants.SLEEP_STEP_VALUE)
            self.startSpin.setValue(abacus.constants.SLEEP_MINIMUM_VALUE)

            self.stopSpin.setMinimum(abacus.constants.SLEEP_MINIMUM_VALUE)
            self.stopSpin.setMaximum(abacus.constants.SLEEP_MAXIMUM_VALUE)
            self.stopSpin.setSingleStep(abacus.constants.SLEEP_STEP_VALUE)
            self.stopSpin.setValue(abacus.constants.SLEEP_MAXIMUM_VALUE)

            self.stepSpin.setMinimum(abacus.constants.SLEEP_STEP_VALUE)
            self.stepSpin.setMaximum(((abacus.constants.SLEEP_MAXIMUM_VALUE - abacus.constants.SLEEP_MINIMUM_VALUE) // abacus.constants.SLEEP_STEP_VALUE) * abacus.constants.SLEEP_STEP_VALUE)
            self.stepSpin.setSingleStep(abacus.constants.SLEEP_STEP_VALUE)
            self.stepSpin.setValue(abacus.constants.SLEEP_STEP_VALUE) #new on v1.4.0 (2020-06-30)
        except AttributeError as e:
            if abacus.constants.DEBUG: print(e)

    def updatePlot(self):
        if constants.IS_LIGHT_THEME: 
            colors_symbols = self.parent.light_colors_in_use
        else: 
            colors_symbols = self.parent.dark_colors_in_use

        channel = self.comboBox.currentText()
        self.plot.setLabel('left', "Counts "+ channel)

        try:
            color = colors_symbols[channel][0]
            symbol = colors_symbols[channel][1]
        except KeyError:
            if constants.IS_LIGHT_THEME:
                color = constants.COLORS[-1]
            else:
                color = constants.DARK_COLORS[-1]
            symbol = constants.SYMBOLS[-1]

        symbolSize = self.parent.symbolSize
        linewidth = self.parent.linewidth
        self.plot_line.opts['pen'] = pg.mkPen(color, width=linewidth)
        self.plot_line.opts['symbol'] = symbol
        self.plot_line.opts['symbolPen'] = color
        self.plot_line.opts['symbolBrush'] = color
        self.plot_line.opts['symbolSize'] = symbolSize

        self.plot_line.setData(self.x_data, self.y_data)
        if self.error != None:
            self.parent.errorWindow(self.error)
            self.error = None

        if self.completed:
            self.saveButton.setEnabled(True)
            self.savePlotsButton.setEnabled(True)
            self.timer.stop()
            self.completed = False
            self.startStopButton.setText("Start")
            self.startStopButton.setStyleSheet("background-color: none")
            self.enableWidgets(True)
            self.parent.check_timer.start()
