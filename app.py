import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Dashboard Distrito 207", layout="wide")

@st.cache_data
def load_data():
    # Cargamos el archivo generado con el cruce de datos
    df = pd.read_csv('cupcodigos_con_estado_2025.csv')
    
    # Asegurar que created_at sea fecha y manejar nulos
    df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
    df = df.dropna(subset=['created_at']) # Eliminamos filas sin fecha para la tendencia
    
    df['estado'] = df['estado'].fillna('Pendiente').replace('', 'Pendiente')
    
    # Extraer Mes y Número de Mes para ordenamiento cronológico
    df['mes_num'] = df['created_at'].dt.month
    df['mes'] = df['created_at'].dt.month_name()
    return df

df = load_data()

# --- BARRA LATERAL (ASIDE) ---
st.sidebar.header("Filtros de Búsqueda")

# MODIFICACIÓN: Filtro fijo inicial para Distrito 207
df_base = df[df['distrito'].astype(str) == '207'].copy()

# 1. Filtro de Ruta
rutas = sorted(df_base['ruta'].astype(str).unique())
ruta_sel = st.sidebar.multiselect("Seleccionar Ruta", rutas)

# 2. Filtro de Cadena
cadenas = sorted(df_base['cadena'].astype(str).unique())
cadena_sel = st.sidebar.multiselect("Seleccionar Cadena", cadenas)

# 3. Filtro de Descripción (Producto)
productos = sorted(df_base['descripcion'].astype(str).unique())
prod_sel = st.sidebar.multiselect("Seleccionar Producto", productos)

# 4. Filtro de Mes (Ordenado cronológicamente)
meses_ordenados = df_base.sort_values('mes_num')['mes'].unique()
mes_sel = st.sidebar.multiselect("Seleccionar Mes", meses_ordenados)

# 5. Filtro de Médico (usando columna id_clientes)
medicos = sorted(df_base['id_clientes'].astype(str).unique())
medico_sel = st.sidebar.multiselect("Seleccionar Médico", medicos)

# --- APLICACIÓN DE FILTROS DINÁMICOS ---
df_filtrado = df_base.copy()

if ruta_sel:
    df_filtrado = df_filtrado[df_filtrado['ruta'].astype(str).isin(ruta_sel)]
if cadena_sel:
    df_filtrado = df_filtrado[df_filtrado['cadena'].astype(str).isin(cadena_sel)]
if prod_sel:
    df_filtrado = df_filtrado[df_filtrado['descripcion'].astype(str).isin(prod_sel)]
if mes_sel:
    df_filtrado = df_filtrado[df_filtrado['mes'].isin(mes_sel)]
if medico_sel:
    df_filtrado = df_filtrado[df_filtrado['id_clientes'].astype(str).isin(medico_sel)]

# --- CUERPO PRINCIPAL ---
# MODIFICACIÓN: Título actualizado
st.title("Gestión de Cheques - Distrito 207")

# --- SECCIÓN DE KPIs CON BARRA DE EFECTIVIDAD ---
total = len(df_filtrado)
redimidos = len(df_filtrado[df_filtrado['estado'] == 'redimido'])
pendientes = total - redimidos
efectividad = (redimidos / total) if total > 0 else 0

c1, c2, c3, c4 = st.columns([1, 1, 1, 2])

with c1:
    st.metric("Generados 2025", f"{total:,}")
with c2:
    st.metric("Redimidos", f"{redimidos:,}")
with c3:
    st.metric("Pendientes", f"{pendientes:,}")
with c4:
    st.write(f"**Efectividad: {efectividad*100:.1f}%**")
    st.progress(efectividad)

st.divider()

# --- SECCIÓN: GRÁFICO LINEAL MENSUAL ---
st.markdown("### Tendencia Mensual")
df_linea = df_filtrado.groupby(['mes_num', 'mes']).size().reset_index(name='cantidad')
df_linea = df_linea.sort_values('mes_num')

if not df_linea.empty:
    fig_line = px.line(df_linea, x='mes', y='cantidad', 
                       markers=True,
                       text='cantidad',
                       labels={'mes': 'Mes', 'cantidad': 'Cheques'},
                       template="plotly_white",
                       height=220) 
    
    fig_line.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False
    )
    fig_line.update_traces(textposition="top center", line_color="#636EFA")
    st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})
else:
    st.info("No hay datos suficientes para mostrar la tendencia.")

# --- OTRAS VISUALIZACIONES ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Estado de Redención")
    fig_pie = px.pie(df_filtrado, names='estado', hole=0.4, 
                     color='estado',
                     color_discrete_map={'redimido':'#00CC96', 'Pendiente':'#F68B77'})
    
    fig_pie.update_layout(
        height=300, 
        margin=dict(l=10, r=10, t=30, b=20)
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    st.subheader("Médicos con más Generación")
    top_medicos = df_filtrado['id_clientes'].value_counts().head(5).reset_index()
    fig_med = px.bar(top_medicos, x='count', y='id_clientes', orientation='h',
                     labels={'count':'Cupones', 'id_clientes':'ID Médico'},
                     color_discrete_sequence=['#3498db'])
    fig_med.update_layout(
        yaxis={'categoryorder':'total ascending'},
        height=300,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_med, use_container_width=True)

# --- TABLA DE DATOS ---
st.subheader("Detalle de Registros Filtrados")

# Definimos las columnas que queremos mostrar
cols_to_show = ['id_clientes', 'descripcion', 'codigobarras', 'cadena', 'ruta', 'estado']

try:
    # MODIFICACIÓN: Corregido el nombre de la columna para el rename (codigobarras)
    df_tabla = df_filtrado[cols_to_show].rename(columns={
        'id_clientes': 'médico',
        'descripcion': 'producto',
        'codigobarras': 'código de barras'
    })
    st.dataframe(df_tabla, use_container_width=True, hide_index=True)
except KeyError as e:
    st.error(f"Error: No se encontró la columna {e}. Verifica los nombres de las columnas en el CSV.")

# Botón de exportación en el Aside
csv = df_filtrado.to_csv(index=False).encode('utf-8')
st.sidebar.download_button(
    label="📥 Descargar CSV Filtrado",
    data=csv,
    file_name='reporte_distrito_207.csv',
    mime='text/csv',
)
