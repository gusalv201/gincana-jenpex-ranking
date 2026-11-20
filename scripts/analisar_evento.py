#!/usr/bin/env python3
"""Calcula as estatísticas da gincana a partir do arquivo exportado no Admin.

    python scripts/analisar_evento.py caminho/jenpex-dados-AAAAMMDD-HHMM.json

Imprime um JSON com os indicadores (participação, top 10, tempos por jogo,
tempo de permanência dos alunos, linha do tempo). Usa só a biblioteca padrão.

Observação sobre os tempos: o sistema registra apenas o horário em que cada
nota foi lançada. Por isso os tempos são ESTIMATIVAS:
- "tempo por rodada" de um jogo = intervalo entre duas notas seguidas na
  mesma mesa (intervalos acima de PAUSA_MIN são tratados como pausa e ignorados);
- "permanência" de um aluno = do 1º ao último jogo dele (só quem fez 2+ jogos).
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo

    FUSO = ZoneInfo("America/Cuiaba")  # Campo Novo do Parecis (MT)
except Exception:  # sem base de fusos no Windows: usa UTC-4 fixo
    FUSO = timezone(timedelta(hours=-4))

PAUSA_MIN = 30
JANELA_MIN = 30


def minutos(segundos: float | None) -> float | None:
    return None if segundos is None else round(segundos / 60, 1)


def resumo(valores: list[float]) -> dict:
    if not valores:
        return {"n": 0}
    return {
        "n": len(valores),
        "media": round(statistics.mean(valores), 1),
        "mediana": round(statistics.median(valores), 1),
        "min": round(min(valores), 1),
        "max": round(max(valores), 1),
    }


def main(caminho: str) -> None:
    dados = json.load(open(caminho, encoding="utf-8"))
    jogos = {g["id"]: g for g in dados["games"]}
    alunos = {p["id"]: p for p in dados["participants"]}
    notas = []
    for s in dados["scores"]:
        if s["participant_id"] not in alunos or s["game_id"] not in jogos:
            continue
        notas.append({**s, "t": datetime.fromisoformat(s["created_at"]).astimezone(FUSO)})
    notas.sort(key=lambda s: s["t"])

    jogos_ativos = [g for g in dados["games"] if g["is_active"]]
    ids_ativos = {g["id"] for g in jogos_ativos}
    alunos_ativos = [p for p in dados["participants"] if p["is_active"]]

    por_aluno: dict[int, list[dict]] = defaultdict(list)
    por_jogo: dict[int, list[dict]] = defaultdict(list)
    for s in notas:
        por_aluno[s["participant_id"]].append(s)
        por_jogo[s["game_id"]].append(s)

    # ---------------- participação
    qtd_jogos = {p["id"]: len({s["game_id"] for s in por_aluno[p["id"]] if s["game_id"] in ids_ativos})
                 for p in alunos_ativos}
    distribuicao = Counter(qtd_jogos.values())
    jogaram = [pid for pid, q in qtd_jogos.items() if q > 0]
    todos = [pid for pid, q in qtd_jogos.items() if ids_ativos and q == len(ids_ativos)]

    # ---------------- ranking (mesmo critério do sistema)
    totais = {p["id"]: sum(s["points"] for s in por_aluno[p["id"]]) for p in alunos_ativos}
    ordem = sorted(alunos_ativos, key=lambda p: (-totais[p["id"]], p["id"]))
    top10 = [
        {
            "posicao": i,
            "nome": p["username"],
            "codigo": p["participant_code"],
            "total": totais[p["id"]],
            "jogos": len(por_aluno[p["id"]]),
            "por_jogo": {jogos[s["game_id"]]["name"]: s["points"] for s in por_aluno[p["id"]]},
        }
        for i, p in enumerate(ordem[:10], start=1)
    ]

    # ---------------- por jogo
    por_jogo_saida = []
    todos_intervalos = []
    for g in dados["games"]:
        lista = por_jogo.get(g["id"], [])
        intervalos = [
            (b["t"] - a["t"]).total_seconds()
            for a, b in zip(lista, lista[1:])
            if 0 < (b["t"] - a["t"]).total_seconds() <= PAUSA_MIN * 60
        ]
        todos_intervalos += intervalos
        duracao = (lista[-1]["t"] - lista[0]["t"]).total_seconds() if len(lista) > 1 else None
        por_jogo_saida.append({
            "jogo": g["name"],
            "chefe": g["master"],
            "ativo": g["is_active"],
            "participantes": len(lista),
            "pct_dos_alunos": round(100 * len(lista) / len(alunos_ativos), 1) if alunos_ativos else 0,
            "pontos": resumo([s["points"] for s in lista]),
            "primeira_nota": lista[0]["t"].strftime("%H:%M") if lista else None,
            "ultima_nota": lista[-1]["t"].strftime("%H:%M") if lista else None,
            "minutos_em_operacao": minutos(duracao),
            "min_por_rodada": resumo([x / 60 for x in intervalos]),
            "alunos_por_hora": round(len(lista) / (duracao / 3600), 1) if duracao else None,
        })

    # ---------------- tempo dos alunos
    permanencia, entre_jogos = [], []
    for pid, lista in por_aluno.items():
        if len(lista) >= 2:
            permanencia.append((lista[-1]["t"] - lista[0]["t"]).total_seconds() / 60)
            entre_jogos += [(b["t"] - a["t"]).total_seconds() / 60 for a, b in zip(lista, lista[1:])]

    # ---------------- linha do tempo
    linha = Counter()
    for s in notas:
        t = s["t"]
        inicio = t.replace(minute=(t.minute // JANELA_MIN) * JANELA_MIN, second=0, microsecond=0)
        linha[inicio] += 1
    linha_saida = [{"inicio": k.strftime("%d/%m %H:%M"), "notas": v} for k, v in sorted(linha.items())]
    pico = max(linha_saida, key=lambda x: x["notas"]) if linha_saida else None

    pontos = [s["points"] for s in notas]
    saida = {
        "gerado_em": dados.get("generated_at"),
        "evento": {
            "primeira_nota": notas[0]["t"].strftime("%d/%m/%Y %H:%M") if notas else None,
            "ultima_nota": notas[-1]["t"].strftime("%d/%m/%Y %H:%M") if notas else None,
            "duracao_horas": round((notas[-1]["t"] - notas[0]["t"]).total_seconds() / 3600, 2) if len(notas) > 1 else None,
            "jogos_cadastrados": len(dados["games"]),
            "jogos_ativos": len(jogos_ativos),
            "chefes_de_mesa": dados.get("staff", {}).get("table_masters"),
            "equipe_recepcao": dados.get("staff", {}).get("reception"),
        },
        "participacao": {
            "alunos_cadastrados": len(dados["participants"]),
            "alunos_ativos": len(alunos_ativos),
            "jogaram_ao_menos_1": len(jogaram),
            "nao_jogaram": len(alunos_ativos) - len(jogaram),
            "jogaram_todos_os_jogos": len(todos),
            "pct_jogaram": round(100 * len(jogaram) / len(alunos_ativos), 1) if alunos_ativos else 0,
            "pct_todos": round(100 * len(todos) / len(alunos_ativos), 1) if alunos_ativos else 0,
            "media_jogos_por_aluno_que_jogou": round(statistics.mean([qtd_jogos[p] for p in jogaram]), 2) if jogaram else 0,
            "distribuicao_qtd_jogos": {str(k): distribuicao[k] for k in sorted(distribuicao)},
            "nomes_que_jogaram_todos": [alunos[p]["username"] for p in todos],
        },
        "notas": {
            "total_lancadas": len(notas),
            "pontos_distribuidos": sum(pontos),
            "pontos_por_nota": resumo(pontos),
            "pontuacao_total_por_aluno": resumo([totais[p] for p in jogaram]),
        },
        "tempos_estimados_min": {
            "por_rodada_todas_as_mesas": resumo([x / 60 for x in todos_intervalos]),
            "permanencia_do_aluno_1o_ao_ultimo_jogo": resumo(permanencia),
            "intervalo_entre_jogos_do_aluno": resumo(entre_jogos),
        },
        "top10": top10,
        "por_jogo": sorted(por_jogo_saida, key=lambda x: -x["participantes"]),
        "linha_do_tempo_30min": linha_saida,
        "pico": pico,
    }
    json.dump(saida, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
