import os
import json
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken


class PasswordManager:
	def __init__(self, config):
		self.fernet = None
		self.config = config

	def get_hash(self, data):
		return hashlib.sha512(data).hexdigest()

	def get_salt(self, size):
		return os.urandom(size)

	def derive_key(self, password, salt, n=2**14, r=8, p=1, dklen=32):
		"""
		Utiliza un key derivation function (scrypt) para obtener una clave a
		partir de la master password.

		Al resultado obtenido se le hace un encode en base64 para que se pueda
		utilizar al momento de encriptar datos con Fernet.
		"""

		key = hashlib.scrypt(
			password,
			salt=salt,
			n=n,
			r=r,
			p=p,
			dklen=dklen,
		)

		return base64.urlsafe_b64encode(key)

	def encrypt_data(self, data):
		return self.fernet.encrypt(data.encode())

	def decrypt_data(self, data):
		return self.fernet.decrypt(data).decode()

	def master_exists(self):
		"""
		Indica si ya fue configurada una master password.
		"""

		master_file = self.config['Files']['master']

		with open(master_file, "rt") as f:
			return f.read().strip() != ""

	def create_master(self, password):
		"""
		Configura la master password por primera vez.

		Se almacena en el archivo master:
		- hash (hash de la clave derivada de la master password + salt)
		- salt (valor random unico, almacenado con un encode en base64)

		No se guarda la master password en ningun momento.
		"""

		salt = self.get_salt(32)
		key = self.derive_key(password.encode(), salt)
		key_hash = self.get_hash(key)

		master_data = {
			"hash": key_hash,
			"salt": base64.b64encode(salt).decode(),
		}

		master_file = self.config['Files']['master']

		with open(master_file, "wt") as f:
			f.write(json.dumps(master_data))

	def verify_master(self, password):
		"""
		Verifica que la master password ingresada sea valida.

		Adicionalmente, si es valida, genera la clave utilizada por Fernet
		para encriptar y desencriptar los datos.

		Retorna:
		- True si la master password es valida.
		- False si la master password no es valida.
		"""

		master_file = self.config['Files']['master']

		with open(master_file, "rt") as f:
			master_data = json.loads(f.read())

		salt = base64.b64decode(master_data["salt"])
		key = self.derive_key(password.encode(), salt)
		key_hash = self.get_hash(key)

		if master_data["hash"] != key_hash:
			return False

		self.fernet = Fernet(key)
		return True

	def load_credentials(self):
		"""
		Lee el archivo de credenciales y desencripta el contenido.

		Retorna un dict con las credenciales { id: { name: "", password: "" } }.
		"""

		credentials_file = self.config['Files']['credentials']

		decrypted_credentials = {}

		with open(credentials_file, "rb") as f:
			encrypted_credentials = f.read()

			if encrypted_credentials != b'':
				decrypted_credentials = json.loads(self.decrypt_data(encrypted_credentials))

		return decrypted_credentials

	def save_credentials(self, credentials):
		"""
		Encripta y almacena las credenciales.

		Se sobreescribe el archivo de credenciales previo con las nuevas.
		"""

		credentials_file = self.config['Files']['credentials']

		with open(credentials_file, "wb") as f:
			if not credentials:
				pass
			else:
				encrypted_credentials = self.encrypt_data(json.dumps(credentials))
				f.write(encrypted_credentials)
