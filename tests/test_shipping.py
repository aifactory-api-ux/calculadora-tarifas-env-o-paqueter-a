"""Pruebas de la API pública de la librería `shipping`."""

import inspect
from decimal import Decimal

import pytest

import shipping
from shipping import billable_weight, shipping_cost, volumetric_weight


class TestSuperficiePublica:
    """Comprueba los nombres y las firmas publicados por el módulo."""

    def test_all_declara_las_tres_funciones_publicas(self):
        assert shipping.__all__ == [
            "volumetric_weight",
            "billable_weight",
            "shipping_cost",
        ]

    def test_los_nombres_publicos_son_funciones_invocables(self):
        for nombre in shipping.__all__:
            assert callable(getattr(shipping, nombre))

    @pytest.mark.parametrize(
        ("funcion", "parametros"),
        [
            (volumetric_weight, ["length_cm", "width_cm", "height_cm"]),
            (
                billable_weight,
                ["actual_kg", "length_cm", "width_cm", "height_cm"],
            ),
            (
                shipping_cost,
                [
                    "actual_kg",
                    "length_cm",
                    "width_cm",
                    "height_cm",
                    "zone",
                    "express",
                ],
            ),
        ],
    )
    def test_nombres_y_orden_de_los_parametros(self, funcion, parametros):
        assert list(inspect.signature(funcion).parameters) == parametros

    def test_express_por_defecto_es_false(self):
        default = inspect.signature(shipping_cost).parameters["express"].default
        assert default is False


class TestHelpersDeValidacion:
    """Contrato de los ayudantes privados de validación de entradas."""

    @pytest.mark.parametrize(
        ("valor", "esperado"),
        [
            (3, Decimal("3")),
            (Decimal("2.5"), Decimal("2.5")),
        ],
    )
    def test_to_decimal_convierte_int_y_decimal(self, valor, esperado):
        assert shipping._to_decimal(valor, "peso") == esperado

    @pytest.mark.parametrize("valor", [True, False, 2.0, "2", None])
    def test_to_decimal_rechaza_bool_y_float(self, valor):
        with pytest.raises(TypeError):
            shipping._to_decimal(valor, "peso")

    def test_require_positive_devuelve_el_valor_validado(self):
        assert shipping._require_positive(Decimal("0.25"), "peso") == Decimal("0.25")

    @pytest.mark.parametrize("valor", [0, -1, Decimal("0"), Decimal("-1")])
    def test_require_positive_rechaza_valores_no_positivos(self, valor):
        with pytest.raises(ValueError):
            shipping._require_positive(valor, "peso")

    def test_require_positive_rechaza_valores_no_finitos(self):
        with pytest.raises(ValueError):
            shipping._require_positive(Decimal("NaN"), "peso")


class TestPesoVolumetrico:
    """Cálculo del peso volumétrico a partir de las dimensiones."""

    def test_dimensiones_de_referencia(self):
        assert volumetric_weight(30, 20, 10) == Decimal("1.20")

    def test_dimensiones_como_decimal(self):
        resultado = volumetric_weight(Decimal("30"), Decimal("20"), Decimal("10"))
        assert resultado == Decimal("1.20")

    def test_tercer_decimal_igual_a_cinco_redondea_hacia_arriba(self):
        assert volumetric_weight(25, 201, 1) == Decimal("1.01")

    def test_valor_inferior_a_la_mitad_redondea_hacia_abajo(self):
        assert volumetric_weight(40, 30, 30) == Decimal("7.20")

    def test_el_resultado_es_decimal_y_no_float(self):
        resultado = volumetric_weight(30, 20, 10)
        assert isinstance(resultado, Decimal)
        assert not isinstance(resultado, float)


class TestPesoFacturable:
    """Cálculo del peso facturable y sus límites."""

    def test_el_peso_real_manda_sobre_el_volumetrico(self):
        assert billable_weight(2, 30, 20, 10) == Decimal("2.00")

    def test_el_peso_volumetrico_manda_sobre_el_real(self):
        assert billable_weight(1, 25, 40, 40) == Decimal("8.00")

    def test_un_multiplo_exacto_de_medio_kilo_se_conserva(self):
        assert billable_weight(Decimal("2.0"), 30, 20, 10) == Decimal("2.00")

    def test_un_kilo_fraccionario_redondea_hacia_arriba(self):
        assert billable_weight(Decimal("2.01"), 30, 20, 10) == Decimal("2.50")

    def test_el_peso_volumetrico_también_redondea_hacia_arriba(self):
        assert billable_weight(1, 40, 30, 30) == Decimal("7.50")

    def test_exactamente_30_kg_se_acepta(self):
        assert billable_weight(30, 30, 20, 10) == Decimal("30.00")

    def test_29_9_kg_redondea_a_30_kg_y_se_acepta(self):
        assert billable_weight(Decimal("29.9"), 30, 20, 10) == Decimal("30.00")

    def test_un_peso_real_sobre_el_límite_se_rechaza(self):
        with pytest.raises(ValueError):
            billable_weight(Decimal("30.5"), 30, 20, 10)

    def test_un_peso_volumetrico_sobre_el_límite_se_rechaza(self):
        with pytest.raises(ValueError):
            billable_weight(1, 100, 100, 100)

    def test_el_error_de_límite_informa_del_peso_calculado(self):
        with pytest.raises(ValueError, match="30.50"):
            billable_weight(Decimal("30.5"), 30, 20, 10)

    def test_el_resultado_es_decimal_y_no_float(self):
        resultado = billable_weight(2, 30, 20, 10)
        assert isinstance(resultado, Decimal)
        assert not isinstance(resultado, float)


