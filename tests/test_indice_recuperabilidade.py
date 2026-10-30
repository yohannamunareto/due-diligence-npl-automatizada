import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from indice_recuperabilidade import (  # noqa: E402
    Garantia,
    Vetor,
    calcular_ir,
    calcular_tcp,
    classificar,
)


def vetores(scores):
    return [
        Vetor(f"V{i}", s, "justificativa de teste", f"Mov. {i}, Fls. {i}")
        for i, s in enumerate(scores, start=1)
    ]


def test_pesos_somam_um():
    from indice_recuperabilidade import PESOS

    assert sum(PESOS.values()) == Decimal("1")


def test_tcp_desconta_gravames_anteriores():
    garantias = [
        Garantia("imóvel", Decimal("1000"), True, gravames_anteriores=Decimal("400")),
        Garantia("veículo", Decimal("100"), True),
    ]
    assert calcular_tcp(garantias, Decimal("1000")) == Decimal("70.00")


def test_tcp_nao_fica_negativo_quando_gravame_supera_o_bem():
    garantias = [Garantia("imóvel", Decimal("500"), True, Decimal("800"))]
    assert calcular_tcp(garantias, Decimal("1000")) == Decimal("0.00")


def test_tcp_exige_divida_positiva():
    with pytest.raises(ValueError):
        calcular_tcp([], Decimal("0"))


def test_ir_maximo_e_minimo():
    assert calcular_ir(vetores([10] * 6), [], Decimal("1")).ir == Decimal("10.00")
    assert calcular_ir(vetores([1] * 6), [], Decimal("1")).ir == Decimal("1.00")


def test_ir_do_caso_ficticio():
    resultado = calcular_ir(vetores([7, 4, 7, 4, 10, 10]), [], Decimal("1"))
    # 2,45 + 0,80 + 1,40 + 0,60 + 0,70 + 0,30
    assert resultado.ir == Decimal("6.25")
    assert resultado.faixa == "MÉDIO RISCO"
    assert resultado.conclusao_sugerida == "AQUISIÇÃO CONDICIONAL"


@pytest.mark.parametrize(
    "ir, faixa",
    [
        ("10.00", "BAIXO RISCO"),
        ("8.00", "BAIXO RISCO"),
        ("7.99", "MÉDIO RISCO"),
        ("6.00", "MÉDIO RISCO"),
        ("5.99", "ALTO RISCO"),
        ("3.50", "ALTO RISCO"),
        ("3.49", "RISCO CRÍTICO"),
        ("0.00", "RISCO CRÍTICO"),
    ],
)
def test_limites_das_faixas(ir, faixa):
    assert classificar(Decimal(ir))[0] == faixa


def test_score_fora_da_escala_e_recusado():
    with pytest.raises(ValueError):
        Vetor("V1", 5, "x", "Mov. 1")


def test_score_sem_fonte_e_recusado():
    with pytest.raises(ValueError):
        Vetor("V1", 7, "x", "  ")


def test_exige_os_seis_vetores():
    with pytest.raises(ValueError):
        calcular_ir(vetores([10] * 5), [], Decimal("1"))


def test_alerta_para_avaliacao_nao_homologada():
    garantias = [Garantia("trator", Decimal("100"), avaliacao_homologada=False)]
    resultado = calcular_ir(vetores([10] * 6), garantias, Decimal("100"))
    assert resultado.alertas == ["Garantia sem avaliação homologada: trator"]
