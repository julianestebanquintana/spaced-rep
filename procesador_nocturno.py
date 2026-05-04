import json
import glob
import os
from datetime import datetime, timedelta
os.chdir(os.path.dirname(os.path.abspath(__file__)))

ARCHIVO_REGISTRO = 'registro_diario.json'
ARCHIVO_ENVIADAS = 'enviadas_hoy.json'

def procesar_sesion():
    hoy = str(datetime.now().date())
    
    # 1. Validar si existen los archivos y corresponden al día de hoy
    if not os.path.exists(ARCHIVO_REGISTRO) or not os.path.exists(ARCHIVO_ENVIADAS):
        print("Faltan archivos de registro. Abortando actualización.")
        return

    with open(ARCHIVO_REGISTRO, 'r') as f: registro = json.load(f)
    with open(ARCHIVO_ENVIADAS, 'r') as f: enviadas = json.load(f)

    fecha_registro = registro.get('fecha', '')
    fecha_enviadas = enviadas.get('fecha', '')
    if not fecha_registro or not fecha_enviadas:
        print("Archivos de registro incompletos. Abortando.")
        return
    # Permite procesar registros de hasta 24 horas atrás
    from datetime import date
    dias_diferencia = (date.fromisoformat(hoy) - date.fromisoformat(fecha_registro)).days
    if dias_diferencia > 1:
        print(f"Registros demasiado antiguos ({fecha_registro}). Abortando.")
        return
        
    if not registro.get('finalizado') and len(registro.get('errores', [])) == 0:
        print("Sesión inactiva (sin clics ni finalización). Los intervalos no se modificarán.")
        return

    ids_enviados = enviadas.get('ids', [])
    ids_errores = registro.get('errores', [])
    archivos_db = glob.glob("db/*.json")
    
    # Excluir los archivos de control del procesamiento
    archivos_db = [f for f in archivos_db if f not in [ARCHIVO_REGISTRO, ARCHIVO_ENVIADAS]]

    # 2. Actualizar las tarjetas en las bases de datos
    for archivo in archivos_db:
        modificado = False
        with open(archivo, 'r', encoding='utf-8') as f:
            datos = json.load(f)
            
        for tarjeta in datos['preguntas']:
            if tarjeta['id'] in ids_enviados:
                modificado = True
                tarjeta['fecha_ultimo_repaso'] = hoy
                
                if tarjeta['id'] in ids_errores:
                    # Lógica de Error (Penalización SM-2)
                    tarjeta['repeticiones'] = 0
                    tarjeta['intervalo'] = 1
                    tarjeta['dificultad'] = max(1.3, round(tarjeta['dificultad'] - 0.2, 2))
                else:
                    # Lógica de Éxito (Avance SM-2)
                    if tarjeta['repeticiones'] == 0:
                        tarjeta['intervalo'] = 1
                    elif tarjeta['repeticiones'] == 1:
                        tarjeta['intervalo'] = 6
                    else:
                        tarjeta['intervalo'] = round(tarjeta['intervalo'] * tarjeta['dificultad'])
                    
                    tarjeta['repeticiones'] += 1
                    # Aumento opcional y sutil del factor de facilidad tras un éxito sostenido
                    tarjeta['dificultad'] = min(2.5, round(tarjeta['dificultad'] + 0.05, 2))
                
                # Calcular la nueva fecha
                nueva_fecha = datetime.now().date() + timedelta(days=tarjeta['intervalo'])
                tarjeta['fecha_proximo_repaso'] = str(nueva_fecha)
                
        if modificado:
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
                
    print("Bases de datos actualizadas con éxito.")
    
    # Limpiar los registros diarios para evitar reprocesos
    os.remove(ARCHIVO_REGISTRO)
    os.remove(ARCHIVO_ENVIADAS)

if __name__ == '__main__':
    procesar_sesion()