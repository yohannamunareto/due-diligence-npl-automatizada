"""Cálculo do TCP e do Índice de Recuperabilidade (IR) de créditos NPL.

Versão de demonstração, com as mesmas regras usadas na ferramenta interna.
Não contém dados reais: os casos de exemplo ficam em data/ e são fictícios.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

PESOS = {
    "V1": Decimal("0.35"),  # cobertura das garantias (TCP)
    "V2": Decimal("0.20"),  # liquidez e qualidade das garantias
    "V3": Decimal("0.20"),  # fase processual
    "V4": Decimal("0.15"),  # passivo e defesas do devedor
    "V5": Decimal("0.07"),  # regularidade da representação
    "V6": Decimal("0.03"),  # localização do devedor e citação
}

SCORES_VALIDOS = {10, 7, 4, 1}

FAIXAS = [
    (Decimal("8.0"), "BAIXO RISCO", "AQUISIÇÃO RECOMENDADA"),
    (Decimal("6.0"), "MÉDIO RISCO", "AQUISIÇÃO CONDICIONAL"),
    (Decimal("3.5"), "ALTO RISCO", "AQUISIÇÃO COM DESÁGIO AGRESSIVO"),
    (Decimal("0.0"), "RISCO CRÍTICO", "AQUISIÇÃO DESACONSELHADA"),
]


@dataclass
class Garantia:
    descricao: str
    valor: Decimal
    avaliacao_homologada: bool
    gravames_anteriores: Decimal = Decimal("0")

    @property
    def valor_liquido(self) -> Decimal:
        """Valor que sobra para o credor depois dos gravames de grau anterior."""
        return max(self.valor - self.gravames_anteriores, Decimal("0"))


@dataclass
class Vetor:
    codigo: str
    score: int
    justificativa: str
    fonte: str

    def __post_init__(self) -> None:
        if self.codigo not in PESOS:
            raise ValueError(f"Vetor desconhecido: {self.codigo}")
        if self.score not in SCORES_VALIDOS:
            raise ValueError(
                f"{self.codigo}: score {self.score} inválido, use 10, 7, 4 ou 1"
            )
        if not self.fonte.strip():
            raise ValueError(f"{self.codigo}: toda pontuação precisa de fonte nos autos")

    @property
    def subscore(self) -> Decimal:
        return Decimal(self.score) * PESOS[self.codigo]


@dataclass
class ResultadoIR:
    tcp: Decimal
    vetores: list[Vetor]
    ir: Decimal
    faixa: str
    conclusao_sugerida: str
    alertas: list[str] = field(default_factory=list)


def _duas_casas(valor: Decimal) -> Decimal:
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular_tcp(garantias: list[Garantia], divida_atualizada: Decimal) -> Decimal:
    """TCP = soma das garantias líquidas / dívida atualizada x 100."""
    if divida_atualizada <= 0:
        raise ValueError("A dívida atualizada precisa ser maior que zero")
    total = sum((g.valor_liquido for g in garantias), Decimal("0"))
    return _duas_casas(total / divida_atualizada * 100)


def classificar(ir: Decimal) -> tuple[str, str]:
    for minimo, faixa, conclusao in FAIXAS:
        if ir >= minimo:
            return faixa, conclusao
    raise ValueError(f"IR fora da escala: {ir}")


def calcular_ir(
    vetores: list[Vetor],
    garantias: list[Garantia],
    divida_atualizada: Decimal,
) -> ResultadoIR:
    """Calcula o TCP primeiro e depois o IR, na ordem exigida pelo modelo."""
    codigos = sorted(v.codigo for v in vetores)
    if codigos != sorted(PESOS):
        raise ValueError("Informe exatamente um score para cada vetor, de V1 a V6")

    tcp = calcular_tcp(garantias, divida_atualizada)
    ir = _duas_casas(sum((v.subscore for v in vetores), Decimal("0")))
    faixa, conclusao = classificar(ir)

    alertas = [
        f"Garantia sem avaliação homologada: {g.descricao}"
        for g in garantias
        if not g.avaliacao_homologada
    ]
    return ResultadoIR(tcp, vetores, ir, faixa, conclusao, alertas)
