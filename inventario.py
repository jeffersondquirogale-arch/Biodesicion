import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import hashlib
import plotly.graph_objects as go
import plotly.express as px

# Configuración de Streamlit
st.set_page_config(page_title="BIODESICION - Inventory", layout="wide", initial_sidebar_state="expanded")

INVENTARIO_FILE = "datos/inventario.csv"
CLIENTES_FILE = "datos/clientes.csv"
VENTAS_FILE = "datos/ventas.csv"
USUARIOS_FILE = "datos/usuarios.csv"
CREDITOS_FILE = "datos/creditos.csv"

os.makedirs("datos", exist_ok=True)

# ===== FUNCIONES BÁSICAS =====
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def crear_usuario_default():
    if not os.path.exists(USUARIOS_FILE):
        usuarios = pd.DataFrame({
            "usuario": ["CamilaM"],
            "contraseña": [hash_password("1234")]
        })
        usuarios.to_csv(USUARIOS_FILE, index=False)

def verificar_usuario(usuario, contraseña):
    if not usuario or not contraseña:
        return False
    crear_usuario_default()
    try:
        usuarios = pd.read_csv(USUARIOS_FILE)
        user_data = usuarios[usuarios["usuario"] == usuario]
        if user_data.empty:
            return False
        return user_data["contraseña"].values[0] == hash_password(contraseña)
    except:
        return False

def cargar_inventario():
    try:
        if os.path.exists(INVENTARIO_FILE):
            inventario = pd.read_csv(INVENTARIO_FILE)
            if "Valor_Unitario" not in inventario.columns:
                inventario["Valor_Unitario"] = 0.0
            if "Cantidad_Total" not in inventario.columns:
                inventario["Cantidad_Total"] = inventario["Cantidad"]
        else:
            inventario = pd.DataFrame({"Caja": [], "Cantidad": [], "Valor_Unitario": [], "Cantidad_Total": []})
            inventario.to_csv(INVENTARIO_FILE, index=False)
        return inventario
    except:
        return pd.DataFrame({"Caja": [], "Cantidad": [], "Valor_Unitario": [], "Cantidad_Total": []})

def cargar_clientes():
    try:
        if os.path.exists(CLIENTES_FILE):
            clientes = pd.read_csv(CLIENTES_FILE, dtype={"Telefono": str})
        else:
            clientes = pd.DataFrame({"Nombre": [], "Cedula": [], "Telefono": []})
            clientes.to_csv(CLIENTES_FILE, index=False)
        return clientes
    except:
        return pd.DataFrame({"Nombre": [], "Cedula": [], "Telefono": []})

def cargar_ventas():
    try:
        if os.path.exists(VENTAS_FILE):
            ventas = pd.read_csv(VENTAS_FILE)
            ventas["Fecha"] = pd.to_datetime(ventas["Fecha"])
            if "Valor_Unitario" not in ventas.columns:
                ventas["Valor_Unitario"] = 0.0
            if "Es_Credito" not in ventas.columns:
                ventas["Es_Credito"] = False
        else:
            ventas = pd.DataFrame(columns=["Fecha", "Cliente", "Caja", "Cantidad", "Valor_Unitario", "Monto", "Es_Credito"])
            ventas.to_csv(VENTAS_FILE, index=False)
        return ventas
    except:
        return pd.DataFrame(columns=["Fecha", "Cliente", "Caja", "Cantidad", "Valor_Unitario", "Monto", "Es_Credito"])

def cargar_creditos():
    try:
        if os.path.exists(CREDITOS_FILE):
            creditos = pd.read_csv(CREDITOS_FILE)
            creditos["Fecha_Credito"] = pd.to_datetime(creditos["Fecha_Credito"])
            if "Fecha_Pago" in creditos.columns:
                creditos["Fecha_Pago"] = pd.to_datetime(creditos["Fecha_Pago"], errors='coerce')
        else:
            creditos = pd.DataFrame(columns=["Cliente", "Monto", "Fecha_Credito", "Pagado", "Fecha_Pago"])
            creditos.to_csv(CREDITOS_FILE, index=False)
        return creditos
    except:
        return pd.DataFrame(columns=["Cliente", "Monto", "Fecha_Credito", "Pagado", "Fecha_Pago"])

