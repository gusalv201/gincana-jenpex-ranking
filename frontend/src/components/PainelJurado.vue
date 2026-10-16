<template>
  <div class="painel-container">
    <div class="painel-header">
      <div>
        <h2>📱 PAINEL DO JURADO / COORDENAÇÃO</h2>
        <p>Lançamento ágil de notas e controle dos desafios da Jenpex</p>
      </div>

      <!-- Abas internas do Painel -->
      <div class="sub-tabs">
        <button 
          :class="['sub-btn', tab === 'lancar' ? 'active' : '']" 
          @click="tab = 'lancar'"
        >
          ⭐ Lançar Pontos
        </button>
        <button 
          :class="['sub-btn', tab === 'cadastrar' ? 'active' : '']" 
          @click="tab = 'cadastrar'"
        >
          ➕ Nova Equipe / Prova
        </button>
      </div>
    </div>

    <!-- ABA 1: FORMULÁRIO DE LANÇAMENTO DE NOTAS -->
    <div v-if="tab === 'lancar'" class="grid-lancar">
      <div class="form-card glass-panel">
        <h3 class="card-title">Atribuir Pontuação para Equipe</h3>

        <form @submit.prevent="submeterPontuacao">
          <!-- Seleção da Equipe -->
          <div class="form-group">
            <label>1. Selecione a Equipe Participante:</label>
            <select v-model="formPontos.equipe_id" required class="custom-select">
              <option :value="null" disabled>-- Escolha a Equipe --</option>
              <option v-for="eq in equipes" :key="eq.id" :value="eq.id">
                {{ eq.nome }} ({{ eq.curso_turma }})
              </option>
            </select>
          </div>

          <!-- Seleção da Prova -->
          <div class="form-group">
            <label>2. Selecione a Prova / Desafio:</label>
            <select v-model="formPontos.prova_id" required class="custom-select" @change="atualizarPontosPadrao">
              <option :value="null" disabled>-- Escolha a Prova --</option>
              <option v-for="pr in provas" :key="pr.id" :value="pr.id">
                {{ pr.titulo }} (Padrão: +{{ pr.pontos_padrao }} pts)
              </option>
            </select>
          </div>

          <!-- Botões de Atalho para Pontuação -->
          <div class="form-group">
            <label>3. Pontos a Atribuir:</label>
            <div class="quick-buttons">
              <button type="button" class="q-btn" @click="formPontos.pontos = 10">+10</button>
              <button type="button" class="q-btn" @click="formPontos.pontos = 25">+25</button>
              <button type="button" class="q-btn q-accent" @click="formPontos.pontos = 50">+50</button>
              <button type="button" class="q-btn q-gold" @click="formPontos.pontos = 100">+100</button>
              <button type="button" class="q-btn q-penalidade" @click="formPontos.pontos = -20">-20 Pen.</button>
            </div>
            <input 
              type="number" 
              v-model.number="formPontos.pontos" 
              required 
              placeholder="Digite o valor ou use os atalhos"
              class="custom-input"
            />
          </div>

          <!-- Justificativa -->
          <div class="form-group">
            <label>4. Observação / Justificativa (Opcional):</label>
            <input 
              type="text" 
              v-model="formPontos.justificativa" 
              placeholder="Ex: Menor tempo no robô seguidor de linha"
              class="custom-input"
            />
          </div>

          <!-- Botão Enviar -->
          <button type="submit" class="btn-primary btn-full" :disabled="loadingEnvio">
            <span v-if="loadingEnvio">Enviando e Atualizando Telão...</span>
            <span v-else>🚀 Confirmar e Transmitir Pontos ao Vivo</span>
          </button>
        </form>

        <!-- Feedback de Sucesso -->
        <div v-if="msgSucesso" class="alert-success">
          ✅ {{ msgSucesso }}
        </div>
      </div>

      <!-- Resumo Lateral: Últimos Lançamentos -->
      <div class="history-card glass-panel">
        <h3 class="card-title">📜 Últimos Lançamentos</h3>
        
        <div v-if="historico.length === 0" class="history-empty">
          Nenhuma nota lançada nesta sessão ainda.
        </div>

        <ul v-else class="history-list">
          <li v-for="item in historico" :key="item.id" class="history-item">
            <div class="h-main">
              <span class="h-team">{{ item.equipe_nome }}</span>
              <span :class="['h-points', item.pontos >= 0 ? 'pos' : 'neg']">
                {{ item.pontos >= 0 ? '+' : '' }}{{ item.pontos }} pts
              </span>
            </div>
            <div class="h-sub">
              <span>{{ item.prova_titulo }}</span>
              <span class="h-time">{{ item.hora }}</span>
            </div>
          </li>
        </ul>
      </div>
    </div>

    <!-- ABA 2: CADASTRO RÁPIDO DE EQUIPES E PROVAS -->
    <div v-if="tab === 'cadastrar'" class="grid-cadastros">
      <!-- Cadastro de Equipe -->
      <div class="form-card glass-panel">
        <h3 class="card-title">➕ Cadastrar Nova Equipe</h3>
        <form @submit.prevent="cadastrarEquipe">
          <div class="form-group">
            <label>Nome da Equipe:</label>
            <input type="text" v-model="novaEquipe.nome" required placeholder="Ex: CyberPantanal" class="custom-input" />
          </div>
          <div class="form-group">
            <label>Curso / Turma:</label>
            <input type="text" v-model="novaEquipe.curso_turma" required placeholder="Ex: Informática 3º Ano" class="custom-input" />
          </div>
          <div class="form-group">
            <label>Cor Identificadora:</label>
            <div class="color-picker-wrap">
              <input type="color" v-model="novaEquipe.cor_hex" class="color-input" />
              <span>{{ novaEquipe.cor_hex }}</span>
            </div>
          </div>
          <button type="submit" class="btn-primary">Salvar Equipe</button>
        </form>
      </div>

      <!-- Cadastro de Prova -->
      <div class="form-card glass-panel">
        <h3 class="card-title">➕ Cadastrar Nova Prova</h3>
        <form @submit.prevent="cadastrarProva">
          <div class="form-group">
            <label>Título da Prova:</label>
            <input type="text" v-model="novaProva.titulo" required placeholder="Ex: Desafio de Robótica" class="custom-input" />
          </div>
          <div class="form-group">
            <label>Pontos Padrão:</label>
            <input type="number" v-model.number="novaProva.pontos_padrao" required class="custom-input" />
          </div>
          <div class="form-group">
            <label>Descrição:</label>
            <textarea v-model="novaProva.descricao" placeholder="Regras básicas ou critérios" class="custom-textarea"></textarea>
          </div>
          <button type="submit" class="btn-primary">Salvar Prova</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  equipes: {
    type: Array,
    default: () => []
  },
  provas: {
    type: Array,
    default: () => []
  },
  apiBaseUrl: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['pontuacao-enviada', 'dados-atualizados'])

