-- =====================================================================
-- SISTEMA DE RANKING EM TEMPO REAL - GINCANA TECNOLÓGICA JENPEX
-- Script de Criação do Banco de Dados e Tabelas (MySQL 8.0+)
-- =====================================================================

CREATE DATABASE IF NOT EXISTS gincana_jenpex
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE gincana_jenpex;

-- 1. TABELA DE EQUIPES
CREATE TABLE IF NOT EXISTS equipes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    curso_turma VARCHAR(100) NOT NULL,
    cor_hex VARCHAR(7) NOT NULL DEFAULT '#3B82F6', -- Ex: #EF4444, #10B981
    lider VARCHAR(100),
    total_pontos INT NOT NULL DEFAULT 0,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. TABELA DE PROVAS E DESAFIOS
CREATE TABLE IF NOT EXISTS provas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(120) NOT NULL,
    descricao TEXT,
    pontos_padrao INT NOT NULL DEFAULT 50,
    ativa BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 3. TABELA DE USUÁRIOS (ADMINISTRADORES E JURADOS)
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    login VARCHAR(50) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    papel ENUM('admin', 'jurado') NOT NULL DEFAULT 'jurado',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 4. TABELA DE HISTÓRICO DE PONTUAÇÕES
CREATE TABLE IF NOT EXISTS pontuacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    equipe_id INT NOT NULL,
    prova_id INT NOT NULL,
    jurado_id INT NULL,
    pontos INT NOT NULL,
    justificativa VARCHAR(255),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pontuacoes_equipe
        FOREIGN KEY (equipe_id) REFERENCES equipes(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_pontuacoes_prova
        FOREIGN KEY (prova_id) REFERENCES provas(id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_pontuacoes_jurado
        FOREIGN KEY (jurado_id) REFERENCES usuarios(id)
        ON DELETE SET NULL
) ENGINE=InnoDB;

-- 5. VIEW CONSOLIDADA PARA O RANKING EM TEMPO REAL
CREATE OR REPLACE VIEW view_ranking AS
SELECT 
    e.id,
    e.nome,
    e.curso_turma,
    e.cor_hex,
    COALESCE(SUM(p.pontos), 0) AS total_pontos,
    COUNT(p.id) AS total_provas_concluidas,
    MAX(p.criado_em) AS ultimo_ponto_em
FROM equipes e
LEFT JOIN pontuacoes p ON e.id = p.equipe_id
GROUP BY e.id, e.nome, e.curso_turma, e.cor_hex
ORDER BY total_pontos DESC, ultimo_ponto_em ASC;
