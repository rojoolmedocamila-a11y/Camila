import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import datetime

archivo_datos = "datos.json"


PERSONAS_DEFAULT = {
    "tochi": "Adrian de la cruz",
    "dayan": "Matus Dayan",
    "chino": "Denisse Omaña",
}

MODELOS_DEFAULT = {
    "Kia": {"base": 3500, "extra": 42},
    "Avanza": {"base": 3500, "extra": 42},
    "BYD": {"base": 5300, "extra": 63},
}

MODELOS_POR_DEFECTO_PERSONA = {
    "tochi": "BYD",
    "dayan": "Avanza",
    "chino": "Kia",
}

meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
         "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

meses_abrev = ["ene", "feb", "mar", "abr", "may", "jun",
               "jul", "ago", "sep", "oct", "nov", "dic"]


dias = ["Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo", "Lunes"]

FORMAS_PAGO = ["Efectivo", "Deposito NU", "Deposito BBVA", "Deposito Inbursa"]



COLOR_FONDO = "#eef3f7"
COLOR_HEADER_BG = "#2c3e50"
COLOR_HEADER_FG = "white"
COLOR_TABLA_HEADER_BG = "#34495e"
COLOR_TABLA_HEADER_FG = "white"
COLOR_TOTAL_BG = "#2980b9"
COLOR_TOTAL_FG = "white"
COLOR_TITULO = "#2c3e50"


def generar_calendario(anio):
    semanas_mes = {}
    mapa_semanas = {}

    d = datetime.date(anio, 1, 1)
    while d.weekday() != 1:
        d -= datetime.timedelta(days=1)

    numero_semana = 1
    fin_anio = datetime.date(anio, 12, 31)

    while d <= fin_anio:
        fin_semana = d + datetime.timedelta(days=6)

        dias_fechas = {}
        cur = d
        for nombre_dia in dias:
            dias_fechas[nombre_dia] = cur.day
            cur += datetime.timedelta(days=1)

        if fin_semana.year != anio:
            txt_fin = "{} {} {}".format(fin_semana.day, meses_abrev[fin_semana.month - 1], fin_semana.year)
        else:
            txt_fin = "{} {}".format(fin_semana.day, meses_abrev[fin_semana.month - 1])

        texto = "Semana {}: {} {} - {}".format(
            numero_semana, d.day, meses_abrev[d.month - 1], txt_fin
        )

        medio = d + datetime.timedelta(days=3)
        mes_nombre = meses[medio.month - 1]

        semanas_mes.setdefault(mes_nombre, []).append(texto)
        mapa_semanas[texto] = {"numero": numero_semana, "dias_fechas": dias_fechas}

        numero_semana += 1
        d = d + datetime.timedelta(days=7)

    return semanas_mes, mapa_semanas


anio_actual = datetime.date.today().year
semanas_mes, mapa_semanas = generar_calendario(anio_actual)


def texto_a_numero(txt):
    try:
        return float(txt)
    except Exception:
        return 0.0


def hora_a_numero(txt):
    txt = txt.strip().lower().replace(".", "")
    if txt == "":
        return None

    es_pm = False
    es_am = False
    if "pm" in txt:
        es_pm = True
        txt = txt.replace("pm", "")
    elif "am" in txt:
        es_am = True
        txt = txt.replace("am", "")

    txt = txt.strip()
    if txt == "":
        return None

    try:
        if ":" in txt:
            partes = txt.split(":")
            h = int(partes[0])
            m = int(partes[1])
        else:
            h = int(txt)
            m = 0
    except Exception:
        return None

    if es_pm and h != 12:
        h = h + 12
    if es_am and h == 12:
        h = 0

    return h + m / 60.0


def calcular_horas_del_rango(txt):
    txt = txt.strip().lower()
    if " a " not in txt:
        return None
    inicio_txt, fin_txt = txt.split(" a ", 1)
    inicio = hora_a_numero(inicio_txt)
    fin = hora_a_numero(fin_txt)
    if inicio is None or fin is None:
        return None
    horas = fin - inicio
    if horas < 0:
        horas = horas + 24
    return horas


def obtener_horas_trabajadas(txt):
    txt = txt.strip()
    if txt == "":
        return 0.0
    try:
        return float(txt)
    except Exception:
        pass
    horas = calcular_horas_del_rango(txt)
    if horas is not None:
        return horas
    return 0.0


def dinero(v):
    try:
        return "$" + format(v, ",.2f")
    except Exception:
        return "$0.00"



