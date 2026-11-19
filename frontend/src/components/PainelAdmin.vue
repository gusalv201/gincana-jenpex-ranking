<template>
  <div class="admin-container">
    <!-- Login -->
    <section v-if="!logado" class="glass-panel admin-card admin-login">
      <span class="section-tag">ADMINISTRAÇÃO</span>
      <h2>Painel do Administrador</h2>
      <form @submit.prevent="entrar">
        <div class="form-group">
          <label for="adm-user">Usuário</label>
          <input id="adm-user" v-model="cred.username" class="input-field" autocomplete="username" required />
        </div>
        <div class="form-group">
          <label for="adm-pass">Senha</label>
          <input id="adm-pass" v-model="cred.password" type="password" class="input-field"
            autocomplete="current-password" required />
        </div>
        <div v-if="erroLogin" class="banner-alert banner-error" role="alert"><div><p>{{ erroLogin }}</p></div></div>
        <button type="submit" class="btn-primary btn-full" :disabled="carregando">
          {{ carregando ? '⏳ Entrando...' : 'Entrar' }}
        </button>
      </form>
    </section>

    <template v-else>
      <header class="glass-panel admin-card admin-topo">
        <div>
          <span class="section-tag">ADMINISTRAÇÃO</span>
          <h2>Painel do Administrador</h2>
        </div>
        <div class="acoes-topo">
          <button class="btn-secondary" :disabled="carregando" @click="carregarTudo">🔄 Atualizar</button>
          <button class="btn-secondary" @click="sair">Sair</button>
        </div>
      </header>

      <nav class="abas">
        <button v-for="a in abas" :key="a.id" :class="['aba', aba === a.id ? 'ativa' : '']" @click="aba = a.id">
          {{ a.rotulo }}
        </button>
      </nav>

      <div v-if="mensagem" :class="['banner-alert', mensagemErro ? 'banner-error' : 'banner-success']" role="status">
        <div><p>{{ mensagem }}</p></div>
      </div>

      <!-- JOGOS -->
      <section v-if="aba === 'jogos'" class="glass-panel admin-card">
        <h3>Novo jogo</h3>
        <form class="linha-form" @submit.prevent="criarJogo">
          <input v-model="novoJogo" class="input-field" placeholder="Nome do jogo (ex.: Robótica)" maxlength="200" required />
          <button class="btn-primary" :disabled="carregando">Criar jogo</button>
        </form>

        <h3>Jogos cadastrados ({{ jogos.length }})</h3>
        <p v-if="!jogos.length" class="field-hint">Nenhum jogo cadastrado.</p>
        <div v-for="jogo in jogos" :key="jogo.id" class="item">
          <div class="item-info">
            <strong>{{ jogo.name }}</strong>
            <span class="sub">
              {{ jogo.master ? `Chefe: ${jogo.master.username}` : 'Sem chefe de mesa' }}
            </span>
          </div>
          <div class="item-acoes">
            <select v-model="vinculo[jogo.id]" class="input-field select">
              <option value="">Escolher chefe...</option>
              <option v-for="m in chefesDisponiveis(jogo)" :key="m.id" :value="m.id">{{ m.username }}</option>
            </select>
            <button class="btn-primary" :disabled="!vinculo[jogo.id] || carregando" @click="vincular(jogo)">
              Vincular
            </button>
          </div>
        </div>
      </section>

      <!-- CHEFES DE MESA -->
      <section v-if="aba === 'chefes'" class="glass-panel admin-card">
        <h3>Novo chefe de mesa</h3>
        <form class="linha-form" @submit.prevent="criarChefe">
          <input v-model="novoChefe.username" class="input-field" placeholder="Usuário (ex.: mesa_robotica)"
            maxlength="100" autocomplete="off" required />
          <input v-model="novoChefe.password" class="input-field" placeholder="Senha (mín. 8 caracteres)"
            minlength="8" maxlength="128" autocomplete="new-password" required />
          <button class="btn-primary" :disabled="carregando">Criar chefe</button>
        </form>
        <p class="field-hint">Anote o usuário e a senha e entregue ao chefe. Depois vincule-o a um jogo na aba Jogos.</p>

        <h3>Chefes cadastrados ({{ chefes.length }})</h3>
        <p v-if="!chefes.length" class="field-hint">Nenhum chefe de mesa cadastrado.</p>
        <div v-for="m in chefes" :key="m.id" class="item">
          <div class="item-info">
            <strong>{{ m.username }}</strong>
            <span class="sub">{{ m.game_name ? `Jogo: ${m.game_name}` : 'Sem jogo vinculado' }}</span>
          </div>
        </div>
      </section>

      <!-- EQUIPE DA RECEPÇÃO -->
      <section v-if="aba === 'equipe'" class="glass-panel admin-card">
        <h3>Novo usuário da recepção</h3>
        <p class="field-hint">
          A recepção pode cadastrar alunos, corrigir nomes, gerar novo PIN e ver os resultados.
          Não pode excluir alunos, criar jogos nem chefes de mesa.
        </p>
        <form class="linha-form" @submit.prevent="criarEquipe">
          <input v-model="novaEquipe.username" class="input-field" placeholder="Usuário (ex.: recepcao_ana)"
            maxlength="100" autocomplete="off" required />
          <input v-model="novaEquipe.password" class="input-field" placeholder="Senha (mín. 10 caracteres)"
            minlength="10" maxlength="128" autocomplete="new-password" required />
          <button class="btn-primary" :disabled="carregando">Criar usuário</button>
        </form>

        <h3>Usuários da recepção ({{ equipe.length }})</h3>
        <p v-if="!equipe.length" class="field-hint">Nenhum usuário da recepção cadastrado.</p>
        <div v-for="u in equipe" :key="u.id" class="item">
          <div class="item-info"><strong>{{ u.username }}</strong></div>
          <div class="item-acoes">
            <button class="btn-danger" :disabled="carregando" @click="removerEquipe(u)">🗑️ Remover acesso</button>
          </div>
        </div>
      </section>

      <!-- ALUNOS -->
      <section v-if="aba === 'alunos'" class="glass-panel admin-card">
        <div class="linha-form">
          <input v-model="busca" class="input-field" placeholder="🔎 Buscar por nome ou código" />
        </div>
        <h3>Alunos cadastrados ({{ alunosFiltrados.length }} de {{ alunos.length }})</h3>
        <p class="field-hint">Detalhes de cada aluno (horários, jogos que faltam) ficam em <a href="#resultados">📊 Resultados</a>.</p>
        <p class="field-hint">Para cadastrar novos alunos, use a aba Recepção.</p>
        <p v-if="!alunosFiltrados.length" class="field-hint">Nenhum aluno encontrado.</p>
        <div v-for="aluno in alunosFiltrados" :key="aluno.id" class="item">
          <div class="item-info">
            <strong>{{ aluno.username }} <small class="code-small">#{{ aluno.participant_code }}</small></strong>
            <span class="sub">
              {{ aluno.total_points }} pts •
              {{ aluno.games_played }} jogo(s)
            </span>
          </div>
          <div class="item-acoes">
            <button class="btn-danger" :disabled="carregando" @click="excluirAluno(aluno)">🗑️ Excluir</button>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  login, getMyProfile, clearAuthToken, retomarSessao,
  listAdminStaff, createAdminStaff, deleteAdminStaff,
  listAdminGames, createAdminGame, listAdminMasters, createAdminMaster, assignMasterToGame,
  listAdminParticipants, deleteAdminParticipant,
} from '../services/api.js'

