# Sistema de Ranking em Tempo Real - Gincana Tecnológica JENPEX

Sistema oficial de placar eletrônico e ranking em tempo real para a Gincana Tecnológica da **JENPEX** (Jornada de Ensino, Pesquisa e Extensão).

O projeto é desenvolvido colaborativamente pelos alunos com orientação docente, utilizando uma arquitetura moderna e dividida em squads pedagógicos.

---

## 🎯 Objetivo do Projeto

Projetar em um **telão** o ranking das equipes participantes da gincana, atualizando posições e pontuações **instantaneamente** (sem necessidade de recarregar a página) conforme os jurados e organizadores lançam os pontos das provas.

---

## 🛠️ Tecnologias Escolhidas (Stack)

*   **Backend**: [Python 3.10+](https://www.python.org/) com [FastAPI](https://fastapi.tiangolo.com/)
    *   *Por que FastAPI?* Criação rápida de APIs REST com documentação interativa automática (`/docs` Swagger) e suporte nativo a **WebSockets** para tempo real.
*   **Banco de Dados**: [MySQL](https://www.mysql.com/)
    *   Modelo relacional simples, robusto e excelente para prática com SQL e ORM (SQLAlchemy).
*   **Frontend**: [Vue.js 3](https://vuejs.org/) + [Vite](https://vitejs.dev/)
    *   *Por que Vue.js?* Possui a curva de aprendizado mais amigável para estudantes. A estrutura de Componentes de Arquivo Único (`<template>`, `<script>`, `<style>`) consolida o aprendizado direto de HTML, JavaScript e CSS sem sobrecarga de configurações complexas.
*   **Comunicação em Tempo Real**: **WebSockets**
    *   Transmissão bidirecional de eventos: quando um ponto é inserido, o servidor avisa o telão imediatamente.

---

## 📂 Estrutura do Repositório

```text
Gincana_tecnologica/
├── .github/                     # Templates de Issues e Pull Requests para os alunos
│   ├── ISSUE_TEMPLATE/
│   └── pull_request_template.md
├── docs/                        # Documentação pedagógica e técnica
│   ├── ARQUITETURA.md           # Diagramas e fluxo de dados
│   ├── CRONOGRAMA_SPRINTS.md    # Rotina semanal até a Jenpex
│   └── DISTRIBUICAO_ALUNOS.md   # Squads e atribuições dos alunos
├── database/                    # Scripts do banco MySQL
│   ├── schema.sql               # Criação de tabelas
│   └── seed.sql                 # Dados de exemplo para testes
├── backend/                     # Código da API Python (FastAPI + WebSockets)
└── frontend/                    # Código da interface Vue.js (Telão + Painel do Jurado)
```

---

## 🚀 Como Executar o Projeto Localmente (Ambiente dos Alunos)

### 1. Pré-requisitos
*   [Git](https://git-scm.com/) instalado
*   [Python 3.10+](https://www.python.org/downloads/)
*   [Node.js (LTS v18 ou v20)](https://nodejs.org/)
*   [MySQL Server](https://dev.mysql.com/downloads/installer/) ou MariaDB / XAMPP

---

### 2. Passo a Passo do Banco de Dados
1. Abra seu cliente MySQL (Workbench, DBeaver, HeidiSQL ou terminal).
2. Execute o script [database/schema.sql](file:///c:/Users/ifmt/Desktop/Gincana_tecnologica/database/schema.sql) para criar o banco e as tabelas.
3. Execute o script [database/seed.sql](file:///c:/Users/ifmt/Desktop/Gincana_tecnologica/database/seed.sql) para inserir equipes de teste.

---

### 3. Passo a Passo do Backend (Python / FastAPI)
```bash
# Entre na pasta backend
cd backend

# Crie o ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# No Windows:
.\venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Inicie o servidor em modo de desenvolvimento
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
> 💡 Acesse a documentação interativa em: `http://localhost:8000/docs`

---

### 4. Passo a Passo do Frontend (Vue.js)
```bash
# Abra outro terminal e entre na pasta frontend
cd frontend

# Instale as dependências
npm install

# Inicie o servidor de desenvolvimento
npm run dev
```
> 💡 Acesse o projeto em: `http://localhost:5173`
> - Telão do Ranking: `http://localhost:5173/telao`
> - Lançador de Notas: `http://localhost:5173/admin`

---

## 🤝 Fluxo de Trabalho e Regras do Git

Para simular o ambiente profissional de desenvolvimento, todos os alunos seguem as seguintes convenções:

1. **Nunca commitar direto na branch `main`!**
2. Crie uma branch para cada tarefa seguindo o padrão:
   - `feat/squad-backend-cadastro-equipes`
   - `feat/squad-telao-animacao-podio`
   - `fix/squad-admin-validacao-pontos`
3. Ao finalizar, abra um **Pull Request (PR)** apontando para a branch `develop`.
4. O PR deve ser revisado por pelo menos 1 colega de equipe e aprovado pelo professor antes do merge.

Veja o guia completo em [CONTRIBUTING.md](file:///c:/Users/ifmt/Desktop/Gincana_tecnologica/CONTRIBUTING.md).

---

## 👥 Organização das Equipes

O projeto é dividido em 4 Squads:
*   🟢 **Squad 1: Backend & Banco de Dados** (FastAPI, MySQL, Modelagem e WebSocket)
*   🟣 **Squad 2: Frontend Telão** (Interface comemorativa, Ranking em tempo real, Efeitos sonoros/visuais)
*   🔵 **Squad 3: Frontend Painel Jurados/Admin** (Formulário ágil de lançamento, autenticação, histórico)
*   🟠 **Squad 4: DevOps, Redes & QA** (Testes, Rede local para o telão, Projeção e Git)

Detalhes completos em [docs/DISTRIBUICAO_ALUNOS.md](file:///c:/Users/ifmt/Desktop/Gincana_tecnologica/docs/DISTRIBUICAO_ALUNOS.md).