class TestTarifasPorZona:
    """Tarifa final por zona y servicio express."""

    def test_zona_a(self):
        assert shipping_cost(2, 30, 20, 10, "A") == Decimal("7.40")

    def test_zona_b(self):
        assert shipping_cost(2, 30, 20, 10, "B") == Decimal("11.10")

    def test_zona_c(self):
        assert shipping_cost(2, 30, 20, 10, "C") == Decimal("17.00")

    def test_la_tarifa_se_calcula_sobre_el_peso_facturable(self):
        assert shipping_cost(1, 40, 30, 30, "A") == Decimal("14.00")

    def test_express_multiplica_el_total_por_uno_coma_cinco(self):
        assert shipping_cost(2, 30, 20, 10, "B", express=True) == Decimal("16.65")

    def test_express_por_defecto_no_se_aplica(self):
        assert shipping_cost(2, 30, 20, 10, "B") == Decimal("11.10")

    def test_express_falso_no_se_aplica(self):
        assert shipping_cost(2, 30, 20, 10, "B", express=False) == Decimal("11.10")

    def test_el_redondeo_final_es_round_half_up(self):
        assert shipping_cost(Decimal("2.5"), 30, 20, 10, "C", express=True) == Decimal(
            "27.38"
        )

    def test_pesos_y_medidas_como_decimal(self):
        resultado = shipping_cost(
            Decimal("2"),
            Decimal("30"),
            Decimal("20"),
            Decimal("10"),
            "B",
        )
        assert resultado == Decimal("11.10")

    def test_el_resultado_es_decimal_y_no_float(self):
        resultado = shipping_cost(2, 30, 20, 10, "B")
        assert isinstance(resultado, Decimal)
        assert not isinstance(resultado, float)


class TestValidaciones:
    """Contrato de validación de la API pública."""

    @pytest.mark.parametrize("peso", [2.0, True, "2", None])
    def test_el_peso_rechaza_tipos_no_admitidos(self, peso):
        with pytest.raises(TypeError):
            shipping_cost(peso, 30, 20, 10, "B")

    @pytest.mark.parametrize("medida", [30.0, True, "30", None])
    def test_las_medidas_rechazan_tipos_no_admitidos(self, medida):
        with pytest.raises(TypeError):
            volumetric_weight(medida, 20, 10)

    @pytest.mark.parametrize("peso", [0, -1, Decimal("0"), Decimal("-1")])
    def test_el_peso_debe_ser_mayor_que_cero(self, peso):
        with pytest.raises(ValueError):
            billable_weight(peso, 30, 20, 10)

    @pytest.mark.parametrize("medida", [0, -20, Decimal("0"), Decimal("-20")])
    def test_las_medidas_deben_ser_mayores_que_cero(self, medida):
        with pytest.raises(ValueError):
            volumetric_weight(30, medida, 10)

    @pytest.mark.parametrize(
        "valor", [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")]
    )
    def test_los_valores_no_finitos_se_rechazan(self, valor):
        with pytest.raises(ValueError):
            billable_weight(valor, 30, 20, 10)

    @pytest.mark.parametrize("zona", ["a", "D", None, 1, ["A"]])
    def test_la_zona_debe_ser_a_b_o_c(self, zona):
        with pytest.raises(ValueError):
            shipping_cost(2, 30, 20, 10, zona)

    @pytest.mark.parametrize("express", [1, "true", None, Decimal("1")])
    def test_express_debe_ser_booleano(self, express):
        with pytest.raises(TypeError):
            shipping_cost(2, 30, 20, 10, "B", express=express)

    @pytest.mark.parametrize("zona", ["A", "B", "C"])
    @pytest.mark.parametrize("express", [True, False])
    def test_las_zonas_y_express_validos_pasan_la_validacion(self, zona, express):
        assert isinstance(shipping_cost(2, 30, 20, 10, zona, express), Decimal)
