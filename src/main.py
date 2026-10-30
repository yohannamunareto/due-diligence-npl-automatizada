"""Executa o cálculo do IR para um caso em JSON e imprime o resumo.

Uso: python src/main.py data/caso_ficticio.json
"""

import json
import sys
from decimal import Decimal
from pathlib import Path

from indice_recuperabilidade import Garantia, Vetor, calcular_ir


def carregar_caso(caminho: Path):
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    garantias = [
        Garantia(
            descricao=g["descricao"],
            valor=Decimal(g["valor"]),
            avaliacao_homologada=g["avaliacao_homologada"],
            gravames_anteriores=Decimal(g.get("gravames_anteriores", "0")),
        )
        for g in dados["garantias"]
    ]
    vetores = [Vetor(**v) for v in dados["vetores"]]
    return dados, garantias, vetores


def formatar_reais(valor: Decimal) -> str:
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def main() -> None:
    caminho = Path(sys.argv[1] if len(sys.argv) > 1 else "data/caso_ficticio.json")
    dados, garantias, vetores = carregar_caso(caminho)
    divida = Decimal(dados["divida_atualizada"])
    resultado = calcular_ir(vetores, garantias, divida)

    print(f"Processo: {dados['processo']} ({dados['tipo_de_feito']})")
    print(f"Dívida atualizada: {formatar_reais(divida)} (data-base {dados['data_base']})")
    print(f"TCP: {str(resultado.tcp).replace('.', ',')}%\n")
    print("Vetor  Score  Peso  Subscore  Fonte")
    for v in resultado.vetores:
        peso = int(Decimal(v.subscore / v.score) * 100)
        print(f"{v.codigo:<6} {v.score:>5}  {peso:>3}%  {v.subscore:>8.2f}  {v.fonte}")
    print(f"\nIR: {str(resultado.ir).replace('.', ',')} | {resultado.faixa}")
    print(f"Conclusão sugerida: {resultado.conclusao_sugerida}")
    for alerta in resultado.alertas:
        print(f"Alerta: {alerta}")


if __name__ == "__main__":
    main()