def guardar_datos(inventario, clientes, ventas, creditos):
    try:
        inventario.to_csv(INVENTARIO_FILE, index=False)
        clientes.to_csv(CLIENTES_FILE, index=False)
        ventas.to_csv(VENTAS_FILE, index=False)
        creditos.to_csv(CREDITOS_FILE, index=False)
        return True
    except:
        return False

def cargar_datos():
    return cargar_inventario(), cargar_clientes(), cargar_ventas(), cargar_creditos()

def verificar_stock_bajo(inventario):
    """Retorna un DataFrame con cajas de stock bajo"""
    if inventario.empty:
        return pd.DataFrame()
    cajas_alerta = inventario[inventario['Cantidad'] <= 2]
    return cajas_alerta

def calcular_ganancia_neta(ventas):
    """
    Ganancia Neta = (Monto Total - 7000) por cada venta
    """
    ganancia_neta = 0
    if not ventas.empty:
        for idx, row in ventas.iterrows():
            try:
                monto = float(row.get('Monto', 0))
                ganancia_por_venta = max(monto - 7000, 0)
                ganancia_neta += ganancia_por_venta
            except:
                continue
    return ganancia_neta

# ===== SESIÓN =====
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'usuario' not in st.session_state:
    st.session_state.usuario = None

# ===== LOGIN =====
if not st.session_state.authenticated:
    st.title("🔐 BIODESICION - INVENTORY")
    st.subheader("Sistema de Gestión de Inventario")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        usuario = st.text_input("👤 Usuario", placeholder="Ingresa tu usuario")
        contraseña = st.text_input("🔑 Contraseña", type="password", placeholder="Ingresa tu contraseña")
        
        col_login, col_exit = st.columns(2)
        
        with col_login:
            if st.button("✅ Iniciar Sesión", use_container_width=True):
                if verificar_usuario(usuario, contraseña):
                    st.session_state.authenticated = True
                    st.session_state.usuario = usuario
                    st.success("✅ ¡Bienvenido!")
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")
        
        with col_exit:
            if st.button("❌ Salir", use_container_width=True):
                st.info("Hasta luego")
        st.markdown("---")

