"""Pruebas de la containerización del proyecto `shipping`.

Comprueban los ficheros de contenedor definidos en el diseño: el `Dockerfile`
de la raíz, que construye una imagen con la librería y con las herramientas de
prueba, y el `docker-compose.yml` de la raíz, cuyo único servicio construye esa
imagen y ejecuta la suite de pruebas sobre el directorio `tests/`.

Las comprobaciones se hacen sobre el texto de los ficheros y únicamente con la
biblioteca estándar: la imagen de pruebas instala sólo `pytest`, sin
dependencias adicionales como PyYAML.
"""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DOCKERFILE = RAIZ / "Dockerfile"
COMPOSE = RAIZ / "docker-compose.yml"
PYPROJECT = RAIZ / "pyproject.toml"

SERVICIO = "shipping-tests"


def leer(ruta: Path) -> str:
    """Devuelve el contenido de un fichero de la raíz del repositorio."""
    assert ruta.is_file(), f"no existe {ruta.name} en la raíz del repositorio"
    return ruta.read_text(encoding="utf-8")


def bloque_del_servicio(compose: str) -> str:
    """Devuelve el bloque del servicio `shipping-tests` del fichero compose.

    El bloque se delimita por indentación: las claves del servicio están
    sangradas cuatro espacios respecto de la sección `services:`.

    Args:
        compose: Contenido del fichero `docker-compose.yml`.

    Returns:
        Las líneas que pertenecen al servicio, sin la línea de cabecera.

    Raises:
        AssertionError: Si el compose no define el servicio.
    """
    lineas = compose.splitlines()
    for indice, linea in enumerate(lineas):
        if linea.strip() == f"{SERVICIO}:":
            bloque: list[str] = []
            for siguiente in lineas[indice + 1 :]:
                if siguiente.strip() and not siguiente.startswith("    "):
                    break
                bloque.append(siguiente)
            return "\n".join(bloque)
    raise AssertionError(f"el compose no define el servicio '{SERVICIO}'")


def valor_de(bloque: str, clave: str) -> str:
    """Devuelve el valor literal de una clave del bloque del servicio.

    Args:
        bloque: Bloque de texto del servicio.
        clave: Nombre de la clave a localizar.

    Returns:
        El valor de la clave sin comillas ni espacios sobrantes; cadena vacía
        si la clave no tiene valor en línea.

    Raises:
        AssertionError: Si la clave no aparece en el bloque.
    """
    coincidencia = re.search(
        rf"^[ \t]*{re.escape(clave)}:[ \t]*(?P<valor>[^\n]*)$", bloque, re.MULTILINE
    )
    assert coincidencia is not None, f"el servicio no declara la clave '{clave}'"
    return coincidencia.group("valor").strip().strip('"').strip("'")


def argumentos_del_comando(comando: str) -> list[str]:
    """Convierte un comando escrito como lista JSON o YAML en sus argumentos.

    Args:
        comando: Texto del comando, por ejemplo `["pytest", "-q"]`.

    Returns:
        La lista de argumentos del comando.
    """
    limpio = comando.strip().strip("[]").replace('"', " ").replace("'", " ")
    return limpio.split()


def contexto_y_dockerfile(bloque: str) -> tuple[str, str]:
    """Resuelve el contexto de construcción y el `Dockerfile` del servicio.

    Admite la forma corta (`build: .`, que usa el `Dockerfile` del contexto) y
    la forma larga (`build:` con las claves `context:` y `dockerfile:`).

    Args:
        bloque: Bloque de texto del servicio.

    Returns:
        Tupla con el contexto de construcción y el nombre del `Dockerfile`.
    """
    build = valor_de(bloque, "build")
    if build:
        return build, "Dockerfile"
    return valor_de(bloque, "context"), valor_de(bloque, "dockerfile")


class TestFicherosDeContenedor:
    """Presencia de los ficheros de contenedor en la raíz del repositorio."""

    def test_existe_el_dockerfile_en_la_raiz(self):
        assert DOCKERFILE.is_file()

    def test_existe_el_compose_en_la_raiz(self):
        assert COMPOSE.is_file()

    def test_la_raiz_del_repositorio_lista_el_dockerfile_y_el_compose(self):
        nombres = {ruta.name for ruta in RAIZ.iterdir() if ruta.is_file()}
        assert {"Dockerfile", "docker-compose.yml"} <= nombres


