import flet as ft
from flet import icons
import sqlite3
from datetime import datetime
import csv
import json
from functools import wraps
import os
import shutil

# Clases para la calculadora
class CalcButton(ft.ElevatedButton):
    def __init__(self, text, button_clicked, expand=1):
        super().__init__()
        self.text = text
        self.expand = expand
        self.on_click = button_clicked
        self.data = text

class DigitButton(CalcButton):
    def __init__(self, text, button_clicked, expand=1):
        super().__init__(text, button_clicked, expand)
        self.bgcolor = ft.colors.WHITE24
        self.color = ft.colors.WHITE

class ActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        super().__init__(text, button_clicked)
        self.bgcolor = ft.colors.ORANGE
        self.color = ft.colors.WHITE

class ExtraActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        super().__init__(text, button_clicked)
        self.bgcolor = ft.colors.BLUE_GREY_100
        self.color = ft.colors.BLACK

class CalculatorApp(ft.Container):
    def __init__(self):
        super().__init__()
        self.result = ft.Text(value="0", color=ft.colors.WHITE, size=20)
        self.current_input = ""
        self.previous_input = ""
        self.operation = ""
        self.width = 300
        self.bgcolor = ft.colors.BLACK
        self.border_radius = ft.border_radius.all(20)
        self.padding = 10
        self.content = ft.Column(
            controls=[
                ft.Row(controls=[self.result], alignment="end"),
                ft.Row(
                    controls=[
                        ExtraActionButton(text="AC", button_clicked=self.button_clicked),
                        ExtraActionButton(text="+/-", button_clicked=self.button_clicked),
                        ExtraActionButton(text="%", button_clicked=self.button_clicked),
                        ActionButton(text="/", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="7", button_clicked=self.button_clicked),
                        DigitButton(text="8", button_clicked=self.button_clicked),
                        DigitButton(text="9", button_clicked=self.button_clicked),
                        ActionButton(text="*", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="4", button_clicked=self.button_clicked),
                        DigitButton(text="5", button_clicked=self.button_clicked),
                        DigitButton(text="6", button_clicked=self.button_clicked),
                        ActionButton(text="-", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="1", button_clicked=self.button_clicked),
                        DigitButton(text="2", button_clicked=self.button_clicked),
                        DigitButton(text="3", button_clicked=self.button_clicked),
                        ActionButton(text="+", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="0", expand=2, button_clicked=self.button_clicked),
                        DigitButton(text=".", button_clicked=self.button_clicked),
                        ActionButton(text="=", button_clicked=self.button_clicked),
                    ]
                ),
            ]
        )

    def button_clicked(self, e):
        text = e.control.data
        try:
            if text.isdigit() or text == ".":
                self.current_input += text
            elif text == "AC":
                self.reset()
            elif text == "+/-":
                if self.current_input and self.current_input != "0":
                    self.current_input = str(-float(self.current_input)) if "." in self.current_input else str(-int(self.current_input))
            elif text == "%":
                if self.current_input and self.current_input != "0":
                    self.current_input = str(float(self.current_input) / 100)
            elif text in "+-*/":
                if self.current_input:
                    self.operation = text
                    self.previous_input = self.current_input
                    self.current_input = ""
            elif text == "=":
                if self.operation and self.previous_input and self.current_input:
                    self.current_input = str(eval(self.previous_input + self.operation + self.current_input))
                    self.operation = ""
                    self.previous_input = ""
            self.update_result()
        except Exception:
            self.current_input = "Error"
            self.update_result()

    def update_result(self):
        self.result.value = self.current_input if self.current_input else "0"
        self.update()

    def reset(self):
        self.current_input = ""
        self.previous_input = ""
        self.operation = ""
        self.update_result()

class Producto:
    def __init__(self, id, nombre, precio, cantidad, imagen=None):
        self.id = id
        self.nombre = nombre
        self.precio = precio
        self.cantidad = cantidad
        self.imagen = imagen

