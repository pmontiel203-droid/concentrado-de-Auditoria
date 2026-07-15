# pruebas/ejecutar_prueba.py
import os
import sys
import pandas as pd

# 1. Esto le permite a Python encontrar tu carpeta 'backend'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.consolidacion import consolidar_reportes

def preparar_y_probar():
    # Definir rutas
    carpeta_temporal_tiendas = "pruebas/archivos_tiendas_test"
    archivo_salida = "informes_de_prueba/concentrado_TEST.xlsx"
    
    # Crear carpetas necesarias si no existen
    os.makedirs(carpeta_temporal_tiendas, exist_ok=True)
    os.makedirs("informes_de_prueba", exist_ok=True)
    
    print("1. Creando tiendas de prueba (datos simulados)...")
    # Tienda 1
    df_t1 = pd.DataFrame({
        'ID_Tienda': ['T-01', 'T-01'],
        'Sensor_Control': ['Correcto', 'Incorrecto'],
        'Faltante_Prendas': [0, 3]
    })
    df_t1.to_excel(f"{carpeta_temporal_tiendas}/tienda_coacalco.xlsx", index=False)
    
    # Tienda 2
    df_t2 = pd.DataFrame({
        'ID_Tienda': ['T-02', 'T-02'],
        'Sensor_Control': ['Correcto', 'Correcto'],
        'Faltante_Prendas': [1, 0]
    })
    df_t2.to_excel(f"{carpeta_temporal_tiendas}/tienda_tizayuca.xlsx", index=False)
    
    print("2. Ejecutando el proceso de consolidación...")
    # Correr la función del backend
    consolidar_reportes(carpeta_temporal_tiendas, archivo_salida)
    
    # 3. Validar el resultado final
    if os.path.exists(archivo_salida):
        resultado = pd.read_excel(archivo_salida)
        print("\n=== ¡PRUEBA EXITOSA! ===")
        print(f"Se generó el reporte final con {len(resultado)} registros en total.")
        print("\nVista previa de los datos unificados:")
        print(resultado)
    else:
        print("\n[ERROR] Algo falló, el archivo final no se generó.")

if __name__ == "__main__":
    preparar_y_probar()
