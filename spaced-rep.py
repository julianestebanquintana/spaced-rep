import os
import json
import glob
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# Carga las variables desde el archivo .env oculto
load_dotenv()

def seleccionar_tarjetas():
    archivos = glob.glob("*.json")
    hoy = datetime.now().date()
    seleccion_total = []

    for archivo in archivos:
        with open(archivo, 'r', encoding='utf-8') as f:
            datos = json.load(f)
            
        tema = datos['metadata']['tema']
        pendientes = []
        
        for tarjeta in datos['preguntas']:
            fecha_repaso = datetime.strptime(tarjeta['fecha_proximo_repaso'], '%Y-%m-%d').date()
            if fecha_repaso <= hoy:
                pendientes.append(tarjeta)
                
        pendientes.sort(key=lambda x: (-x['repeticiones'], x['dificultad']))
        
        if pendientes:
            seleccion_total.append((tema, pendientes[:10]))
            
    return seleccion_total

def enviar_correo(seleccion):
    remitente = os.environ.get("EMAIL_REMIT")
    destinatario = os.environ.get("EMAIL_DESTIN")
    password = os.environ.get("EMAIL_PASS")
    ip_vps = os.environ.get("VPS_IP")

    if not all([remitente, password, ip_vps]):
        print("Error: Faltan credenciales en el archivo .env")
        return

    msg = MIMEMultipart()
    msg['Subject'] = f"Repaso Espaciado - {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = remitente
    msg['To'] = destinatario

    html = "<html><body style='font-family: sans-serif;'>"
    html += "<h2>Repaso Diario</h2>"

    for tema, tarjetas in seleccion:
        html += f"<h3>{tema}</h3><ul style='list-style-type: none; padding-left: 0;'>"
        for t in tarjetas:
            html += f"<li style='margin-bottom: 20px;'>"
            html += f"<strong>{t['pregunta']}</strong><br>"
            html += f"<span style='color:gray; font-size:12px;'>[R: {t['repeticiones']} | EF: {t['dificultad']}]</span><br>"
            html += f"<a href='http://{ip_vps}:5000/calificar?id={t['id']}&resultado=error' style='color: #d9534f; text-decoration: none; font-size: 14px;'>[ Marcar como Difícil / Error ]</a>"
            html += f"</li>"
        html += "</ul><hr>"

    html += f"<div style='text-align: center; margin-top: 30px;'>"
    html += f"<a href='http://{ip_vps}:5000/finalizar' style='background-color: #5cb85c; color: white; padding: 10px 20px; text-decoration: none; font-weight: bold; border-radius: 5px;'>Finalizar repaso diario</a>"
    html += "</div></body></html>"

    msg.attach(MIMEText(html, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remitente, password)
        server.send_message(msg)
        server.quit()
        print("Correo enviado exitosamente.")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

if __name__ == "__main__":
    tarjetas_del_dia = seleccionar_tarjetas()
    if tarjetas_del_dia:
        enviar_correo(tarjetas_del_dia)
    else:
        print("No hay tarjetas programadas para repaso hoy.")