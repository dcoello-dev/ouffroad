# Ouffroad - Gestión de Rutas y Multimedia

## Descripción del Proyecto

`Ouffroad` es un backend desarrollado en Python con FastAPI diseñado para la gestión y visualización de rutas GPS (en formatos como GPX y FIT) y archivos multimedia asociados (fotografías JPG y vídeos MP4). Ofrece una API RESTful robusta para la subida, procesamiento, almacenamiento y consulta de estos datos, facilitando su integración con aplicaciones frontend.

## Características Principales

*   **Subida Flexible**: Permite la carga de ficheros GPX, FIT, JPG y MP4 a través de un único endpoint.
*   **Extracción de Metadatos**: Procesa automáticamente los metadatos de los archivos (ej. datos EXIF de fotos, información de tracks GPS).
*   **Almacenamiento Estructurado**: Organiza los ficheros en el sistema de almacenamiento según políticas configurables (ej. basado en fechas).
*   **API GeoJSON**: Proporciona una interfaz para obtener la representación GeoJSON de tracks y puntos multimedia.
*   **Manejo de Errores Robusto**: Implementa una jerarquía de excepciones personalizada y un manejador centralizado para ofrecer respuestas claras y predecibles.

## Arquitectura y Tecnologías

El backend está construido sobre una **arquitectura en capas** bien definida, que separa claramente las responsabilidades:
*   **Capa de API**: Implementada con FastAPI, gestiona las solicitudes HTTP y las respuestas.
*   **Capa de Servicios**: Contiene la lógica de negocio y orquesta las operaciones.
*   **Capa de Repositorio**: Abstrae el acceso a los datos, permitiendo almacenar en el sistema de ficheros.
*   **Modelos de Dominio**: Define las entidades clave del negocio (`ITrack`, `IMedia`) y sus implementaciones concretas.

**Tecnologías clave:**
*   **Python 3.12+**
*   **FastAPI**: Framework web de alto rendimiento.
*   **Uvicorn**: Servidor ASGI para ejecutar la aplicación FastAPI.
*   **Pillow**: Para el procesamiento de imágenes (EXIF).
*   **gpxpy, fitparse**: Librerías para el parseo de ficheros GPX y FIT.
*   **Jinja2Templates**: Para el renderizado del frontend básico.

## Configuración del Entorno de Desarrollo

Sigue estos pasos para poner el proyecto en marcha:

1.  **Clonar el Repositorio:**
    ```bash
    git clone [URL_DE_TU_REPOSITORIO]
    cd ouffroad
    ```
2.  **Crear y Activar un Entorno Virtual:**
    Es altamente recomendable usar un entorno virtual para gestionar las dependencias del proyecto.
    ```bash
    python -m venv .venv
    # En Linux/macOS:
    source .venv/bin/activate
    # En Windows:
    .venv\Scripts\activate
    ```
3.  **Instalar Dependencias:**
    Instala todas las librerías necesarias.
    ```bash
    pip install -r requirements.txt
    ```
    *(Asegúrate de que `requirements.txt` existe y está actualizado. Si no, puedes generarlo con `pip freeze > requirements.txt`)*

4.  **Instalar y Configurar Pre-commit Hooks (Recomendado):**
    Para asegurar la calidad del código y mantener un estilo consistente, se utiliza `pre-commit`.
    ```bash
    pip install pre-commit
    pre-commit install
    ```
    Para ejecutar las comprobaciones en todos los ficheros existentes:
    ```bash
    pre-commit run --all-files
    ```

## Ejecutar la Aplicación

Para iniciar el servidor de desarrollo:

```bash
# Para activar el modo "reload" (recarga automática al cambiar código)
# y especificar la ruta al repositorio (por defecto es 'uploads')
# En Linux/macOS:
ENV=development python -m src.ouffroad --repo mi_repositorio/
# En Windows (CMD):
set ENV=development
python -m src.ouffroad --repo mi_repositorio/
# En Windows (PowerShell):
$env:ENV="development"
python -m src.ouffroad --repo mi_repositorio/

# Si no se especifica --repo, se usará el directorio 'uploads' por defecto.

# Sin modo "reload" (para producción):
python -m src.ouffroad --repo mi_repositorio/
```
La aplicación estará disponible en `http://0.0.0.0:8000`.

