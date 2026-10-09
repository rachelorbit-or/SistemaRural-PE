"""Ventana principal con tkinter (paradigma orientado a eventos).

Cada botón, cada selección de lista y la tecla Enter disparan un manejador (listener)
que llama al sistema y muestra el resultado. Los errores esperados se muestran como avisos.
"""
import functools
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from sistemarural.errores import (AccesoDenegado, ErrorDeAlmacenamiento, ErrorDeCifrado,
                                  ErrorDeValidacion, PacienteDuplicado, PacienteNoEncontrado,
                                  StockInsuficiente)
from sistemarural.historia_clinica import RESOLUCIONES
from sistemarural.horarios import DIAS, TURNOS
from sistemarural.validadores import convertir_fecha, convertir_items

ERRORES_CONOCIDOS = (ErrorDeValidacion, AccesoDenegado, PacienteDuplicado, PacienteNoEncontrado,
                     StockInsuficiente, ErrorDeAlmacenamiento, ErrorDeCifrado)


def manejar_errores(manejador):
    """Decorador: si el manejador lanza un error esperado, lo muestra en un aviso."""
    @functools.wraps(manejador)
    def envoltura(self, *args, **kwargs):
        try:
            return manejador(self, *args, **kwargs)
        except ERRORES_CONOCIDOS as error:
            messagebox.showerror("No se pudo completar la acción", str(error))
    return envoltura