const abas = [
  { id: 'jogos', rotulo: '🎮 Jogos' },
  { id: 'chefes', rotulo: '🧑‍⚖️ Chefes de mesa' },
  { id: 'alunos', rotulo: '🎓 Alunos' },
  { id: 'equipe', rotulo: '🧾 Equipe da recepção' },
]

const logado = ref(false)
const carregando = ref(false)
const erroLogin = ref('')
const cred = ref({ username: '', password: '' })
const aba = ref('jogos')
const mensagem = ref('')
const mensagemErro = ref(false)

const jogos = ref([])
const chefes = ref([])
const alunos = ref([])
const equipe = ref([])
const novaEquipe = ref({ username: '', password: '' })
const vinculo = ref({})
const novoJogo = ref('')
const novoChefe = ref({ username: '', password: '' })
const busca = ref('')

function normalizar(v) {
  return (v || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim()
}

const alunosFiltrados = computed(() => {
  const b = normalizar(busca.value)
  if (!b) return alunos.value
  return alunos.value.filter(
    (a) => normalizar(a.username).includes(b) || normalizar(a.participant_code).includes(b)
  )
})

function chefesDisponiveis(jogo) {
  return chefes.value.filter((m) => !m.game_id || m.game_id === jogo.id)
}

function avisar(texto, erro = false) {
  mensagem.value = texto
  mensagemErro.value = erro
  if (!erro) setTimeout(() => { if (mensagem.value === texto) mensagem.value = '' }, 4000)
}

function tratarErro(e) {
  if (e.status === 401) {
    sair()
    erroLogin.value = 'Sessão expirada. Entre novamente.'
    return
  }
  avisar(e.message || 'Erro ao comunicar com o servidor.', true)
}

async function entrar() {
  erroLogin.value = ''
  carregando.value = true
  try {
    await login({ username: cred.value.username.trim(), password: cred.value.password })
    const perfil = await getMyProfile()
    if (perfil?.role !== 'admin') {
      clearAuthToken()
      erroLogin.value = 'Este usuário não é administrador.'
      return
    }
    cred.value.password = ''
    logado.value = true
    await carregarTudo()
  } catch (e) {
    erroLogin.value = e.message || 'Falha na autenticação.'
  } finally {
    carregando.value = false
  }
}

function sair() {
  clearAuthToken()
  logado.value = false
  jogos.value = []
  chefes.value = []
  alunos.value = []
}

async function carregarTudo() {
  carregando.value = true
  try {
    const [g, m, a, e] = await Promise.all([
      listAdminGames(), listAdminMasters(), listAdminParticipants(), listAdminStaff(),
    ])
    jogos.value = g
    chefes.value = m
    alunos.value = a
    equipe.value = e
  } catch (e) {
    tratarErro(e)
  } finally {
    carregando.value = false
  }
}

async function executar(acao, sucesso) {
  carregando.value = true
  try {
    await acao()
    avisar(sucesso)
    await carregarTudo()
    return true
  } catch (e) {
    tratarErro(e)
    return false
  } finally {
    carregando.value = false
  }
}

async function criarJogo() {
  const nome = novoJogo.value.trim()
  if (!nome) return
  if (await executar(() => createAdminGame({ name: nome }), `Jogo "${nome}" criado.`)) novoJogo.value = ''
}

async function criarChefe() {
  const username = novoChefe.value.username.trim()
  const password = novoChefe.value.password
  if (password.length < 8) return avisar('A senha do chefe precisa ter pelo menos 8 caracteres.', true)
  if (await executar(() => createAdminMaster({ username, password }), `Chefe "${username}" criado.`)) {
    novoChefe.value = { username: '', password: '' }
  }
}

async function vincular(jogo) {
  const masterId = Number(vinculo.value[jogo.id])
  const chefe = chefes.value.find((m) => m.id === masterId)
  if (await executar(() => assignMasterToGame(jogo.id, { master_id: masterId }),
    `${chefe?.username} vinculado a "${jogo.name}".`)) {
    vinculo.value[jogo.id] = ''
  }
}

async function criarEquipe() {
  const username = novaEquipe.value.username.trim()
  const password = novaEquipe.value.password
  if (password.length < 10) return avisar('A senha da recepção precisa ter pelo menos 10 caracteres.', true)
  if (await executar(() => createAdminStaff({ username, password }), `Usuário da recepção "${username}" criado.`)) {
    novaEquipe.value = { username: '', password: '' }
  }
}

async function removerEquipe(u) {
  if (!window.confirm(`Remover o acesso de "${u.username}" à recepção?`)) return
  await executar(() => deleteAdminStaff(u.id), `Acesso de "${u.username}" removido.`)
}

onMounted(async () => {
  if (await retomarSessao(['admin'])) {
    logado.value = true
    await carregarTudo()
  }
})

async function excluirAluno(aluno) {
  const aviso = aluno.games_played
    ? `\n\nATENÇÃO: as ${aluno.games_played} pontuação(ões) dele (${aluno.total_points} pts) também serão apagadas.`
    : ''
  if (!window.confirm(`Excluir o aluno "${aluno.username}" (código ${aluno.participant_code})?${aviso}\n\nIsso não pode ser desfeito.`)) return
  await executar(() => deleteAdminParticipant(aluno.id), `Aluno "${aluno.username}" excluído.`)
}
</script>

<style scoped>
.code-small { font-size: 0.72em; opacity: 0.7; font-weight: 500; letter-spacing: 1px; }
.admin-container {
  max-width: 980px;
  margin: 0 auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.admin-card {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.admin-card h2, .admin-card h3 { margin: 4px 0; }
.admin-login { max-width: 460px; margin: 24px auto; width: 100%; }
.btn-full { width: 100%; margin-top: 8px; }
.admin-topo { flex-direction: row; justify-content: space-between; align-items: center; flex-wrap: wrap; }
.acoes-topo { display: flex; gap: 8px; }
.abas { display: flex; gap: 8px; flex-wrap: wrap; }
.aba {
  padding: 10px 16px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.05);
  color: inherit;
  cursor: pointer;
  font-weight: 600;
}
.aba.ativa { background: rgba(255, 255, 255, 0.18); }
.linha-form { display: flex; gap: 8px; flex-wrap: wrap; }
.linha-form .input-field { flex: 1 1 200px; }
.item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.06);
  flex-wrap: wrap;
}
.item-info { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.sub { opacity: 0.8; font-size: 0.9rem; }
.item-acoes { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.select { min-width: 180px; }
.btn-danger {
  padding: 10px 16px;
  border-radius: 10px;
  border: none;
  background: #c62828;
  color: #fff;
  font-weight: 700;
  cursor: pointer;
}
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }
.banner-success {
  border-left: 4px solid #2e7d32;
}
</style>
