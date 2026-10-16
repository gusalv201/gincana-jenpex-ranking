# 👥 Distribuição de Tarefas e Squads Pedagógicos

Para que todos os alunos participem ativamente e aprendam na prática, a turma será dividida em **4 Squads Multidisciplinares**. Cada squad possui objetivos claros e tecnologias específicas.

---

## 🎯 Mapa dos Squads

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   SISTEMA DE RANKING JENPEX                            │
├────────────────────┬───────────────────┬───────────────────────────────┤
│ 🟢 SQUAD 1         │ 🟣 SQUAD 2        │ 🔵 SQUAD 3                    │
│ Backend & MySQL    │ Frontend Telão    │ Frontend Admin/Jurados        │
│ (Python + FastAPI) │ (Vue.js + CSS)    │ (Vue.js + Formulários)        │
├────────────────────┴───────────────────┴───────────────────────────────┤
│ 🟠 SQUAD 4                                                             │
│ DevOps, Redes, QA & Infraestrutura do Telão                            │
│ (Git, Docker/LAN, Testes de Integração, Resolução de Problemas)        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🟢 SQUAD 1: Backend & Banco de Dados (Python & MySQL)

*Perfil ideal: Alunos que gostam de lógica de programação, dados, regras de negócio e APIs.*

### 🛠️ Tecnologias
- Python 3.10+
- FastAPI (Framework web)
- SQLAlchemy / PyMySQL (Acesso ao MySQL)
- WebSockets (Comunicação em tempo real)

### 📌 Atribuições do Squad
1. Criar e manter o esquema do banco de dados MySQL (`database/schema.sql`).
2. Criar os endpoints REST no FastAPI (cadastro de equipes, provas e pontuações).
3. Implementar a lógica que soma os pontos e devolve o ranking ordenado por posição.
4. Implementar a transmissão via WebSocket quando uma nova pontuação for inserida.
5. Garantir que a documentação interativa Swagger (`/docs`) esteja sempre atualizada.

---

## 🟣 SQUAD 2: Frontend Telão & Gamificação (Vue.js & Design)

*Perfil ideal: Alunos com interesse em design, interfaces visuais, CSS, animações e experiência do usuário (UX).*

### 🛠️ Tecnologias
- Vue.js 3 (Composition API)
- CSS Moderno (Glassmorphism, gradientes e transições fluidas)
- WebSocket Client (Nativo do navegador)
- Biblioteca de Som / Web Audio API

### 📌 Atribuições do Squad
1. Desenhar a interface de impacto para exibição em telão/projetor de alta resolução.
2. Criar cards para as equipes com cores customizadas, logotipo e total de pontos.
3. Criar a visualização especial para o **Pódio (1º, 2º e 3º lugares)**.
4. Integrar o WebSocket para escutar atualizações e animar a reordenação das equipes na tela (efeito visual de ultrapassagem).
5. Adicionar efeitos especiais (sons comemorativos, confetes ao anunciar o campeão).
6. Implementar botão de tela cheia (modo apresentação).

---

## 🔵 SQUAD 3: Frontend Painel do Jurado / Admin (Vue.js & Usabilidade)

*Perfil ideal: Alunos focados em desenvolvimento web prático, formulários, validações e usabilidade mobile.*

### 🛠️ Tecnologias
- Vue.js 3
- HTML Semântico & CSS Responsivo (Mobile-First para celular)
- Axios / Fetch API

### 📌 Atribuições do Squad
1. Criar interface limpa e rápida para ser usada no celular ou notebook pelos jurados.
2. Tela de lançamento de notas:
   - Seleção rápida da Equipe.
   - Seleção da Prova da gincana.
   - Campo numérico de pontos com botões de atalho (+10, +50, +100).
   - Campo opcional de justificativa/observação.
3. Criar tela de histórico de lançamentos com opção de cancelar lançamentos errados.
4. Criar tela administrativa para cadastrar novas equipes e provas em tempo real durante o evento.

---

## 🟠 SQUAD 4: DevOps, Redes, QA & Infraestrutura (Qualidade e Operação)

*Perfil ideal: Alunos com perfil analítico, interesse em redes de computadores, testes, Git e suporte no dia do evento.*

### 🛠️ Tecnologias
- Git & GitHub (Gerenciamento de branches, PRs e Issues)
- Redes locais (Wi-Fi, IP local, portas de firewall, roteador)
- Postman / Thunder Client / Insomnia (Testes de API)

### 📌 Atribuições do Squad
1. Manter a integridade do repositório no GitHub (ajudar colegas com conflitos de Git).
2. Testar todos os endpoints e telas antes dos merges para `develop` e `main`.
3. Simular cenários de falha (queda de internet, envio de pontos simultâneos por 5 jurados ao mesmo tempo).
4. Configurar a rede local no dia da Jenpex (garantir que jurados acessem o servidor via IP local `http://192.168.x.x:5173`).
5. Responsáveis pelo telão físico no dia: posicionamento do projetor, cabos HDMI e som da caixa do auditório.

---

## 💡 Dicas Pedagógicas para o Professor

1. **Duplas de Programação (Pair Programming)**:
   - Em cada squad, forme duplas unindo um aluno com mais facilidade com outro que precisa de mais apoio.
2. **Papel de "Líder Técnico Mirim" (Rotativo por Sprint)**:
   - Em cada sprint, escolha um aluno do squad para apresentar a entrega na sexta-feira. Isso desenvolve oratória e liderança técnica.
3. **Quadro Kanban no GitHub Projects**:
   - Crie 4 colunas simples:
     - 📌 **A Fazer (Backlog)**
     - ⏳ **Em Andamento (WIP)**
     - 🔍 **Em Revisão (Pull Request)**
     - ✅ **Concluído (Pronto no Develop)**