# ===== APLICACIÓN PRINCIPAL =====
else:
    st.sidebar.title(f"👤 {st.session_state.usuario}")
    st.sidebar.markdown(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.usuario = None
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Cargar datos
    inventario, clientes, ventas, creditos = cargar_datos()
    
    # Menú de navegación
    menu = st.sidebar.radio(
        "📋 MENÚ",
        ["📊 Dashboard", "👥 Clientes", "📦 Productos", "🛒 Ventas", "💳 Créditos", "📈 Reportes"]
    )
    
    # ===== DASHBOARD =====
    if menu == "📊 Dashboard":
        st.title("📊 PANEL DE CONTROL")
        
        # Calcular estadísticas
        venta_total = ventas['Monto'].sum() if not ventas.empty else 0
        creditos_pendientes = creditos[creditos['Pagado'] == False]['Monto'].sum() if not creditos.empty else 0
        valor_inventario = (inventario['Cantidad'] * inventario['Valor_Unitario']).sum() if not inventario.empty else 0
        ganancia_neta = calcular_ganancia_neta(ventas)
        
        # Mostrar métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👥 CLIENTES", len(clientes))
        with col2:
            st.metric("📦 INVENTARIO", f"${valor_inventario:,.0f}")
        with col3:
            st.metric("💲 GANANCIA NETA", f"${ganancia_neta:,.0f}")
        
        col4, col5 = st.columns(2)
        with col4:
            st.metric("💳 VENTA TOTAL", f"${venta_total:,.0f}")
        with col5:
            st.metric("💳 CRÉDITO PENDIENTE", f"${creditos_pendientes:,.0f}")
        
        st.markdown("---")
        
        # ===== GRÁFICA DE COMPORTAMIENTO DEL INVENTARIO =====
        st.subheader("📊 COMPORTAMIENTO DEL INVENTARIO")
        
        # Filtro de vista
        opcion_vista = st.radio("Ver por:", ["Mes Completo", "Filtrar por Mes"], horizontal=True)
        
        if not ventas.empty:
            ventas_copy = ventas.copy()
            ventas_copy['Fecha'] = pd.to_datetime(ventas_copy['Fecha'])
            ventas_copy['Mes'] = ventas_copy['Fecha'].dt.to_period('M')
            ventas_copy['Día'] = ventas_copy['Fecha'].dt.date
            
            if opcion_vista == "Mes Completo":
                # Mostrar por mes
                ventas_por_mes = ventas_copy.groupby('Mes')['Cantidad'].sum().reset_index()
                ventas_por_mes['Mes'] = ventas_por_mes['Mes'].astype(str)
                
                fig_mes = go.Figure()
                fig_mes.add_trace(go.Bar(
                    x=ventas_por_mes['Mes'],
                    y=ventas_por_mes['Cantidad'],
                    name='Cantidad de Productos',
                    marker_color='#16a085',
                    text=ventas_por_mes['Cantidad'],
                    textposition='outside'
                ))
                fig_mes.update_layout(
                    title="📊 INVENTARIO POR MES",
                    xaxis_title="Mes",
                    yaxis_title="Cantidad de Productos",
                    hovermode='x unified',
                    height=400
                )
                st.plotly_chart(fig_mes, use_container_width=True)
            
            else:
                # Filtrar por mes específico
                meses_disponibles = sorted(ventas_copy['Mes'].unique(), reverse=True)
                if len(meses_disponibles) > 0:
                    mes_seleccionado = st.selectbox(
                        "Selecciona un mes:",
                        meses_disponibles,
                        format_func=lambda x: str(x)
                    )
                    
                    ventas_mes = ventas_copy[ventas_copy['Mes'] == mes_seleccionado]
                    ventas_por_dia = ventas_mes.groupby('Día')['Cantidad'].sum().reset_index()
                    
                    fig_dia = go.Figure()
                    fig_dia.add_trace(go.Bar(
                        x=ventas_por_dia['Día'],
                        y=ventas_por_dia['Cantidad'],
                        name='Cantidad de Productos',
                        marker_color='#e74c3c',
                        text=ventas_por_dia['Cantidad'],
                        textposition='outside'
                    ))
                    fig_dia.add_trace(go.Scatter(
                        x=ventas_por_dia['Día'],
                        y=ventas_por_dia['Cantidad'],
                        name='Tendencia',
                        mode='lines+markers',
                        line=dict(color='#3498db', width=3),
                        marker=dict(size=8)
                    ))
                    fig_dia.update_layout(
                        title=f"📊 COMPORTAMIENTO DEL INVENTARIO - {mes_seleccionado}",
                        xaxis_title="Día",
                        yaxis_title="Cantidad de Productos",
                        hovermode='x unified',
                        height=400
                    )
                    st.plotly_chart(fig_dia, use_container_width=True)
                else:
                    st.info("Sin datos disponibles")
        else:
            st.info("Sin datos de inventario")
        
        st.markdown("---")
        
        # ===== GRÁFICA DE COMPORTAMIENTO DE VENTAS =====
        st.subheader("📈 COMPORTAMIENTO DE VENTAS (Últimos 30 Días)")
        
        if not ventas.empty:
            ventas_copy = ventas.copy()
            ventas_copy['Fecha'] = pd.to_datetime(ventas_copy['Fecha']).dt.date
            fecha_limite = datetime.now().date() - timedelta(days=30)
            ventas_copy = ventas_copy[ventas_copy['Fecha'] >= fecha_limite]
            
            if not ventas_copy.empty:
                ventas_agrupadas = ventas_copy.groupby('Fecha')['Monto'].sum().sort_index()
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=ventas_agrupadas.index,
                    y=ventas_agrupadas.values,
                    name='Monto de Ventas',
                    marker_color='#16a085',
                    text=[f'${v:,.0f}' for v in ventas_agrupadas.values],
                    textposition='outside'
                ))
                fig.add_trace(go.Scatter(
                    x=ventas_agrupadas.index,
                    y=ventas_agrupadas.values,
                    name='Tendencia',
                    mode='lines+markers',
                    line=dict(color='#e74c3c', width=3),
                    marker=dict(size=8)
                ))
                fig.update_layout(
                    title="📈 COMPORTAMIENTO DE VENTAS - ÚLTIMOS 30 DÍAS",
                    xaxis_title="Fecha",
                    yaxis_title="Monto ($)",
                    hovermode='x unified',
                    height=400,
                    showlegend=True
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sin datos en últimos 30 días")
        else:
            st.info("Sin datos de ventas")
        
        st.markdown("---")
        
        # Tabla de últimas ventas
        st.subheader("Últimas Ventas")
        if not ventas.empty:
            ventas_display = ventas.tail(15)[['Fecha', 'Cliente', 'Caja', 'Cantidad', 'Monto']].copy()
            ventas_display['Fecha'] = ventas_display['Fecha'].dt.strftime("%d/%m/%Y")
            ventas_display['Monto'] = ventas_display['Monto'].apply(lambda x: f"${x:,.0f}")
            st.dataframe(ventas_display, use_container_width=True, hide_index=True)
        else:
            st.info("Sin ventas registradas")
    
    # ===== CLIENTES =====
    elif menu == "👥 Clientes":
        st.title("👥 GESTIÓN DE CLIENTES")
        
        tab1, tab2 = st.tabs(["Ver Clientes", "Agregar Cliente"])
        
        with tab1:
            if not clientes.empty:
                st.dataframe(clientes, use_container_width=True, hide_index=True)
                
                # Eliminar cliente
                st.subheader("Eliminar Cliente")
                if not clientes.empty:
                    cliente_a_eliminar = st.selectbox("Selecciona cliente a eliminar", clientes['Nombre'].tolist())
                    if st.button("🗑️ Eliminar", key="eliminar_cliente"):
                        clientes = clientes[clientes['Nombre'] != cliente_a_eliminar].reset_index(drop=True)
                        guardar_datos(inventario, clientes, ventas, creditos)
                        st.success("✅ Cliente eliminado")
                        st.rerun()
            else:
                st.info("Sin clientes registrados")
        
        with tab2:
            st.subheader("Agregar Nuevo Cliente")
            nombre = st.text_input("Nombre")
            cedula = st.text_input("Cédula")
            telefono = st.text_input("Teléfono")
            
            if st.button("💾 Guardar Cliente", use_container_width=True):
                if nombre and cedula:
                    nuevo = pd.DataFrame({
                        "Nombre": [nombre],
                        "Cedula": [cedula],
                        "Telefono": [telefono]
                    })
                    clientes = pd.concat([clientes, nuevo], ignore_index=True)
                    guardar_datos(inventario, clientes, ventas, creditos)
                    st.success("✅ Cliente agregado")
                    st.rerun()
                else:
                    st.error("Completa nombre y cédula")
    
    # ===== PRODUCTOS =====
    elif menu == "📦 Productos":
        st.title("📦 GESTIÓN DE PRODUCTOS (CAJAS)")
        
        tab1, tab2, tab3 = st.tabs(["Ver Cajas", "Agregar Nueva Caja", "➕ AGREGAR UNIDADES"])
        
        with tab1:
            if not inventario.empty:
                st.subheader("📊 Inventario de Cajas")
                
                # Crear tabla con formato especial
                for idx, row in inventario.iterrows():
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1.5, 1.5])
                    
                    with col1:
                        st.write(f"**📦 Caja:** {row['Caja']}")
                    
                    with col2:
                        st.write(f"**💰 Precio:** ${row['Valor_Unitario']:,.0f}")
                    
                    with col3:
                        cantidad = int(row['Cantidad'])
                        if cantidad <= 2:
                            st.warning(f"**⚠️ Stock:** {cantidad} unidades")
                        else:
                            st.write(f"**📦 Stock:** {cantidad} unidades")
                    
                    with col4:
                        st.write(f"**📈 Total Registrado:** {int(row['Cantidad_Total'])} unidades")
                    
                    with col5:
                        if st.button("🗑️ Eliminar", key=f"eliminar_caja_{idx}"):
                            inventario = inventario.drop(idx).reset_index(drop=True)
                            guardar_datos(inventario, clientes, ventas, creditos)
                            st.success("✅ Caja eliminada")
                            st.rerun()
                    
                    st.divider()
            else:
                st.info("Sin cajas registradas")
        
        with tab2:
            st.subheader("Agregar Nueva Caja")
            caja = st.text_input("Nombre de la Caja")
            cantidad = st.number_input("Cantidad Inicial", min_value=1, value=1)
            valor_unitario = st.number_input("Valor Unitario ($)", min_value=0, value=0, step=1000)
            
            if st.button("💾 Guardar Caja", use_container_width=True):
                if caja and valor_unitario > 0:
                    nuevo = pd.DataFrame({
                        "Caja": [caja],
                        "Cantidad": [cantidad],
                        "Valor_Unitario": [valor_unitario],
                        "Cantidad_Total": [cantidad]
                    })
                    inventario = pd.concat([inventario, nuevo], ignore_index=True)
                    guardar_datos(inventario, clientes, ventas, creditos)
                    st.success(f"✅ Caja '{caja}' agregada con {cantidad} unidades")
                    st.rerun()
                else:
                    st.error("Completa todos los campos correctamente")
        
        with tab3:
            st.subheader("➕ AGREGAR UNIDADES A UNA CAJA")
            
            if not inventario.empty:
                # Crear opciones de caja
                opciones = []
                for idx, row in inventario.iterrows():
                    text = f"{row['Caja']} - Stock Actual: {int(row['Cantidad'])} unidades"
                    opciones.append((text, idx))
                
                caja_seleccionada_text = st.selectbox(
                    "🔍 Selecciona una Caja:",
                    [opt[0] for opt in opciones],
                    key="agregar_unidades_combo"
                )
                
                # Obtener índice
                indice = next(opt[1] for opt in opciones if opt[0] == caja_seleccionada_text)
                
                cantidad_actual = int(inventario.iloc[indice]['Cantidad'])
                cantidad_total_registrada = int(inventario.iloc[indice]['Cantidad_Total'])
                precio_actual = int(inventario.iloc[indice]['Valor_Unitario'])
                
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    unidades_agregar = st.number_input("📦 ¿Cuántas unidades deseas agregar?", min_value=1, value=10)
                
                with col2:
                    nuevo_precio = st.number_input("💰 Nuevo Precio Unitario ($)", min_value=0, value=precio_actual, step=1000)
                
                nueva_cantidad = cantidad_actual + unidades_agregar
                nueva_cantidad_total = cantidad_total_registrada + unidades_agregar
                
                # Mostrar información
                st.info(f"""
                🔍 **INFORMACIÓN DE LA CAJA: {inventario.iloc[indice]['Caja']}**
                
                **Stock Actual:** {cantidad_actual} unidades  
                **Unidades a Agregar:** {unidades_agregar} unidades  
                **Stock Final:** {nueva_cantidad} unidades  
                
                **Total Registrado Anteriormente:** {cantidad_total_registrada} unidades  
                **Total Registrado Final:** {nueva_cantidad_total} unidades  
                
                **Precio Anterior:** ${precio_actual:,.0f}  
                **Precio Nuevo:** ${nuevo_precio:,.0f}
                """)
                
                if st.button("💾 Guardar Cambios", use_container_width=True, key="guardar_unidades"):
                    inventario.at[indice, "Cantidad"] = nueva_cantidad
                    inventario.at[indice, "Cantidad_Total"] = nueva_cantidad_total
                    inventario.at[indice, "Valor_Unitario"] = nuevo_precio
                    guardar_datos(inventario, clientes, ventas, creditos)
                    caja_nombre = inventario.iloc[indice]["Caja"]
                    st.success(f"""
                    ✅ Caja '{caja_nombre}' actualizada:
                    - Se agregaron {unidades_agregar} unidades
                    - Total registrado: {nueva_cantidad_total} unidades
                    - Nuevo precio: ${nuevo_precio:,.0f}
                    """)
                    st.rerun()
            else:
                st.error("❌ No hay cajas registradas")
    
    # ===== VENTAS =====
    elif menu == "🛒 Ventas":
        st.title("🛒 REGISTRAR VENTA")
        
        tab1, tab2 = st.tabs(["Nueva Venta", "Historial"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                fecha = st.date_input("Fecha", value=datetime.now().date())
            
            with col2:
                cliente = st.selectbox("Cliente", clientes['Nombre'].tolist() if not clientes.empty else ["Sin clientes"])
            
            col3, col4 = st.columns(2)
            
            with col3:
                caja = st.selectbox("Caja", inventario['Caja'].tolist() if not inventario.empty else ["Sin cajas"])
            
            with col4:
                if caja != "Sin cajas" and not inventario.empty:
                    caja_info = inventario[inventario['Caja'] == caja].iloc[0]
                    disponibles = int(caja_info['Cantidad'])
                    st.metric("Disponibles", disponibles)
            
            col5, col6 = st.columns(2)
            
            with col5:
                cantidad = st.number_input("Cantidad", min_value=1, value=1)
            
            with col6:
                if caja != "Sin cajas" and not inventario.empty:
                    valor_unitario = int(inventario[inventario['Caja'] == caja].iloc[0]['Valor_Unitario'])
                    st.metric("Valor Unitario", f"${valor_unitario:,.0f}")
                else:
                    valor_unitario = 0
            
            monto = cantidad * valor_unitario
            st.metric("Monto Total", f"${monto:,.0f}")
            
            es_credito = st.checkbox("✅ Venta a Crédito")
            
            if st.button("💾 Guardar Venta", use_container_width=True):
                if cliente != "Sin clientes" and caja != "Sin cajas":
                    # Validar stock
                    caja_idx = None
                    nueva_cantidad = 0
                    for i, row in inventario.iterrows():
                        if row["Caja"] == caja:
                            caja_idx = i
                            nueva_cantidad = int(row["Cantidad"]) - cantidad
                            if nueva_cantidad < 0:
                                st.error("❌ No hay suficiente stock")
                                break
                            # Actualizar cantidad (SE DESCUENTA AUTOMÁTICAMENTE)
                            inventario.at[i, "Cantidad"] = nueva_cantidad
                            break
                    
                    if caja_idx is not None and nueva_cantidad >= 0:
                        # Guardar venta
                        nueva_venta = pd.DataFrame({
                            "Fecha": [pd.Timestamp(fecha)],
                            "Cliente": [cliente],
                            "Caja": [caja],
                            "Cantidad": [cantidad],
                            "Valor_Unitario": [valor_unitario],
                            "Monto": [monto],
                            "Es_Credito": [es_credito]
                        })
                        ventas = pd.concat([ventas, nueva_venta], ignore_index=True)
                        
                        # Guardar crédito si aplica
                        if es_credito:
                            nuevo_credito = pd.DataFrame({
                                "Cliente": [cliente],
                                "Monto": [monto],
                                "Fecha_Credito": [pd.Timestamp(fecha)],
                                "Pagado": [False],
                                "Fecha_Pago": [pd.NaT]
                            })
                            creditos = pd.concat([creditos, nuevo_credito], ignore_index=True)
                        
                        guardar_datos(inventario, clientes, ventas, creditos)
                        st.success("✅ Venta guardada y stock actualizado automáticamente")
                        st.rerun()
                else:
                    st.error("❌ Completa todos los campos")
        
        with tab2:
            st.subheader("Historial de Ventas")

            if 'mostrar_pwd_ventas' not in st.session_state:
                st.session_state.mostrar_pwd_ventas = False

            if not ventas.empty:
                ventas_display = ventas[['Fecha', 'Cliente', 'Caja', 'Cantidad', 'Monto', 'Es_Credito']].copy()
                ventas_display['Fecha'] = ventas_display['Fecha'].dt.strftime("%d/%m/%Y")
                ventas_display.insert(0, 'Seleccionar', False)

                edited_df = st.data_editor(
                    ventas_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Seleccionar": st.column_config.CheckboxColumn("✓", default=False, width="small"),
                        "Monto": st.column_config.NumberColumn("Monto ($)", format="$%d"),
                    },
                    key="tabla_ventas_historial"
                )

                indices_seleccionados = edited_df[edited_df['Seleccionar']].index.tolist()
                num_seleccionados = len(indices_seleccionados)

                if num_seleccionados > 0:
                    st.info(f"📋 {num_seleccionados} venta(s) seleccionada(s)")
                    if st.button(
                        f"🗑️ Eliminar {num_seleccionados} Venta(s) Seleccionada(s)",
                        type="primary",
                        key="btn_eliminar_ventas"
                    ):
                        st.session_state.mostrar_pwd_ventas = True

                if st.session_state.get('mostrar_pwd_ventas', False):
                    st.warning("⚠️ Esta acción eliminará las ventas seleccionadas y restaurará el stock.")
                    pwd = st.text_input("🔑 Contraseña de confirmación:", type="password", key="pwd_confirm_ventas")

                    col_ok, col_cancel = st.columns(2)
                    with col_ok:
                        if st.button("✅ Confirmar Eliminación", key="confirmar_eliminar_ventas"):
                            if pwd == "112915":
                                ventas_a_eliminar = ventas.iloc[indices_seleccionados]

                                # Restaurar stock
                                for _, venta in ventas_a_eliminar.iterrows():
                                    idx_caja = inventario[inventario['Caja'] == venta['Caja']].index
                                    if not idx_caja.empty:
                                        inventario.at[idx_caja[0], 'Cantidad'] += int(venta['Cantidad'])

                                # Eliminar créditos asociados
                                for _, venta in ventas_a_eliminar.iterrows():
                                    if venta.get('Es_Credito', False):
                                        fecha_venta = venta['Fecha'].date()
                                        mask = (
                                            (creditos['Cliente'] == venta['Cliente']) &
                                            (creditos['Monto'] == venta['Monto']) &
                                            (creditos['Fecha_Credito'].dt.date == fecha_venta)
                                        )
                                        creditos = creditos[~mask].reset_index(drop=True)

                                # Eliminar ventas
                                ventas = ventas.drop(indices_seleccionados).reset_index(drop=True)
                                guardar_datos(inventario, clientes, ventas, creditos)
                                st.session_state.mostrar_pwd_ventas = False
                                st.success(f"✅ {num_seleccionados} venta(s) eliminada(s) y stock restaurado.")
                                st.rerun()
                            else:
                                st.error("❌ Contraseña incorrecta")
                    with col_cancel:
                        if st.button("❌ Cancelar", key="cancelar_eliminar_ventas"):
                            st.session_state.mostrar_pwd_ventas = False
                            st.rerun()
            else:
                st.info("Sin ventas")
    
    # ===== CRÉDITOS =====
    elif menu == "💳 Créditos":
        st.title("💳 GESTIÓN DE CRÉDITOS")
        
        if not creditos.empty:
            creditos_pendientes = creditos[creditos['Pagado'] == False]
            total_credito = creditos_pendientes['Monto'].sum()
            cantidad_clientes = creditos_pendientes['Cliente'].nunique()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💳 TOTAL PENDIENTE", f"${total_credito:,.0f}")
            with col2:
                st.metric("👥 CLIENTES CON DEUDA", cantidad_clientes)
            with col3:
                st.metric("📋 REGISTROS PENDIENTES", len(creditos_pendientes))
        
        st.markdown("---")
        st.subheader("📋 PERSONAS CON CRÉDITO PENDIENTE")
        
        if not creditos.empty:
            for idx, row in creditos.iterrows():
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1.2, 1.3])
                    
                    with col1:
                        st.write(f"**👤 {row['Cliente']}**")
                    
                    with col2:
                        st.write(f"**💰 ${row.get('Monto', 0):,.0f}**")
                    
                    with col3:
                        fecha_credito = row['Fecha_Credito'].strftime("%d/%m/%Y") if pd.notna(row['Fecha_Credito']) else ""
                        st.write(f"📅 {fecha_credito}")
                    
                    with col4:
                        if row['Pagado']:
                            st.success("✅ PAGADO")
                        else:
                            st.error("❌ PENDIENTE")
                    
                    with col5:
                        if not row['Pagado']:
                            if st.button("💰 Pagar", key=f"pagar_{idx}", use_container_width=True):
                                creditos.at[idx, 'Pagado'] = True
                                creditos.at[idx, 'Fecha_Pago'] = pd.Timestamp(datetime.now())
                                guardar_datos(inventario, clientes, ventas, creditos)
                                st.success(f"✅ Pago registrado: {row['Cliente']} pagó ${row['Monto']:,.0f}")
                                st.rerun()
                    
                    st.divider()
        else:
            st.info("✅ Sin créditos pendientes - ¡Excelente!")
    
    # ===== REPORTES =====
    elif menu == "📈 Reportes":
        st.title("📈 REPORTES Y ANÁLISIS")
        
        venta_total = ventas['Monto'].sum() if not ventas.empty else 0
        creditos_pendientes = creditos[creditos['Pagado'] == False]['Monto'].sum() if not creditos.empty else 0
        valor_inventario = (inventario['Cantidad'] * inventario['Valor_Unitario']).sum() if not inventario.empty else 0
        ganancia_neta = calcular_ganancia_neta(ventas)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💵 Valor Inventario", f"${valor_inventario:,.0f}")
        with col2:
            st.metric("💳 Venta Total", f"${venta_total:,.0f}")
        with col3:
            st.metric("💳 Crédito Pendiente", f"${creditos_pendientes:,.0f}")
        with col4:
            st.metric("💲 Ganancia Neta", f"${ganancia_neta:,.0f}")
        
        st.markdown("---")
        
        # Ventas por cliente
        st.subheader("📊 Ventas por Cliente")
        if not ventas.empty:
            ventas_por_cliente = ventas.groupby('Cliente').agg({
                'Monto': 'sum',
                'Cantidad': 'sum',
                'Es_Credito': 'sum'
            }).reset_index()
            ventas_por_cliente.columns = ['Cliente', 'Total Vendido', 'Cantidad', 'Crédito']
            ventas_por_cliente['Total Vendido'] = ventas_por_cliente['Total Vendido'].apply(lambda x: f"${x:,.0f}")
            
            st.dataframe(ventas_por_cliente, use_container_width=True, hide_index=True)
            
            # Gráfico de ventas por cliente
            ventas_grafico = ventas.groupby('Cliente')['Monto'].sum().reset_index()
            fig = px.bar(ventas_grafico, x='Cliente', y='Monto', title='Ventas por Cliente',
                        labels={'Monto': 'Monto ($)', 'Cliente': 'Cliente'},
                        color='Monto', color_continuous_scale='Viridis')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin ventas")
        
        st.markdown("---")
        
        # Descargar reportes
        st.subheader("📥 Descargar Reportes")
        
        if st.button("📥 Descargar Excel", use_container_width=True):
            try:
                archivo = f"Reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                with pd.ExcelWriter(archivo, engine="openpyxl") as writer:
                    if not ventas.empty:
                        ventas.to_excel(writer, index=False, sheet_name="Ventas")
                    if not inventario.empty:
                        inventario.to_excel(writer, index=False, sheet_name="Inventario")
                    if not clientes.empty:
                        clientes.to_excel(writer, index=False, sheet_name="Clientes")
                    if not creditos.empty:
                        creditos.to_excel(writer, index=False, sheet_name="Créditos")
                st.success(f"✅ Reporte guardado: {archivo}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")