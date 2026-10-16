-- =====================================================================
-- DADOS INICIAIS DE TESTE (SEED) - GINCANA TECNOLÓGICA JENPEX
-- =====================================================================

USE gincana_jenpex;

-- Limpeza prévia para testes
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE pontuacoes;
TRUNCATE TABLE provas;
TRUNCATE TABLE equipes;
TRUNCATE TABLE usuarios;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. Inserção de Equipes de Teste
INSERT INTO equipes (nome, curso_turma, cor_hex, lider, total_pontos) VALUES
('CyberPantanal', 'Técnico em Informática 3º Ano', '#3B82F6', 'Lucas Silva', 320),
('Binários do Cerrado', 'Técnico em Informática 2º Ano', '#10B981', 'Mariana Souza', 290),
('Algoritmos da Chapada', 'Bacharelado em Engenharia/Sistemas', '#F59E0B', 'Rafael Santos', 250),
('ByteMat Tech', 'Técnico em Redes 1º Ano', '#8B5CF6', 'Beatriz Lima', 210),
('Hackers do Vale', 'Tecnologia em Análise e Des. de Sistemas', '#EC4899', 'Gabriel Costa', 180),
('NullPointer Masters', 'Técnico em Informática 1º Ano', '#6366F1', 'Ana Clara Alves', 150);

-- 2. Inserção de Provas Típicas da Gincana
INSERT INTO provas (titulo, descricao, pontos_padrao, ativa) VALUES
('Quiz de Hardware & Arquitetura', 'Perguntas rápidas sobre componentes, barramentos e memórias.', 50, TRUE),
('Desafio de Robótica & Sensores', 'Percurso de robô seguidor de linha com obstáculos.', 100, TRUE),
('Caça ao Bug (Debugging Relâmpago)', 'Corrigir 3 erros de lógica de programação em menos de 10 minutos.', 80, TRUE),
('Arrecadação de Lixo Eletrônico', 'Pontuação baseada no peso de sucata eletrônica coletada.', 150, TRUE),
('Torta na Cara Tech', 'Batalha de perguntas e respostas sobre história da computação e tecnologia.', 60, TRUE);

-- 3. Inserção de Usuários Padrão (Jurados e Administradores)
-- Nota: Em produção usar hash bcrypt
INSERT INTO usuarios (nome, login, senha_hash, papel) VALUES
('Prof. Coordenador Jenpex', 'admin', 'admin123', 'admin'),
('Jurado 1 - Prova Robótica', 'jurado1', 'jurado123', 'jurado'),
('Jurado 2 - Prova Quiz', 'jurado2', 'jurado123', 'jurado');

-- 4. Inserção de Pontuações de Exemplo
INSERT INTO pontuacoes (equipe_id, prova_id, jurado_id, pontos, justificativa) VALUES
(1, 1, 2, 50, 'Gabaritou todas as questões do Quiz'),
(1, 2, 1, 100, 'Robô completou o trajeto sem colisões'),
(1, 3, 2, 80, 'Resolveu o desafio de debugging em 6 minutos'),
(1, 5, 1, 90, 'Vencedor do round final da Torta na Cara Tech'),
(2, 1, 2, 40, 'Errou apenas 1 pergunta no Quiz'),
(2, 2, 1, 100, 'Robô fez o menor tempo do percurso'),
(2, 4, 1, 150, 'Maior quantidade de pilhas e componentes arrecadados'),
(3, 2, 1, 80, 'Robô teve 1 penalidade mas concluiu'),
(3, 3, 2, 80, 'Debugging resolvido em 7 minutos'),
(3, 5, 1, 90, 'Bom desempenho na batalha de perguntas'),
(4, 1, 2, 30, 'Pontuação média no Quiz'),
(4, 3, 2, 80, 'Desafio de código concluído'),
(4, 2, 1, 100, 'Excelente apresentação do robô'),
(5, 4, 1, 150, 'Ótima arrecadação de sucata eletrônica'),
(5, 1, 2, 30, 'Pontuação no Quiz'),
(6, 1, 2, 50, 'Excelente no Quiz'),
(6, 3, 2, 100, 'Destaque no desafio de programação');

-- Sincronizar o total de pontos na tabela equipes com base nas pontuações inseridas
UPDATE equipes e
SET total_pontos = (
    SELECT COALESCE(SUM(p.pontos), 0)
    FROM pontuacoes p
    WHERE p.equipe_id = e.id
);
