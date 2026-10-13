# Buscador documental público

Versión independiente de la aplicación local. Lee los originales, las vistas PDF y el índice alojados en Supabase. No consulta carpetas del computador del usuario, no requiere Word de Windows y no ejecuta OCR desde la web pública.

## Configuración

1. Ejecutar `schema.sql` en el proyecto Supabase elegido. Crea una tabla exclusiva del buscador, con lectura pública y sin escritura para visitantes, y un bucket público exclusivo.
2. Procesar los documentos con `admin_upload.py` desde un servidor Linux con LibreOffice y las dependencias de `requirements-admin.txt` instaladas. Configurar `SUPABASE_URL` y `SUPABASE_ADMIN_KEY` en el entorno de ese servidor. La clave administrativa no se incorpora a GitHub ni a la aplicación pública.
3. Subir el contenido de esta carpeta a un repositorio GitHub. No subir los documentos ni claves: los archivos estarán en Supabase.
4. Publicar `app.py` en Streamlit Community Cloud, con Python 3.12. Configurar `SUPABASE_URL` y `SUPABASE_PUBLISHABLE_KEY` en Secrets, siguiendo `secrets.example.toml`.
5. Probar desde otro dispositivo: búsqueda, equivalencia MF100A/MF-100A, visor completo y descarga original. Apagar el PC no afecta la versión publicada.

## Operación

Los originales se guardan sin modificaciones. La preparación convierte Word mediante LibreOffice, agrega texto OCR invisible únicamente a la vista PDF y almacena los fragmentos del índice en SQL. La conversión de LibreOffice puede diferir ligeramente del diseño de Microsoft Word. Los PDF escaneados pueden contener errores OCR.

Los archivos se publican solo con el proceso administrativo. Agregar archivos al Escritorio no actualiza la nube. Los documentos públicos pueden ser leídos y descargados por cualquier persona; no publicar claves, información privada no autorizada ni otros archivos fuera del conjunto aprobado.

La herramienta de carga agrega o actualiza documentos; no elimina publicaciones anteriores al borrar archivos de la carpeta. Para retirar una publicación, un administrador debe establecer `published=false` y retirar los objetos públicos de Storage. Esta acción debe autorizarse por separado.

No se ha realizado una publicación real hasta configurar los servicios y validar el acceso externo.

Referencias: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy y https://supabase.com/docs/guides/storage/security/access-control.
