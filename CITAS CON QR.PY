import json
import threading
import time
import datetime
import smtplib
from email.mime.text import MIMEText
import qrcode
from flask import Flask, request, render_template_string
import os

# -----------------------------------
# CONFIGURACIÓN
# -----------------------------------
ARCHIVO = "citas.json"
QR_PATH = "cita_qr.png"

# Cambia estos datos por los tuyos
REM_CORREO = "TU_CORREO@gmail.com"
REM_CONTRASEÑA = "CONTRASEÑA_APP"

# -----------------------------------
# VALIDAR FECHA Y HORA
# -----------------------------------
def validar_fecha_hora(fecha, hora):
    try:
        datetime.datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
        return True
    except ValueError:
        return False

# -----------------------------------
# GUARDAR / CARGAR CITAS
# -----------------------------------
def cargar_citas():
    try:
        with open(ARCHIVO, "r") as f:
            return json.load(f)
    except:
        return []

def guardar_cita(cita):
    citas = cargar_citas()
    citas.append(cita)
    with open(ARCHIVO, "w") as f:
        json.dump(citas, f, indent=4)

# -----------------------------------
# ENVÍO DE CORREO
# -----------------------------------
def enviar_correo(destinatario, asunto, mensaje):
    msg = MIMEText(mensaje)
    msg["Subject"] = asunto
    msg["From"] = REM_CORREO
    msg["To"] = destinatario
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(REM_CORREO, REM_CONTRASEÑA)
            smtp.send_message(msg)
        print(f"✔ Correo enviado a {destinatario}")
    except Exception as e:
        print(f"❌ Error enviando correo: {e}")

# -----------------------------------
# RECORDATORIOS AUTOMÁTICOS
# -----------------------------------
def recordatorios():
    while True:
        citas = cargar_citas()
        ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        for cita in citas:
            fecha_hora = f"{cita['fecha']} {cita['hora']}"
            if fecha_hora == ahora and not cita.get("recordada", False):
                enviar_correo(
                    cita["email"],
                    "Recordatorio de cita",
                    f"Te recordamos tu cita:\n\n{cita['descripcion']}"
                )
                cita["recordada"] = True
                with open(ARCHIVO, "w") as f:
                    json.dump(citas, f, indent=4)
        time.sleep(60)

def iniciar_recordatorios():
    threading.Thread(target=recordatorios, daemon=True).start()

# -----------------------------------
# SERVIDOR WEB
# -----------------------------------
app = Flask(__name__)
FORMULARIO_HTML = """
<h1>Registrar Cita</h1>
<form method="POST">
  <label>Fecha (YYYY-MM-DD):</label><br>
  <input name="fecha"><br><br>
  <label>Hora (HH:MM):</label><br>
  <input name="hora"><br><br>
  <label>Descripción:</label><br>
  <input name="descripcion"><br><br>
  <label>Email:</label><br>
  <input name="email"><br><br>
  <button type="submit">Guardar Cita</button>
</form>
"""

EXITO_HTML = "<h1>¡Cita guardada correctamente!</h1>"

@app.route("/", methods=["GET", "POST"])
def registrar_cita_web():
    if request.method == "POST":
        fecha = request.form["fecha"]
        hora = request.form["hora"]
        descripcion = request.form["descripcion"]
        email = request.form["email"]
        if not validar_fecha_hora(fecha, hora):
            return "❌ Fecha u hora inválida. Usa formato YYYY-MM-DD y HH:MM."
        cita = {
            "fecha": fecha,
            "hora": hora,
            "descripcion": descripcion,
            "email": email,
            "recordada": False
        }
        guardar_cita(cita)
        return EXITO_HTML
    return FORMULARIO_HTML

# -----------------------------------
# GENERAR QR AUTOMÁTICO
# -----------------------------------
def generar_qr(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(QR_PATH)
    print(f"✔ QR generado: {QR_PATH}")
    print(f"🔹 Escanéalo para registrar citas desde cualquier dispositivo")
    print(f"🔹 Formato de fecha: YYYY-MM-DD")
    print(f"🔹 Formato de hora: HH:MM (24h)")

# -----------------------------------
# EJECUCIÓN PRINCIPAL
# -----------------------------------
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    HOST = "0.0.0.0"

    print("🔹 Iniciando agenda de citas")
    iniciar_recordatorios()  # Recordatorios en segundo plano

    # Detectar URL pública en Render automáticamente
    # Render asigna la URL pública como variable de entorno opcional (si no, usa localhost temporal)
    URL_PUBLICA = os.environ.get("RENDER_EXTERNAL_URL", f"http://localhost:{PORT}")

    generar_qr(URL_PUBLICA)  # Genera QR apuntando a la URL pública

    print(f"✔ Escanea el QR o abre en navegador: {URL_PUBLICA}")
    app.run(host=HOST, port=PORT)
