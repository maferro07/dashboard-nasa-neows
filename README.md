# Asteroides cerca de la Tierra

Dashboard de Streamlit para la actividad de Herramientas de Visualización. Usa NASA Asteroids NeoWs para explorar aproximaciones de asteroides a la Tierra.

## Datos y gráficas

- **Datos de la evaluación** abre los 227 registros de `respuesta.json` del 1 de octubre al 7 de noviembre de 2026. Este modo funciona sin consultar NASA.
- **Consultar API NASA** solicita datos al endpoint `https://api.nasa.gov/neo/rest/v1/feed` para un intervalo de uno a siete días. El tablero indica la fuente y el periodo de los datos mostrados.
- Pandas convierte el JSON en una tabla con una fila por aproximación, transforma fechas y valores numéricos y omite filas incompletas.
- Las gráficas muestran aproximaciones por día, distribución del diámetro máximo estimado, velocidad promedio por clasificación y relación entre tamaño y velocidad. Los filtros se aplican a los indicadores, las gráficas y el CSV descargable.

## Evidencias incluidas

- [Tablero con los 227 registros de la evaluación](evidencias/01-datos-evaluacion.png)
- [Consulta a NASA con el filtro de asteroides potencialmente peligrosos](evidencias/02-api-nasa-y-filtro.png)

## Ejecutar en VS Code

Abre la carpeta del proyecto y ejecuta estos comandos en la terminal, con Python 3.12.

```bash
python -m venv .venv
```

En Windows PowerShell, usa el Python del entorno virtual directamente.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run dashboard.py
```

En Ubuntu o WSL, usa estos comandos.

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run dashboard.py
```

Abre [http://localhost:8501](http://localhost:8501).

## Publicar en GitHub y Streamlit Community Cloud

1. Crea un repositorio en GitHub, por ejemplo `dashboard-nasa-neows`, con un README para habilitar la subida desde el navegador. Usa visibilidad pública si tu profesor necesita abrir el enlace sin invitación.
2. Descomprime el ZIP. En el repositorio, entra a **Add file → Upload files** y arrastra los archivos de dentro de la carpeta `dashboard-nasa-neows`. Sube también la carpeta `.streamlit` con `config.toml` para conservar el tema. Confirma con **Commit changes**. `dashboard.py`, `requirements.txt` y `respuesta.json` deben quedar juntos en la raíz.
3. En [Streamlit Community Cloud](https://share.streamlit.io/), inicia sesión con GitHub. Pulsa **Create app** y elige la opción para desplegar desde un repositorio.
4. Selecciona tu repositorio y la rama `main`. En **Main file path**, escribe `dashboard.py`. En **Advanced settings**, selecciona Python 3.12 y pulsa **Deploy**.
5. Abre la URL que termina en `.streamlit.app`. Guarda una captura del tablero y otra después de entrar a **Consultar API NASA** y ejecutar una consulta. Puedes usar el periodo del 1 al 7 de noviembre de 2026.
6. Entrega el enlace del repositorio y las capturas o el video. Si te piden el tablero publicado, incluye la URL de Streamlit.

La consulta usa la clave pública `DEMO_KEY` por defecto. Si alcanza el límite de solicitudes, puedes obtener una [clave personal de NASA](https://api.nasa.gov/) y agregarla en **Advanced settings → Secrets** al desplegar o en **Settings → Secrets** si ya publicaste la app.

```toml
NASA_API_KEY = "PEGA_AQUÍ_TU_CLAVE"
```

En local puedes colocar esa configuración en `.streamlit/secrets.toml`. El archivo está excluido de Git por `.gitignore`.

[Documentación de NASA NeoWs](https://api.nasa.gov/) · [Guía de despliegue en Streamlit](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
