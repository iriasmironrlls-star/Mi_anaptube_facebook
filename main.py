from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import requests
from mutagen.mp4 import MP4, MP4Cover
import re

app = Flask(__name__)

def limpiar(t):
    """Limpia nombres de archivos y carpetas para evitar errores"""
    return re.sub(r'[\\/*?:"<>|]', '', " ".join(t.split()))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/descargar', methods=['POST'])
def descargar():
    url = request.form['url']
    
    # En servidores como Render, usamos la carpeta temporal /tmp/
    # para procesar el archivo antes de enviártelo.
    base_ruta = '/tmp/' if os.environ.get('RENDER') else '/sdcard/'
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 1. Analizar link de Facebook
            info = ydl.extract_info(url, download=False)
            autor = limpiar(info.get('uploader', 'Facebook_User'))
            titulo = limpiar(info.get('title', 'FB_Media'))
            
            # 2. Gestionar Carpeta
            carpeta = os.path.join(base_ruta, autor)
            if not os.path.exists(carpeta): 
                os.makedirs(carpeta)
            
            # 3. Descargar temporalmente
            ruta_m4a = os.path.join(carpeta, f"{titulo}.m4a")
            ydl_opts['outtmpl'] = os.path.join(carpeta, f"{titulo}.%(ext)s")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl_down:
                ydl_down.download([url])

            # 4. Metadatos Estilo Snaptube (Carátula y Artista)
            audio = MP4(ruta_m4a)
            img_data = requests.get(info['thumbnail']).content
            audio["covr"] = [MP4Cover(img_data, imageformat=MP4Cover.FORMAT_JPEG)]
            audio["\xa9nam"] = titulo
            audio["\xa9ART"] = autor
            audio["\xa9alb"] = autor
            audio.save()

            # 5. Renombrar a MP3
            nombre_mp3 = os.path.join(carpeta, f"{titulo}.mp3")
            if os.path.exists(nombre_mp3): 
                os.remove(nombre_mp3)
            os.rename(ruta_m4a, nombre_mp3)

            # --- EL PASO LEGENDARIO ---
            # Enviamos el archivo procesado directamente al navegador del usuario
            return send_file(nombre_mp3, as_attachment=True)

    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == '__main__':
    # Puerto estándar para Render y Pydroid
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

