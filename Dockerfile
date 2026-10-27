# Imagen de pruebas del proyecto `shipping`.
#
# La librería no expone servidor: lo único ejecutable del repositorio es la
# suite de pruebas, de modo que la imagen se construye para ejecutarla.
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Metadatos y código de la librería: se copian antes que las pruebas para que
# la instalación del paquete no se invalide al añadir ficheros posteriores.
COPY pyproject.toml ./
COPY src/ ./src/

# El paquete se instala con sus dependencias de ejecución y `pytest` como
# herramienta de pruebas, ya que la imagen ejecuta la suite, no un servidor.
RUN pip install --no-cache-dir . \
    && pip install --no-cache-dir pytest

# Suite de pruebas y ficheros de contenedor: se copian para que
# `tests/test_container.py` pueda verificarlos también dentro de la imagen.
# El README se copia porque la suite comprueba la documentación publicada.
COPY tests/ ./tests/
COPY README.md ./
COPY Dockerfile docker-compose.yml ./

# La suite se ejecuta sin privilegios de root.
RUN useradd --create-home --uid 10001 shipping \
    && chown -R shipping:shipping /app
USER shipping

CMD ["pytest", "-q"]
