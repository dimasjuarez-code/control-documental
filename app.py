from pathlib import Path
import streamlit as st
from cloud_store import CloudStore
from cloud_highlight import highlight
from documental.search import Fragment
from documental.browse import filter_documents

st.set_page_config(page_title='Buscador documental', page_icon=':material/search:', layout='wide')
st.badge('Biblioteca pública', icon=':material/public:', color='violet')
st.title('Tu centro documental')
st.caption('Consulta documentos, encuentra códigos y descarga sus archivos originales.')
try:
    store = CloudStore(st.secrets['SUPABASE_URL'], st.secrets['SUPABASE_PUBLISHABLE_KEY'])
except Exception:
    st.info('Falta configurar la conexión con Supabase en los secretos del servidor.')
    st.stop()


@st.cache_data(ttl=60, max_entries=4)
def catalog(url, key):
    return CloudStore(url, key).rows()


@st.cache_data(ttl=300, max_entries=12)
def asset(url, key, path):
    return CloudStore(url, key).read(path)


@st.cache_data(max_entries=12)
def marked(data, query):
    return highlight(data, query)


try:
    rows = catalog(store.url, st.secrets['SUPABASE_PUBLISHABLE_KEY'])
except Exception:
    st.error('No se pudo leer la biblioteca. Revisa la configuración del servidor y los permisos de Supabase.')
    st.stop()
documents = {row['id']: {'name': row['name'], 'fragments': [Fragment(row['id'], row['name'], item['location'], item['text']) for item in row['fragments']]} for row in rows}
row_by_id = {row['id']: row for row in rows}
search, button = st.columns([5, 1], vertical_alignment='bottom')
query = search.text_input('Buscar documentos', key='query', live=True, placeholder='Ejemplo: MF100A o filtros cartucho')
button.button('Buscar', type='primary', icon=':material/search:', width='stretch')
first, second = st.columns(2)
folder = first.selectbox('Carpeta', ['Todas'] + sorted({Path(doc['name']).parent.as_posix() for doc in documents.values()}))
file_format = second.selectbox('Formato', ['Todos'] + sorted({Path(doc['name']).suffix.lstrip('.').upper() for doc in documents.values()}))
matches = filter_documents(documents, query or '', folder, file_format)
st.badge(f'{len(matches)} coincidencias · {len(documents)} documentos', color='blue')
signature = (query, folder, file_format)
if st.session_state.get('last_search') != signature:
    st.session_state.last_search = signature
    st.session_state.selected = None
if not matches:
    st.info('No hay coincidencias. Prueba con otras palabras o cambia los filtros.')
else:
    with st.container(height=360, border=True):
        for identity, document, _ in matches:
            if st.button(Path(document['name']).name, key=f'open_{identity}', icon=':material/description:', width='stretch'):
                st.session_state.selected = identity
            st.caption(document['name'])
selected = st.session_state.get('selected')
if selected in {match[0] for match in matches}:
    row = row_by_id[selected]
    st.subheader(Path(row['name']).name)
    st.link_button('Descargar documento original', store.asset_url(row['original_path']) + '?download=' + __import__('urllib.parse', fromlist=['quote']).quote(Path(row['name']).name), type='primary', icon=':material/download:')
    try:
        data = asset(store.url, st.secrets['SUPABASE_PUBLISHABLE_KEY'], row['preview_path'])
        if query:
            data, pages = marked(data, query)
            st.caption('Páginas con coincidencias: ' + ', '.join(map(str, pages)) if pages else 'Sin coincidencias localizables en la vista previa.')
        st.pdf(data, height=850, key=f'pdf_{selected}_{query}', alt='Documento completo con resaltados')
    except Exception:
        st.warning('No se pudo cargar la vista previa. Puedes descargar el original.')
