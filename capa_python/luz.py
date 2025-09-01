import tkinter as tk

class Luz:
	def __init__(self, parent_controls, parent_canvas, nombre, color_off, color_on):
		self.nombre = nombre
		self.color_off = color_off
		self.color_on = color_on
		self.encendida = False
		self.parent_canvas = parent_canvas
		self.circle = None  # referencia al círculo en el canvas
		self._on_duration_change = None  # callback opcional para cambios del scale
		self.http = None  # cliente HTTP opcional para controlar hardware

		# Botón de la luz
		self.boton = tk.Button(
			parent_controls,
			text="OFF",
			bg=color_off,
			fg="black",
			font=("Arial", 14, "bold"),
			width=7,
			height=1,
			command=self.toggle
		)

		# Slider de sincronización/tiempo (segundos)
		self.scale = tk.Scale(
			parent_controls,
			from_=0,
			to=10,
			orient="horizontal",
			bg=color_off,
			fg="black",
			font=("Arial", 12),
			length=270,
			showvalue=True,
			tickinterval=2,
			command=self.on_scale_change  # notifica cambios
		)

	def place_button(self, x, y):
		self.boton.place(x=x, y=y)

	def place_scale(self, x, y):
		self.scale.place(x=x, y=y)

	def place_circle(self, x1, y1, x2, y2):
		"""Crea un óvalo en el canvas en la posición dada."""
		self.circle = self.parent_canvas.create_oval(
			x1, y1, x2, y2,
			fill=self.color_off,
			outline="black"
		)

	def on_scale_change(self, value):
		try:
			valor = int(float(value))
		except Exception:
			valor = 0
		# Avisar al controlador (p.ej., Semaforo) para reiniciar la rutina con los nuevos tiempos
		if self._on_duration_change:
			self._on_duration_change(self.nombre, valor)
		# En modo manual (sin rutina) no afectamos la luz; el scale solo representa duración de la rutina

	def toggle(self):
		self.encendida = not self.encendida
		if self.encendida:
			self.boton.config(bg=self.color_on, fg="white", text="ON")
			if self.circle:
				self.parent_canvas.itemconfig(self.circle, fill=self.color_on)
			# HTTP: encender LED en hardware (opcional)
			if self.http:
				try:
					self.http.request_encender_led(self.nombre)
				except Exception as e:
					print(f"HTTP error encender {self.nombre}: {e}")

		else:
			self.boton.config(bg=self.color_off, fg="black", text="OFF")
			if self.circle:
				self.parent_canvas.itemconfig(self.circle, fill=self.color_off)
			# HTTP: apagar LED en hardware (opcional)
			if self.http:
				try:
					self.http.request_apagar_led(self.nombre)
				except Exception as e:
					print(f"HTTP error apagar {self.nombre}: {e}")

	
	def activar(self):
		self.boton.config(state="normal")
		self.scale.config(state="normal")

	def desactivar(self):
		self.encendida = False
		self.boton.config(state="disabled", bg=self.color_off, fg="black", text="OFF")
		self.scale.config(state="disabled", bg=self.color_off)
		if self.circle:
			self.parent_canvas.itemconfig(self.circle, fill=self.color_off)

	def activar_circle(self):
		if self.circle:
			self.parent_canvas.itemconfig(self.circle, fill=self.color_on)
	
	def desactivar_circle(self):
		if self.circle:
			self.parent_canvas.itemconfig(self.circle, fill=self.color_off)

	# ---- Utilidades para integración con la rutina ----
	def set_duration_change_callback(self, callback):
		"""Registra un callback que recibe (nombre_luz: str, valor: int) al cambiar el scale."""
		self._on_duration_change = callback

	def set_http_client(self, http_client):
		"""Registra un cliente HTTP para enviar comandos al hardware en modo manual."""
		self.http = http_client

	def disable_button(self):
		"""Deshabilita solo el botón (mantiene el scale habilitado)."""
		self.boton.config(state="disabled")

	def enable_button(self):
		"""Habilita solo el botón (no toca el scale)."""
		self.boton.config(state="normal")
