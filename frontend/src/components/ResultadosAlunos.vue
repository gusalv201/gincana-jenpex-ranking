<template>
  <div class="res-container">
    <!-- Login (admin ou recepção) -->
    <section v-if="!logado" class="glass-panel res-card res-login">
      <span class="section-tag">RESULTADOS</span>
      <h2>Resultados por aluno</h2>
      <p class="field-hint">Acesso do administrador ou da equipe da recepção.</p>
      <form @submit.prevent="entrar">
        <div class="form-group">
          <label for="res-user">Usuário</label>
          <input id="res-user" v-model="cred.username" class="input-field" autocomplete="username" required />
        </div>
        <div class="form-group">
          <label for="res-pass">Senha</label>
          <input id="res-pass" v-model="cred.password" type="password" class="input-field"
            autocomplete="current-password" required />
        </div>
        <div v-if="erro" class="banner-alert banner-error" role="alert"><div><p>{{ erro }}</p></div></div>
        <button type="submit" class="btn-primary btn-full" :disabled="carregando">
          {{ carregando ? '⏳ Entrando...' : 'Entrar' }}
        </button>
      </form>
    </section>

    <div v-else class="res-grid">
      <!-- Lista de alunos -->
      <section class="glass-panel res-card">
        <div class="topo">
          <h3>Alunos ({{ filtrados.length }})</h3>
          <button class="btn-secondary" :disabled="carregando" @click="carregarLista">🔄</button>
        </div>
        <input v-model="busca" class="input-field" placeholder="🔎 Buscar por nome ou código" />
        <div class="lista">
          <button v-for="a in filtrados" :key="a.id"
            :class="['aluno', detalhe && detalhe.id === a.id ? 'ativo' : '']" @click="abrir(a.id)">
            <span class="nome">{{ a.username }} <small>#{{ a.participant_code }}</small></span>
            <span class="meta">{{ a.total_points }} pts • {{ a.games_played }} jogo(s)</span>
          </button>
          <p v-if="!filtrados.length" class="field-hint">Nenhum aluno encontrado.</p>
        </div>
      </section>

      <!-- Detalhes -->
      <section class="glass-panel res-card">
        <p v-if="!detalhe" class="field-hint">Selecione um aluno para ver os detalhes da participação.</p>
        <template v-else>
          <div class="topo">
            <div>
              <h2>{{ detalhe.username }} <small class="codigo">#{{ detalhe.participant_code }}</small></h2>
              <span v-if="detalhe.position">{{ detalhe.position }}º lugar de {{ detalhe.total_participants }}</span>
              <span v-else class="field-hint">Inativo (fora do ranking)</span>
            </div>
            <div class="total">
              <span class="total-label">TOTAL</span>
              <span class="total-valor">{{ detalhe.total_points }}</span>
            </div>
          </div>

          <div class="resumo-linha">
            <span>🎮 Jogou <b>{{ detalhe.played.length }}</b> de {{ detalhe.played.length + detalhe.missing.length }} jogos</span>
            <span v-if="detalhe.played.length">
              🕒 Primeiro às <b>{{ hora(detalhe.played[0].created_at) }}</b>,
              último às <b>{{ hora(detalhe.played[detalhe.played.length - 1].created_at) }}</b>
            </span>
          </div>

          <h3>✅ Jogos realizados</h3>
          <p v-if="!detalhe.played.length" class="field-hint">Nenhum jogo realizado ainda.</p>
          <table v-else class="tabela">
            <thead>
              <tr><th>Horário</th><th>Jogo</th><th>Chefe de mesa</th><th>Pontos</th></tr>
            </thead>
            <tbody>
              <tr v-for="j in detalhe.played" :key="j.game_id">
                <td>{{ hora(j.created_at) }}</td>
                <td>{{ j.game_name }}</td>
                <td>{{ j.master_username || '—' }}</td>
                <td><b>{{ j.points }}</b></td>
              </tr>
            </tbody>
          </table>

          <h3>⏳ Jogos que faltam ({{ detalhe.missing.length }})</h3>
          <p v-if="!detalhe.missing.length" class="field-hint">🎉 Participou de todos os jogos ativos.</p>
          <div v-else class="faltam">
            <span v-for="j in detalhe.missing" :key="j.game_id" class="chip-falta">{{ j.game_name }}</span>
          </div>
        </template>
        <div v-if="erro" class="banner-alert banner-error" role="alert"><div><p>{{ erro }}</p></div></div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  login, getMyProfile, clearAuthToken, retomarSessao,
  listStaffParticipants, getStaffParticipantDetail,
} from '../services/api.js'

