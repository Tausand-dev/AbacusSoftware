#Ejecutable para actualizar los archivos de la aplicación
#Solo ejecutar cuando se ha realizado o se va a realizar un nuevo release en github
#Si la aplicación no ejecuta revisar el path, tener en cuenta que es un archivo creado unicamente para un desarrollador

import os

version="1.6.1"
#Actualizamos el archivo constants.py

def actualizar_constants(nombre_archivo,nuevo_numero_version):  
    
    with open(nombre_archivo, 'r') as archivo:
        lineas = archivo.readlines()

    for i, linea in enumerate(lineas):
        if '__version__ =' in linea:
            lineas[i] = "__version__ = '"+str(nuevo_numero_version)+"'\n"

    with open(nombre_archivo, 'w') as archivo:
        archivo.writelines(lineas)



#actualizamos el archivo txt llamado fileversion.txt
def actualizar_numero_version_fileversion(nombre_archivo,nuevo_numero_version):  
    
    with open(nombre_archivo, 'r') as archivo:
        lineas = archivo.readlines()
    version_lista=str(nuevo_numero_version).split(".")
    version_comas=", ".join(version_lista)

    for i, linea in enumerate(lineas):
        if 'FileVersion' in linea:
            lineas[i] = "        StringStruct(u'FileVersion', u'"+str(nuevo_numero_version)+".0'),\n"
        elif 'ProductVersion' in linea:
            lineas[i] = "        StringStruct(u'ProductVersion', u'"+str(nuevo_numero_version)+".0')])\n" 
        elif 'filevers=' in linea:
            lineas[i] = "    filevers=("+version_comas+", 0),\n"    
        elif 'prodvers=' in linea:
            lineas[i] = "    prodvers=("+version_comas+", 0),\n"    

    with open(nombre_archivo, 'w') as archivo:
        archivo.writelines(lineas)

#actualizaremos el archivo llamado installer_builder.iss        
def actualizar_numero_version_installer_builder(nombre_archivo,nuevo_numero_version):  
    
    with open(nombre_archivo, 'r') as archivo:
        lineas = archivo.readlines()    

    for i, linea in enumerate(lineas):
        if 'MyAppVersion ' in linea:
            lineas[i] = '#define MyAppVersion "'+version+'"\n'

    with open(nombre_archivo, 'w') as archivo:
        archivo.writelines(lineas)




#Aquí actualizaremos el release history
def actualizar_release_history(archivo_a, archivo_b):
    # Leer el contenido del archivo A
    with open(archivo_a, 'r') as file_a:
        contenido_a = file_a.read()
    enter_line="\n"
    

    # Leer el contenido del archivo B
    with open(archivo_b, 'r') as file_b:
        contenido_b = file_b.read()

    # Concatenar el contenido de A al principio del contenido de B
    contenido_combinado = contenido_a+enter_line + contenido_b

    # Escribir el contenido combinado en el archivo B
    with open(archivo_b, 'w') as file_b:
        file_b.write(contenido_combinado)

#Actualizaremos el setup cfg
def actualizar_setup_cfg(nombre_archivo,nuevo_numero_version):  
    
    with open(nombre_archivo, 'r') as archivo:
        lineas = archivo.readlines()

    for i, linea in enumerate(lineas):
        if 'version =' in linea:
            lineas[i] = "version = "+version+'\n'
    with open(nombre_archivo, 'w') as archivo:
        archivo.writelines(lineas)
        
        



nombre_archivo = "fileversion.txt"  # Nombre del archivo
# Obtener la ruta absoluta del archivo
ruta_absoluta = os.path.abspath("fileversion.txt")

nombre_archivo_iss="installer_builder.iss"
ruta_absoluta_iss = os.path.abspath("..\\installers")+"\\"+nombre_archivo_iss

actualizar_numero_version_fileversion(ruta_absoluta,version)
actualizar_numero_version_installer_builder(ruta_absoluta_iss,version)

#Aqui se actualiza el release md de acuerdo a las notas de la ultima actualizacion}

ruta_absoluta_release_history_md = os.path.abspath("..\\release_history.md")
ruta_absoluta_last_patch = os.path.abspath("LastVersionNotes.md")
actualizar_release_history(ruta_absoluta_last_patch,ruta_absoluta_release_history_md)

#Aqui se actualizara el setup cfg
ruta_absoluta_setup_cfg = os.path.abspath("..\\setup.cfg")
actualizar_setup_cfg(ruta_absoluta_setup_cfg,version)

#Aqui se actualizara constants.py 
ruta_absoluta_constants = os.path.abspath("constants.py")
actualizar_constants(ruta_absoluta_constants,version)


