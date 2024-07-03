import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_lottie import st_lottie
import requests
import folium
from streamlit_folium import st_folium

# Page configuration
st.set_page_config(
    page_title="Dashboard Flavio Cesar",
    page_icon="🛩️",
    layout="wide",
    initial_sidebar_state="expanded")

# Función para cargar una animación Lottie desde una URL
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Cargar la animación Lottie
lottie_url = "https://lottie.host/becb33b8-1bf2-4eca-bc4a-b6d68375c4d5/FJ1dgjVxNg.json"
lottie_json = load_lottieurl(lottie_url)
st_lottie(lottie_json, speed=1, width=1300, height=350, key="dashboard")

# Cargar datos
aeropuerto_detalle = pd.read_csv('aeropuertos_detalle.csv', delimiter=';')

# Cargar datos de vuelos
files = ['202405-informe-ministerio.csv', '202312-informe-ministerio.csv']
data_frames = []

for file in files:
    df = pd.read_csv(file, delimiter=';')
    data_frames.append(df)

# Concatenar los DataFrames
vuelos = pd.concat(data_frames, ignore_index=True)

# Transformar y limpiar datos
vuelos['Fecha UTC'] = pd.to_datetime(vuelos['Fecha UTC'], format='%d/%m/%Y')
vuelos['YearMonth'] = vuelos['Fecha UTC'].dt.to_period('M').astype(str)
vuelos['Quarter'] = vuelos['Fecha UTC'].dt.to_period('Q')

# Título del Dashboard
st.title('🛫 Dashboard de Análisis de Aeropuertos(🇦🇷) 🛬')
st.markdown('### Resumen de vuelos y rendimiento 📊')

# Logo en la barra lateral
st.sidebar.image("logo3.jpg", use_column_width=True)

# Filtros en la barra lateral con expanders
with st.sidebar:
    st.title('🕒 Filtros')
    with st.expander("📅 Filtro por Fechas"):
        start_date = st.date_input('Fecha de inicio', vuelos['Fecha UTC'].min())
        end_date = st.date_input('Fecha de fin', vuelos['Fecha UTC'].max())
    with st.expander("🌍 Filtro por Aeropuerto"):
        airport_filter = st.selectbox('Selecciona Aeropuerto', ['Todos'] + list(vuelos['Aeropuerto'].unique()))
    with st.expander("✈️ Filtro por Aerolínea"):
        airline_filter = st.selectbox('Selecciona Aerolínea', ['Todos'] + list(vuelos['Aerolinea Nombre'].unique()))
    with st.expander("🛫 Filtro por Tipo de Movimiento"):
        movement_filter = st.selectbox('Selecciona Movimiento', ['Todos'] + list(vuelos['Tipo de Movimiento'].unique()))
    with st.expander("🔍 Búsqueda por Coordenadas"):
        latitude = st.number_input("Latitud", value=0.0, format="%.6f")
        longitude = st.number_input("Longitud", value=0.0, format="%.6f")
        search_button = st.button("Buscar Coordenadas")

# Aplicar filtros
filtered_data = vuelos[
    (vuelos['Fecha UTC'] >= pd.to_datetime(start_date)) &
    (vuelos['Fecha UTC'] <= pd.to_datetime(end_date))
]

if airport_filter != 'Todos':
    filtered_data = filtered_data[filtered_data['Aeropuerto'] == airport_filter]
if airline_filter != 'Todos':
    filtered_data = filtered_data[filtered_data['Aerolinea Nombre'] == airline_filter]
if movement_filter != 'Todos':
    filtered_data = filtered_data[filtered_data['Tipo de Movimiento'] == movement_filter]

# KPIs principales
total_flights = filtered_data.shape[0]
total_passengers = filtered_data['PAX'].sum()
unique_airports = filtered_data['Aeropuerto'].nunique()
quarterly_flights = filtered_data.groupby('Quarter')['Aeropuerto'].count()