const tab = ref('lancar')
const loadingEnvio = ref(false)
const msgSucesso = ref('')

const formPontos = ref({
  equipe_id: null,
  prova_id: null,
  pontos: 50,
  justificativa: ''
})

const historico = ref([])

const novaEquipe = ref({
  nome: '',
  curso_turma: '',
  cor_hex: '#3B82F6'
})

const novaProva = ref({
  titulo: '',
  pontos_padrao: 50,
  descricao: ''
})

function atualizarPontosPadrao() {
  const selecionada = props.provas.find(p => p.id === formPontos.value.prova_id)
  if (selecionada && selecionada.pontos_padrao) {
    formPontos.value.pontos = selecionada.pontos_padrao
  }
}

async function submeterPontuacao() {
  loadingEnvio.value = true
  msgSucesso.value = ''

  try {
    const res = await fetch(`${props.apiBaseUrl}/api/pontuacoes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formPontos.value)
    })

    if (!res.ok) {
      const err = await res.json()
      alert(`Erro: ${err.detail || 'Falha ao lançar nota'}`)
      loadingEnvio.value = false
      return
    }

    const data = await res.json()
    const eq = props.equipes.find(e => e.id === formPontos.value.equipe_id)
    const pr = props.provas.find(p => p.id === formPontos.value.prova_id)

    // Adiciona ao histórico local
    historico.value.unshift({
      id: Date.now(),
      equipe_nome: eq ? eq.nome : 'Equipe',
      prova_titulo: pr ? pr.titulo : 'Prova',
      pontos: formPontos.value.pontos,
      hora: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
    })

    msgSucesso.value = `Pontuação de ${formPontos.value.pontos} pts enviada para ${eq ? eq.nome : 'a equipe'}!`
    emit('pontuacao-enviada', {
      equipe: eq ? eq.nome : 'Equipe',
      prova: pr ? pr.titulo : 'Prova',
      pontos: formPontos.value.pontos
    })

    // Limpa formulário
    formPontos.value.justificativa = ''
    setTimeout(() => { msgSucesso.value = '' }, 4000)
  } catch (error) {
    alert("Erro de comunicação com o servidor: " + error.message)
  } finally {
    loadingEnvio.value = false
  }
}

async function cadastrarEquipe() {
  try {
    const res = await fetch(`${props.apiBaseUrl}/api/equipes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(novaEquipe.value)
    })
    if (res.ok) {
      alert("Equipe cadastrada com sucesso!")
      novaEquipe.value = { nome: '', curso_turma: '', cor_hex: '#3B82F6' }
      emit('dados-atualizados')
      tab.value = 'lancar'
    } else {
      const err = await res.json()
      alert("Erro ao cadastrar: " + err.detail)
    }
  } catch (e) {
    alert("Erro de conexão: " + e.message)
  }
}

