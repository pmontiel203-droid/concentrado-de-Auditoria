import os
import pandas as pd

def consolidar_reportes(carpeta_origen, archivo_salida):
    todos_los_datos = []
    
    # Validar si la carpeta existe
    if not os.path.exists(carpeta_origen):
        print(f"[Error] La carpeta {carpeta_origen} no existe.")
        return

    # Listar archivos de Excel
    for archivo in os.listdir(carpeta_origen):
        if archivo.endswith('.xlsx') and not archivo.startswith('~$'):
            ruta_completa = os.path.join(carpeta_origen, archivo)
            try:
                # Leer el Excel
                df = pd.read_excel(ruta_completa)
                # Añadimos columna para saber de qué tienda/archivo viene el dato
                df['Origen_Archivo'] = archivo 
                todos_los_datos.append(df)
            except Exception as e:
                print(f"No se pudo leer {archivo}: {e}")
                
    if todos_los_datos:
        # Unir todos los datos en uno solo
        concentrado_final = pd.concat(todos_los_datos, ignore_index=True)
        # Guardar en la ruta de salida
        concentrado_final.to_excel(archivo_salida, index=False)
        print(f"-> Archivo consolidado con éxito en: {archivo_salida}")
    else:
        print("No se encontraron datos para consolidar.")
