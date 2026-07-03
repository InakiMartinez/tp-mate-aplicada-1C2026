from util import *


def menu_a():
	while True:
		print(
		"\n"
		"1 - Desbloquear aplicacion.\n"
		"0 - Salir.\n"
		)

		try:
			option = int(input("Opcion: "))

			if option == 0 or option == 1:
				return option
		except ValueError:
			pass

		print("\nOpcion invalida.")


def menu_b():
	while True:
		print(
		"\n"
		"2 - Bloquear aplicacion.\n"
		"3 - Agregar credencial.\n"
		"4 - Obtener credenciales.\n"
		"5 - Eliminar credencial.\n"
		"6 - Modificar credencial.\n"
		)

		try:
			option = int(input("Opcion: "))

			if option >= 2 and option <= 6:
				return option
		except ValueError:
			pass

		print("\nOpcion invalida.")


def main():
	util = Util("config.ini")

	if not util.pm.master_exists():
		util.setup_master()

	util.set_current_menu(menu_a)

	while True:
		option = util.current_menu()

		if option == 1:
			if util.unlock():
				util.set_current_menu(menu_b)
		elif option == 2:
			util.lock()
			util.set_current_menu(menu_a)
		elif option == 3:
			util.insert_credentials()
		elif option == 4:
			util.view_credentials()
		elif option == 5:
			util.delete_credentials()
		elif option == 6:
			util.modify_credentials()
		elif option == 0:
			break
		else:
			print("\nError.")
			exit(1)


main()
