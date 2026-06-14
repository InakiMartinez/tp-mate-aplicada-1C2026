import os
import base64
import getpass
import configparser

from passman import *
from configparser import *
from zxcvbn import zxcvbn


class Util:
	def __init__(self, config_path):
		self.load_config(config_path)
		self.create_directories()
		self.create_files()

		self.unlocked = False
		self.pm = PasswordManager(self.config)

	def load_config(self, path):
		self.config = configparser.ConfigParser(interpolation=ExtendedInterpolation())
		self.config.read(path)

	def set_current_menu(self, menu):
		self.current_menu = menu

	def is_password_strong(self, password):
		"""
		Mide la fortaleza de la contraseña usando zxcvbn.

		Retorna True solo si obtiene el puntaje maximo (4).
		"""

		result = zxcvbn(password)

		if result['score'] == 4:
			return True

		return False

	def get_strong_password(self, length=12):
		"""
		Genera una contraseña aleatoria que supere el medidor de fortaleza.
		"""

		password = base64.b64encode(os.urandom(length)).decode()

		while not self.is_password_strong(password):
			password = base64.b64encode(os.urandom(length)).decode()

		return password

	def get_user_password(self):
		"""
		Solicita una contraseña al usuario, o la genera de forma aleatoria.

		Si el usuario ingresa la contraseña manualmente, se valida su fortaleza.
		"""

		gen_pass = input("Generar contraseña ? [s/N]: ")

		if gen_pass.lower() == "s":
			password = self.get_strong_password()
			print("Contraseña generada:", password)
		else:
			password = getpass.getpass("Contraseña: ")

			while password == "":
				password = getpass.getpass("Contraseña: ")

			while not self.is_password_strong(password):
				print(
				"\nLa contraseña ingresada es debil.\n"
				"\nUna contraseña fuerte consiste de:\n"
				"- Una longitud mayor o igual a 12.\n"
				"- Uno o mas numeros.\n"
				"- Uno o mas caracteres en minuscula.\n"
				"- Uno o mas caracteres en mayuscula.\n"
				"- Uno o mas caracteres especiales. ( ej: !<=>*()+,- )\n"
				)

				password = getpass.getpass("\nContraseña: ")

		return password

	def create_directories(self):
		for _ in self.config['Paths']:
			d = self.config['Paths'][_]

			if not os.path.exists(d):
				os.makedirs(d)

			if d == "home":
				os.chdir(d)

	def create_files(self):
		for _ in self.config['Files']:
			f = self.config['Files'][_]

			if not os.path.exists(f):
				with open(f, "w"):
					pass

	def setup_master(self):
		"""
		Configura la master password la primera vez que se ejecuta la app.
		"""

		print(
		"\nNo hay una master password configurada.\n"
		"Esta clave protege todas tus credenciales y no puede recuperarse.\n"
		)

		password = self.get_user_password()
		self.pm.create_master(password)
		print("\nMaster password configurada.")

	def unlock(self):
		"""
		Desbloquea la aplicacion verificando la master password.
		"""

		password = getpass.getpass("\nMaster password: ")

		if self.pm.verify_master(password):
			self.unlocked = True
			print("\nAplicacion desbloqueada.")
			return True
		else:
			self.unlocked = False
			print("\nMaster password invalida.")
			return False

	def lock(self):
		"""
		Bloquea la aplicacion y descarta la clave de cifrado.
		"""

		self.pm.fernet = None
		self.unlocked = False
		print("\nAplicacion bloqueada.")

	def view_credentials(self):
		credentials = self.pm.load_credentials()

		if credentials:
			for i, (_, v) in enumerate(credentials.items(), 1):
				print(f'\n{i})\nNombre: {v["name"]}\nContraseña: {v["password"]}')
		else:
			print("\nNo hay credenciales almacenadas.")

	def insert_credentials(self):
		print("\nIngrese los datos de su credencial:\n")

		name = input("Nombre: ")

		while name == "":
			name = input("Nombre: ")

		password = self.get_user_password()

		credentials = self.pm.load_credentials()
		credential_id = base64.b64encode(os.urandom(12)).decode()

		while credentials.get(credential_id) != None:
			credential_id = base64.b64encode(os.urandom(12)).decode()

		credentials[credential_id] = {"name": name, "password": password}
		self.pm.save_credentials(credentials)
		print("\nCredencial almacenada.")

	def delete_credentials(self):
		temp = {}
		credentials = self.pm.load_credentials()
		credentials_len = len(credentials)

		if credentials:
			for i, (k, v) in enumerate(credentials.items(), 1):
				print(f'\n{i})\nNombre: {v["name"]}\nContraseña: {v["password"]}')
				temp[i] = k

			while True:
				print("\nIngrese el numero de la credencial que desea eliminar [ 0 para cancelar ].")

				try:
					option = int(input("\nOpcion: "))

					if option == 0:
						break

					if option >= 1 and option <= credentials_len:
						del credentials[temp[option]]
						self.pm.save_credentials(credentials)
						print("\nCredencial eliminada.")
						break
				except ValueError:
					pass

				print("\nOpcion invalida.")
		else:
			print("\nNo hay credenciales almacenadas.")

	def modify_credentials(self):
		temp = {}
		credentials = self.pm.load_credentials()
		credentials_len = len(credentials)

		if credentials:
			for i, (k, v) in enumerate(credentials.items(), 1):
				print(f'\n{i})\nNombre: {v["name"]}\nContraseña: {v["password"]}')
				temp[i] = k

			while True:
				print("\nIngrese el numero de la credencial que desea modificar [ 0 para cancelar ].")

				try:
					option = int(input("\nOpcion: "))

					if option == 0:
						break

					if option >= 1 and option <= credentials_len:
						print("\nIngrese los nuevos datos de su credencial:\n")

						name = input("Nombre: ")

						while name == "":
							name = input("Nombre: ")

						password = self.get_user_password()

						credentials[temp[option]] = {"name": name, "password": password}
						self.pm.save_credentials(credentials)
						print("\nCredencial modificada.")
						break
				except ValueError:
					pass

				print("\nOpcion invalida.")
		else:
			print("\nNo hay credenciales almacenadas.")
