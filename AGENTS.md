# AGENTS.md - Guía de Contribución para Agentes

¡Gracias por tu interés en contribuir a `Ouffroad`! Este documento te guiará sobre cómo extender la aplicación para soportar nuevos formatos de tracks GPS o archivos multimedia.

## ¿Qué es un "Agente" en Ouffroad?

En `Ouffroad`, un "Agente" es una clase que implementa la lógica específica para parsear, extraer metadatos y representar un tipo particular de fichero (ya sea un track o un medio). Estas clases heredan de las interfaces base `ITrack` o `IMedia` y son gestionadas por sus respectivas factorías (`TrackFactory`, `MediaFactory`).

## Cómo Añadir un Nuevo Agente de Track (Ejemplo: Formato TCX)

Para añadir soporte a un nuevo formato de track (por ejemplo, `TCX`), sigue estos pasos:

1.  **Crea la Nueva Clase de Track**:
    *   En `src/ouffroad/track/`, crea un nuevo fichero (ej. `TCXTrack.py`).
    *   Define una clase `TCXTrack` que herede de `src/ouffroad/track/ITrack.py`.
    *   Asegúrate de importar `MetadataError` de `src/ouffroad/core/exceptions.py` para un manejo consistente de errores.

    ```python
    # src/ouffroad/track/TCXTrack.py
    import pathlib
    import logging
    from datetime import datetime
    # Importa aquí cualquier librería necesaria para parsear TCX (ej. `tcxparser`)

    from .ITrack import ITrack
    from .Formats import TCX_FORMAT_CONSTANT # Define esta constante en Formats.py
    from ouffroad.core.exceptions import MetadataError

    logger = logging.getLogger(__name__)

    class TCXTrack(ITrack):
        def __init__(self, path: pathlib.Path, content: bytes | None = None):
            super().__init__(TCX_FORMAT_CONSTANT, path)
            self.content_ = content
            self.tcx_data = None # Aquí almacenarás los datos parseados del TCX

        def load(self) -> None:
            """Carga y parsea el fichero TCX."""
            try:
                if self.content_:
                    # Lógica para parsear TCX desde bytes
                    self.tcx_data = parse_tcx_from_bytes(self.content_)
                else:
                    with open(self.path_, 'r', encoding='utf-8') as tcx_file:
                        # Lógica para parsear TCX desde fichero
                        self.tcx_data = parse_tcx_from_file(tcx_file)
            except Exception as e:
                logger.error(f"Error cargando fichero TCX {self.path_}: {e}")
                raise MetadataError(f"Fallo al cargar el fichero TCX: {self.path_}") from e

        def date(self) -> datetime | None:
            """Extrae la fecha principal del track TCX."""
            # Implementa la lógica para extraer la fecha del TCX
            if self.tcx_data and hasattr(self.tcx_data, 'start_time'): # Ejemplo
                return self.tcx_data.start_time
            return None

        def geojson(self) -> dict:
            """Retorna la representación GeoJSON del track TCX."""
            # Implementa la lógica para convertir el track TCX a GeoJSON
            return {"type": "FeatureCollection", "features": []} # Ejemplo

        def save(self) -> None:
            """Guarda el track TCX (si aplica)."""
            # Implementa la lógica para guardar si es necesario, o déjalo vacío si es de solo lectura.
            pass
    ```

2.  **Define el Formato en `Formats.py`**:
    *   Añade una constante para el nuevo formato en `src/ouffroad/track/Formats.py`.

    ```python
    # src/ouffroad/track/Formats.py
    # ... otras constantes ...
    TCX = "tcx"
    ```

3.  **Integra con `TrackFactory`**:
    *   En `src/ouffroad/track/TrackFactory.py`, importa tu nueva clase `TCXTrack`.
    *   Añade la lógica para que la factoría cree una instancia de `TCXTrack` cuando el fichero tenga la extensión `.tcx`.

    ```python
    # src/ouffroad/track/TrackFactory.py
    from .GPXTrack import GPXTrack
    from .FITTrack import FITTrack
    from .TCXTrack import TCXTrack # Tu nueva clase

    class TrackFactory:
        @staticmethod
        def create(file_path: pathlib.Path, content: bytes = None) -> list[ITrack]:
            ext = file_path.suffix.lower()
            if ext == '.gpx':
                return [GPXTrack(file_path, content)]
            elif ext == '.fit':
                return [FITTrack(file_path, content)]
            elif ext == '.tcx': # Nuevo
                return [TCXTrack(file_path, content)]
            else:
                return []
    ```

4.  **Define la Categoría en `storage.toml`**:
    *   Para que tu nuevo tipo de fichero sea reconocido y se le pueda asignar una categoría, edita el fichero `storage.toml` en la raíz de tu repositorio. Define la categoría, el `type` (track o media) y las `extensions` que soporta tu agente.

    ```toml
    # /path/to/your/repo/storage.toml

    [categories.mi_nueva_categoria_tcx]
    name = "mi_nueva_categoria_tcx"
    type = "track"
    extensions = [".tcx"] # La extensión de tu nuevo agente
    storage_policy = { name = "DateBasedPolicy" } # O la que prefieras
    ```

5.  **Escribe Pruebas Unitarias**:
    *   Crea un nuevo fichero de tests en `tests/` (ej. `test_tcx_track.py`).
    *   Asegúrate de cubrir los casos de éxito (fichero TCX válido) y los casos de fallo (fichero TCX corrupto o con metadatos inesperados).

## Cómo Añadir un Nuevo Agente Multimedia (Ejemplo: Imágenes RAW)

El proceso es muy similar al de los tracks:

1.  **Crea la Nueva Clase de Medio**:
    *   En `src/ouffroad/media/`, crea un nuevo fichero (ej. `RawImage.py`).
    *   Define una clase `RawImage` que herede de `src/ouffroad/media/IMedia.py`.
    *   Asegúrate de importar `MetadataError`.
    *   Implementa los métodos `load()`, `date()`, `geojson()` y `save()`.

2.  **Integra con `MediaFactory`**:
    *   En `src/ouffroad/media/MediaFactory.py`, importa tu nueva clase `RawImage`.
    *   Añade la lógica para que la factoría cree una instancia de `RawImage` cuando la extensión del fichero sea la correcta (ej. `.cr2`, `.nef`).

3.  **Define la Categoría en `storage.toml`**:
    *   Edita el fichero `storage.toml` en la raíz de tu repositorio para definir la categoría, el `type` (media) y las `extensions` que soporta tu agente.

    ```toml
    # /path/to/your/repo/storage.toml

    [categories.mi_nueva_categoria_raw]
    name = "mi_nueva_categoria_raw"
    type = "media"
    extensions = [".cr2", ".nef"] # Las extensiones de tu nuevo agente
    storage_policy = { name = "FlatPolicy" } # O la que prefieras
    ```

4.  **Escribe Pruebas Unitarias**:
    *   Crea un nuevo fichero de tests en `tests/` (ej. `test_raw_image.py`).
    *   Cubre los casos de éxito y los casos de fallo.

## Directrices Generales de Contribución

*   **Estilo de Código**: Sigue el estilo de código existente. El sistema `pre-commit` te ayudará a mantenerlo.
*   **Pruebas**: Toda nueva funcionalidad debe venir acompañada de pruebas unitarias y, si es necesario, de integración.
*   **Documentación**: Documenta el código nuevo con docstrings claros.
*   **Pull Requests**: Envía tus cambios a través de Pull Requests. Asegúrate de que las pruebas pasan y de que el linter y el formateador no reportan problemas.

---
¡Gracias de nuevo por tu ayuda en la mejora de Ouffroad!
