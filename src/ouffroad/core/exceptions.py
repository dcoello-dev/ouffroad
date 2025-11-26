# src/ouffroad/core/exceptions.py


class OuffroadException(Exception):
    """Excepción base para todos los errores de la aplicación Ouffroad."""

    pass


class MetadataError(OuffroadException):
    """Ocurrió un error al parsear o procesar metadatos de un fichero."""

    pass


class FileProcessingError(OuffroadException):
    """Ocurrió un error general al procesar un fichero."""

    pass


class RepositoryError(OuffroadException):
    """Ocurrió un error en la capa de persistencia."""

    pass