class TestDockerfile:
    """Contenido del `Dockerfile` de la raíz."""

    def test_la_imagen_parte_de_python_312_slim(self):
        contenido = leer(DOCKERFILE)
        assert re.search(r"^FROM\s+python:3\.12-slim\s*$", contenido, re.MULTILINE)

    def test_el_directorio_de_trabajo_es_app(self):
        contenido = leer(DOCKERFILE)
        assert re.search(r"^WORKDIR\s+/app\s*$", contenido, re.MULTILINE)

    def test_copia_el_pyproject_y_el_codigo_de_la_biblioteca(self):
        contenido = leer(DOCKERFILE)
        assert re.search(r"^COPY\s+pyproject\.toml\b", contenido, re.MULTILINE)
        assert re.search(r"^COPY\s+src/", contenido, re.MULTILINE)

    def test_instala_el_paquete_y_pytest(self):
        contenido = leer(DOCKERFILE)
        assert "pip install --no-cache-dir ." in contenido
        assert re.search(r"pip install --no-cache-dir\s+pytest", contenido)

    def test_copia_la_suite_de_pruebas(self):
        contenido = leer(DOCKERFILE)
        assert re.search(r"^COPY\s+tests/", contenido, re.MULTILINE)

    def test_el_comando_por_defecto_ejecuta_pytest(self):
        contenido = leer(DOCKERFILE)
        assert re.search(r'^CMD\s+\["pytest",\s*"-q"\]\s*$', contenido, re.MULTILINE)

    def test_las_copias_no_usan_operadores_de_shell(self):
        contenido = leer(DOCKERFILE)
        copias = [
            linea
            for linea in contenido.splitlines()
            if linea.strip().upper().startswith("COPY")
        ]
        assert copias
        for linea in copias:
            assert not any(operador in linea for operador in ("&&", "||", ";", ">"))

    def test_la_imagen_no_copia_ficheros_de_secretos(self):
        contenido = leer(DOCKERFILE)
        copias = [
            linea
            for linea in contenido.splitlines()
            if linea.strip().upper().startswith("COPY")
        ]
        for linea in copias:
            assert ".env" not in linea


class TestDockerCompose:
    """Contenido del `docker-compose.yml` de la raíz."""

    def test_el_compose_declara_la_seccion_de_servicios(self):
        compose = leer(COMPOSE)
        assert re.search(r"^services:[ \t]*$", compose, re.MULTILINE)

    def test_el_compose_define_un_unico_servicio(self):
        compose = leer(COMPOSE)
        servicios = re.findall(
            r"^  ([A-Za-z0-9_.-]+):[ \t]*$", compose, re.MULTILINE
        )
        assert servicios == [SERVICIO]

    def test_el_servicio_construye_desde_el_dockerfile_de_la_raiz(self):
        compose = leer(COMPOSE)
        contexto, dockerfile = contexto_y_dockerfile(bloque_del_servicio(compose))
        assert contexto == "."
        assert dockerfile == "Dockerfile"
        assert (RAIZ / dockerfile).is_file()

    def test_el_comando_del_servicio_ejecuta_pytest(self):
        compose = leer(COMPOSE)
        comando = valor_de(bloque_del_servicio(compose), "command")
        assert "pytest" in comando

    def test_el_servicio_no_se_reinicia(self):
        compose = leer(COMPOSE)
        assert valor_de(bloque_del_servicio(compose), "restart") == "no"

    def test_el_servicio_no_publica_puertos(self):
        compose = leer(COMPOSE)
        assert "ports" not in bloque_del_servicio(compose)

    def test_el_servicio_no_depende_de_servicios_externos(self):
        compose = leer(COMPOSE)
        assert "depends_on" not in bloque_del_servicio(compose)


class TestEjecucionDeLaSuite:
    """La imagen ejecuta la suite completa sobre el directorio `tests/`."""

    def test_la_suite_se_recoge_desde_el_directorio_tests(self):
        pyproject = leer(PYPROJECT)
        assert re.search(r'^\s*testpaths\s*=\s*\[\s*"tests"\s*\]\s*$', pyproject, re.MULTILINE)

    def test_la_imagen_incluye_la_biblioteca_y_la_suite(self):
        contenido = leer(DOCKERFILE)
        assert re.search(r"^COPY\s+src/", contenido, re.MULTILINE)
        assert re.search(r"^COPY\s+tests/", contenido, re.MULTILINE)

    def test_el_comando_por_defecto_y_el_servicio_coinciden(self):
        contenido = leer(DOCKERFILE)
        compose = leer(COMPOSE)
        comando_dockerfile = re.search(
            r'^CMD\s+\[(?P<valor>[^\]]+)\]\s*$', contenido, re.MULTILINE
        )
        assert comando_dockerfile is not None
        comando_compose = valor_de(bloque_del_servicio(compose), "command")
        assert argumentos_del_comando(comando_dockerfile.group("valor")) == (
            argumentos_del_comando(comando_compose)
        )