def cargar_datos():
    base = {
        "personas": dict(PERSONAS_DEFAULT),
        "modelos": dict(MODELOS_DEFAULT),
        "registros": {},
    }
    if os.path.exists(archivo_datos):
        try:
            with open(archivo_datos, "r", encoding="utf-8") as f:
                cargado = json.load(f)
            if "personas" in cargado:
                base["personas"] = cargado["personas"]
            if "modelos" in cargado:
                base["modelos"] = cargado["modelos"]
            if "registros" in cargado:
                base["registros"] = cargado["registros"]
        except Exception:
            pass
    return base


def guardar_datos():
    with open(archivo_datos, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


datos = cargar_datos()
personas = datos["personas"]
modelos = datos["modelos"]

ventana = tk.Tk()
ventana.title("Control de Horarios")
ventana.geometry("1250x850")
ventana.config(bg=COLOR_FONDO)

contenedor = tk.Frame(ventana, bg=COLOR_FONDO)
contenedor.pack(fill="both", expand=True)
contenedor.grid_rowconfigure(0, weight=1)
contenedor.grid_columnconfigure(0, weight=1)

pantalla_principal = tk.Frame(contenedor, bg=COLOR_FONDO)
pantalla_depositos = tk.Frame(contenedor, bg=COLOR_FONDO)

for p in (pantalla_principal, pantalla_depositos):
    p.grid(row=0, column=0, sticky="nsew")


def mostrar_principal():
    pantalla_principal.tkraise()


def mostrar_depositos():
    actualizar_depositos()
    pantalla_depositos.tkraise()


persona_actual = None
bloqueado = False
editando = False
calculo_actual = {
    "total_extra_horas": 0,
    "total_extra_dinero": 0,
    "total_abonos": 0,
    "total_pagar": 0,
    "total_pagar_sin_extras": 0,
}

horario_entradas = {}
abonos_entradas = {}
extras_labels = {}
horastot_labels = {}
horario_header_labels = {}
sueldos_header_labels = {}
dia_total_labels = {}

modelo_var = tk.StringVar()
mes_var = tk.StringVar()
semana_var = tk.StringVar()
buscar_var = tk.StringVar()

cajas_personas = {}


def seleccionar_persona(nombre_clave):
    global persona_actual
    persona_actual = nombre_clave
    label_nombre.config(text=personas[nombre_clave])
    for k in cajas_personas:
        if k == nombre_clave:
            cajas_personas[k].config(relief="sunken")
        else:
            cajas_personas[k].config(relief="raised")
    cargar_registro()


def refrescar_botones_personas():
    for w in fc.winfo_children():
        w.destroy()
    cajas_personas.clear()
    for clave in personas:
        b = tk.Button(fc, text=clave.capitalize(), width=10, height=2,
                      command=lambda k=clave: seleccionar_persona(k))
        b.pack(side="left", padx=5)
        cajas_personas[clave] = b


def refrescar_combo_modelos():
    valores = list(modelos.keys())
    combo_modelo["values"] = valores
    if valores and modelo_var.get() not in valores:
        modelo_var.set(valores[0])


def buscar_enter(event=None):
    txt = buscar_var.get().strip().lower()
    encontrado = None
    for clave, nombre in personas.items():
        if txt == clave or txt in nombre.lower():
            encontrado = clave
            break
    if encontrado:
        seleccionar_persona(encontrado)
    else:
        messagebox.showinfo("Buscar", "No se encontro ese conductor")


def actualizar_encabezados_dias():
    info = mapa_semanas.get(semana_var.get())
    for d in dias:
        numero = ""
        if info:
            numero = str(info["dias_fechas"].get(d, ""))
        texto = d + ("\n" + numero if numero else "")
        if d in horario_header_labels:
            horario_header_labels[d].config(text=texto)
        if d in sueldos_header_labels:
            sueldos_header_labels[d].config(text=texto)


def cambio_mes(event=None):
    mes = mes_var.get()
    lista_semanas = semanas_mes.get(mes, [])
    combo_semana["values"] = lista_semanas
    if lista_semanas:
        semana_var.set(lista_semanas[0])
    actualizar_encabezados_dias()
    cargar_registro()


def cambio_semana(event=None):
    actualizar_encabezados_dias()
    cargar_registro()


def cargar_registro():
    global bloqueado, editando

    poner_estado_campos("normal")

    for d in dias:
        horario_entradas[d].delete(0, tk.END)
        for forma in FORMAS_PAGO:
            abonos_entradas[d][forma].delete(0, tk.END)

    bloqueado = False
    editando = False

    valores_modelo = list(modelos.keys())
    modelo_default = MODELOS_POR_DEFECTO_PERSONA.get(persona_actual)
    if modelo_default and modelo_default in modelos:
        modelo_var.set(modelo_default)
    elif valores_modelo:
        modelo_var.set(valores_modelo[0])

    if persona_actual and mes_var.get() and semana_var.get():
        reg = datos["registros"].get(persona_actual, {}).get(mes_var.get(), {}).get(semana_var.get())
        if reg:
            for d in dias:
                horario_entradas[d].insert(0, reg.get("horario", {}).get(d, ""))
                abonos_dia = reg.get("abonos", {}).get(d, {})
                for forma in FORMAS_PAGO:
                    abonos_entradas[d][forma].insert(0, abonos_dia.get(forma, ""))
            if reg.get("modelo") and reg.get("modelo") in modelos:
                modelo_var.set(reg["modelo"])
            bloqueado = True

    calcular_todo()
    actualizar_botones()


def calcular_todo(event=None):
    horas_trabajadas = {}
    for d in dias:
        horas_trabajadas[d] = obtener_horas_trabajadas(horario_entradas[d].get())

    horario_val = {}
    extra_val = {}
    horastot_val = {}
    for d in dias:
        if horas_trabajadas[d] > 12:
            horario_val[d] = 12
            extra_val[d] = horas_trabajadas[d] - 12
        else:
            horario_val[d] = horas_trabajadas[d]
            extra_val[d] = 0
        horastot_val[d] = horario_val[d] + extra_val[d]

    total_horario = sum(horario_val.values())
    total_extra = sum(extra_val.values())
    total_horastot = sum(horastot_val.values())

    for d in dias:
        extras_labels[d].config(text=str(extra_val[d]))
        horastot_labels[d].config(text=str(horastot_val[d]))
    label_total_horario.config(text=str(total_horario))
    label_total_extra.config(text=str(total_extra))
    label_total_horastot.config(text=str(total_horastot))

    abonos_dia_val = {}
    for d in dias:
        suma_dia = 0.0
        for forma in FORMAS_PAGO:
            suma_dia += texto_a_numero(abonos_entradas[d][forma].get())
        abonos_dia_val[d] = suma_dia
        dia_total_labels[d].config(text=dinero(suma_dia))

    total_abonos = sum(abonos_dia_val.values())

    info_modelo = modelos.get(modelo_var.get(), {"base": 0, "extra": 0})
    base = info_modelo.get("base", 0)
    tarifa = info_modelo.get("extra", 0)

    total_extra_dinero = tarifa * total_extra
    total_pagar = base + total_extra_dinero - total_abonos
    total_pagar_sin_extras = total_pagar - total_extra_dinero

    label_abonos_totales.config(text=dinero(total_abonos))
    label_total_extra_dinero.config(text=dinero(total_extra_dinero))
    label_total_pagar.config(text=dinero(total_pagar))
    label_total_pagar_sin_extras.config(text=dinero(total_pagar_sin_extras))

    global calculo_actual
    calculo_actual = {
        "total_extra_horas": total_extra,
        "total_extra_dinero": total_extra_dinero,
        "total_abonos": total_abonos,
        "total_pagar": total_pagar,
        "total_pagar_sin_extras": total_pagar_sin_extras,
    }


def poner_estado_campos(estado):
    for d in dias:
        horario_entradas[d].config(state=estado)
        for forma in FORMAS_PAGO:
            abonos_entradas[d][forma].config(state=estado)
    combo_modelo.config(state="readonly")


def actualizar_botones():
    if persona_actual is None:
        poner_estado_campos("disabled")
        boton_guardar.config(state="disabled")
        boton_editar.config(state="disabled")
        return

    if bloqueado and not editando:
        poner_estado_campos("disabled")
        boton_guardar.config(state="disabled")
        boton_editar.config(state="normal")
    else:
        poner_estado_campos("normal")
        boton_guardar.config(state="normal")
        boton_editar.config(state="disabled")


def click_editar():
    global editando
    editando = True
    actualizar_botones()


def click_guardar():
    global bloqueado, editando

    if not (persona_actual and mes_var.get() and semana_var.get()):
        messagebox.showwarning("Falta info", "Selecciona persona, mes y semana")
        return

    calcular_todo()

    info_semana = mapa_semanas.get(semana_var.get(), {})

    reg = {
        "horario": {d: horario_entradas[d].get() for d in dias},
        "abonos": {d: {forma: abonos_entradas[d][forma].get() for forma in FORMAS_PAGO} for d in dias},
        "modelo": modelo_var.get(),
        "semana_numero": info_semana.get("numero"),
        "total_extra_horas": calculo_actual["total_extra_horas"],
        "total_extra_dinero": calculo_actual["total_extra_dinero"],
        "abonos_totales": calculo_actual["total_abonos"],
        "total_a_pagar": calculo_actual["total_pagar"],
        "total_pagar_sin_extras": calculo_actual["total_pagar_sin_extras"],
    }

    registros = datos["registros"]
    if persona_actual not in registros:
        registros[persona_actual] = {}
    if mes_var.get() not in registros[persona_actual]:
        registros[persona_actual][mes_var.get()] = {}
    registros[persona_actual][mes_var.get()][semana_var.get()] = reg

    guardar_datos()

    bloqueado = True
    editando = False
    actualizar_botones()

    if abs(calculo_actual["total_pagar"]) > 0.009:
        messagebox.showinfo(
            "Listo",
            "Se guardo la informacion.\nOjo: quedo un saldo pendiente de " + dinero(calculo_actual["total_pagar"])
        )
    else:
        messagebox.showinfo("Listo", "Se guardo la informacion. Semana saldada en $0.00")


def abrir_nuevo_conductor():
    win = tk.Toplevel(ventana)
    win.title("Nuevo conductor")
    win.geometry("320x180")
    win.config(bg=COLOR_FONDO)
    win.grab_set()

    tk.Label(win, text="Apodo (clave corta):", bg=COLOR_FONDO).pack(anchor="w", padx=10, pady=(15, 0))
    entry_apodo = tk.Entry(win, width=30)
    entry_apodo.pack(padx=10)

    tk.Label(win, text="Nombre completo del chofer:", bg=COLOR_FONDO).pack(anchor="w", padx=10, pady=(10, 0))
    entry_nombre = tk.Entry(win, width=30)
    entry_nombre.pack(padx=10)

    def guardar():
        apodo = entry_apodo.get().strip().lower()
        nombre = entry_nombre.get().strip()
        if not apodo or not nombre:
            messagebox.showwarning("Falta info", "Escribe el apodo y el nombre", parent=win)
            return
        if apodo in personas:
            messagebox.showwarning("Ya existe", "Ese apodo ya esta usado", parent=win)
            return
        personas[apodo] = nombre
        guardar_datos()
        refrescar_botones_personas()
        actualizar_depositos()
        win.destroy()

    tk.Button(win, text="Guardar", command=guardar).pack(pady=15)


def abrir_eliminar_conductor():
    win = tk.Toplevel(ventana)
    win.title("Eliminar conductor")
    win.geometry("320x260")
    win.config(bg=COLOR_FONDO)
    win.grab_set()

    tk.Label(win, text="Selecciona el conductor a eliminar:", bg=COLOR_FONDO).pack(anchor="w", padx=10, pady=10)
    lista = tk.Listbox(win, width=35, height=8)
    lista.pack(padx=10)
    claves = list(personas.keys())
    for c in claves:
        lista.insert(tk.END, c + " - " + personas[c])

    def eliminar():
        global persona_actual
        sel = lista.curselection()
        if not sel:
            return
        clave = claves[sel[0]]
        if messagebox.askyesno("Confirmar", "¿Eliminar a " + personas[clave] + "? Se borrara tambien su historial.", parent=win):
            personas.pop(clave, None)
            datos["registros"].pop(clave, None)
            if persona_actual == clave:
                persona_actual = None
                label_nombre.config(text="Selecciona una persona")
            guardar_datos()
            refrescar_botones_personas()
            actualizar_depositos()
            actualizar_botones()
            win.destroy()

    tk.Button(win, text="Eliminar", command=eliminar, fg="red").pack(pady=10)


def abrir_nuevo_modelo():
    win = tk.Toplevel(ventana)
    win.title("Nuevo modelo de carro")
    win.geometry("320x230")
    win.config(bg=COLOR_FONDO)
    win.grab_set()

    tk.Label(win, text="Nombre del modelo:", bg=COLOR_FONDO).pack(anchor="w", padx=10, pady=(15, 0))
    entry_nombre = tk.Entry(win, width=30)
    entry_nombre.pack(padx=10)

    tk.Label(win, text="Cantidad total a pagar (base semanal):", bg=COLOR_FONDO).pack(anchor="w", padx=10, pady=(10, 0))
    entry_base = tk.Entry(win, width=30)
    entry_base.pack(padx=10)

    tk.Label(win, text="Costo de cada hora extra:", bg=COLOR_FONDO).pack(anchor="w", padx=10, pady=(10, 0))
    entry_extra = tk.Entry(win, width=30)
    entry_extra.pack(padx=10)

    def guardar():
        nombre = entry_nombre.get().strip()
        base = texto_a_numero(entry_base.get())
        extra = texto_a_numero(entry_extra.get())
        if not nombre:
            messagebox.showwarning("Falta info", "Escribe el nombre del modelo", parent=win)
            return
        if nombre in modelos:
            messagebox.showwarning("Ya existe", "Ese modelo ya esta registrado", parent=win)
            return
        modelos[nombre] = {"base": base, "extra": extra}
        guardar_datos()
        refrescar_combo_modelos()
        win.destroy()

    tk.Button(win, text="Guardar", command=guardar).pack(pady=15)


def abrir_eliminar_modelo():
    win = tk.Toplevel(ventana)
    win.title("Eliminar modelo")
    win.geometry("320x260")
    win.config(bg=COLOR_FONDO)
    win.grab_set()

    tk.Label(win, text="Selecciona el modelo a eliminar:", bg=COLOR_FONDO).pack(anchor="w", padx=10, pady=10)
    lista = tk.Listbox(win, width=35, height=8)
    lista.pack(padx=10)
    nombres = list(modelos.keys())
    for n in nombres:
        lista.insert(tk.END, n)

    def eliminar():
        sel = lista.curselection()
        if not sel:
            return
        nombre = nombres[sel[0]]
        if messagebox.askyesno("Confirmar", "¿Eliminar el modelo " + nombre + "?", parent=win):
            modelos.pop(nombre, None)
            guardar_datos()
            refrescar_combo_modelos()
            calcular_todo()
            win.destroy()

    tk.Button(win, text="Eliminar", command=eliminar, fg="red").pack(pady=10)



menu_arriba = tk.Frame(pantalla_principal, bg=COLOR_HEADER_BG)
menu_arriba.pack(side="top", fill="x")
tk.Label(menu_arriba, text="Control de Horarios", font=("Arial", 11, "bold"),
         bg=COLOR_HEADER_BG, fg=COLOR_HEADER_FG).pack(side="left", padx=10, pady=5)
tk.Button(menu_arriba, text="Depositos finales", command=mostrar_depositos).pack(side="right", padx=10, pady=5)

menu_gestion = tk.Frame(pantalla_principal, bg=COLOR_FONDO)
menu_gestion.pack(side="top", fill="x", pady=(0, 5))
tk.Button(menu_gestion, text="+ Nuevo conductor", command=abrir_nuevo_conductor).pack(side="left", padx=5)
tk.Button(menu_gestion, text="- Eliminar conductor", command=abrir_eliminar_conductor).pack(side="left", padx=5)
tk.Button(menu_gestion, text="+ Nuevo modelo", command=abrir_nuevo_modelo).pack(side="left", padx=5)
tk.Button(menu_gestion, text="- Eliminar modelo", command=abrir_eliminar_modelo).pack(side="left", padx=5)

fila_arriba = tk.Frame(pantalla_principal, bg=COLOR_FONDO)
fila_arriba.pack(fill="x", padx=10, pady=10)

izquierda = tk.Frame(fila_arriba, bg=COLOR_FONDO)
izquierda.pack(side="left", anchor="n")

f1 = tk.Frame(izquierda, bg=COLOR_FONDO)
f1.pack(anchor="w", pady=3)
tk.Label(f1, text="Modelo de carro", bg=COLOR_FONDO).pack(side="left")
combo_modelo = ttk.Combobox(f1, textvariable=modelo_var, values=list(modelos.keys()), state="readonly", width=10)
combo_modelo.pack(side="left", padx=5)
combo_modelo.bind("<<ComboboxSelected>>", calcular_todo)

f2 = tk.Frame(izquierda, bg=COLOR_FONDO)
f2.pack(anchor="w", pady=3)
tk.Label(f2, text="Mes", bg=COLOR_FONDO).pack(side="left")
combo_mes = ttk.Combobox(f2, textvariable=mes_var, values=meses, state="readonly", width=14)
combo_mes.pack(side="left", padx=5)
combo_mes.bind("<<ComboboxSelected>>", cambio_mes)

f3 = tk.Frame(izquierda, bg=COLOR_FONDO)
f3.pack(anchor="w", pady=3)
tk.Label(f3, text="Semana", bg=COLOR_FONDO).pack(side="left")
combo_semana = ttk.Combobox(f3, textvariable=semana_var, state="readonly", width=30)
combo_semana.pack(side="left", padx=5)
combo_semana.bind("<<ComboboxSelected>>", cambio_semana)

derecha = tk.Frame(fila_arriba, bg=COLOR_FONDO)
derecha.pack(side="right", anchor="n")

fb = tk.Frame(derecha, bg=COLOR_FONDO)
fb.pack(anchor="e")
tk.Label(fb, text="Buscar:", bg=COLOR_FONDO).pack(side="left")
entrada_buscar = tk.Entry(fb, textvariable=buscar_var, width=20)
entrada_buscar.pack(side="left", padx=5)
entrada_buscar.bind("<Return>", buscar_enter)

fc = tk.Frame(derecha, pady=8, bg=COLOR_FONDO)
fc.pack(anchor="e")

label_nombre = tk.Label(pantalla_principal, text="Selecciona una persona", font=("Arial", 18, "bold"),
                         bg=COLOR_FONDO, fg=COLOR_TITULO)
label_nombre.pack(pady=10)

tk.Label(pantalla_principal, text="HORARIO", font=("Arial", 14, "bold"),
         bg=COLOR_FONDO, fg=COLOR_TITULO).pack(anchor="w", padx=15)
tk.Label(pantalla_principal, text='Escribe la hora asi: 10am a 1pm  (o un numero de horas)',
         font=("Arial", 8), bg=COLOR_FONDO).pack(anchor="w", padx=15)

tabla_horario = tk.Frame(pantalla_principal, padx=15, bg=COLOR_FONDO)
tabla_horario.pack(fill="x", pady=5)

tk.Label(tabla_horario, text="", width=12, bg=COLOR_FONDO).grid(row=0, column=0)
for j, d in enumerate(dias):
    lbl = tk.Label(tabla_horario, text=d, width=9, relief="ridge",
                    bg=COLOR_TABLA_HEADER_BG, fg=COLOR_TABLA_HEADER_FG)
    lbl.grid(row=0, column=j + 1)
    horario_header_labels[d] = lbl
tk.Label(tabla_horario, text="Total", width=9, relief="ridge",
         bg=COLOR_TABLA_HEADER_BG, fg=COLOR_TABLA_HEADER_FG).grid(row=0, column=8)

tk.Label(tabla_horario, text="Horario", width=12, relief="ridge",
         bg=COLOR_TABLA_HEADER_BG, fg=COLOR_TABLA_HEADER_FG).grid(row=1, column=0)
for j, d in enumerate(dias):
    e = tk.Entry(tabla_horario, width=9, justify="center")
    e.grid(row=1, column=j + 1, padx=1, pady=1)
    e.bind("<KeyRelease>", calcular_todo)
    horario_entradas[d] = e
label_total_horario = tk.Label(tabla_horario, text="0", width=9, relief="groove",
                                bg=COLOR_TOTAL_BG, fg=COLOR_TOTAL_FG)
label_total_horario.grid(row=1, column=8)

tk.Label(tabla_horario, text="Extras", width=12, relief="ridge",
         bg=COLOR_TABLA_HEADER_BG, fg=COLOR_TABLA_HEADER_FG).grid(row=2, column=0)
for j, d in enumerate(dias):
    lbl = tk.Label(tabla_horario, text="0", width=9, relief="groove")
    lbl.grid(row=2, column=j + 1, padx=1, pady=1)
    extras_labels[d] = lbl
label_total_extra = tk.Label(tabla_horario, text="0", width=9, relief="groove",
                              bg=COLOR_TOTAL_BG, fg=COLOR_TOTAL_FG)
label_total_extra.grid(row=2, column=8)

tk.Label(tabla_horario, text="Horas Totales", width=12, relief="ridge",
         bg=COLOR_TABLA_HEADER_BG, fg=COLOR_TABLA_HEADER_FG).grid(row=3, column=0)
for j, d in enumerate(dias):
    lbl = tk.Label(tabla_horario, text="0", width=9, relief="groove")
    lbl.grid(row=3, column=j + 1, padx=1, pady=1)
    horastot_labels[d] = lbl
label_total_horastot = tk.Label(tabla_horario, text="0", width=9, relief="groove",
                                 bg=COLOR_TOTAL_BG, fg=COLOR_TOTAL_FG)
label_total_horastot.grid(row=3, column=8)

tk.Label(pantalla_principal, text="SUELDOS", font=("Arial", 14, "bold"),
         bg=COLOR_FONDO, fg=COLOR_TITULO).pack(anchor="w", padx=15)
tk.Label(pantalla_principal, text='Captura la cantidad en cada forma de pago que aplique (puedes dejar en 0 o llenar varias)',
         font=("Arial", 8), bg=COLOR_FONDO).pack(anchor="w", padx=15)

tabla_sueldos = tk.Frame(pantalla_principal, padx=15, bg=COLOR_FONDO)
tabla_sueldos.pack(fill="x", pady=5)

tk.Label(tabla_sueldos, text="Forma de pago", width=14, relief="ridge",
         bg=COLOR_TABLA_HEADER_BG, fg=COLOR_TABLA_HEADER_FG).grid(row=0, column=0)
for j, d in enumerate(dias):
    lbl = tk.Label(tabla_sueldos, text=d, width=10, relief="ridge",
                    bg=COLOR_TABLA_HEADER_BG, fg=COLOR_TABLA_HEADER_FG)
    lbl.grid(row=0, column=j + 1)
    sueldos_header_labels[d] = lbl
tk.Label(tabla_sueldos, text="Abonos\nTotales", width=10, relief="ridge",
         bg=COLOR_TABLA_HEADER_BG, fg=COLOR_TABLA_HEADER_FG).grid(row=0, column=8)
tk.Label(tabla_sueldos, text="Total horas\nextras $", width=10, relief="ridge",
         bg=COLOR_TABLA_HEADER_BG, fg=COLOR_TABLA_HEADER_FG).grid(row=0, column=9)
tk.Label(tabla_sueldos, text="Total a\npagar", width=10, relief="ridge",
         bg=COLOR_TABLA_HEADER_BG, fg=COLOR_TABLA_HEADER_FG).grid(row=0, column=10)
tk.Label(tabla_sueldos, text="Total a pagar\n(sin extra)", width=12, relief="ridge",
         bg=COLOR_TABLA_HEADER_BG, fg=COLOR_TABLA_HEADER_FG).grid(row=0, column=11)

for i, forma in enumerate(FORMAS_PAGO):
    fila = i + 1
    tk.Label(tabla_sueldos, text=forma, width=14, relief="ridge",
             bg=COLOR_TABLA_HEADER_BG, fg=COLOR_TABLA_HEADER_FG).grid(row=fila, column=0)
    for j, d in enumerate(dias):
        fr = tk.Frame(tabla_sueldos, bg=COLOR_FONDO)
        fr.grid(row=fila, column=j + 1, padx=1, pady=1)
        tk.Label(fr, text="$", bg=COLOR_FONDO).pack(side="left")
        e = tk.Entry(fr, width=7, justify="center")
        e.pack(side="left")
        e.bind("<KeyRelease>", calcular_todo)
        abonos_entradas.setdefault(d, {})[forma] = e

fila_totales = len(FORMAS_PAGO) + 1
tk.Label(tabla_sueldos, text="Total dia", width=14, relief="ridge", font=("Arial", 9, "bold"),
         bg=COLOR_TABLA_HEADER_BG, fg=COLOR_TABLA_HEADER_FG).grid(row=fila_totales, column=0)
for j, d in enumerate(dias):
    lbl = tk.Label(tabla_sueldos, text="$0.00", width=10, relief="groove")
    lbl.grid(row=fila_totales, column=j + 1, padx=1, pady=1)
    dia_total_labels[d] = lbl

label_abonos_totales = tk.Label(tabla_sueldos, text="$0.00", width=10, relief="groove",
                                 bg=COLOR_TOTAL_BG, fg=COLOR_TOTAL_FG)
label_abonos_totales.grid(row=fila_totales, column=8)
label_total_extra_dinero = tk.Label(tabla_sueldos, text="$0.00", width=10, relief="groove",
                                     bg=COLOR_TOTAL_BG, fg=COLOR_TOTAL_FG)
label_total_extra_dinero.grid(row=fila_totales, column=9)
label_total_pagar = tk.Label(tabla_sueldos, text="$0.00", width=10, relief="groove", font=("Arial", 9, "bold"),
                              bg=COLOR_TOTAL_BG, fg=COLOR_TOTAL_FG)
label_total_pagar.grid(row=fila_totales, column=10)

label_total_pagar_sin_extras = tk.Label(tabla_sueldos, text="$0.00", width=12, relief="groove", font=("Arial", 9, "bold"),
                                         bg=COLOR_TOTAL_BG, fg=COLOR_TOTAL_FG)
label_total_pagar_sin_extras.grid(row=fila_totales, column=11, padx=1, pady=1)

fila_botones = tk.Frame(pantalla_principal, pady=10, bg=COLOR_FONDO)
fila_botones.pack()
boton_guardar = tk.Button(fila_botones, text="Guardar", width=14, command=click_guardar)
boton_guardar.pack(side="left", padx=10)
boton_editar = tk.Button(fila_botones, text="Editar", width=14, command=click_editar)
boton_editar.pack(side="left", padx=10)


menu_dep = tk.Frame(pantalla_depositos, bg=COLOR_HEADER_BG)
menu_dep.pack(fill="x")
tk.Label(menu_dep, text="Depositos Finales", font=("Arial", 11, "bold"),
         bg=COLOR_HEADER_BG, fg=COLOR_HEADER_FG).pack(side="left", padx=10, pady=5)
tk.Button(menu_dep, text="Inicio", command=mostrar_principal).pack(side="right", padx=10, pady=5)

dep_mes_var = tk.StringVar()
dep_semana_var = tk.StringVar()

fila_dep = tk.Frame(pantalla_depositos, pady=15, bg=COLOR_FONDO)
fila_dep.pack()

tk.Label(fila_dep, text="Mes", bg=COLOR_FONDO).grid(row=0, column=0, padx=5, pady=5)
combo_dep_mes = ttk.Combobox(fila_dep, textvariable=dep_mes_var, values=meses, state="readonly", width=14)
combo_dep_mes.grid(row=0, column=1, padx=5, pady=5)

tk.Label(fila_dep, text="Semana", bg=COLOR_FONDO).grid(row=1, column=0, padx=5, pady=5)
combo_dep_semana = ttk.Combobox(fila_dep, textvariable=dep_semana_var, state="readonly", width=30)
combo_dep_semana.grid(row=1, column=1, padx=5, pady=5)

tk.Label(pantalla_depositos, text="Conductores", font=("Arial", 14, "bold"),
         bg=COLOR_FONDO, fg=COLOR_TITULO).pack(pady=(10, 5))

frame_conductores_dep = tk.Frame(pantalla_depositos, bg=COLOR_FONDO)
frame_conductores_dep.pack()

label_total_dep = tk.Label(pantalla_depositos, text="", font=("Arial", 14, "bold"), pady=10,
                            bg=COLOR_FONDO, fg=COLOR_TITULO)
label_total_dep.pack()

tk.Label(pantalla_depositos, text="Deudores", font=("Arial", 14, "bold"),
         bg=COLOR_FONDO, fg=COLOR_TITULO).pack(pady=(15, 5))
tk.Label(pantalla_depositos, text="",
         font=("Arial", 8), bg=COLOR_FONDO).pack()

frame_deudores = tk.Frame(pantalla_depositos, padx=15, bg=COLOR_FONDO)
frame_deudores.pack(fill="x", pady=10)


def cambio_dep_mes(event=None):
    lista = semanas_mes.get(dep_mes_var.get(), [])
    combo_dep_semana["values"] = lista
    if lista:
        dep_semana_var.set(lista[0])
    actualizar_depositos()


def cambio_dep_semana(event=None):
    actualizar_depositos()


combo_dep_mes.bind("<<ComboboxSelected>>", cambio_dep_mes)
combo_dep_semana.bind("<<ComboboxSelected>>", cambio_dep_semana)


def calcular_deudas(clave):
    deudas = []
    registros_persona = datos["registros"].get(clave, {})
    for mes, semanas in registros_persona.items():
        for texto_semana, reg in semanas.items():
            monto = reg.get("total_a_pagar", 0)
            if abs(monto) > 0.009:
                numero = texto_semana.split(":")[0].strip()
                deudas.append((mes, numero, monto))
    return deudas


def actualizar_depositos():
    if not dep_mes_var.get():
        dep_mes_var.set(meses[0])
        lista = semanas_mes.get(dep_mes_var.get(), [])
        combo_dep_semana["values"] = lista
        if lista:
            dep_semana_var.set(lista[0])

    mes = dep_mes_var.get()
    semana = dep_semana_var.get()

    for w in frame_conductores_dep.winfo_children():
        w.destroy()

    total = 0
    if mes and semana:
        for clave, nombre in personas.items():
            reg = datos["registros"].get(clave, {}).get(mes, {}).get(semana)
            if reg:
                monto = reg.get("abonos_totales", 0)
                total = total + monto
                texto = nombre + "  ->  Abonos Totales: " + dinero(monto)
            else:
                texto = nombre + "  ->  (sin datos)"
            tk.Label(frame_conductores_dep, text=texto, font=("Arial", 12),
                     bg=COLOR_FONDO).pack(pady=3)

        semana_num = semana.split(":")[0]
        label_total_dep.config(text="Mes: " + mes + "   " + semana_num + "\nTotal a depositar: " + dinero(total))
    else:
        label_total_dep.config(text="")

    for w in frame_deudores.winfo_children():
        w.destroy()

    for clave, nombre in personas.items():
        deudas = calcular_deudas(clave)
        fila = tk.Frame(frame_deudores, bg=COLOR_FONDO)
        fila.pack(anchor="w", fill="x", pady=2)
        tk.Label(fila, text=nombre, width=20, anchor="w", font=("Arial", 10, "bold"),
                 bg=COLOR_FONDO).pack(side="left")
        if not deudas:
            tk.Label(fila, text="Sin adeudos", fg="green", bg=COLOR_FONDO).pack(side="left", padx=5)
        else:
            total_deuda = 0.0
            for mes_d, numero_d, monto_d in deudas:
                chip = tk.Label(fila, text=mes_d + " " + numero_d + ": " + dinero(monto_d),
                                 relief="groove", padx=4)
                chip.pack(side="left", padx=2)
                total_deuda += monto_d
            tk.Label(fila, text="Total deuda: " + dinero(total_deuda),
                     font=("Arial", 10, "bold"), fg="red", bg=COLOR_FONDO).pack(side="left", padx=10)



refrescar_botones_personas()
refrescar_combo_modelos()
mes_var.set(meses[datetime.date.today().month - 1])
cambio_mes()
actualizar_botones()
mostrar_principal()

ventana.mainloop()