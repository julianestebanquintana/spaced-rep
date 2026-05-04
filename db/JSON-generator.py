import json
import re
import glob

def limpiar_texto(texto):
    texto = re.sub(r'\[([^\]]+)\]\(https://www.notion.so/[^\)]+\)', r'\1', texto)
    texto = re.sub(r'!\[[^\]]*\]\([^\)]+\)', '', texto)
    return texto.strip()

def procesar_documentos():
    archivos = glob.glob("*.txt")
    fecha_hoy = "2026-04-05"
    
    for archivo in archivos:
        tema = archivo.replace('.txt', '').split(' ', 1)[-1] if ' ' in archivo else archivo.replace('.txt', '')
        
        with open(archivo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
            
        bases_datos = []
        subtema_actual = "General"
        preguntas = []
        contador_id = 1
        pregunta_actual = None
        respuesta_actual = []
        
        def guardar_pregunta():
            nonlocal pregunta_actual, respuesta_actual, preguntas, contador_id
            if pregunta_actual:
                preguntas.append({
                    "id": f"{tema[:3].lower().strip()}_{contador_id:03d}",
                    "pregunta": pregunta_actual,
                    "respuesta": " ".join(respuesta_actual).strip(),
                    "repeticiones": 0,
                    "intervalo": 0,
                    "dificultad": 2.5,
                    "fecha_ultimo_repaso": fecha_hoy,
                    "fecha_proximo_repaso": fecha_hoy
                })
                contador_id += 1
                pregunta_actual = None
                respuesta_actual = []

        def guardar_base():
            nonlocal preguntas, subtema_actual, bases_datos
            if preguntas:
                bases_datos.append({
                    "metadata": {
                        "tema": tema,
                        "subtema": subtema_actual,
                        "autor": "Admin",
                        "version": "1.0.0",
                        "fecha_actualizacion": fecha_hoy,
                        "idioma": "es"
                    },
                    "preguntas": preguntas
                })
                preguntas = []

        for linea in lineas:
            linea_limpia = limpiar_texto(linea)
            if not linea_limpia:
                continue
                
            if linea_limpia.startswith('# '):
                guardar_pregunta()
                guardar_base()
                subtema_actual = linea_limpia.replace('# ', '').strip()
                contador_id = 1
            elif linea_limpia.startswith('- ¿') or linea_limpia.startswith('- Qué') or linea_limpia.startswith('- Cuál') or linea_limpia.startswith('- Definir') or (linea_limpia.startswith('- ') and '?' in linea_limpia):
                guardar_pregunta()
                pregunta_actual = linea_limpia[2:].strip()
            else:
                if pregunta_actual and "notion.so" not in linea_limpia:
                    respuesta_actual.append(linea_limpia)
                    
        guardar_pregunta()
        guardar_base()
        
        for base in bases_datos:
            nombre_salida = f"{tema} - {base['metadata']['subtema'].replace('/', '-')}.json"
            with open(nombre_salida, 'w', encoding='utf-8') as f:
                json.dump(base, f, ensure_ascii=False, indent=2)
                
if __name__ == "__main__":
    procesar_documentos()