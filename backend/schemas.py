from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# ----------------- EQUIPES -----------------
class EquipeBase(BaseModel):
    nome: str = Field(..., example="CyberPantanal")
    curso_turma: str = Field(..., example="Técnico em Informática 3º Ano")
    cor_hex: str = Field("#3B82F6", example="#3B82F6")
    lider: Optional[str] = Field(None, example="Lucas Silva")

class EquipeCreate(EquipeBase):
    pass

class EquipeResponse(EquipeBase):
    id: int
    total_pontos: int
    criado_em: datetime

    class Config:
        from_attributes = True


# ----------------- PROVAS -----------------
class ProvaBase(BaseModel):
    titulo: str = Field(..., example="Quiz de Hardware & Redes")
    descricao: Optional[str] = Field(None, example="Perguntas rápidas sobre arquitetura")
    pontos_padrao: int = Field(50, example=50)
    ativa: bool = True

class ProvaCreate(ProvaBase):
    pass

class ProvaResponse(ProvaBase):
    id: int
    criado_em: datetime

    class Config:
        from_attributes = True


# ----------------- PONTUAÇÕES -----------------
class PontuacaoCreate(BaseModel):
    equipe_id: int = Field(..., example=1)
    prova_id: int = Field(..., example=2)
    pontos: int = Field(..., example=50)
    justificativa: Optional[str] = Field(None, example="Primeiro lugar no percurso do robô")
    jurado_id: Optional[int] = Field(None, example=1)

class PontuacaoResponse(BaseModel):
    id: int
    equipe_id: int
    prova_id: int
    pontos: int
    justificativa: Optional[str]
    criado_em: datetime

    class Config:
        from_attributes = True


# ----------------- RANKING (TELÃO) -----------------
class RankingItemResponse(BaseModel):
    posicao: int
    id: int
    nome: str
    curso_turma: str
    cor_hex: str
    total_pontos: int
    ultima_atualizacao: Optional[datetime] = None

class RankingResponse(BaseModel):
    total_equipes: int
    atualizado_em: datetime
    ranking: List[RankingItemResponse]
