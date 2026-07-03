# Demo rápida — Administrador de Contraseñas

Guía para mostrar la aplicación en clase en pocos minutos. Pensada para una
exposición ágil: cada paso indica qué tipear y qué decir mientras se ejecuta.

## Antes de empezar

Instalar dependencias (una sola vez):

```
pip install cryptography zxcvbn
```

> Tip: borrá la carpeta `Datos/` antes de la demo para arrancar limpio y poder
> mostrar el alta de la master password. Si no existe, se crea sola.

Ejecutar:

```
python main.py
```

## Paso 1 — Configurar la master password

La primera vez la app pide configurar la clave privada que protege todo.

```
Generar contraseña ? [s/N]: N
Contraseña: ************
```

**Qué decir:** esta master password nunca se guarda; a partir de ella se deriva
una clave con scrypt + salt. Solo se almacena su hash. Si se pierde, no hay
recuperación.

## Paso 2 — Desbloquear la aplicación

```
1 - Desbloquear aplicacion.
0 - Salir.

Opcion: 1

Master password: ************
```

**Qué decir:** acá se vuelve a derivar la clave y se compara el hash. Si
coincide, se genera la clave Fernet en memoria que cifra y descifra las
credenciales.

## Paso 3 — Agregar una credencial (con contraseña generada)

```
Opcion: 3

Nombre: GitHub
Generar contraseña ? [s/N]: s
Contraseña generada: P8AtlwvTsV476W+X
```

**Qué decir:** muestra el **generador aleatorio**. La contraseña se genera con
bytes aleatorios y se valida con el medidor de fortaleza hasta que sea segura.

## Paso 4 — Agregar otra credencial (mostrando el medidor)

```
Opcion: 3

Nombre: Mail
Generar contraseña ? [s/N]: N
Contraseña: 123
```

Al ingresar una débil, aparece el aviso del **medidor de fortaleza**:

```
La contraseña ingresada es debil.
...
```

Después tipeá una fuerte, p. ej. `MiClave_2024!Segura`, para que la acepte.

**Qué decir:** el medidor (zxcvbn) rechaza contraseñas débiles y exige una
fuerte.

## Paso 5 — Listar credenciales

```
Opcion: 4

1)
Nombre: GitHub
Contraseña: P8AtlwvTsV476W+X

2)
Nombre: Mail
Contraseña: MiClave_2024!Segura
```

**Qué decir:** los datos se leyeron desde el archivo cifrado y se descifraron en
el momento.

## Paso 6 — Modificar una credencial

```
Opcion: 6

Ingrese el numero de la credencial que desea modificar [ 0 para cancelar ].
Opcion: 1

Nombre: GitHub-personal
Generar contraseña ? [s/N]: s
```

## Paso 7 — Eliminar una credencial

```
Opcion: 5

Ingrese el numero de la credencial que desea eliminar [ 0 para cancelar ].
Opcion: 2
```

## Paso 8 — Mostrar que el archivo está cifrado (el momento clave)

Sin cerrar la app, abrí otra terminal y mostrá el contenido del archivo:

```
cat Datos/credenciales.dat
```

**Qué decir:** se ve un bloque ilegible (base64 cifrado), no las contraseñas en
texto plano. Sin la master password no se puede descifrar.

## Paso 9 — Bloquear y salir

```
Opcion: 2   (bloquear: descarta la clave de cifrado de memoria)
Opcion: 0   (salir)
```

## Resumen para cerrar

- Una sola **master password** protege todo (clave privada).
- Las credenciales se guardan **cifradas** con Fernet (AES + HMAC).
- La clave se deriva con **scrypt + salt**; la master nunca se guarda.
- Extras: **generador** de contraseñas y **medidor de fortaleza**.

**Duración estimada:** 3–4 minutos.