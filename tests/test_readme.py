"""Pruebas de la documentación de la librería `shipping`.

Comprueban que el README existe y que documenta la superficie pública, las
tarifas por zona, el factor express, las reglas de redondeo, el contrato de
validación y los ejemplos de uso publicados.
"""

import re
from decimal import Decimal
from pathlib import Path

import pytest

from shipping import shipping_cost

README_PATH = Path(__file__).resolve().parents[1] / "README.md"

# (argumentos, kwargs, importe esperado según el README).
EJEMPLOS = (
    ((2, 30, 20, 10, "B"), {}, "11.10"),
    ((2, 30, 20, 10, "B"), {"express": True}, "16.65"),
    ((1, 40, 30, 30, "A"), {}, "14.00"),
)

# (zona, precio base, precio por kg facturable).
TARIFAS = (
    ("A", "5.00", "1.20"),
    ("B", "7.50", "1.80"),
    ("C", "12.00", "2.50"),
)


@pytest.fixture(scope="module")
def readme() -> str:
    """Contenido del README de la raíz del repositorio."""
    assert README_PATH.is_file(), "no existe README.md en la raíz del repositorio"
    return README_PATH.read_text(encoding="utf-8")


@pytest.mark.parametrize("funcion", ["volumetric_weight", "billable_weight", "shipping_cost"])
def test_el_readme_documenta_las_funciones_publicas(readme: str, funcion: str):
    assert funcion in readme


@pytest.mark.parametrize("firma", ["volumetric_weight(", "billable_weight(", "shipping_cost("])
def test_el_readme_muestra_la_firma_de_cada_funcion(readme: str, firma: str):
    assert firma in readme


@pytest.mark.parametrize(("zona", "base", "por_kg"), TARIFAS)
def test_el_readme_documenta_la_tarifa_de_cada_zona(
    readme: str, zona: str, base: str, por_kg: str
):
    fila = re.compile(
        rf"\|\s*`?\"?{zona}\"?`?\s*\|\s*{re.escape(base)}\s*\|\s*{re.escape(por_kg)}\s*\|"
    )
    assert fila.search(readme), f"falta la fila de tarifas de la zona {zona}"


def test_el_readme_documenta_las_tres_zonas(readme: str):
    for zona in ("A", "B", "C"):
        assert f'"{zona}"' in readme


def test_el_readme_documenta_el_multiplicador_express(readme: str):
    assert "1.5" in readme
    assert "express" in readme


def test_el_readme_documenta_las_reglas_de_redondeo(readme: str):
    assert "ROUND_HALF_UP" in readme
    assert "0.5" in readme
    assert "30" in readme


def test_el_readme_documenta_el_contrato_de_validacion(readme: str):
    for elemento in ("TypeError", "ValueError", "int", "Decimal", "float", "bool"):
        assert elemento in readme


@pytest.mark.parametrize(("importe",), [(importe,) for _, _, importe in EJEMPLOS])
def test_el_readme_publica_los_importes_de_ejemplo(readme: str, importe: str):
    assert importe in readme


@pytest.mark.parametrize(("argumentos", "kwargs", "importe"), EJEMPLOS)
def test_los_ejemplos_del_readme_coinciden_con_la_biblioteca(
    argumentos: tuple, kwargs: dict, importe: str
):
    assert shipping_cost(*argumentos, **kwargs) == Decimal(importe)
