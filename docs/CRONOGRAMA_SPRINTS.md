# 📅 Cronograma de Sprints e Rotina de Tarefas - Rumo à JENPEX

Este cronograma foi desenhado em **4 Sprints Semanais** de metodologia ágil adaptada à sala de aula. Cada semana entrega uma versão funcional e visualmente testável do software.

---

## 🧭 Visão Geral do Calendário

| Sprint | Período | Foco Principal | Meta Visual / Entregável |
| :--- | :--- | :--- | :--- |
| **Sprint 1** | Semana 1 | Fundação & Arquitetura | Banco rodando, Git configurado, Swagger `/docs` e Telão com dados mockados |
| **Sprint 2** | Semana 2 | CRUDs & Integração Básica | Painel cadastra equipes no MySQL e lista no Telão via API REST |
| **Sprint 3** | Semana 3 | Tempo Real (WebSockets) & Efeitos | Jurado lança nota e o Telão atualiza sozinho com animação e som |
| **Sprint 4** | Semana 4 | Testes de Carga, Ensaio Geral & Deploy | Simulação com 100% dos alunos, teste no projetor/auditório e backup |

---

## 🚀 Detalhamento das Sprints

### 🟢 SPRINT 1: Fundação, Setup e Primeiras Telas
*Objetivo: Todos os alunos com ambiente configurado e primeiros componentes rodando.*

- **Backend (Squad 1)**:
  - Criar o banco MySQL executando o script `database/schema.sql`.
  - Configurar projeto FastAPI com SQLAlchemy.
  - Criar rota `GET /api/health` e `GET /api/equipes` com dados de teste.
  - Testar a documentação Swagger em `http://localhost:8000/docs`.
- **Frontend Telão (Squad 2)**:
  - Iniciar projeto Vue.js com Vite.
  - Desenhar o layout do Telão em tela cheia (modo escuro de alto contraste para projetor).
  - Exibir tabela mockada com 5 equipes, cores e pontuações fictícias.
- **Frontend Admin (Squad 3)**:
  - Criar página inicial do painel com abas simples: *Equipes*, *Provas* e *Lançar Pontos*.
  - Criar formulário HTML com validação básica.
- **DevOps & QA (Squad 4)**:
  - Criar o repositório no GitHub e convidar os alunos.
  - Configurar as branches `main` e `develop`.
  - Validar se todos os alunos conseguem clonar o repositório e rodar o projeto.

---

### 🟣 SPRINT 2: Integração REST e Persistência no MySQL
*Objetivo: Lançamento de dados pelo frontend gravando de verdade no banco de dados.*

- **Backend (Squad 1)**:
  - Criar endpoints de cadastro e listagem: `POST /api/equipes`, `POST /api/provas`.
  - Criar endpoint `POST /api/pontuacoes` com gravação na tabela histórica.
  - Implementar cálculo da soma total de pontos ordenado decrescente: `GET /api/ranking`.
- **Frontend Telão (Squad 2)**:
  - Conectar o Telão ao backend via `fetch` / `axios` para carregar o ranking real do banco.
  - Adicionar cards visuais com destaque para o **Top 3 (Ouro, Prata, Bronze)**.
- **Frontend Admin (Squad 3)**:
  - Formulário funcional que envia equipes e provas para o backend.
  - Tela de lançamento rápido: Select de Equipe + Select de Prova + Input de Pontos + Botão Enviar.
- **DevOps & QA (Squad 4)**:
  - Testar todas as rotas no Swagger e registrar bugs no GitHub Issues.
  - Criar dados de teste realistas no banco (nomes das turmas/cursos do IFMT).

---

### ⚡ SPRINT 3: Tempo Real (WebSockets), Gamificação e Polimento
*Objetivo: Telão autônomo e dinâmico, sem F5!*

- **Backend (Squad 1)**:
  - Implementar o `ConnectionManager` de WebSockets no FastAPI (`/ws/ranking`).
  - Ao salvar uma pontuação em `POST /api/pontuacoes`, disparar broadcast para todos os clientes conectados.
- **Frontend Telão (Squad 2)**:
  - Conectar o Telão ao WebSocket com reconexão automática.
  - Implementar animações CSS / Vue Transition Group para as equipes trocarem de posição de forma fluida.
  - Adicionar efeitos sonoros (opcional com botão mute): sino ao pontuar, fanfarra ao mudar o 1º lugar.
  - Modo telão com botão de tela cheia (F11).
- **Frontend Admin (Squad 3)**:
  - Toast de confirmação ("Pontos enviados com sucesso para a Equipe X!").
  - Histórico dos últimos 5 lançamentos com botão para estornar/cancelar em caso de erro do jurado.
- **DevOps & QA (Squad 4)**:
  - Testar múltiplos dispositivos abrindo o Telão ao mesmo tempo.
  - Testar a estabilidade do WebSocket com desconexões propositais de cabo/Wi-Fi.

---

### 🏆 SPRINT 4: Ensaio Geral, Rede Local e Dia do Evento
*Objetivo: Garantir que nada quebre na hora da Gincana da Jenpex.*

- **Backend & Banco (Squad 1)**:
  - Criar script de backup automático do MySQL a cada 10 minutos.
  - Endpoint de "Zerar Placar" com senha de segurança para a largada da gincana.
- **Frontend Telão (Squad 2)**:
  - Testar resolução e contraste no projetor real onde será exibido.
  - Ajustar tamanho das fontes para leitura a 15 metros de distância.
- **Frontend Admin (Squad 3)**:
  - Testar usabilidade em celulares dos jurados (responsividade).
- **DevOps & QA (Squad 4)**:
  - Configurar servidor na rede local do IFMT (IP fixo para que jurados acessem via Wi-Fi do campus).
  - **Ensaio Geral (Simulação)**: Rodar uma gincana fictícia de 30 minutos em sala de aula.
  - Preparar plano de contingência (roteador próprio caso a rede do campus fique instável).

---

## ⏱️ Rotina Semanal de Comunicação (Cerimônias Ágeis)

Para manter os alunos engajados sem sobrecarregar as aulas:

1. **Kickoff da Sprint (Início da semana - 20 min)**:
   - Professor apresenta as metas da semana e divide as tarefas no GitHub Projects.
2. **Check-in Rápido / Daily (Início de cada aula - 10 min)**:
   - Cada squad responde:
     1. *O que fiz desde a última aula?*
     2. *O que vou fazer hoje?*
     3. *Tem algum impedimento travando meu squad?*
3. **Demo & Retrospectiva (Fim da semana - 20 min)**:
   - Telão é projetado na sala para todos verem a evolução coletiva do sistema.
   - Aplausos para as entregas e ajustes para a próxima sprint.
