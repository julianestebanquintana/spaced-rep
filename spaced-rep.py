import os
import json
import glob
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# Carga las variables desde el archivo .env oculto
load_dotenv()
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def seleccionar_tarjetas():
    archivos = glob.glob("db/*.json")
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
            seleccion_total.append((tema, pendientes[:5]))

    return seleccion_total

def enviar_correo(seleccion):
    destinatario = os.environ.get("EMAIL_DESTIN")
    api_key = os.environ.get("MAILGUN_API_KEY")
    dominio = "mail.calleydato.com"

    html = "<html><body style='font-family: sans-serif;'>"
    html += "<h2>Repaso Diario</h2>"
    ip_vps = os.environ.get("VPS_IP")

    for tema, tarjetas in seleccion:
        html += f"<h3>{tema}</h3><ul style='list-style-type: none; padding-left: 0;'>"
        for t in tarjetas:
            html += f"<li style='margin-bottom: 20px;'>"
            html += f"<strong>{t['pregunta']}</strong><br>"
            html += f"<span style='color:gray; font-size:12px;'>[R: {t['repeticiones']} | EF: {t['dificultad']}]</span><br>"
            html += f"<a href='https://rep.calleydato.com/calificar?id={t['id']}' style='color: #d9534f; text-decoration: none; font-size: 14px;'>[ Marcar como Difícil / Error ]</a>"
            html += f"</li>"
        html += "</ul><hr>"

    html += f"<div style='text-align: center; margin-top: 30px;'>"
    html += f"<a href='https://rep.calleydato.com/finalizar' style='background-color: #5cb85c; color: white; padding: 10px 20px; text-decoration: none; font-weight: bold; border-radius: 5px;'>Finalizar repaso diario</a>"
    html += "</div></body></html>"

    try:
        response = requests.post(
            f"https://api.mailgun.net/v3/{dominio}/messages",
            auth=("api", api_key),
            data={
                "from": f"Repaso Diario <ghost@{dominio}>",
                "to": destinatario,
                "subject": f"Repaso Espaciado - {datetime.now().strftime('%Y-%m-%d')}",
                "html": html
            }
        )
        if response.status_code == 200:
            print("Correo enviado exitosamente.")
        else:
            print(f"Error de Mailgun: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

if __name__ == "__main__":
    tarjetas_del_dia = seleccionar_tarjetas()
    if tarjetas_del_dia:
        ids_enviados = [t['id'] for tema, tarjetas in tarjetas_del_dia for t in tarjetas]
        with open('enviadas_hoy.json', 'w') as f:
            json.dump({"fecha": str(datetime.now().date()), "ids": ids_enviados}, f)
        enviar_correo(tarjetas_del_dia)
    else:
        print("No hay tarjetas programadas para repaso hoy.")