# Primera fila de KPIs
st.markdown("## 🔑 KPIs Principales")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric('Total de Vuelos', f'{total_flights}', delta="Mejora respecto al mes anterior", delta_color="inverse")

with col2:
    st.metric('Total de Pasajeros', f'{total_passengers:,}')

with col3:
    st.metric('Número de Aeropuertos', f'{unique_airports}')

with col4:
    st.metric('Vuelos Trimestrales', f'{quarterly_flights.sum()}')

# Segunda fila de gráficos
st.markdown("## 📈 Gráficos de Vuelos")
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader('📅 Vuelos Totales por Mes')
    monthly_flights = filtered_data.groupby('YearMonth')['Aeropuerto'].count().reset_index()
    fig = px.bar(monthly_flights, x='YearMonth', y='Aeropuerto', title="Vuelos Totales por Mes",
                 labels={'YearMonth':'Mes', 'Aeropuerto':'Vuelos Totales'}, color='Aeropuerto', color_continuous_scale='Blues')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader('🌍 Vuelos por Aeropuerto')
    airport_flights = filtered_data.groupby('Aeropuerto')['Aeropuerto'].count().reset_index(name='Vuelos')
    fig = px.pie(airport_flights, values='Vuelos', names='Aeropuerto', title="Vuelos por Aeropuerto", hole=.3,
                 color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(fig, use_container_width=True)

# Tercera fila de gráficos
col3, col4 = st.columns([2, 1])

with col3:
    st.subheader('✈️ Vuelos por Aerolínea')
    airline_flights = filtered_data.groupby('Aerolinea Nombre')['Aeropuerto'].count().reset_index(name='Vuelos')
    fig = px.bar(airline_flights, x='Aerolinea Nombre', y='Vuelos', title="Vuelos por Aerolínea",
                 labels={'Aerolinea Nombre':'Aerolínea', 'Vuelos':'Cantidad de Vuelos'}, color='Vuelos', color_continuous_scale='Viridis')
    fig.update_layout(xaxis={'categoryorder':'total descending'})
    st.plotly_chart(fig, use_container_width=True)

with col4:
    st.subheader('🛫 Vuelos por Tipo de Movimiento')
    movement_flights = filtered_data.groupby('Tipo de Movimiento')['Aeropuerto'].count().reset_index(name='Vuelos')
    fig = px.pie(movement_flights, values='Vuelos', names='Tipo de Movimiento', title="Vuelos por Tipo de Movimiento", hole=.3,
                 color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(fig, use_container_width=True)

# Detalles de aeropuertos
st.markdown("## 📋 Detalles de Aeropuertos")
st.dataframe(aeropuerto_detalle)

# Crear un mapa centrado en un punto central
if search_button and latitude != 0.0 and longitude != 0.0:
    map_center = [latitude, longitude]
else:
    map_center = [-38.4161, -63.6167]  # Coordenadas de Buenos Aires, Argentina
mymap = folium.Map(location=map_center, zoom_start=5)

# Añadir marcadores al mapa
for _, row in aeropuerto_detalle.iterrows():
    folium.Marker(
        location=[row['latitud'], row['longitud']],
        popup=(
            f"<b>{row['denominacion']}</b><br>"
            f"{row['local']}<br>"
            f"{row['provincia']}<br>"
            f"{row['latitud']}, {row['longitud']}"
        ),
        icon=folium.Icon(icon='plane', prefix='fa')
    ).add_to(mymap)

# Añadir un marcador en la ubicación buscada
if search_button and latitude != 0.0 and longitude != 0.0:
    folium.Marker(
        location=[latitude, longitude],
        popup=f"<b>Ubicación buscada:</b><br>{latitude}, {longitude}",
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(mymap)

# Mostrar el mapa en Streamlit
st.markdown('<div style="display: flex; justify-content: center; align-items: center;">', unsafe_allow_html=True)
st_folium(mymap, width=900, height=700)
st.markdown('</div>', unsafe_allow_html=True)
