# Administrador de Contraseñas

Trabajo Práctico Final de Criptografía — Matemática Aplicada.

Aplicación de consola que permite crear, modificar y eliminar registros del
estilo **NOMBRE - CONTRASEÑA**. Las credenciales se guardan en un archivo
cifrado que solo puede leerse conociendo la *master password*. Incluye un
generador de contraseñas aleatorias y un medidor de fortaleza.

## Características

- Almacenamiento cifrado de las credenciales en disco.
- Acceso protegido por una única *master password* (clave privada).
- Alta, baja, modificación y consulta de credenciales.
- Generador de contraseñas aleatorias seguras.
- Medidor de fortaleza de contraseñas.

## Cómo funciona la criptografía

1. **Master password.** Al ejecutar la aplicación por primera vez se configura
   una master password. Esta clave nunca se guarda: a partir de ella, y de un
   *salt* aleatorio único, se deriva una clave con **scrypt**. Del resultado se
   almacena solo su *hash* (SHA-512) junto con el *salt* en `master.txt`. En
   cada desbloqueo se repite la derivación y se compara el hash para validar la
   master password.

2. **Cifrado de credenciales.** La clave derivada con scrypt se usa como clave
   de **Fernet** (AES-128 en modo CBC + HMAC-SHA256). El archivo de
   credenciales se cifra por completo, garantizando confidencialidad,
   integridad y autenticación. Sin la master password correcta no es posible
   descifrarlo.

3. **Salt.** El salt aleatorio evita que dos master passwords iguales produzcan
   la misma clave derivada y protege frente a ataques con tablas precalculadas
   (*rainbow tables*).

## Requisitos

- Python 3.8 o superior.
- Dependencias:

```
pip install cryptography zxcvbn
```

## Uso

Desde la carpeta del proyecto:

### Versión con Interfaz Gráfica (Recomendado)

```
python gui.py
```

### Versión de Consola

```
python main.py
```

La primera vez se solicitará configurar la master password. Luego se muestra el
menú principal:

```
1 - Desbloquear aplicacion.
0 - Salir.
```

Una vez desbloqueada la aplicación con la master password:

```
2 - Bloquear aplicacion.
3 - Agregar credencial.
4 - Obtener credenciales.
5 - Eliminar credencial.
6 - Modificar credencial.
```

Al agregar o modificar una credencial se puede ingresar la contraseña
manualmente (se valida su fortaleza) o generar una aleatoria automáticamente.

## Estructura del proyecto

```
config.ini    Rutas y archivos de la aplicación.
passman.py    PasswordManager: derivación de clave, cifrado y descifrado.
util.py       Util: lógica de menús, generador y medidor de fortaleza.
main.py       Punto de entrada y menús.
gui.py        Punto de entrada de la interfaz gráfica (GUI) con CustomTkinter.
```

Los datos se almacenan en la carpeta `Datos/`, que se crea automáticamente:

```
Datos/master.txt          Hash y salt de la master password.
Datos/credenciales.dat    Credenciales cifradas.
```

> **Importante:** la master password no puede recuperarse. Si se pierde, las
> credenciales almacenadas quedan inaccesibles.