class Aplicacion(tk.Tk):
    """Ventana con una pestaña por área: pacientes, atención, citas, farmacia, horarios y reporte."""

    def __init__(self, sistema):
        super().__init__()
        self.title("SistemaRural-PE · Puesto de Salud Chontapaccha")
        self.geometry("980x680")
        self.__aplicar_estilo()
        self.__sistema = sistema
        self.__usuario = None
        self.__usuarios = {}
        self.__v = {}                 # variables de los campos de texto
        self.__personal_por_lista = {}  # lista (c_personal o h_personal) -> {texto: DNI}
        self.__citas_listadas = {}     # fila de la tabla -> cita

        self.__construir_barra_usuario()
        pestanas = ttk.Notebook(self)
        pestanas.pack(fill="both", expand=True, padx=8, pady=8)
        self.__construir_pacientes(self.__nueva_pestana(pestanas, "Pacientes"))
        self.__construir_atencion(self.__nueva_pestana(pestanas, "Atención"))
        self.__construir_citas(self.__nueva_pestana(pestanas, "Citas"))
        self.__construir_farmacia(self.__nueva_pestana(pestanas, "Farmacia"))
        self.__construir_horarios(self.__nueva_pestana(pestanas, "Horarios"))
        self.__construir_reporte(self.__nueva_pestana(pestanas, "Reporte DIRESA"))

        self.__refrescar_usuarios()
        self.__buscar_pacientes()
        self.__refrescar_inventario()

    # ---------- Colores y tipografía ----------
    def __aplicar_estilo(self):
        """Define los colores de la ventana. Para cambiar la paleta, edite estas variables."""
        fondo = "#f4fbff"        # fondo general (azul muy claro)
        principal = "#8ecae6"    # color de botones, pestaña activa y encabezados
        oscuro = "#6bb5d8"       # color de los botones al pasar el mouse
        pestana = "#dff1fb"      # pestañas que no están elegidas
        letra = ("Segoe UI", 10)

        estilo = ttk.Style(self)
        estilo.theme_use("clam")  # tema que permite cambiar los colores
        self.configure(background=fondo)
        estilo.configure(".", background=fondo, font=letra)
        estilo.configure("TFrame", background=fondo)
        estilo.configure("TLabel", background=fondo)
        estilo.configure("TNotebook", background=fondo)
        estilo.configure("TNotebook.Tab", background=pestana, padding=(14, 6))
        estilo.map("TNotebook.Tab", background=[("selected", principal)],
                   foreground=[("selected", "#1d3557")])
        estilo.configure("TButton", background=principal, foreground="#1d3557", padding=6)
        estilo.map("TButton", background=[("active", oscuro)])
        estilo.configure("Treeview.Heading", background=principal, foreground="#1d3557",
                         font=("Segoe UI", 10, "bold"))
        estilo.configure("Treeview", background="#ffffff", fieldbackground="#ffffff")
        estilo.configure("TEntry", fieldbackground="#ffffff")
        estilo.configure("TCombobox", fieldbackground="#ffffff")

    # ---------- Ayudas para armar la ventana ----------
    @staticmethod
    def __nueva_pestana(pestanas, titulo):
        marco = ttk.Frame(pestanas, padding=10)
        pestanas.add(marco, text=titulo)
        return marco

    def __var(self, nombre, valor=""):
        variable = tk.StringVar(value=valor)
        self.__v[nombre] = variable
        return variable

    def __campo(self, marco, etiqueta, nombre, fila, ancho=30, valor=""):
        ttk.Label(marco, text=etiqueta).grid(row=fila, column=0, sticky="w", padx=4, pady=2)
        entrada = ttk.Entry(marco, textvariable=self.__var(nombre, valor), width=ancho)
        entrada.grid(row=fila, column=1, sticky="w", padx=4, pady=2)
        return entrada

    def __lista(self, marco, etiqueta, nombre, valores, fila, ancho=30, al_elegir=None):
        ttk.Label(marco, text=etiqueta).grid(row=fila, column=0, sticky="w", padx=4, pady=2)
        combo = ttk.Combobox(marco, textvariable=self.__var(nombre), values=valores,
                             state="readonly", width=ancho)
        combo.grid(row=fila, column=1, sticky="w", padx=4, pady=2)
        if al_elegir:
            combo.bind("<<ComboboxSelected>>", al_elegir)
        return combo

    def __limpiar(self, *nombres):
        for nombre in nombres:
            self.__v[nombre].set("")

    @staticmethod
    def __mostrar(cuadro, contenido):
        cuadro.configure(state="normal")
        cuadro.delete("1.0", "end")
        cuadro.insert("end", contenido)
        cuadro.configure(state="disabled")

    def __cargar_personal(self, combo, nombre_servicio, variable):
        """Llena la lista de personal con el servicio elegido y borra la elección anterior."""
        personal = self.__sistema.obtener_servicio(nombre_servicio).listar_personal()
        self.__personal_por_lista[variable] = {f"{p.nombres} — {p.cargo}": p.dni for p in personal}
        combo["values"] = list(self.__personal_por_lista[variable])
        self.__v[variable].set("")

    def __dni_de_personal(self, nombre_variable):
        dni = self.__personal_por_lista.get(nombre_variable, {}).get(self.__v[nombre_variable].get())
        if dni is None:
            raise ErrorDeValidacion("Elija el personal de la lista (primero elija el servicio).")
        return dni

    # ---------- Usuario actual ----------
    def __construir_barra_usuario(self):
        barra = ttk.Frame(self)
        barra.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(barra, text="Usuario actual:").pack(side="left")
        self.__combo_usuario = ttk.Combobox(barra, textvariable=self.__var("usuario"),
                                            state="readonly", width=42)
        self.__combo_usuario.pack(side="left", padx=6)
        self.__combo_usuario.bind("<<ComboboxSelected>>", self.__al_cambiar_usuario)

    def __refrescar_usuarios(self):
        self.__usuarios = {f"{p.nombres} — {p.cargo}": p for p in self.__sistema.listar_personal()}
        self.__combo_usuario["values"] = list(self.__usuarios)
        if self.__usuarios and not self.__v["usuario"].get():
            primero = next(iter(self.__usuarios))
            self.__v["usuario"].set(primero)
            self.__usuario = self.__usuarios[primero]

    def __al_cambiar_usuario(self, _evento=None):
        self.__usuario = self.__usuarios.get(self.__v["usuario"].get())

    # ---------- Pestaña Pacientes ----------
    def __construir_pacientes(self, marco):
        self.__campo(marco, "DNI", "p_dni", 0, 12)
        self.__campo(marco, "Nombres", "p_nombres", 1, 40)
        self.__campo(marco, "Fecha de nacimiento (AAAA-MM-DD)", "p_fecha", 2, 14)
        self.__campo(marco, "Dirección", "p_direccion", 3, 40)
        botones = ttk.Frame(marco)
        botones.grid(row=4, column=0, columnspan=2, pady=6)
        ttk.Button(botones, text="Registrar paciente",
                   command=self.__registrar_paciente).pack(side="left", padx=4)
        ttk.Button(botones, text="Abrir historia clínica",
                   command=self.__abrir_historia).pack(side="left", padx=4)
        buscador = self.__campo(marco, "Buscar (DNI o nombre)", "p_buscar", 5, 30)
        buscador.bind("<Return>", self.__buscar_pacientes)
        ttk.Button(marco, text="Buscar", command=self.__buscar_pacientes).grid(row=5, column=2)
        columnas = ("dni", "nombres", "edad", "historia")
        self.__tabla_pacientes = ttk.Treeview(marco, columns=columnas, show="headings", height=9)
        for columna, titulo in zip(columnas, ("DNI", "Nombres", "Edad", "Historia clínica")):
            self.__tabla_pacientes.heading(columna, text=titulo)
        self.__tabla_pacientes.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=8)
        self.__tabla_pacientes.bind("<<TreeviewSelect>>", self.__al_elegir_paciente)

    @manejar_errores
    def __registrar_paciente(self, _evento=None):
        v = self.__v
        dni = v["p_dni"].get().strip()
        self.__sistema.registrar_paciente(
            self.__usuario, dni, v["p_nombres"].get(),
            convertir_fecha(v["p_fecha"].get()), v["p_direccion"].get())
        messagebox.showinfo("Paciente registrado", "El paciente se registró correctamente.")
        # Se conserva el DNI para poder abrir la historia clínica enseguida.
        self.__limpiar("p_nombres", "p_fecha", "p_direccion")
        for nombre in ("a_dni", "c_dni", "f_dni"):
            v[nombre].set(dni)
        self.__buscar_pacientes()

    @manejar_errores
    def __abrir_historia(self, _evento=None):
        historia = self.__sistema.abrir_historia(self.__usuario, self.__v["p_dni"].get().strip())
        messagebox.showinfo("Historia clínica", f"Se abrió la historia {historia.numero}.")
        self.__buscar_pacientes()

    @manejar_errores
    def __buscar_pacientes(self, _evento=None):
        tabla = self.__tabla_pacientes
        tabla.delete(*tabla.get_children())
        for p in self.__sistema.buscar_pacientes(self.__v["p_buscar"].get()):
            historia = p.historia.numero if p.historia else "Sin historia"
            tabla.insert("", "end", iid=p.dni, values=(p.dni, p.nombres, p.edad(), historia))

    def __al_elegir_paciente(self, _evento=None):
        """Al elegir un paciente de la tabla, se copia su DNI a los demás formularios."""
        seleccion = self.__tabla_pacientes.selection()
        if seleccion:
            for nombre in ("p_dni", "a_dni", "c_dni", "f_dni"):
                self.__v[nombre].set(seleccion[0])

    # ---------- Pestaña Atención ----------
    def __construir_atencion(self, marco):
        self.__campo(marco, "DNI del paciente", "a_dni", 0, 12)
        self.__campo(marco, "Motivo de consulta", "a_motivo", 1, 60)
        self.__campo(marco, "Diagnóstico", "a_diagnostico", 2, 60)
        self.__lista(marco, "Resolución", "a_resolucion", list(RESOLUCIONES), 3, 14)
        self.__v["a_resolucion"].set(RESOLUCIONES[0])
        botones = ttk.Frame(marco)
        botones.grid(row=4, column=0, columnspan=2, pady=6)
        ttk.Button(botones, text="Registrar atención",
                   command=self.__registrar_atencion).pack(side="left", padx=4)
        ttk.Button(botones, text="Ver diagnósticos",
                   command=self.__ver_diagnosticos).pack(side="left", padx=4)
        ttk.Button(botones, text="Preparar historia",
                   command=self.__preparar_historia).pack(side="left", padx=4)
        self.__texto_atencion = tk.Text(marco, height=14, width=100, state="disabled")
        self.__texto_atencion.grid(row=5, column=0, columnspan=3, pady=8)

    @manejar_errores
    def __registrar_atencion(self, _evento=None):
        v = self.__v
        self.__sistema.registrar_atencion(
            self.__usuario, v["a_dni"].get().strip(), v["a_motivo"].get(),
            v["a_diagnostico"].get(), v["a_resolucion"].get())
        messagebox.showinfo("Atención registrada", "La atención se guardó con el diagnóstico cifrado.")
        self.__limpiar("a_motivo", "a_diagnostico")

    @manejar_errores
    def __ver_diagnosticos(self, _evento=None):
        filas = self.__sistema.ver_diagnosticos(self.__usuario, self.__v["a_dni"].get().strip())
        lineas = [f"{fecha:%Y-%m-%d %H:%M} · {motivo}: {diagnostico}"
                  for fecha, motivo, diagnostico in filas]
        self.__mostrar(self.__texto_atencion,
                       "\n".join(lineas) or "El paciente no tiene atenciones registradas.")

    @manejar_errores
    def __preparar_historia(self, _evento=None):
        r = self.__sistema.preparar_historia(self.__usuario, self.__v["a_dni"].get().strip())
        ultima = r["ultima_atencion"] or "sin atenciones"
        self.__mostrar(self.__texto_atencion,
                       f"Historia {r['numero']} lista.\nAtenciones registradas: "
                       f"{r['total_atenciones']}\nÚltima atención: {ultima}\n"
                       "(Los diagnósticos solo los puede ver el médico.)")

    # ---------- Pestaña Citas ----------
    def __construir_citas(self, marco):
        self.__campo(marco, "DNI del paciente", "c_dni", 0, 12)
        nombres = [s.nombre for s in self.__sistema.listar_servicios()]
        self.__lista(marco, "Servicio", "c_servicio", nombres, 1, 28, self.__al_elegir_servicio_cita)
        self.__combo_personal_cita = self.__lista(marco, "Personal", "c_personal", [], 2, 40)
        self.__campo(marco, "Fecha (AAAA-MM-DD)", "c_fecha", 3, 14)
        self.__lista(marco, "Turno", "c_turno", list(TURNOS), 4, 14)
        botones = ttk.Frame(marco)
        botones.grid(row=5, column=0, columnspan=2, pady=6)
        ttk.Button(botones, text="Programar cita",
                   command=self.__programar_cita).pack(side="left", padx=4)
        ttk.Button(botones, text="Ver citas del servicio",
                   command=self.__listar_citas).pack(side="left", padx=4)
        ttk.Button(botones, text="Cancelar cita elegida",
                   command=self.__cancelar_cita).pack(side="left", padx=4)
        columnas = ("paciente", "fecha", "turno", "personal")
        self.__tabla_citas = ttk.Treeview(marco, columns=columnas, show="headings", height=8)
        for columna, titulo in zip(columnas, ("Paciente", "Fecha", "Turno", "Personal")):
            self.__tabla_citas.heading(columna, text=titulo)
        self.__tabla_citas.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=8)

    @manejar_errores
    def __al_elegir_servicio_cita(self, _evento=None):
        self.__cargar_personal(self.__combo_personal_cita, self.__v["c_servicio"].get(), "c_personal")
        self.__listar_citas()

    @manejar_errores
    def __programar_cita(self, _evento=None):
        v = self.__v
        self.__sistema.programar_cita(
            self.__usuario, v["c_dni"].get().strip(), v["c_servicio"].get(),
            self.__dni_de_personal("c_personal"), convertir_fecha(v["c_fecha"].get()),
            v["c_turno"].get())
        messagebox.showinfo("Cita programada", "La cita se programó correctamente.")
        self.__listar_citas()

    @manejar_errores
    def __listar_citas(self, _evento=None):
        tabla = self.__tabla_citas
        tabla.delete(*tabla.get_children())
        self.__citas_listadas = {}
        servicio = self.__v["c_servicio"].get()
        if not servicio:
            return
        for i, cita in enumerate(self.__sistema.listar_citas(servicio)):
            self.__citas_listadas[str(i)] = cita
            tabla.insert("", "end", iid=str(i), values=(
                cita.paciente.nombres, cita.fecha.isoformat(), cita.turno, cita.personal.nombres))

    @manejar_errores
    def __cancelar_cita(self, _evento=None):
        seleccion = self.__tabla_citas.selection()
        if not seleccion:
            raise ErrorDeValidacion("Seleccione una cita de la lista.")
        self.__sistema.cancelar_cita(self.__usuario, self.__citas_listadas[seleccion[0]])
        self.__listar_citas()

    # ---------- Pestaña Farmacia ----------
    def __construir_farmacia(self, marco):
        columnas = ("codigo", "medicamento", "stock", "estado")
        self.__tabla_inventario = ttk.Treeview(marco, columns=columnas, show="headings", height=9)
        for columna, titulo in zip(columnas, ("Código", "Medicamento", "Stock", "Estado")):
            self.__tabla_inventario.heading(columna, text=titulo)
        self.__tabla_inventario.tag_configure("bajo", foreground="#b00020")
        self.__tabla_inventario.grid(row=0, column=0, columnspan=3, sticky="nsew", pady=4)
        self.__etiqueta_alerta = ttk.Label(marco, text="")
        self.__etiqueta_alerta.grid(row=1, column=0, columnspan=3, sticky="w")
        self.__campo(marco, "DNI del paciente", "f_dni", 2, 12)
        self.__campo(marco, "Medicamentos (CÓDIGO:CANTIDAD, ...)", "f_items", 3, 40)
        botones = ttk.Frame(marco)
        botones.grid(row=4, column=0, columnspan=2, pady=6)
        ttk.Button(botones, text="Dispensar receta",
                   command=self.__dispensar).pack(side="left", padx=4)
        ttk.Button(botones, text="Actualizar inventario",
                   command=self.__refrescar_inventario).pack(side="left", padx=4)

    def __refrescar_inventario(self, _evento=None):
        tabla = self.__tabla_inventario
        tabla.delete(*tabla.get_children())
        bajos = {m.codigo for m in self.__sistema.inventario.stock_bajo()}
        for m in self.__sistema.inventario.listar():
            es_bajo = m.codigo in bajos
            tabla.insert("", "end", iid=m.codigo, tags=("bajo",) if es_bajo else (),
                         values=(m.codigo, m.nombre, m.stock, "STOCK BAJO" if es_bajo else "OK"))
        self.__etiqueta_alerta.configure(
            text="Alerta: hay medicamentos por reponer." if bajos else "Stock en orden.")

    @manejar_errores
    def __dispensar(self, _evento=None):
        items = convertir_items(self.__v["f_items"].get())
        self.__sistema.dispensar_receta(self.__usuario, self.__v["f_dni"].get().strip(), items)
        messagebox.showinfo("Receta dispensada", "Se descontó el stock del inventario.")
        self.__limpiar("f_items")
        self.__refrescar_inventario()

    # ---------- Pestaña Horarios ----------
    def __construir_horarios(self, marco):
        nombres = [s.nombre for s in self.__sistema.listar_servicios()]
        self.__lista(marco, "Servicio", "h_servicio", nombres, 0, 28, self.__al_elegir_servicio_horario)
        self.__lista(marco, "Día", "h_dia", list(DIAS), 1, 14)
        self.__lista(marco, "Turno", "h_turno", list(TURNOS), 2, 14)
        self.__combo_personal_horario = self.__lista(marco, "Personal", "h_personal", [], 3, 40)
        ttk.Button(marco, text="Asignar al horario",
                   command=self.__asignar_horario).grid(row=4, column=0, pady=6)
        ttk.Button(marco, text="Quitar del horario",
                   command=self.__quitar_horario).grid(row=4, column=1, pady=6)
        self.__texto_horarios = tk.Text(marco, height=14, width=100, state="disabled")
        self.__texto_horarios.grid(row=5, column=0, columnspan=3, pady=8)

    @manejar_errores
    def __al_elegir_servicio_horario(self, _evento=None):
        self.__cargar_personal(self.__combo_personal_horario, self.__v["h_servicio"].get(), "h_personal")
        self.__mostrar_horarios()

    @manejar_errores
    def __asignar_horario(self, _evento=None):
        v = self.__v
        self.__sistema.asignar_horario(self.__usuario, v["h_servicio"].get(), v["h_dia"].get(),
                                       v["h_turno"].get(), self.__dni_de_personal("h_personal"))
        self.__mostrar_horarios()

    def __mostrar_horarios(self):
        servicio = self.__sistema.obtener_servicio(self.__v["h_servicio"].get())
        lineas = [f"{servicio.nombre} · {h.dia.capitalize()} · {h.turno}: "
                  + ", ".join(p.nombres for p in h.listar_personal())
                  for h in servicio.listar_horarios()]
        self.__mostrar(self.__texto_horarios,
                       "\n".join(lineas) or "Este servicio aún no tiene horarios asignados.")
       
    @manejar_errores
    def __quitar_horario(self, _evento=None):
        v = self.__v
        self.__sistema.quitar_de_horario(self.__usuario, v["h_servicio"].get(), v["h_dia"].get(),
                                         v["h_turno"].get(), self.__dni_de_personal("h_personal"))
        self.__mostrar_horarios()

    # ---------- Pestaña Reporte ----------
    def __construir_reporte(self, marco):
        hoy = date.today()
        self.__campo(marco, "Desde (AAAA-MM-DD)", "r_desde", 0, 14, hoy.replace(day=1).isoformat())
        self.__campo(marco, "Hasta (AAAA-MM-DD)", "r_hasta", 1, 14, hoy.isoformat())
        ttk.Button(marco, text="Generar reporte",
                   command=self.__generar_reporte).grid(row=2, column=0, columnspan=2, pady=6)
        self.__texto_reporte = tk.Text(marco, height=16, width=100, state="disabled")
        self.__texto_reporte.grid(row=3, column=0, columnspan=3, pady=8)

    @manejar_errores
    def __generar_reporte(self, _evento=None):
        r = self.__sistema.reporte(convertir_fecha(self.__v["r_desde"].get()),
                                   convertir_fecha(self.__v["r_hasta"].get()))
        por_resolucion = "\n".join(f"  · {nombre}: {cantidad}"
                                   for nombre, cantidad in sorted(r["por_resolucion"].items()))
        self.__mostrar(self.__texto_reporte, (
            f"Reporte de atenciones del {r['desde']} al {r['hasta']}\n"
            f"Total de atenciones: {r['total']}\n{por_resolucion or '  (sin atenciones)'}\n\n"
            f"Medicamentos por reponer: {', '.join(r['a_reponer']) or 'ninguno'}\n"
            f"Unidades en stock: {r['unidades_en_stock']}"))
