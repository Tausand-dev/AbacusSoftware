#NOTA: No cambiar el nombre de la variable __version__
import os
import sys
import pyAbacus as abacus
from .common import findDocuments


__version__ = '1.6.1'

CURRENT_OS = sys.platform
#DIRECTORY = os.path.dirname(sys.executable)
dirName = findDocuments() + "/Tausand/"
if not os.path.exists(dirName):
    os.mkdir(dirName)
DIRECTORY = dirName
SETTINGS_PATH = os.path.join(DIRECTORY, "settings.py")
LOGFILE_PATH = "logfile.txt"
# LOGFILE_PATH = os.path.join(DIRECTORY, "logfile.txt")

if abacus.constants.DEBUG:
    print("SETTINGS PATH ON:", SETTINGS_PATH)

SETTING_FILE_EXISTS = False

BREAKLINE = "\n"
if CURRENT_OS == "win32":
    BREAKLINE = "\r\n"

EXTENSION_DATA = '.dat'
PARAMS_SUFFIX = "_settings"
FILE_PREFIX = "abacusdata"
EXTENSION_PARAMS = PARAMS_SUFFIX + '.txt'
SUPPORTED_EXTENSIONS = {'.dat': 'Plain text data file (*.dat)', '.csv' : 'CSV data files (*.csv)'}
WINDOWS_NAMES=['win32','cygwin','msys']
MAC_NAMES=['darwin']
LINUX_NAMES=['linux','linux2']
NOT_SUPPORTED_WINDOWS_CHARACTER_NAMES = ['<','>',':','"','/','\\','|','?','*']
NOT_SUPPORTED_WINDOWS_RESERVED_WORDS = ['CON', 'PRN', 'AUX', 'NUL','COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9'
'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9','COM','LPT']
NOT_SUPPORTED_MAC_CHARACTER = [':','/']
NOT_SUPPORTED_LINUX_CHARACTER = [':','/']
DELIMITER = ","
DELIMITERS = [",", ";", "Tab", "Space"]

PARAMS_HEADER = "##### SETTINGS FILE #####" + BREAKLINE + "Tausand Abacus session began at %s"

CONNECT_EMPTY_LABEL = "No devices found.\nYou might verify the device is conected, turned on, and not being\nused by other software. Also verify the driver is correctly installed."
CONNECT_LABEL = "Please select one of the available ports: "

WINDOW_NAME = "Tausand Abacus Sofware %s"%__version__

DATA_REFRESH_RATE = 250 # fastest data refresh rate (ms)
CHECK_RATE = 250

BUFFER_ROWS = 10000

COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#7f7f7f",
        "#8c564b", "#e377c2",  "#bcdb22", "#9467bd", "#14becf", "#23ab00"]
COLORS_NAMES = ['Blue', 'Orange', 'Green', 'Red', 'Gray',
        'Brown', 'Pink', 'Olive', 'Purple', 'Cyan', 'Limeade'] # Names from Matplotlib except for the last one

DARK_COLORS = ["#ffffff", "#20fc03", "#b4c4fd", "#b4fdb9",  "#03fcec",
         "#feffcc", "#fc6467", "#e9e21c",  "#dcb4fd", "#fc03df", "#fffe08"]
DARK_COLORS_NAMES = ['White', 'Harlequin', 'Melrose', 'Reef',  'Aqua',
         'Cream', 'Carnation', 'Sunflower', 'Mauve', 'Pizzazz', 'Yellow'] # Names from https://chir.ag/projects/name-that-color

SYMBOLS = ['o', 's', 't', 't1', 't2', 't3', 'd', '+', 'x', 'p', 'h', 'star']

WIDGETS_NAMES = ["checkBox", "lineEdit", "comboBox", "spinBox"]
WIDGETS_GET_ACTIONS = ["self.%s.isChecked()", "self.%s.text()", "self.%s.currentText()", "self.%s.value()"]
WIDGETS_SET_ACTIONS = ["class_.%s.setChecked(%s)", "class_.%s.setText('%s')", "class_.%s.setCurrentIndex(class_.%s.findText('%s'))", "class_.%s.setValue(%d)"]

NUMBER_OF_TRIES = 10

ICON = None

IS_LIGHT_THEME = False

def actualizar_numero_version(nombre_archivo):
    nuevo_numero_version=__version__    
    with open(nombre_archivo, 'r') as archivo:
        lineas = archivo.readlines()

    version_lista=str(nuevo_numero_version).split(".")
    version_comas=", ".join(version_lista)


    for i, linea in enumerate(lineas):
        if 'FileVersion' in linea:
            lineas[i] = "        StringStruct(u'FileVersion', u'"+str(nuevo_numero_version)+".0'),"
        elif 'ProductVersion' in linea:
            lineas[i] = "        StringStruct(u'ProductVersion', u'"+str(nuevo_numero_version)+".0')])" 
        elif 'filevers=' in linea:
            lineas[i] = "    filevers=("+version_comas+", 0),"    
        elif 'prodvers=' in linea:
            lineas[i] = "    prodvers=("+version_comas+", 0),"    
            

            break

    
    with open(nombre_archivo, 'w') as archivo:
        archivo.writelines(lineas)


