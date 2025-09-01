import requests

class HTTPClient:
	def __init__(self, ip):
		self.ip = ip
		self.base_url = f"http://{self.ip}"

	def request_encender_led(self, color):
		url = f"{self.base_url}/led/{color}/on"
		try:
			response = requests.get(url, timeout=2)
			response.raise_for_status()
			return response.text
		except Exception as e:
			print(f"Error HTTP GET: {e}")
			return None

	def request_apagar_led(self, color):
		url = f"{self.base_url}/led/{color}/off"
		try:
			response = requests.get(url, timeout=2)
			response.raise_for_status()
			return response.text 
		except Exception as e:
			print(f"Error HTTP GET: {e}")
			return None

	def request_comenzar_rutina(self, color, tiempo):
		url = f"{self.base_url}/rutina/{color}/{tiempo}/on"
		try:
			response = requests.get(url, timeout=2)
			response.raise_for_status()
			return response.text
		except Exception as e:
			print(f"Error HTTP GET: {e}")
			return None
		
	def request_detener_rutina(self):
		url = f"{self.base_url}/rutina/off"
		try:
			response = requests.get(url, timeout=2)
			response.raise_for_status()
			return response.text
		except Exception as e:
			print(f"Error HTTP GET: {e}")
			return None
		
	def pussyDestruction(self):
		url = f"{self.base_url}/destruction"
		try:
			response = requests.get(url, timeout=2)
			response.raise_for_status()
			return response.text
		except Exception as e:
			print(f"Error HTTP GET: {e}")
			return None