const PERFIS = ['admin', 'reception']
const logado = ref(false)
const carregando = ref(false)
const erro = ref('')
const cred = ref({ username: '', password: '' })
const alunos = ref([])
const busca = ref('')
const detalhe = ref(null)

function normalizar(v) {
  return (v || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim()
}

const filtrados = computed(() => {
  const b = normalizar(busca.value)
  if (!b) return alunos.value
  return alunos.value.filter(
    (a) => normalizar(a.username).includes(b) || normalizar(a.participant_code).includes(b)
  )
})

function hora(iso) {
  try {
    return new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

function tratarErro(e) {
  if (e.status === 401 || e.status === 403) {
    clearAuthToken()
    logado.value = false
    erro.value = 'Sessão expirada. Entre novamente.'
  } else {
    erro.value = e.message || 'Erro ao comunicar com o servidor.'
  }
}

async function carregarLista() {
  carregando.value = true
  erro.value = ''
  try {
    alunos.value = await listStaffParticipants()
    if (detalhe.value) await abrir(detalhe.value.id)
  } catch (e) {
    tratarErro(e)
  } finally {
    carregando.value = false
  }
}

async function abrir(id) {
  erro.value = ''
  try {
    detalhe.value = await getStaffParticipantDetail(id)
  } catch (e) {
    if (e.status === 404) {
      detalhe.value = null
      erro.value = 'Aluno não encontrado (pode ter sido excluído).'
    } else {
      tratarErro(e)
    }
  }
}

async function entrar() {
  erro.value = ''
  carregando.value = true
  try {
    await login({ username: cred.value.username.trim(), password: cred.value.password })
    const perfil = await getMyProfile()
    if (!PERFIS.includes(perfil?.role)) {
      clearAuthToken()
      erro.value = 'Este usuário não tem acesso aos resultados.'
      return
    }
    cred.value.password = ''
    logado.value = true
    await carregarLista()
  } catch (e) {
    erro.value = e.message || 'Falha na autenticação.'
  } finally {
    carregando.value = false
  }
}

onMounted(async () => {
  if (await retomarSessao(PERFIS)) {
    logado.value = true
    await carregarLista()
  }
})
</script>

<style scoped>
.res-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px;
}
.res-card {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}
.res-card h2, .res-card h3 { margin: 4px 0; }
.res-login { max-width: 460px; margin: 24px auto; }
.btn-full { width: 100%; margin-top: 8px; }
.res-grid {
  display: grid;
  grid-template-columns: minmax(260px, 1fr) 2fr;
  gap: 14px;
  align-items: start;
}
@media (max-width: 820px) {
  .res-grid { grid-template-columns: 1fr; }
}
.topo {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.lista {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 60vh;
  overflow-y: auto;
}
.aluno {
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid transparent;
  background: rgba(255, 255, 255, 0.06);
  color: inherit;
  cursor: pointer;
}
.aluno.ativo { border-color: rgba(255, 255, 255, 0.5); background: rgba(255, 255, 255, 0.14); }
.aluno small, .codigo { font-size: 0.7em; opacity: 0.7; letter-spacing: 1px; }
.meta { font-size: 0.85rem; opacity: 0.8; }
.total { display: flex; flex-direction: column; align-items: center; }
.total-label { font-size: 0.75rem; opacity: 0.8; }
.total-valor { font-size: 2.4rem; font-weight: 800; }
.resumo-linha { display: flex; flex-wrap: wrap; gap: 6px 18px; }
.tabela { width: 100%; border-collapse: collapse; }
.tabela th, .tabela td {
  text-align: left;
  padding: 8px 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}
.tabela th { font-size: 0.8rem; opacity: 0.8; }
.faltam { display: flex; flex-wrap: wrap; gap: 6px; }
.chip-falta {
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px dashed rgba(255, 255, 255, 0.35);
}
</style>