async function cadastrarProva() {
  try {
    const res = await fetch(`${props.apiBaseUrl}/api/provas`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(novaProva.value)
    })
    if (res.ok) {
      alert("Prova cadastrada com sucesso!")
      novaProva.value = { titulo: '', pontos_padrao: 50, descricao: '' }
      emit('dados-atualizados')
      tab.value = 'lancar'
    } else {
      const err = await res.json()
      alert("Erro ao cadastrar: " + err.detail)
    }
  } catch (e) {
    alert("Erro de conexão: " + e.message)
  }
}
</script>

<style scoped>
.painel-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 10px 24px 60px;
}

.painel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 18px;
}

.painel-header h2 {
  font-size: 1.6rem;
  font-weight: 900;
}

.painel-header p {
  color: var(--text-muted);
}

.sub-tabs {
  display: flex;
  gap: 8px;
}

.sub-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  padding: 8px 16px;
  border-radius: 10px;
  font-family: var(--font-display);
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.sub-btn.active {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border-color: rgba(59, 130, 246, 0.5);
}

.grid-lancar {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 24px;
}

.grid-cadastros {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.form-card, .history-card {
  padding: 24px;
}

.card-title {
  font-size: 1.25rem;
  margin-bottom: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  padding-bottom: 12px;
}

.form-group {
  margin-bottom: 18px;
}

.form-group label {
  display: block;
  font-size: 0.88rem;
  font-weight: 700;
  margin-bottom: 8px;
  color: #cbd5e1;
}

.custom-select, .custom-input, .custom-textarea {
  width: 100%;
  padding: 12px 16px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  font-family: var(--font-display);
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s;
}

.custom-select:focus, .custom-input:focus, .custom-textarea:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.custom-textarea {
  resize: vertical;
  min-height: 80px;
}

.quick-buttons {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.q-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  padding: 6px 14px;
  border-radius: 8px;
  font-weight: 800;
  cursor: pointer;
  font-family: var(--font-mono);
}

.q-btn:hover { background: rgba(255, 255, 255, 0.14); }
.q-accent { background: rgba(59, 130, 246, 0.25); color: #60a5fa; }
.q-gold { background: rgba(245, 158, 11, 0.25); color: #fbbf24; }
.q-penalidade { background: rgba(239, 68, 68, 0.2); color: #f87171; }

.btn-full {
  width: 100%;
  justify-content: center;
  font-size: 1.05rem;
  padding: 14px;
  margin-top: 10px;
}

.alert-success {
  margin-top: 16px;
  padding: 12px;
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.4);
  border-radius: 10px;
  color: #34d399;
  font-weight: 700;
}

.history-empty {
  color: var(--text-muted);
  text-align: center;
  padding: 30px;
}

.history-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.history-item {
  padding: 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.h-main {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.h-team { font-weight: 700; color: #f3f4f6; }
.h-points { font-weight: 900; font-family: var(--font-mono); }
.h-points.pos { color: #34d399; }
.h-points.neg { color: #f87171; }

.h-sub {
  display: flex;
  justify-content: space-between;
  font-size: 0.78rem;
  color: var(--text-sub);
}

.color-picker-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

.color-input {
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  background: transparent;
}

@media (max-width: 800px) {
  .painel-header { flex-direction: column; align-items: flex-start; gap: 12px; }
  .grid-lancar, .grid-cadastros { grid-template-columns: 1fr; }
}
</style>
