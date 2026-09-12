import streamlit as st
import requests
import json
import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Control de Horarios Uber", layout="wide")

FIREBASE_URL = "https://servicio-uber-default-rtdb.firebaseio.com"

if FIREBASE_URL.endswith("/"):
    FIREBASE_URL = FIREBASE_URL[:-1]

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
        dias_fechas = {nombre_dia: (d + datetime.timedelta(days=i)).day for i, nombre_dia in enumerate(dias)}

        txt_fin = f"{fin_semana.day} {meses_abrev[fin_semana.month - 1]}" + (f" {fin_semana.year}" if fin_semana.year != anio else "")
        texto = f"Semana {numero_semana}: {d.day} {meses_abrev[d.month - 1]} - {txt_fin}"
        
        medio = d + datetime.timedelta(days=3)
        mes_nombre = meses[medio.month - 1]

        semanas_mes.setdefault(mes_nombre, []).append(texto)
        mapa_semanas[texto] = {"numero": numero_semana, "dias_fechas": dias_fechas}

        numero_semana += 1
        d += datetime.timedelta(days=7)

    return semanas_mes, mapa_semanas

anio_actual = datetime.date.today().year
semanas_mes, mapa_semanas = generar_calendario(anio_actual)

def texto_a_numero(txt):
    try: return float(txt)
    except Exception: return 0.0

def hora_a_numero(txt):
    txt = str(txt).strip().lower().replace(".", "")
    if not txt: return None
    es_pm, es_am = "pm" in txt, "am" in txt
    txt = txt.replace("pm", "").replace("am", "").strip()
    if not txt: return None
    try: h, m = map(int, txt.split(":")) if ":" in txt else (int(txt), 0)
    except Exception: return None
    if es_pm and h != 12: h += 12
    if es_am and h == 12: h = 0
    return h + m / 60.0

def obtener_horas_trabajadas(txt):
    txt = str(txt).strip()
    if not txt: return 0.0
    try: return float(txt)
    except Exception: pass
    if " a " in txt.lower():
        i, f = txt.lower().split(" a ", 1)
        h_i, h_f = hora_a_numero(i), hora_a_numero(f)
        if h_i is not None and h_f is not None:
            res = h_f - h_i
            return res + 24 if res < 0 else res
    return 0.0

def dinero(v):
    return f"${v:,.2f}"

# --- FUNCIONES DE NUBE (FIREBASE) ---
def cargar_datos_nube():
    base = {"personas": dict(PERSONAS_DEFAULT), "modelos": dict(MODELOS_DEFAULT), "registros": {}}
    try:
        res = requests.get(f"{FIREBASE_URL}/datos.json")
        if res.status_code == 200 and res.json() is not None:
            cargado = res.json()
            base["personas"].update(cargado.get("personas", {}))
            base["modelos"].update(cargado.get("modelos", {}))
            base["registros"] = cargado.get("registros", {})
    except Exception as e:
        st.error(f"Error al conectar con la nube: {e}")
    return base

def guardar_datos_nube():
    try:
        res = requests.put(f"{FIREBASE_URL}/datos.json", json=st.session_state.datos)
        if res.status_code == 200:
            return True
        else:
            st.error(f"Error al guardar en Firebase: Código {res.status_code}")
            return False
    except Exception as e:
        st.error(f"Error de conexión al guardar: {e}")
        return False

# BOTÓN DE RECARGA EN LA BARRA LATERAL (Limpia la memoria antes de cargar)
if st.sidebar.button("🔄 Recargar datos de la Nube", use_container_width=True):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.datos = cargar_datos_nube()
    st.rerun()

# CARGA INICIAL
if "datos" not in st.session_state:
    st.session_state.datos = cargar_datos_nube()

datos = st.session_state.datos

# --- INTERFAZ STREAMLIT ---
st.title("☁️ Control de Horarios Uber (Nube Automática)")

tab1, tab2, tab3 = st.tabs(["📋 Captura de Horarios", "💰 Depósitos y Deudas", "⚙️ Gestión (Choferes/Autos)"])

