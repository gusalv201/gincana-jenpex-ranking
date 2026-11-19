# Deploy na nuvem (gratuito): Render + Aiven

| Peça | Serviço | Plano |
| --- | --- | --- |
| App (API FastAPI + frontend Vue numa única URL) | [Render](https://render.com) | Free |
| Banco MySQL 8 | [Aiven](https://aiven.io) | Free |

Toda vez que alguém faz push/merge na branch `main` do GitHub, o Render publica a nova versão sozinho.

> ⚠️ O plano free do Render "dorme" após 15 min sem acesso. O primeiro acesso depois disso leva cerca de 1 minuto.
> No dia do evento, abra o telão uns minutos antes. Com o telão aberto, o serviço não dorme, porque ele consulta o ranking a cada 2 s.

---

## 1. Banco de dados (Aiven)

1. Crie uma conta em https://console.aiven.io (pode entrar com o GitHub).
2. **Create service** → **MySQL** → plano **Free**. Escolha uma região qualquer.
3. Quando o serviço estiver *Running*, abra a aba **Overview** e anote:
   - **Host**, **Port**, **User** (`avnadmin`), **Password** e **Database** (`defaultdb`).
   - Baixe o **CA certificate** (`ca.pem`).
4. Monte a `DATABASE_URL` neste formato:

   ```
   mysql+asyncmy://avnadmin:SENHA@HOST:PORTA/defaultdb
   ```

   Se a senha tiver caracteres especiais (`@`, `/`, `:`, `#`), troque-os pelo código URL correspondente (`@` → `%40`).

As tabelas são criadas automaticamente quando o app sobe pela primeira vez.

## 2. Aplicação (Render)

1. Crie uma conta em https://render.com entrando com o GitHub que tem acesso ao repositório.
2. **New → Blueprint** → selecione o repositório `gincana-jenpex-ranking`. O Render lê o arquivo `render.yaml`.
3. Preencha as variáveis que ele pedir:

   | Variável | Valor |
   | --- | --- |
   | `DATABASE_URL` | a URL do passo 1 |
   | `DATABASE_CA_CERT` | cole o conteúdo inteiro do `ca.pem`, incluindo as linhas `-----BEGIN CERTIFICATE-----` e `-----END CERTIFICATE-----` |
   | `ADMIN_USERNAME` | usuário do administrador, por exemplo `admin` |
   | `ADMIN_PASSWORD` | **senha definida por você**, com no mínimo 12 caracteres |

   O `JWT_SECRET_KEY` é gerado automaticamente pelo Render, e o `DATABASE_SSL` já vem como `on`.
4. **Apply**. O primeiro build leva alguns minutos. No fim, a URL fica parecida com `https://jenpex-gincana.onrender.com`.
5. Para testar, abra `https://SUA-URL/api/`. A resposta deve ser `{"status": "..."}`.

**Trocar a senha do admin:** Render → serviço → *Environment* → altere `ADMIN_PASSWORD` → *Save* (o serviço reinicia e a senha nova passa a valer).

## 3. Endereços de uso

| Quem | Endereço | Login |
| --- | --- | --- |
| TV / telão (notebook) | `https://SUA-URL/#ranking` | não precisa (só exibe código e pontos) |
| Recepção (cadastro de alunos) | `https://SUA-URL/#cadastro` | admin |
| Chefes de mesa (celular/notebook) | `https://SUA-URL/#mesa` | usuário/senha do chefe |
| Alunos (celular) | `https://SUA-URL/#notas` | código do aluno + PIN |
| Administração (jogos, chefes, recepção, alunos) | `https://SUA-URL/#admin` | admin |
| Resultados detalhados por aluno | `https://SUA-URL/#resultados` | admin ou recepção |

## 4. Preparar o evento (admin)

Abra `https://SUA-URL/#admin` e entre como admin:

1. **🎮 Jogos:** crie cada jogo.
2. **🧑‍⚖️ Chefes de mesa:** crie cada chefe (usuário e senha definidos por você) e, na aba Jogos, vincule-o ao jogo dele.
3. **🧾 Equipe da recepção:** crie usuários para os alunos que vão cadastrar participantes. Eles conseguem cadastrar, corrigir nomes, gerar novo PIN e ver resultados, mas não excluem alunos nem mexem em jogos e chefes.
4. **🎓 Alunos:** consulte e exclua alunos (a exclusão apaga também as notas).

A documentação técnica da API (`/api/docs`) fica desligada por padrão. Para ligar temporariamente, crie a variável `ENABLE_API_DOCS=on` no Render.

## 5. Segurança aplicada

- **Ninguém se cadastra sozinho:** somente o admin e a equipe da recepção cadastram participantes. Jogos, chefes de mesa e usuários da recepção são criados apenas pelo admin.
- **Permissões por papel:** o chefe de mesa só lança notas no jogo dele, o aluno só vê as próprias notas e o telão é somente leitura.
- **Senhas:** são armazenadas com hash Argon2, nunca em texto. A senha do admin vem de uma variável de ambiente, nunca do código.
- **Tentativas de login:** após 8 erros para o mesmo usuário a partir do mesmo IP (ou 100 erros de um mesmo IP), aquele IP fica bloqueado por 10 minutos. Um atacante não consegue trancar a conta de um chefe de mesa que está em outra rede.
- **Cabeçalhos de proteção do navegador:** CSP, HSTS e bloqueio de incorporação em outros sites.
- **Conexões:** HTTPS automático no Render e TLS com verificação de certificado até o banco no Aiven.
- **Tokens:** expiram em 8 horas e ficam só na memória da aba. Fechar ou recarregar a aba obriga a entrar de novo.

## 6. Rodar localmente (desenvolvimento)

```bash
# Backend
cd backend
python -m venv venv && venv\Scripts\activate   # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env    # edite DATABASE_URL, JWT_SECRET_KEY, ADMIN_USERNAME e ADMIN_PASSWORD
uvicorn main:app --reload

# Frontend (outro terminal)
cd frontend
npm install
npm run dev               # http://localhost:5173 (faz proxy de /api para o backend)
```

Também é possível testar a imagem de produção: `docker build -t jenpex .` e rodar o container com as mesmas variáveis de ambiente.
