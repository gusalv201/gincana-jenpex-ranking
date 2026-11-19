<template>
  <div class="notas-container">
    <section v-if="!perfil" class="glass-panel notas-card">
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
          <h2>{{ perfil.username }}</h2>
          <span class="codigo">Código {{ perfil.participant_code }}</span>
        </div>
        <div class="total">
          <span class="total-label">TOTAL</span>
          <span class="total-valor">{{ total }}</span>
        </div>
      </div>

      <p v-if="notas.length === 0" class="field-hint">Você ainda não tem pontuações registradas.</p>
      <ul v-else class="lista-notas">
        <li v-for="(nota, i) in notas" :key="i">
          <span>{{ nota.game_name }}</span>
          <strong>{{ nota.points }} pts</strong>
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
import { ref, computed } from 'vue'
import { login, getMyProfile, getMyScores, clearAuthToken } from '../services/api.js'

const codigo = ref('')
const senha = ref('')
const perfil = ref(null)
const notas = ref([])
const erro = ref('')
const carregando = ref(false)

const total = computed(() => notas.value.reduce((soma, n) => soma + n.points, 0))

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
    perfil.value = dados
    senha.value = ''
    notas.value = await getMyScores()
  } catch (e) {
    clearAuthToken()
    perfil.value = null
    erro.value = e.status === 401 ? 'Código ou senha incorretos.' : e.message
  } finally {
    carregando.value = false
  }
}

async function atualizar() {
  erro.value = ''
  carregando.value = true
  try {
    notas.value = await getMyScores()
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
  perfil.value = null
  notas.value = []
  codigo.value = ''
}
</script>

<style scoped>
.notas-container {
  max-width: 520px;
  margin: 0 auto;
  padding: 16px;
}
.notas-card {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.notas-card h2 {
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
  opacity: 0.8;
  letter-spacing: 2px;
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
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.06);
}
.acoes {
  display: flex;
  gap: 10px;
}
.acoes button {
  flex: 1;
}
</style>
