import tkinter as tk
import threading
from PIL import Image, ImageTk
from luz import Luz
from httpClient import HTTPClient

class Semaforo:
	def __init__(self, cuadro):
		self.http = HTTPClient("172.26.166.131")  # Cambiar por la IP del servidor
		self.cuadro = cuadro
		self.cuadro.geometry("1000x720")
		self.cuadro.title("SemaforoOGT")
		self.rutina = False
		self._scheduled = []  # ids de after programados para poder cancelarlos

		# Background principal
		bg = tk.Frame(self.cuadro, bg="black", width=1000, height=720)
		bg.place(x=0, y=0)

		 # Frame controles
		self.controles = tk.Frame(self.cuadro, bg="#CBCBCA", width=300, height=650)
		self.controles.place(x=30, y=40)

		self.semaforo_frame = tk.Canvas(self.cuadro, bg="black", width=650, height=720, highlightthickness=0)
		self.semaforo_frame.place(x=350, y=0)

		# Títulos
		tk.Label(self.controles, text="Controles", bg="#CBCBCA", fg="black",
				 font=("Lucida Console", 26)).place(x=55, y=15)
		tk.Label(self.controles, text="Luces", bg="#CBCBCA", fg="black",
				 font=("Lucida Console", 19)).place(x=10, y=70)
		
		# Luces
		self.luz_verde = Luz(self.controles, self.semaforo_frame, "verde", "#D5E8D4", "#00E800")
		self.luz_amarilla = Luz(self.controles, self.semaforo_frame, "amarillo", "#FFF2CC", "#FFF800")
		self.luz_roja = Luz(self.controles, self.semaforo_frame, "rojo", "#F8CECC", "#E51400")

		self.luz_verde.http = self.http
		self.luz_amarilla.http = self.http
		self.luz_roja.http = self.http

		# Cuando cambie cualquier scale, reiniciar la rutina (si está activa)
		for luz in (self.luz_verde, self.luz_amarilla, self.luz_roja):
			luz.set_duration_change_callback(self._on_scale_duration_changed)

		self.luz_verde.place_button(7, 110)
		self.luz_amarilla.place_button(102, 110)
		self.luz_roja.place_button(197, 110)

		self.luz_verde.place_scale(10, 355)
		self.luz_amarilla.place_scale(10, 425)
		self.luz_roja.place_scale(10, 495)



		tk.Label(self.controles, text="Rutina", bg="#CBCBCA", fg="black",
				 font=("Lucida Console", 19)).place(x=10, y=180)

		self.rutina_on = tk.Button(self.controles, text="ON", bg="#D5E8D4", fg="black",
								   font=("Arial", 14, "bold"), width=11, command=self.activar_rutina)
		self.rutina_off = tk.Button(self.controles, text="OFF", bg="#E51400", fg="white",
									font=("Arial", 14, "bold"), width=11, state="disabled", command=self.desactivar_rutina)

		self.rutina_on.place(x=7, y=220)
		self.rutina_off.place(x=150, y=220)

		# Label sincronizacion
		tk.Label(self.controles, text="Sincronizacion\n de tiempo", bg="#CBCBCA", fg="black",
				 font=("Lucida Console", 19)).place(x=10, y=290)
		
		 # Botón cerrar
		tk.Button(self.controles, text="Cerrar", bg="#E51400", fg="white",
				  font=("Lucida Console", 14, "bold"), width=15, height=1,
				  command=self.Close_Window).place(x=55, y=600)

		# Imagen de fondo en el Canvas
		img = Image.open(r"D:\Documents\UNI\Universidad\BUAP\9no Semestre\Arq SOft\CODES\source\Interfaz_Semaforo_3\semaforoPY\semaforo2.png")
		img = img.resize((400, 600))
		self.img_tk = ImageTk.PhotoImage(img)
		self.semaforo_frame.create_image(325, 360, image=self.img_tk)  # centrado

		self.luz_roja.place_circle(265, 150, 380, 270)
		self.luz_amarilla.place_circle(265, 325, 380, 445)
		self.luz_verde.place_circle(265, 500, 380, 615)

	def activar_rutina(self):
		# Deshabilita solo los botones; mantener scales habilitados para ajustar tiempos
		self.luz_verde.disable_button()
		self.luz_amarilla.disable_button()
		self.luz_roja.disable_button()
		# Asegurar que cualquier parpadeo manual se detenga
		self.luz_verde.encendida = False
		self.luz_amarilla.encendida = False
		self.luz_roja.encendida = False
		# Asegurar círculos apagados al iniciar
		self.luz_verde.desactivar_circle()
		self.luz_amarilla.desactivar_circle()
		self.luz_roja.desactivar_circle()

		self.rutina_on.config(bg="#00E800", fg="white")
		self.rutina_off.config(bg="#F8CECC", fg="black")
		self.rutina = True

		self.rutina_on.config(state="disabled")
		self.rutina_off.config(state="normal")
		# Enviar rutina actual al hardware
		self._send_routine_update()
		self._start_routine_cycle()

	def _on_scale_duration_changed(self, nombre_luz, valor):
		# Si la rutina está activa, reiniciar el ciclo con los nuevos tiempos
		if self.rutina:
			self._cancel_scheduled()
			# Apagar de inmediato para no dejar residuos encendidos
			self.luz_verde.desactivar_circle()
			self.luz_amarilla.desactivar_circle()
			self.luz_roja.desactivar_circle()
			# Enviar actualización de rutina al hardware con los nuevos valores
			self._send_routine_update()
			# Reinicia inmediatamente el ciclo con los valores actuales
			self._start_routine_cycle()

	def _send_routine_update(self):
		"""Envía las duraciones actuales de la rutina al hardware usando HTTP en un hilo."""
		if not hasattr(self, 'http') or self.http is None:
			return
		v = int(self.luz_verde.scale.get())
		a = int(self.luz_amarilla.scale.get())
		r = int(self.luz_roja.scale.get())
		def _worker():
			try:
				self.http.request_comenzar_rutina("verde", v)
				self.http.request_comenzar_rutina("amarillo", a)
				self.http.request_comenzar_rutina("rojo", r)
			except Exception as e:
				print(f"HTTP rutina error: {e}")
		threading.Thread(target=_worker, daemon=True).start()

	def _cancel_scheduled(self):
		for after_id in self._scheduled:
			try:
				self.cuadro.after_cancel(after_id)
			except Exception:
				pass
		self._scheduled.clear()

	def _schedule(self, delay_ms, callback):
		"""Programa un after y guarda su id para poder cancelarlo al reiniciar."""
		after_id = self.cuadro.after(delay_ms, callback)
		self._scheduled.append(after_id)
		return after_id

	def _start_routine_cycle(self):
		self._cancel_scheduled()
		if not self.rutina:
			return
		# Poner todas las luces en OFF antes de iniciar el nuevo ciclo
		self.luz_verde.desactivar_circle()
		self.luz_amarilla.desactivar_circle()
		self.luz_roja.desactivar_circle()
		# Leer duraciones desde los scales (segundos -> ms)
		self.dur_verde = int(self.luz_verde.scale.get())
		self.dur_amarillo = int(self.luz_amarilla.scale.get())
		self.dur_rojo = int(self.luz_roja.scale.get())
		# Comienza con verde
		self._fase_verde_on()

	def _rutina_loop(self):
		# Obsoleto: se reemplaza por _start_routine_cycle
		self._start_routine_cycle()

	def _rutina_verde_parpadeo(self):
		if not self.rutina:
			self.luz_verde.desactivar_circle()
			return
				# Fase 2: Verde parpadeo 3 veces
		self.luz_verde.desactivar_circle()
		self.parpadeos = 0
		self._verde_parpadeo_step()

	def _verde_parpadeo_step(self):
		if not self.rutina:
			self.luz_verde.desactivar_circle()
			return

		if self.parpadeos < 3:
			self.luz_verde.activar_circle()
			self._schedule(500, self._verde_parpadeo_off)
		else:
			self.luz_verde.desactivar_circle()
			self._schedule(100, self._rutina_amarillo)

	def _verde_parpadeo_off(self):
		if not self.rutina:
			self.luz_verde.desactivar_circle()
			return

		self.luz_verde.desactivar_circle()
		self.parpadeos += 1
		self._schedule(500, self._verde_parpadeo_step)

	def _rutina_amarillo(self):
		if not self.rutina:
			self.luz_amarilla.desactivar_circle()
			return

		# Fase 3: Amarillo encendido durante su duración
		self.luz_amarilla.activar_circle()
		self._schedule(max(0, int(self.dur_amarillo * 1000)), self._rutina_amarillo_off)

	def _rutina_amarillo_off(self):
		self.luz_amarilla.desactivar_circle()
		self._schedule(100, self._rutina_rojo)

	def _rutina_rojo(self):
		if not self.rutina:
			self.luz_roja.desactivar_circle()
			return

		# Fase 4: Rojo encendido durante su duración
		self.luz_roja.activar_circle()
		self._schedule(max(0, int(self.dur_rojo * 1000)), self._rutina_rojo_off)

	def _rutina_rojo_off(self):
		self.luz_roja.desactivar_circle()
		self._schedule(100, self._start_routine_cycle)  # Vuelve a iniciar el ciclo

	# ---- Nuevas fases con duraciones dinámicas ----
	def _fase_verde_on(self):
		if not self.rutina:
			return
		# Si duración de verde es 0, saltar directo a amarillo
		if self.dur_verde <= 0:
			self.luz_verde.desactivar_circle()
			return self._rutina_amarillo()
		self.luz_verde.activar_circle()
		# Encendido por duración indicada, luego parpadeo 3 veces como avisador
		self._schedule(int(self.dur_verde * 1000), self._rutina_verde_parpadeo)


	def desactivar_rutina(self):
		self.rutina = False
		self._cancel_scheduled()
		self.rutina_on.config(bg="#D5E8D4", fg="black")
		self.rutina_off.config(bg="#E51400", fg="white")

		self.luz_verde.desactivar_circle()
		self.luz_amarilla.desactivar_circle()
		self.luz_roja.desactivar_circle()

		# Rehabilitar botones manuales y dejar las luces en OFF visualmente
		self.luz_verde.enable_button()
		self.luz_amarilla.enable_button()
		self.luz_roja.enable_button()
		# reset apariencia de botones
		self.luz_verde.boton.config(bg=self.luz_verde.color_off, fg="black", text="OFF")
		self.luz_amarilla.boton.config(bg=self.luz_amarilla.color_off, fg="black", text="OFF")
		self.luz_roja.boton.config(bg=self.luz_roja.color_off, fg="black", text="OFF")

		self.rutina_on.config(state="normal")
		self.rutina_off.config(state="disabled")

		# Notificar al hardware que se detuvo la rutina
		if hasattr(self, 'http') and self.http is not None:
			def _stop_worker():
				try:
					self.http.request_detener_rutina()
				except Exception as e:
					print(f"HTTP rutina off error: {e}")
			threading.Thread(target=_stop_worker, daemon=True).start()

	def Close_Window(self):
		self.cuadro.destroy()

if __name__ == "__main__":
	cuadro = tk.Tk()
	app = Semaforo(cuadro)
	cuadro.mainloop()
