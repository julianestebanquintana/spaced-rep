from flask import Flask, request
import json
import os
from datetime import datetime

app = Flask(__name__)
ARCHIVO_REGISTRO = 'registro_diario.json'

def inicializar_registro():
    """Crea el archivo de registro si no existe o si es de un día anterior."""
    hoy = str(datetime.now().date())
    
    if os.path.exists(ARCHIVO_REGISTRO):
        with open(ARCHIVO_REGISTRO, 'r') as f:
            try:
                datos = json.load(f)
                if datos.get('fecha') == hoy:
                    return # El archivo de hoy ya existe
            except json.JSONDecodeError:
                pass # Si el archivo está corrupto, lo sobreescribimos
                
    # Crea un registro en blanco para el día de hoy
    with open(ARCHIVO_REGISTRO, 'w') as f:
        json.dump({"fecha": hoy, "errores": [], "finalizado": False}, f)

@app.route('/calificar', methods=['GET'])
def calificar():
    id_tarjeta = request.args.get('id')
    if not id_tarjeta:
        return "Falta el ID de la tarjeta.", 400
        
    inicializar_registro()
    
    with open(ARCHIVO_REGISTRO, 'r+') as f:
        datos = json.load(f)
        if id_tarjeta not in datos['errores']:
            datos['errores'].append(id_tarjeta)
        
        # Sobreescribir el archivo con el nuevo error
        f.seek(0)
        json.dump(datos, f, indent=2)
        f.truncate()
        
    return f"""
    <html><body style='font-family: sans-serif; text-align: center; padding-top: 50px;'>
        <h2 style='color: #d9534f;'>Registro Exitoso</h2>
        <p>La tarjeta <strong>{id_tarjeta}</strong> ha sido marcada para repaso temprano.</p>
        <p><em>Puedes cerrar esta ventana.</em></p>
    </body></html>
    """

@app.route('/finalizar', methods=['GET'])
def finalizar():
    inicializar_registro()
    
    with open(ARCHIVO_REGISTRO, 'r+') as f:
        datos = json.load(f)
        datos['finalizado'] = True
        
        f.seek(0)
        json.dump(datos, f, indent=2)
        f.truncate()
        
    return """
    <html><body style='font-family: sans-serif; text-align: center; padding-top: 50px;'>
        <h2 style='color: #5cb85c;'>¡Sesión Finalizada!</h2>
        <p>Has completado el repaso de hoy. Esta noche se actualizarán tus intervalos.</p>
        <p><em>Puedes cerrar esta ventana.</em></p>
    </body></html>
    """

if __name__ == '__main__':
    # host='0.0.0.0' permite recibir conexiones externas (necesario en el VPS)
    app.run(host='0.0.0.0', port=5000)