## Configuración del Repositorio

`Ouffroad` utiliza un sistema de configuración centralizado que permite definir las categorías de archivos y sus políticas de almacenamiento. Esta configuración se lee desde un fichero `storage.toml` que debe estar en la raíz del directorio especificado como repositorio (por ejemplo, `mi_repositorio/storage.toml`).

### Estructura de `storage.toml`

El fichero `storage.toml` define las diferentes categorías de almacenamiento (ej. "trail", "media") y, para cada una, el tipo de contenido que acepta (`track` o `media`), las extensiones de archivo asociadas y la política de almacenamiento que se debe aplicar.

Ejemplo de `storage.toml`:

```toml
[categories.trail]
name = "trail"
type = "track"
extensions = [".gpx", ".fit"]
storage_policy = { name = "DateBasedPolicy" } # Opcional, por defecto es DateBasedPolicy

[categories.media]
name = "media"
type = "media"
extensions = [".jpg", ".mp4", ".jpeg"]
storage_policy = { name = "FlatPolicy" } # Ejemplo de otra política
```

Las políticas de almacenamiento disponibles son:
*   `DateBasedPolicy`: Organiza los ficheros en subdirectorios por año/mes (ej. `categoría/año/mes/fichero.ext`).
*   `FlatPolicy`: Guarda todos los ficheros de la categoría directamente en el directorio de la categoría (ej. `categoría/fichero.ext`).
*   `ConfigurablePolicy`: Permite una configuración más avanzada (actualmente no implementada de forma genérica en el `.toml`).

La estructura de esta configuración es validada internamente por modelos de `Pydantic`, asegurando la corrección de los datos.

## Endpoints de la API

Aquí tienes un resumen de los principales endpoints:

*   **`GET /`**: Accede al frontend básico de la aplicación.
*   **`POST /api/upload`**: Sube ficheros de tracks o multimedia.
    *   **Método**: `POST`
    *   **Parámetros de formulario**: `file` (el archivo), `category` (ej. "trail", "media"), `latitude` (opcional), `longitude` (opcional).
*   **`GET /api/tracks`**: Lista todos los tracks y elementos multimedia disponibles.
*   **`GET /api/track/{filename:path}`**: Obtiene la representación GeoJSON de un track o elemento multimedia específico.
    *   **Parámetros de ruta**: `filename` (ruta relativa del fichero, ej. "media/carba/IMG-20251012-WA0014.jpg").

## Estructura del Proyecto

*   `src/ouffroad/`: Contiene todo el código fuente del backend.
    *   `api.py`: Definición de las rutas de la API.
    *   `services/`: Lógica de negocio.
    *   `repository/`: Abstracción de la capa de datos.
    *   `track/`: Implementaciones para tracks GPX/FIT.
    *   `media/`: Implementaciones para fotos/vídeos.
    *   `core/`: Excepciones base y otras utilidades.
*   `front/`: Ficheros estáticos y plantillas del frontend básico.
*   `uploads/`: Directorio donde se almacenan los archivos subidos.
*   `tests/`: Tests unitarios y de integración.
*   `.pre-commit-config.yaml`: Configuración para `pre-commit`.
*   `requirements.txt`: Dependencias del proyecto.
*   `pyproject.toml`: Configuración de herramientas y metadatos del proyecto.

## Contribuciones

¡Las contribuciones son bienvenidas! Por favor, consulta el fichero `AGENTS.md` para las directrices de contribución y cómo añadir nuevos "agentes" (ej. nuevos formatos de tracks o multimedia).

## Licencia

[Aquí puedes especificar la licencia, por ejemplo, MIT, Apache 2.0, etc.]
