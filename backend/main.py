from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc

import models
import schemas
from database import engine, get_db, Base
from websocket_manager import ws_manager

# Cria tabelas caso ainda não existam (útil para desenvolvimento rápido)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"⚠️ Aviso ao conectar no banco na inicialização: {e}")
    print("👉 Certifique-se de executar 'database/schema.sql' no seu MySQL!")

app = FastAPI(
    title="🏆 API de Ranking em Tempo Real - JENPEX",
    description="Backend oficial da Gincana Tecnológica desenvolvido com FastAPI, MySQL e WebSockets.",
    version="1.0.0"
)

# Configuração de CORS para permitir acesso de qualquer navegador na rede local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------
# FUNÇÕES AUXILIARES
# -------------------------------------------------------------
def calcular_ranking(db: Session) -> schemas.RankingResponse:
    """Calcula e formata o ranking atualizado com as posições ordenadas."""
    equipes = db.query(models.Equipe).order_by(
        desc(models.Equipe.total_pontos),
        models.Equipe.atualizado_em.asc()
    ).all()

    ranking_itens = []
    for index, eq in enumerate(equipes, start=1):
        ranking_itens.append(schemas.RankingItemResponse(
            posicao=index,
            id=eq.id,
            nome=eq.nome,
            curso_turma=eq.curso_turma,
            cor_hex=eq.cor_hex,
            total_pontos=eq.total_pontos,
            ultima_atualizacao=eq.atualizado_em
        ))

    return schemas.RankingResponse(
        total_equipes=len(ranking_itens),
        atualizado_em=datetime.utcnow(),
        ranking=ranking_itens
    )


# -------------------------------------------------------------
# ROTAS PÚBLICAS E HEALTH CHECK
# -------------------------------------------------------------
@app.get("/", tags=["Geral"])
def root():
    return {
        "status": "online",
        "evento": "Gincana Tecnológica JENPEX",
        "docs_url": "/docs",
        "telao_websocket": "/ws/ranking"
    }

@app.get("/api/health", tags=["Geral"])
def health_check(db: Session = Depends(get_db)):
    try:
        # Testa a conectividade com o banco
        db.execute(models.Equipe.__table__.select().limit(1))
        return {"banco": "conectado", "status": "ok"}
    except Exception as e:
        return {"banco": "erro_conexao", "detalhe": str(e), "status": "alerta"}


# -------------------------------------------------------------
# ROTAS DE EQUIPES
# -------------------------------------------------------------
@app.get("/api/equipes", response_model=List[schemas.EquipeResponse], tags=["Equipes"])
def listar_equipes(db: Session = Depends(get_db)):
    """Retorna todas as equipes cadastradas."""
    return db.query(models.Equipe).all()

@app.post("/api/equipes", response_model=schemas.EquipeResponse, status_code=201, tags=["Equipes"])
def cadastrar_equipe(equipe: schemas.EquipeCreate, db: Session = Depends(get_db)):
    """Cadastra uma nova equipe participante da gincana."""
    existente = db.query(models.Equipe).filter(models.Equipe.nome == equipe.nome).first()
    if existente:
        raise HTTPException(status_code=400, detail="Já existe uma equipe com este nome.")

    nova_equipe = models.Equipe(**equipe.model_dump())
    db.add(nova_equipe)
    db.commit()
    db.refresh(nova_equipe)
    return nova_equipe


# -------------------------------------------------------------
# ROTAS DE PROVAS
# -------------------------------------------------------------
@app.get("/api/provas", response_model=List[schemas.ProvaResponse], tags=["Provas"])
def listar_provas(db: Session = Depends(get_db)):
    """Retorna todas as provas cadastradas para a gincana."""
    return db.query(models.Prova).filter(models.Prova.ativa == True).all()

@app.post("/api/provas", response_model=schemas.ProvaResponse, status_code=201, tags=["Provas"])
def cadastrar_prova(prova: schemas.ProvaCreate, db: Session = Depends(get_db)):
    """Cadastra uma nova prova ou desafio."""
    nova_prova = models.Prova(**prova.model_dump())
    db.add(nova_prova)
    db.commit()
    db.refresh(nova_prova)
    return nova_prova


# -------------------------------------------------------------
# ROTAS DE PONTUAÇÃO & RANKING (O CORAÇÃO DO SISTEMA)
# -------------------------------------------------------------
@app.get("/api/ranking", response_model=schemas.RankingResponse, tags=["Ranking"])
def obter_ranking(db: Session = Depends(get_db)):
    """Retorna a classificação geral atualizada das equipes."""
    return calcular_ranking(db)

@app.post("/api/pontuacoes", response_model=schemas.PontuacaoResponse, status_code=201, tags=["Pontuações"])
async def lancar_pontuacao(pontuacao_in: schemas.PontuacaoCreate, db: Session = Depends(get_db)):
    """
    Lança pontos para uma equipe.
    Automaticamente:
    1. Grava no histórico de pontuações
    2. Atualiza a pontuação total da equipe
    3. Notifica todas as telas do Telão via WebSocket em tempo real!
    """
    equipe = db.query(models.Equipe).filter(models.Equipe.id == pontuacao_in.equipe_id).first()
    if not equipe:
        raise HTTPException(status_code=404, detail="Equipe não encontrada.")

    prova = db.query(models.Prova).filter(models.Prova.id == pontuacao_in.prova_id).first()
    if not prova:
        raise HTTPException(status_code=404, detail="Prova não encontrada.")

    # 1. Cria o registro histórico
    nova_pontuacao = models.Pontuacao(
        equipe_id=pontuacao_in.equipe_id,
        prova_id=pontuacao_in.prova_id,
        jurado_id=pontuacao_in.jurado_id,
        pontos=pontuacao_in.pontos,
        justificativa=pontuacao_in.justificativa
    )
    db.add(nova_pontuacao)

    # 2. Atualiza a pontuação da equipe
    equipe.total_pontos += pontuacao_in.pontos
    equipe.atualizado_em = datetime.utcnow()

    db.commit()
    db.refresh(nova_pontuacao)

    # 3. Dispara Broadcast via WebSocket para todos os telões conectados
    ranking_atualizado = calcular_ranking(db)
    payload_ws = {
        "evento": "PONTOS_ATUALIZADOS",
        "equipe_nome": equipe.nome,
        "pontos_adicionados": pontuacao_in.pontos,
        "prova_titulo": prova.titulo,
        "ranking": ranking_atualizado.model_dump(mode="json")
    }
    await ws_manager.broadcast(payload_ws)

    return nova_pontuacao

@app.get("/api/pontuacoes/historico", tags=["Pontuações"])
def historico_pontuacoes(limite: int = 20, db: Session = Depends(get_db)):
    """Retorna os últimos lançamentos de pontos realizados."""
    return db.query(models.Pontuacao).order_by(desc(models.Pontuacao.criado_em)).limit(limite).all()


# -------------------------------------------------------------
# WEBSOCKET EM TEMPO REAL (CANAL DO TELÃO)
# -------------------------------------------------------------
@app.websocket("/ws/ranking")
async def websocket_ranking(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    Canal de comunicação bidirecional contínuo.
    O telão se conecta aqui para receber atualizações sem refresh.
    """
    await ws_manager.connect(websocket)

    # Ao conectar, envia imediatamente o estado atual do ranking
    ranking_inicial = calcular_ranking(db)
    await websocket.send_json({
        "evento": "CONEXAO_ESTABELECIDA",
        "ranking": ranking_inicial.model_dump(mode="json")
    })

    try:
        while True:
            # Mantém a conexão aberta escutando eventuais pings do front
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
