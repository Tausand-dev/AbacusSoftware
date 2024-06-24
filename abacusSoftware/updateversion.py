#Executable to update the application files
#Only run when a new release has been made or is going to be made on GitHub
#If the application does not run, check the path. Keep in mind that this is a file created solely for a developer


import os

version="1.6.1"
#We update the constants.py file

def actualizar_constants(nombre_archivo,nuevo_numero_version):  
    
    with open(nombre_archivo, 'r') as archivo:
        lineas = archivo.readlines()

    for i, linea in enumerate(lineas):
        if '__version__ =' in linea:
            lineas[i] = "__version__ = '"+str(nuevo_numero_version)+"'\n"

    with open(nombre_archivo, 'w') as archivo:
        archivo.writelines(lineas)



# We update the text file named fileversion.txt
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

#We will update the file named installer_builder.iss
def actualizar_numero_version_installer_builder(nombre_archivo,nuevo_numero_version):  
    
    with open(nombre_archivo, 'r') as archivo:
        lineas = archivo.readlines()    

    for i, linea in enumerate(lineas):
        if 'MyAppVersion ' in linea:
            lineas[i] = '#define MyAppVersion "'+version+'"\n'

    with open(nombre_archivo, 'w') as archivo:
        archivo.writelines(lineas)




#Here we will update the release history
def actualizar_release_history(archivo_a, archivo_b):
    #Read the contents of file A
    with open(archivo_a, 'r') as file_a:
        contenido_a = file_a.read()
    enter_line="\n"
    

    #Read the contents of file B
    with open(archivo_b, 'r') as file_b:
        contenido_b = file_b.read()

    #Concatenate the contents of A at the beginning of the contents of B
    contenido_combinado = contenido_a+enter_line + contenido_b

    #Write the combined content into file B
    with open(archivo_b, 'w') as file_b:
        file_b.write(contenido_combinado)

#We will update the setup.cfg
def actualizar_setup_cfg(nombre_archivo,nuevo_numero_version):  
    
    with open(nombre_archivo, 'r') as archivo:
        lineas = archivo.readlines()

    for i, linea in enumerate(lineas):
        if 'version =' in linea:
            lineas[i] = "version = "+version+'\n'
    with open(nombre_archivo, 'w') as archivo:
        archivo.writelines(lineas)
        
        



nombre_archivo = "fileversion.txt"  # Name of the file
# get the absolute path
ruta_absoluta = os.path.abspath("fileversion.txt")

nombre_archivo_iss="installer_builder.iss"
ruta_absoluta_iss = os.path.abspath("..\\installers")+"\\"+nombre_archivo_iss

actualizar_numero_version_fileversion(ruta_absoluta,version)
actualizar_numero_version_installer_builder(ruta_absoluta_iss,version)

#Here we update the release md according to last version notes

ruta_absoluta_release_history_md = os.path.abspath("..\\release_history.md")
ruta_absoluta_last_patch = os.path.abspath("LastVersionNotes.md")
actualizar_release_history(ruta_absoluta_last_patch,ruta_absoluta_release_history_md)

#Here we update setup cfg 
ruta_absoluta_setup_cfg = os.path.abspath("..\\setup.cfg")
actualizar_setup_cfg(ruta_absoluta_setup_cfg,version)

#Here we update constatns.py
ruta_absoluta_constants = os.path.abspath("constants.py")
actualizar_constants(ruta_absoluta_constants,version)