with tab1:
    c1, c2, c3 = st.columns(3)
    with c1:
        persona_sel = st.selectbox("Seleccionar Chofer", list(datos["personas"].keys()), 
                                  format_func=lambda x: f"{x.capitalize()} ({datos['personas'][x]})")
    with c2:
        mes_sel = st.selectbox("Mes", meses, index=datetime.date.today().month - 1)
    with c3:
        lista_sems = semanas_mes.get(mes_sel, [])
        semana_sel = st.selectbox("Semana", lista_sems if lista_sems else ["Sin semanas"])

    modelo_def = MODELOS_POR_DEFECTO_PERSONA.get(persona_sel, list(datos["modelos"].keys())[0])
    modelo_sel = st.selectbox("Modelo de Carro", list(datos["modelos"].keys()), 
                              index=list(datos["modelos"].keys()).index(modelo_def) if modelo_def in datos["modelos"] else 0)

    reg_existente = datos["registros"].get(persona_sel, {}).get(mes_sel, {}).get(semana_sel, {})

    st.subheader(f"Horarios - {datos['personas'].get(persona_sel, '')}")
    st.caption("Escribe las horas como: '10am a 1pm' o el número de horas trabajadas directamente.")

    cols = st.columns(7)
    horarios_captura = {}
    for i, d in enumerate(dias):
        val_prev = reg_existente.get("horario", {}).get(d, "")
        key_horario = f"h_{persona_sel}_{mes_sel}_{semana_sel}_{d}"
        horarios_captura[d] = cols[i].text_input(d, value=val_prev, key=key_horario)

    horas_extra = {}
    horas_totales = {}
    for d in dias:
        ht = obtener_horas_trabajadas(horarios_captura[d])
        ext = max(0.0, ht - 12.0)
        horas_extra[d] = ext
        horas_totales[d] = ht

    tot_ext = sum(horas_extra.values())
    tot_hrs = sum(horas_totales.values())

    st.write(f"**Total Horas Extra:** {tot_ext:.1f} hrs | **Total Horas Trabajadas:** {tot_hrs:.1f} hrs")

    st.subheader("Captura de Abonos / Pagos")
    abonos_captura = {}
    for forma in FORMAS_PAGO:
        st.write(f"**{forma}**")
        cols_pago = st.columns(7)
        abonos_captura[forma] = {}
        for i, d in enumerate(dias):
            val_p = reg_existente.get("abonos", {}).get(d, {}).get(forma, "")
            key_abono = f"p_{persona_sel}_{mes_sel}_{semana_sel}_{forma}_{d}"
            abonos_captura[forma][d] = cols_pago[i].text_input(f"{forma} {d}", value=val_p, label_visibility="collapsed", key=key_abono)

    total_abonos = sum(texto_a_numero(abonos_captura[f][d]) for f in FORMAS_PAGO for d in dias)
    info_mod = datos["modelos"].get(modelo_sel, {"base": 0, "extra": 0})
    dinero_extra = tot_ext * info_mod["extra"]
    total_a_pagar = info_mod["base"] + dinero_extra - total_abonos

    m1, m2, m3 = st.columns(3)
    m1.metric("Abonos Totales", dinero(total_abonos))
    m2.metric("Total Extras ($)", dinero(dinero_extra))
    m3.metric("Saldo Pendiente a Pagar", dinero(total_a_pagar))

    if st.button("☁️ Guardar Registro en la Nube", use_container_width=True):
        info_sem = mapa_semanas.get(semana_sel, {})
        reg = {
            "horario": horarios_captura,
            "abonos": abonos_captura,
            "modelo": modelo_sel,
            "semana_numero": info_sem.get("numero"),
            "total_extra_horas": tot_ext,
            "total_extra_dinero": dinero_extra,
            "abonos_totales": total_abonos,
            "total_a_pagar": total_a_pagar,
        }
        datos["registros"].setdefault(persona_sel, {}).setdefault(mes_sel, {})[semana_sel] = reg
        if guardar_datos_nube():
            st.success("¡Registro guardado exitosamente en la nube!")
            # Borramos la memoria local de la sesión para obligar a leer la nube limpia
            for key in list(st.session_state.keys()):
                if key != "datos":
                    del st.session_state[key]
            st.rerun()

with tab2:
    st.subheader("Resumen de Depósitos")
    cd1, cd2 = st.columns(2)
    mes_dep = cd1.selectbox("Mes Depósito", meses, key="dep_m")
    sems_dep = semanas_mes.get(mes_dep, [])
    sem_dep = cd2.selectbox("Semana Depósito", sems_dep if sems_dep else ["Sin semanas"], key="dep_s")

    tot_dep = 0.0
    for k, nombre in datos["personas"].items():
        r = datos["registros"].get(k, {}).get(mes_dep, {}).get(sem_dep, {})
        monto = r.get("abonos_totales", 0)
        tot_dep += monto
        st.write(f"• **{nombre}:** {dinero(monto)}")
    st.info(f"**Total a depositar en {mes_dep} ({sem_dep.split(':')[0]}): {dinero(tot_dep)}**")

    st.markdown("---")
    st.subheader("Deudores Pendientes")
    for k, nombre in datos["personas"].items():
        deudas = []
        for m, sems in datos["registros"].get(k, {}).items():
            for s_txt, r in sems.items():
                p = r.get("total_a_pagar", 0)
                if abs(p) > 0.01:
                    deudas.append(f"{m} ({s_txt.split(':')[0]}): {dinero(p)}")
        if deudas:
            st.write(f"🔴 **{nombre}:** " + " | ".join(deudas))
        else:
            st.write(f"🟢 **{nombre}:** Sin adeudos")

with tab3:
    st.subheader("Agregar Nuevo Conductor")
    c_apodo = st.text_input("Apodo / Clave")
    c_nombre = st.text_input("Nombre Completo")
    if st.button("Agregar Conductor"):
        if c_apodo and c_nombre:
            datos["personas"][c_apodo.lower()] = c_nombre
            if guardar_datos_nube():
                st.success(f"Conductor {c_nombre} agregado a la nube.")
                st.rerun()

    st.markdown("---")
    st.subheader("Agregar Nuevo Modelo de Carro")
    m_nombre = st.text_input("Nombre del Modelo")
    m_base = st.number_input("Base Semanal ($)", value=3500)
    m_extra = st.number_input("Costo Hora Extra ($)", value=40)
    if st.button("Agregar Modelo"):
        if m_nombre:
            datos["modelos"][m_nombre] = {"base": m_base, "extra": m_extra}
            if guardar_datos_nube():
                st.success(f"Modelo {m_nombre} agregado a la nube.")
                st.rerun()
