from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from database import Base

class Equipe(Base):
    __tablename__ = "equipes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), unique=True, nullable=False, index=True)
    curso_turma = Column(String(100), nullable=False)
    cor_hex = Column(String(7), nullable=False, default="#3B82F6")
    lider = Column(String(100), nullable=True)
    total_pontos = Column(Integer, nullable=False, default=0)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamento com as pontuações
    pontuacoes = relationship("Pontuacao", back_populates="equipe", cascade="all, delete-orphan")


class Prova(Base):
    __tablename__ = "provas"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(120), nullable=False)
    descricao = Column(Text, nullable=True)
    pontos_padrao = Column(Integer, nullable=False, default=50)
    ativa = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    pontuacoes = relationship("Pontuacao", back_populates="prova")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    login = Column(String(50), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    papel = Column(Enum("admin", "jurado", name="papel_usuario"), nullable=False, default="jurado")
    criado_em = Column(DateTime, default=datetime.utcnow)

    pontuacoes = relationship("Pontuacao", back_populates="jurado")


class Pontuacao(Base):
    __tablename__ = "pontuacoes"

    id = Column(Integer, primary_key=True, index=True)
    equipe_id = Column(Integer, ForeignKey("equipes.id", ondelete="CASCADE"), nullable=False)
    prova_id = Column(Integer, ForeignKey("provas.id", ondelete="RESTRICT"), nullable=False)
    jurado_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    pontos = Column(Integer, nullable=False)
    justificativa = Column(String(255), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    equipe = relationship("Equipe", back_populates="pontuacoes")
    prova = relationship("Prova", back_populates="pontuacoes")
    jurado = relationship("Usuario", back_populates="pontuacoes")
