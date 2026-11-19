<template>
  <div class="notas-container">
    <section v-if="!resumo" class="glass-panel notas-card">
      <span class="section-tag">ÁREA DO ALUNO</span>
      <h2>Minhas Notas</h2>
      <p class="field-hint">Informe o código recebido na recepção e sua senha/PIN.</p>

      <form @submit.prevent="entrar">
        <div class="form-group">
          <label for="aluno-codigo">Código do participante</label>
          <input id="aluno-codigo" v-model="codigo" type="text" class="input-field input-codigo"
            maxlength="6" autocomplete="username" autocapitalize="characters" required
            :disabled="carregando" placeholder="Ex.: A7K9P2" />
        </div>
        <div class="form-group">
          <label for="aluno-senha">Senha / PIN</label>
          <input id="aluno-senha" v-model="senha" type="password" class="input-field"
            inputmode="numeric" autocomplete="current-password" required :disabled="carregando" />
        </div>
        <div v-if="erro" class="banner-alert banner-error" role="alert">
          <div><p>{{ erro }}</p></div>
        </div>
        <button type="submit" class="btn-primary btn-full" :disabled="carregando">
          {{ carregando ? '⏳ Entrando...' : 'Ver minhas notas' }}
        </button>
      </form>
    </section>

    <section v-else class="glass-panel notas-card">
      <div class="notas-header">
        <div>
          <span class="section-tag">PARTICIPANTE</span>
          <h2>{{ resumo.username }} <small class="codigo">#{{ resumo.participant_code }}</small></h2>
          <span v-if="resumo.position" class="posicao">
            {{ resumo.position }}º lugar de {{ resumo.total_participants }}
          </span>
        </div>
        <div class="total">
          <span class="total-label">TOTAL</span>
          <span class="total-valor">{{ resumo.total_points }}</span>
        </div>
      </div>

      <h3>✅ Jogos que você já fez ({{ resumo.played.length }})</h3>
      <p v-if="resumo.played.length === 0" class="field-hint">Você ainda não tem pontuações registradas.</p>
      <ul v-else class="lista-notas">
        <li v-for="nota in resumo.played" :key="nota.game_id">
          <span>{{ nota.game_name }} <small class="hora">{{ formatarHora(nota.created_at) }}</small></span>
          <strong>{{ nota.points }} pts</strong>
        </li>
      </ul>

      <h3>⏳ Jogos que faltam ({{ resumo.missing.length }})</h3>
      <p v-if="resumo.missing.length === 0" class="field-hint">🎉 Você já participou de todos os jogos!</p>
      <ul v-else class="lista-notas lista-faltam">
        <li v-for="jogo in resumo.missing" :key="jogo.game_id">
          <span>{{ jogo.game_name }}</span>
          <span class="pendente">pendente</span>
        </li>
      </ul>

      <div v-if="erro" class="banner-alert banner-error" role="alert">
        <div><p>{{ erro }}</p></div>
      </div>

      <div class="acoes">
        <button type="button" class="btn-primary" :disabled="carregando" @click="atualizar">
          {{ carregando ? '⏳' : '🔄 Atualizar' }}
        </button>
        <button type="button" class="btn-secondary" @click="sair">Sair</button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { login, getMyProfile, getMySummary, clearAuthToken } from '../services/api.js'

const codigo = ref('')
const senha = ref('')
const resumo = ref(null)
const erro = ref('')
const carregando = ref(false)

function formatarHora(iso) {
  try {
    return new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

async function entrar() {
  if (carregando.value) return
  erro.value = ''
  carregando.value = true
  try {
    await login({ username: codigo.value.trim().toUpperCase(), password: senha.value })
    const dados = await getMyProfile()
    if (dados?.role !== 'participant') {
      clearAuthToken()
      erro.value = 'Esta área é exclusiva para alunos participantes.'
      return
    }
    senha.value = ''
    resumo.value = await getMySummary()
  } catch (e) {
    clearAuthToken()
    resumo.value = null
    erro.value = e.status === 401 ? 'Código ou senha incorretos.' : e.message
  } finally {
    carregando.value = false
  }
}

async function atualizar() {
  erro.value = ''
  carregando.value = true
  try {
    resumo.value = await getMySummary()
  } catch (e) {
    if (e.status === 401) {
      sair()
      erro.value = 'Sessão expirada. Entre novamente.'
    } else {
      erro.value = e.message
    }
  } finally {
    carregando.value = false
  }
}

function sair() {
  clearAuthToken()
  resumo.value = null
  codigo.value = ''
}
</script>

<style scoped>
.notas-container {
  max-width: 560px;
  margin: 0 auto;
  padding: 16px;
}
.notas-card {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.notas-card h2, .notas-card h3 {
  margin: 4px 0;
}
.input-codigo {
  text-transform: uppercase;
  letter-spacing: 4px;
  font-weight: 700;
}
.btn-full {
  width: 100%;
  margin-top: 8px;
}
.notas-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.codigo {
  font-size: 0.6em;
  opacity: 0.7;
  letter-spacing: 2px;
}
.posicao {
  font-weight: 700;
}
.total {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.total-label {
  font-size: 0.75rem;
  opacity: 0.8;
}
.total-valor {
  font-size: 2.4rem;
  font-weight: 800;
}
.lista-notas {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.lista-notas li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.06);
}
.lista-faltam li {
  border: 1px dashed rgba(255, 255, 255, 0.25);
  background: transparent;
}
.hora {
  opacity: 0.7;
  margin-left: 6px;
}
.pendente {
  font-size: 0.8rem;
  opacity: 0.8;
}
.acoes {
  display: flex;
  gap: 10px;
}
.acoes button {
  flex: 1;
}
</style>