class InventarioCajaApp:
    def __init__(self):
        self.conn = sqlite3.connect('inventario_caja.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.crear_tablas()
        self.version_history = {
            "1.0": {"date": "2025-02-21", "changes": "Versión inicial"},
            "1.1": {"date": "2025-02-22", "changes": "Mejorado menú lateral y estadísticas"},
            "1.2": {"date": "2025-02-23", "changes": "Añadida confirmación de eliminación con decorador"},
            "1.3": {"date": "2025-02-24", "changes": "Optimizado CRUD de productos"},
            "1.4": {"date": "2025-02-25", "changes": "Añadida funcionalidad para subir y mostrar imágenes de productos"},
            "1.5": {"date": "2025-02-26", "changes": "Corregida compatibilidad de base de datos y manejo de historial"},
            "1.6": {"date": "2025-02-27", "changes": "Corregidas miniaturas, menú lateral y estadísticas"}
        }
        self.current_version = "1.6"
        self.imagenes_dir = os.path.abspath("imagenes_productos")
        if not os.path.exists(self.imagenes_dir):
            os.makedirs(self.imagenes_dir)

    def crear_tablas(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            precio REAL NOT NULL CHECK(precio >= 0),
            cantidad INTEGER NOT NULL CHECK(cantidad >= 0),
            imagen TEXT
        )
        ''')
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER,
            cantidad INTEGER,
            total REAL,
            fecha TEXT,
            medio_pago TEXT,
            FOREIGN KEY (producto_id) REFERENCES productos (id) ON DELETE CASCADE
        )
        ''')
        self.cursor.execute("PRAGMA table_info(productos)")
        columns = [col[1] for col in self.cursor.fetchall()]
        if 'imagen' not in columns:
            self.cursor.execute('ALTER TABLE productos ADD COLUMN imagen TEXT')
        self.conn.commit()

    def agregar_producto(self, nombre, precio, cantidad, imagen=None):
        try:
            if not nombre or precio < 0 or cantidad < 0:
                return False, "Datos inválidos"
            imagen_path = self._guardar_imagen(imagen) if imagen else None
            self.cursor.execute('''
            INSERT INTO productos (nombre, precio, cantidad, imagen)
            VALUES (?, ?, ?, ?)
            ''', (nombre, precio, cantidad, imagen_path))
            self.conn.commit()
            return True, f"Producto '{nombre}' agregado"
        except sqlite3.IntegrityError:
            return False, f"Error: El producto '{nombre}' ya existe"
        except sqlite3.Error as e:
            return False, f"Error en la base de datos: {str(e)}"

    def obtener_productos(self):
        try:
            self.cursor.execute('SELECT id, nombre, precio, cantidad, imagen FROM productos ORDER BY nombre')
            return [Producto(*row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error al leer productos: {e}")
            return []

    def obtener_producto_por_id(self, id):
        try:
            self.cursor.execute('SELECT id, nombre, precio, cantidad, imagen FROM productos WHERE id = ?', (id,))
            row = self.cursor.fetchone()
            return Producto(*row) if row else None
        except sqlite3.Error:
            return None

    def actualizar_producto(self, id, nombre, precio, cantidad, imagen=None):
        try:
            if not nombre or precio < 0 or cantidad < 0:
                return False, "Datos inválidos"
            producto_actual = self.obtener_producto_por_id(id)
            if not producto_actual:
                return False, "Producto no encontrado"
            imagen_path = self._guardar_imagen(imagen) if imagen else producto_actual.imagen
            self.cursor.execute('''
            UPDATE productos
            SET nombre = ?, precio = ?, cantidad = ?, imagen = ?
            WHERE id = ?
            ''', (nombre, precio, cantidad, imagen_path, id))
            if self.cursor.rowcount == 0:
                return False, "Producto no encontrado"
            self.conn.commit()
            return True, "Producto actualizado"
        except sqlite3.IntegrityError:
            return False, "Error: El nombre ya existe en otro producto"
        except sqlite3.Error as e:
            return False, f"Error en la base de datos: {str(e)}"

    def eliminar_producto(self, id):
        try:
            self.cursor.execute('SELECT nombre, imagen FROM productos WHERE id = ?', (id,))
            result = self.cursor.fetchone()
            if not result:
                return False, "Producto no encontrado"
            nombre, imagen = result
            self.cursor.execute('DELETE FROM productos WHERE id = ?', (id,))
            self.conn.commit()
            if imagen and os.path.exists(imagen):
                os.remove(imagen)
            return True, f"Producto '{nombre}' eliminado"
        except sqlite3.Error as e:
            return False, f"Error al eliminar: {str(e)}"

    def _guardar_imagen(self, imagen_path):
        if not imagen_path or not os.path.exists(imagen_path):
            return None
        nombre_archivo = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(imagen_path)}"
        destino = os.path.join(self.imagenes_dir, nombre_archivo)
        shutil.copy(imagen_path, destino)
        return destino

    def registrar_venta(self, producto_id, cantidad, total, medio_pago):
        try:
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute('''
            INSERT INTO ventas (producto_id, cantidad, total, medio_pago, fecha)
            VALUES (?, ?, ?, ?, ?)
            ''', (producto_id, cantidad, total, medio_pago, fecha))
            self.cursor.execute('''
            UPDATE productos
            SET cantidad = cantidad - ?
            WHERE id = ?
            ''', (cantidad, producto_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error al registrar la venta: {e}")
            return False

    def obtener_cuadre_caja(self):
        try:
            self.cursor.execute('''
            SELECT SUM(total) FROM ventas
            WHERE DATE(fecha) = DATE('now')
            ''')
            return self.cursor.fetchone()[0] or 0
        except sqlite3.Error:
            return 0

    def generar_reporte_csv(self, filename='reporte_inventario.csv'):
        try:
            with open(filename, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['ID', 'Nombre', 'Precio', 'Cantidad', 'Valor Total', 'Imagen'])
                for producto in self.obtener_productos():
                    writer.writerow([producto.id, producto.nombre, producto.precio,
                                     producto.cantidad, producto.precio * producto.cantidad, producto.imagen])
            return True
        except IOError:
            return False

    def obtener_historial_ventas(self):
        try:
            self.cursor.execute('''
            SELECT v.id, p.nombre, v.cantidad, v.total, v.medio_pago, v.fecha
            FROM ventas v
            JOIN productos p ON v.producto_id = p.id
            ORDER BY v.fecha DESC
            ''')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener historial de ventas: {e}")
            return []

    def get_version_info(self):
        return {"current_version": self.current_version, "history": self.version_history}

    def get_statistics(self):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM productos")
            total_productos = self.cursor.fetchone()[0]
            self.cursor.execute("""
            SELECT medio_pago, SUM(total), COUNT(*)
            FROM ventas
            WHERE DATE(fecha) = DATE('now')
            GROUP BY medio_pago
            """)
            ventas_medio = {row[0]: {"total": row[1] or 0, "count": row[2]} for row in self.cursor.fetchall()}
            self.cursor.execute("""
            SELECT p.nombre, SUM(v.cantidad)
            FROM ventas v
            JOIN productos p ON v.producto_id = p.id
            GROUP BY p.id, p.nombre
            ORDER BY SUM(v.cantidad) DESC
            LIMIT 1
            """)
            top_product = self.cursor.fetchone() or ("N/A", 0)
            return {
                "total_productos": total_productos,
                "ventas_medio": ventas_medio,
                "top_product": {"name": top_product[0], "units": top_product[1]},
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
        except sqlite3.Error as e:
            print(f"Error al obtener estadísticas: {e}")
            return {"total_productos": 0, "ventas_medio": {}, "top_product": {"name": "N/A", "units": 0}, "timestamp": "N/A"}

def main(page: ft.Page):
    app = InventarioCajaApp()

    page.title = f"Inventario Crisoull v{app.current_version}"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 900
    page.window.height = 800

    def confirmar_accion(mensaje="¿Está seguro?"):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                def confirmar(e):
                    dialog.open = False
                    page.update()
                    func(*args, **kwargs)

                def cancelar(e):
                    dialog.open = False
                    page.update()

                dialog = ft.AlertDialog(
                    title=ft.Text("Confirmar Acción"),
                    content=ft.Text(mensaje),
                    actions=[
                        ft.TextButton("Sí", on_click=confirmar),
                        ft.TextButton("No", on_click=cancelar)
                    ]
                )
                page.overlay.append(dialog)
                dialog.open = True
                page.update()
            return wrapper
        return decorator

    def mostrar_toast(mensaje, color=ft.colors.GREEN, duration=3000):
        snack_bar = ft.SnackBar(
            ft.Text(mensaje),
            bgcolor=color,
            duration=duration,
            action="Cerrar",
            action_color=ft.colors.WHITE,
            elevation=10,
        )
        page.overlay.append(snack_bar)
        snack_bar.open = True
        page.update()

    productos_row = ft.Row(wrap=True, scroll="auto", expand=True)
    nombre_input = ft.TextField(label="Nombre del producto", expand=1, prefix_icon=icons.INVENTORY)
    precio_input = ft.TextField(label="Precio", expand=1, prefix_icon=icons.ATTACH_MONEY)
    cantidad_input = ft.TextField(label="Cantidad", expand=1, prefix_icon=icons.NUMBERS)
    imagen_input = ft.FilePicker(on_result=lambda e: agregar_imagen(e))
    busqueda_input = ft.TextField(label="Buscar producto", expand=1, prefix_icon=icons.SEARCH)
    cuadre_texto = ft.Text(size=20)
    total_inventario_texto = ft.Text(size=20)
    imagen_seleccionada = ft.Ref[str]()

    def agregar_imagen(e):
        if e.files:
            imagen_seleccionada.current = e.files[0].path
            mostrar_toast(f"Imagen seleccionada: {os.path.basename(imagen_seleccionada.current)}")
        else:
            imagen_seleccionada.current = None

    def actualizar_lista_productos(filtro=None):
        productos_row.controls.clear()
        try:
            productos = app.obtener_productos()
            if filtro:
                productos = [p for p in productos if filtro.lower() in p.nombre.lower()]
            if not productos:
                productos_row.controls.append(ft.Text("No hay productos registrados", italic=True))
            for producto in productos:
                imagen_path = producto.imagen if producto.imagen and os.path.exists(producto.imagen) else None
                imagen_widget = ft.Image(src=imagen_path, width=50, height=50, fit=ft.ImageFit.CONTAIN) if imagen_path else ft.Icon(icons.IMAGE_NOT_SUPPORTED)
                productos_row.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    imagen_widget,
                                    ft.ListTile(
                                        title=ft.Text(f"{producto.nombre}", size=16, weight="bold"),
                                        subtitle=ft.Text(f"Precio: ${producto.precio:.2f}\nCantidad: {producto.cantidad}"),
                                    )
                                ]),
                                ft.Row([
                                    ft.IconButton(icons.EDIT, on_click=lambda _, p=producto: editar_producto(p)),
                                    ft.IconButton(icons.DELETE, on_click=lambda _, id=producto.id: eliminar_producto(id)),
                                    ft.IconButton(icons.SHOPPING_CART, on_click=lambda _, p=producto: registrar_venta_dialog(p))
                                ], alignment=ft.MainAxisAlignment.END)
                            ]),
                            width=300,
                            padding=10,
                        )
                    )
                )
            page.update()
        except Exception as e:
            mostrar_toast(f"Error al actualizar lista: {str(e)}", ft.colors.RED_400)

    def agregar_producto(e):
        try:
            nombre = nombre_input.value.strip()
            precio = float(precio_input.value)
            cantidad = int(cantidad_input.value)
            imagen = imagen_seleccionada.current if imagen_seleccionada.current else None
            success, message = app.agregar_producto(nombre, precio, cantidad, imagen)
            if success:
                actualizar_lista_productos()
                nombre_input.value = ""
                precio_input.value = ""
                cantidad_input.value = ""
                imagen_seleccionada.current = None
                actualizar_cuadre()
                calcular_total_inventario()
                mostrar_toast(message)
            else:
                mostrar_toast(message, ft.colors.RED_400)
        except ValueError:
            mostrar_toast("Ingrese valores numéricos válidos para precio y cantidad", ft.colors.RED_400)
        except Exception as e:
            mostrar_toast(f"Error inesperado: {str(e)}", ft.colors.RED_400)

    def editar_producto(producto):
        nombre_editar = ft.TextField(value=producto.nombre, label="Nombre del producto")
        precio_editar = ft.TextField(value=str(producto.precio), label="Precio")
        cantidad_editar = ft.TextField(value=str(producto.cantidad), label="Cantidad")
        imagen_editar = ft.FilePicker(on_result=lambda e: editar_imagen(e))
        imagen_seleccionada_editar = ft.Ref[str]()
        imagen_actual = ft.Image(src=producto.imagen, width=100, height=100, fit=ft.ImageFit.CONTAIN) if producto.imagen and os.path.exists(producto.imagen) else ft.Text("Sin imagen")

        def editar_imagen(e):
            if e.files:
                imagen_seleccionada_editar.current = e.files[0].path
                imagen_actual.src = imagen_seleccionada_editar.current
                page.update()
            else:
                imagen_seleccionada_editar.current = None

        def guardar_cambios(e):
            try:
                nombre = nombre_editar.value.strip()
                precio = float(precio_editar.value)
                cantidad = int(cantidad_editar.value)
                imagen = imagen_seleccionada_editar.current if imagen_seleccionada_editar.current else producto.imagen
                success, message = app.actualizar_producto(producto.id, nombre, precio, cantidad, imagen)
                if success:
                    actualizar_lista_productos()
                    actualizar_cuadre()
                    calcular_total_inventario()
                    mostrar_toast(message)
                    dialog.open = False
                else:
                    mostrar_toast(message, ft.colors.RED_400)
                page.update()
            except ValueError:
                mostrar_toast("Ingrese valores numéricos válidos", ft.colors.RED_400)
            except Exception as e:
                mostrar_toast(f"Error inesperado: {str(e)}", ft.colors.RED_400)

        dialog = ft.AlertDialog(
            title=ft.Text(f"Editar Producto (ID: {producto.id})"),
            content=ft.Column([
                nombre_editar,
                precio_editar,
                cantidad_editar,
                ft.Row([ft.Text("Imagen:"), imagen_actual]),
                ft.ElevatedButton("Cambiar Imagen", on_click=lambda e: imagen_editar.pick_files(allowed_extensions=["jpg", "png", "jpeg"]))
            ]),
            actions=[
                ft.TextButton("Guardar", on_click=guardar_cambios),
                ft.TextButton("Cancelar", on_click=lambda _: setattr(dialog, 'open', False))
            ]
        )
        page.overlay.append(imagen_editar)
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def registrar_venta_dialog(producto):
        cantidad_venta = ft.TextField(label="Cantidad a vender")
        medio_pago = ft.Dropdown(
            options=[ft.dropdown.Option("Efectivo"), ft.dropdown.Option("Transferencia"), ft.dropdown.Option("Débito")],
            value="Efectivo"
        )

        def registrar(e):
            try:
                cantidad = int(cantidad_venta.value)
                if cantidad <= 0:
                    mostrar_toast("La cantidad debe ser mayor a 0", ft.colors.ORANGE_400)
                    return
                if cantidad > producto.cantidad:
                    mostrar_toast("No hay suficiente stock", ft.colors.ORANGE_400)
                    return
                total = cantidad * producto.precio
                if app.registrar_venta(producto.id, cantidad, total, medio_pago.value):
                    actualizar_lista_productos()
                    actualizar_cuadre()
                    mostrar_toast("Venta registrada exitosamente")
                    dialog.open = False
                    page.update()
                else:
                    mostrar_toast("Error al registrar la venta", ft.colors.RED_400)
            except ValueError:
                mostrar_toast("Ingrese una cantidad válida", ft.colors.RED_400)

        dialog = ft.AlertDialog(
            title=ft.Text(f"Vender: {producto.nombre}"),
            content=ft.Column([cantidad_venta, medio_pago]),
            actions=[
                ft.TextButton("Registrar", on_click=registrar),
                ft.TextButton("Cancelar", on_click=lambda _: setattr(dialog, 'open', False))
            ]
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    @confirmar_accion("¿Seguro que desea eliminar este producto?")
    def eliminar_producto(id):
        success, message = app.eliminar_producto(id)
        if success:
            actualizar_lista_productos()
            actualizar_cuadre()
            calcular_total_inventario()
            mostrar_toast(message)
        else:
            mostrar_toast(message, ft.colors.RED_400)

    def actualizar_cuadre():
        try:
            cuadre_texto.value = f"Cuadre de Caja: ${app.obtener_cuadre_caja():.2f}"
            page.update()
        except Exception as e:
            mostrar_toast(f"Error al actualizar cuadre: {str(e)}", ft.colors.RED_400)

    def calcular_total_inventario():
        try:
            total = sum(p.precio * p.cantidad for p in app.obtener_productos())
            total_inventario_texto.value = f"Total Inventario: ${total:.2f}"
            page.update()
        except Exception as e:
            mostrar_toast(f"Error al calcular inventario: {str(e)}", ft.colors.RED_400)

    def toggle_menu(e):
        page.drawer.open = not page.drawer.open
        page.update()

    def actualizar_historial():
        try:
            historial_container.controls = [
                ft.ListTile(
                    leading=ft.Icon(icons.RECEIPT),
                    title=ft.Text(f"{v[1]} - {v[2]} uds", weight="bold"),
                    subtitle=ft.Text(f"${v[3]:.2f} - {v[4]} - {v[5]}"),
                    trailing=ft.Icon(icons.CHECK_CIRCLE, color=ft.colors.GREEN),
                ) for v in app.obtener_historial_ventas()
            ]
            page.update()
        except Exception as e:
            mostrar_toast(f"Error al actualizar historial: {str(e)}", ft.colors.RED_400)

    stats_text = ft.Text(value="Cargando estadísticas...", size=14, font_family="Roboto Mono")

    def actualizar_estadisticas():
        try:
            stats = app.get_statistics()
            ventas_medio_str = "\n".join(
                f"{medio}: ${data['total']:.2f} ({data['count']} ops)"
                for medio, data in stats.get("ventas_medio", {}).items()
            )
            stats_text.value = (
                f"Productos: {stats.get('total_productos', 0)}\n"
                f"Top: {stats.get('top_product', {}).get('name')} ({stats.get('top_product', {}).get('units')} uds)\n"
                f"Ventas por medio:\n{ventas_medio_str or 'Sin ventas'}\n"
                f"Actualizado: {stats.get('timestamp', '-')}"
            )
            page.update()
        except Exception as e:
            mostrar_toast(f"Error al actualizar estadísticas: {str(e)}", ft.colors.RED_400)

    calculadora = CalculatorApp()
    historial_container = ft.ListView(expand=True, spacing=5, padding=10)

    page.drawer = ft.NavigationDrawer(
        bgcolor=ft.colors.SURFACE,
        elevation=16,
        controls=[
            ft.Container(
                padding=ft.padding.all(20),
                content=ft.Column([
                    ft.Row([ft.Icon(icons.DASHBOARD, size=30), ft.Text("Panel de Control", style=ft.TextThemeStyle.HEADLINE_SMALL)]),
                    ft.Divider(height=20),
                    ft.ExpansionTile(
                        title=ft.Text("Calculadora"),
                        leading=ft.Icon(icons.CALCULATE),
                        maintain_state=True,
                        controls=[ft.Container(content=calculadora, padding=10, border=ft.border.all(1, ft.colors.GREY_300), border_radius=10)]
                    ),
                    ft.ExpansionTile(
                        title=ft.Text("Historial de Ventas"),
                        leading=ft.Icon(icons.HISTORY),
                        trailing=ft.IconButton(icon=icons.REFRESH, on_click=lambda e: actualizar_historial()),
                        maintain_state=True,
                        controls=[ft.Container(content=historial_container, height=300, border=ft.border.all(1, ft.colors.GREY_300), border_radius=10)]
                    ),
                    ft.ExpansionTile(
                        title=ft.Text("Estadísticas"),
                        leading=ft.Icon(icons.ANALYTICS),
                        trailing=ft.IconButton(icon=icons.REFRESH, on_click=lambda e: actualizar_estadisticas()),
                        maintain_state=True,
                        controls=[ft.Container(content=stats_text, padding=10, border=ft.border.all(1, ft.colors.GREY_300), border_radius=10)]
                    ),
                    ft.ExpansionTile(
                        title=ft.Text("Historial de Versiones"),
                        leading=ft.Icon(icons.UPDATE),
                        maintain_state=True,
                        controls=[ft.Container(content=ft.Column([ft.Text(f"v{ver}: {info['date']} - {info['changes']}")
                                                                 for ver, info in app.version_history.items()]),
                                               padding=10, border=ft.border.all(1, ft.colors.GREY_300), border_radius=10)]
                    ),
                    ft.Divider(height=20),
                    ft.Text("Acciones Rápidas", style=ft.TextThemeStyle.TITLE_MEDIUM),
                    ft.Column([
                        ft.ElevatedButton(
                            "Generar Reporte CSV",
                            icon=icons.DOWNLOAD,
                            on_click=lambda e: generar_reporte(),
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), bgcolor=ft.colors.BLUE_600, color=ft.colors.WHITE),
                            width=200
                        ),
                        ft.ElevatedButton(
                            "Respaldar BD",
                            icon=icons.BACKUP,
                            on_click=lambda e: respaldar_base_datos(),
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), bgcolor=ft.colors.PURPLE_600, color=ft.colors.WHITE),
                            width=200
                        ),
                        ft.ElevatedButton(
                            "Cerrar Caja",
                            icon=icons.LOCK,
                            on_click=lambda e: cerrar_caja(),
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), bgcolor=ft.colors.GREEN_600, color=ft.colors.WHITE),
                            width=200
                        ),
                        ft.ElevatedButton(
                            "Exportar Config",
                            icon=icons.SETTINGS,
                            on_click=lambda e: exportar_configuracion(),
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), bgcolor=ft.colors.ORANGE_600, color=ft.colors.WHITE),
                            width=200
                        )
                    ], spacing=10)
                ], scroll=ft.ScrollMode.AUTO)
            )
        ]
    )

    def generar_reporte():
        try:
            if app.generar_reporte_csv():
                mostrar_toast("Reporte CSV generado exitosamente")
            else:
                mostrar_toast("Error al generar el reporte", ft.colors.RED_400)
        except Exception as e:
            mostrar_toast(f"Error al generar reporte: {str(e)}", ft.colors.RED_400)

    def respaldar_base_datos():
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(f"backup_inventario_{timestamp}.db", "wb") as backup:
                for line in app.conn.iterdump():
                    backup.write(f"{line}\n".encode())
            mostrar_toast("Respaldo creado exitosamente")
        except Exception as e:
            mostrar_toast(f"Error al crear respaldo: {str(e)}", ft.colors.RED_400)

    def cerrar_caja():
        try:
            cuadre = app.obtener_cuadre_caja()
            dialog = ft.AlertDialog(
                title=ft.Text("Cerrar Caja"),
                content=ft.Text(f"Total del día: ${cuadre:.2f}\n¿Confirmar cierre?"),
                actions=[
                    ft.TextButton("Sí", on_click=lambda e: confirmar_cierre(dialog)),
                    ft.TextButton("No", on_click=lambda e: setattr(dialog, 'open', False))
                ]
            )
            page.overlay.append(dialog)
            dialog.open = True
            page.update()
        except Exception as e:
            mostrar_toast(f"Error al cerrar caja: {str(e)}", ft.colors.RED_400)

    def confirmar_cierre(dialog):
        try:
            app.cursor.execute("INSERT INTO ventas (total, fecha, medio_pago) VALUES (?, ?, ?)",
                               (app.obtener_cuadre_caja(), datetime.now(), "CIERRE"))
            app.conn.commit()
            mostrar_toast("Caja cerrada exitosamente")
            dialog.open = False
            actualizar_estadisticas()
            actualizar_cuadre()
            page.update()
        except Exception as e:
            mostrar_toast(f"Error al cerrar caja: {str(e)}", ft.colors.RED_400)

    def exportar_configuracion():
        try:
            config = {"version": app.current_version, "theme": page.theme_mode.value, "window_size": {"width": page.window.width, "height": page.window.height}}
            with open("config.json", "w") as f:
                json.dump(config, f)
            mostrar_toast("Configuración exportada exitosamente")
        except Exception as e:
            mostrar_toast(f"Error al exportar configuración: {str(e)}", ft.colors.RED_400)

    def cambiar_tema(e):
        page.theme_mode = ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        theme_icon.icon = icons.DARK_MODE if page.theme_mode == ft.ThemeMode.LIGHT else icons.LIGHT_MODE
        page.update()

    menu_button = ft.IconButton(icon=icons.MENU, on_click=toggle_menu, tooltip="Menú")
    theme_icon = ft.IconButton(icon=icons.BRIGHTNESS_6, on_click=cambiar_tema, tooltip="Cambiar tema")

    page.add(
        ft.AppBar(
            leading=menu_button,
            title=ft.Text(f"Inventario Crisoull ® v{app.current_version}"),
            actions=[
                ft.IconButton(icons.DOWNLOAD, on_click=lambda e: generar_reporte(), tooltip="Exportar CSV"),
                ft.IconButton(icons.ANALYTICS, on_click=lambda e: actualizar_estadisticas(), tooltip="Actualizar Stats"),
                theme_icon,
            ],
            bgcolor=ft.colors.SURFACE_VARIANT,
            elevation=4,
        ),
        ft.Row([
            ft.Column([
                ft.Row([
                    nombre_input,
                    precio_input,
                    cantidad_input,
                    ft.ElevatedButton("Subir Imagen", icon=icons.UPLOAD, on_click=lambda e: imagen_input.pick_files(allowed_extensions=["jpg", "png", "jpeg"])),
                    ft.ElevatedButton("Agregar", on_click=agregar_producto, icon=icons.ADD,
                                      style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_600, color=ft.colors.WHITE))
                ]),
                ft.Divider(),
                ft.Row([busqueda_input, ft.ElevatedButton("Buscar", on_click=lambda e: actualizar_lista_productos(busqueda_input.value), icon=icons.SEARCH)]),
                ft.Divider(),
                productos_row,
                ft.Divider(),
                ft.Row([cuadre_texto, total_inventario_texto], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], expand=True, scroll=ft.ScrollMode.AUTO)
        ], expand=True)
    )
    page.overlay.append(imagen_input)

    # Inicialización
    actualizar_lista_productos()
    actualizar_cuadre()
    calcular_total_inventario()
    actualizar_historial()
    actualizar_estadisticas()

ft.app(target=main, assets_dir="assets")
