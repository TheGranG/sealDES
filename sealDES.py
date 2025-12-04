import customtkinter as ctk
import yt_dlp
import os
import threading
from pathlib import Path

# --- 1. CONFIGURACIÓN DE RUTAS Y APARIENCIA ---

# Definir la carpeta donde se guardarán los archivos
# Busca la carpeta "Downloads" del usuario y crea una subcarpeta específica.
CARPETA_BASE_DESCARGAS = str(Path.home() / "Downloads")
CARPETA_DESTINO = os.path.join(CARPETA_BASE_DESCARGAS, "DescargasVideoApp")

# Configuración global de CustomTkinter
ctk.set_appearance_mode("System") 
ctk.set_default_color_theme("blue") 

class DescargadorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuración de la Ventana
        self.title("DESCARGADOR VIDEO/AUDIO")
        self.geometry("550x450") 
        
        # Crear la carpeta de destino si no existe
        if not os.path.exists(CARPETA_DESTINO):
            os.makedirs(CARPETA_DESTINO)
        
        # Variables de estado
        self.formato_seleccionado = ctk.StringVar(value="Video (MP4)")
        self.calidad_seleccionada = ctk.StringVar(value="Máxima (1080p)") 

        # --- Elementos de la GUI ---
        
        # 1. Campo de Entrada para la URL
        self.url_label = ctk.CTkLabel(self, text="URL del Video:")
        self.url_label.pack(pady=(20, 5), padx=10)
        
        self.url_entry = ctk.CTkEntry(self, width=400, placeholder_text="Pega la URL aquí...")
        self.url_entry.pack(pady=5, padx=10)
        
        # 2. Selector de Formato (con comando de actualización de calidad)
        self.formato_selector = ctk.CTkOptionMenu(
            self,
            values=["Video (MP4)", "Audio (MP3)"],
            variable=self.formato_seleccionado,
            command=self.mostrar_ocultar_calidad 
        )
        self.formato_selector.pack(pady=10, padx=10)
        
        # 3. Selector de Calidad (Se maneja por la función mostrar_ocultar_calidad)
        self.calidad_label = ctk.CTkLabel(self, text="Calidad del Video:")
        self.calidad_label.pack(pady=5, padx=10)
        
        self.calidad_selector = ctk.CTkOptionMenu(
            self,
            values=["Máxima (1080p)", "Alta (720p)", "Media (480p)"], 
            variable=self.calidad_seleccionada
        )
        self.calidad_selector.pack(pady=5, padx=10)
        
        # 4. Botón de Descarga
        self.download_button = ctk.CTkButton(
            self,
            text="DESCARGAR",
            command=self.iniciar_descarga
        )
        self.download_button.pack(pady=15, padx=10)

        # 5. Etiqueta de Estado/Progreso
        self.status_label = ctk.CTkLabel(self, text="Esperando URL...", text_color="gray")
        self.status_label.pack(pady=5, padx=10)
        
        # 6. Barra de Progreso
        self.progress_bar = ctk.CTkProgressBar(self, width=400)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5, padx=10)
        
        # 7. Etiqueta informativa de la ruta de guardado
        self.ruta_info_label = ctk.CTkLabel(self, 
                                            text=f"Guardando en: {CARPETA_DESTINO}",
                                            font=ctk.CTkFont(size=10),
                                            text_color="gray")
        self.ruta_info_label.pack(pady=(5, 10), padx=10)
        
        # Estado inicial (Asegura que la calidad se vea al inicio)
        self.mostrar_ocultar_calidad(self.formato_seleccionado.get())


    def mostrar_ocultar_calidad(self, choice):
        """Muestra u oculta el selector de calidad si se elige audio."""
        if choice == "Audio (MP3)":
            self.calidad_selector.pack_forget()
            self.calidad_label.pack_forget()
        else:
            self.calidad_label.pack(pady=5, padx=10)
            self.calidad_selector.pack(pady=5, padx=10)


    # --- Lógica de la Descarga ---
    
    def hook_progreso(self, d):
        """Función llamada por yt-dlp para actualizar el estado de la descarga."""
        
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            
            if total_bytes:
                downloaded = d.get('downloaded_bytes', 0)
                self.progress_bar.set(downloaded / total_bytes)
                self.status_label.configure(
                    text=f"Descargando: {d['_percent_str']} a {d['_speed_str']}",
                    text_color="orange"
                )
            
        elif d['status'] == 'finished':
            # La descarga terminó, ahora FFmpeg fusiona los archivos
            self.progress_bar.set(1)
            self.status_label.configure(text="Fusionando video y audio (FFmpeg)...", text_color="blue")
            
            
    def iniciar_descarga(self):
        url = self.url_entry.get()
        if not url:
            self.status_label.configure(text="Error: ¡Introduce una URL!", text_color="red")
            return

        # Desactivar elementos, reiniciar barra y estado
        self.download_button.configure(state="disabled")
        self.progress_bar.set(0)
        self.status_label.configure(text="Buscando información del video...", text_color="orange")

        # Iniciar la descarga en un hilo separado
        download_thread = threading.Thread(target=self.ejecutar_descarga, args=(url,))
        download_thread.start()

    def ejecutar_descarga(self, url):
        modo_audio = self.formato_seleccionado.get() == "Audio (MP3)"
        
        # --- Lógica para el Filtro de Calidad ---
        filtro_calidad = ""
        if not modo_audio:
            calidad_texto = self.calidad_seleccionada.get()
            if "720p" in calidad_texto:
                filtro_calidad = "bestvideo[height<=720]" 
            elif "480p" in calidad_texto:
                filtro_calidad = "bestvideo[height<=480]"
            else:
                filtro_calidad = "bestvideo" 

        # 1. Configuración de yt-dlp
        if modo_audio:
            formato_yt_dlp = 'bestaudio/best'
        else:
            # Combina el filtro de calidad + el mejor audio + la mejor opción genérica
            formato_yt_dlp = f"{filtro_calidad}+bestaudio[ext=m4a]/best[ext=mp4]/best"


        ydl_opts = {
            'format': formato_yt_dlp,
            # Usamos la ruta fija de Descargas
            'outtmpl': os.path.join(CARPETA_DESTINO, '%(title)s.%(ext)s'), 
            'progress_hooks': [self.hook_progreso],
            
            # Opciones para suprimir mensajes no esenciales y advertencias
            'quiet': True,              
            'no_warnings': True,        
            'logtostderr': False,
            
            # Configuración de FFmpeg para MP3
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if modo_audio else [],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Éxito
            self.status_label.configure(text="¡Descarga Completa!", text_color="green")
            
        except Exception as e:
            # Manejo de errores
            error_text = str(e)
            if "ffmpeg is not installed" in error_text:
                error_msg = "Error: FFmpeg no está instalado/accesible."
            elif "Unsupported URL" in error_text:
                error_msg = "Error: URL no soportada o inválida."
            else:
                error_msg = f"Error Desconocido: {error_text[:45]}..."
                
            self.status_label.configure(text=error_msg, text_color="red")
            self.progress_bar.set(0)
            
        finally:
            self.download_button.configure(state="normal")

if __name__ == "__main__":
    app = DescargadorApp()
    app.mainloop()
