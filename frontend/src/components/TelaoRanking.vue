<template>
  <div class="telao-container">
    <!-- Notificação Flutuante de Pontos em Tempo Real -->
    <transition name="toast-slide">
      <div v-if="lastScoreToast" class="live-toast glass-panel">
        <span class="toast-bolt">⚡</span>
        <div class="toast-info">
          <strong>+{{ lastScoreToast.pontos }} pontos</strong> para 
          <span class="highlight-team">{{ lastScoreToast.equipe }}</span>
          <span class="toast-proof">• {{ lastScoreToast.prova }}</span>
        </div>
      </div>
    </transition>

    <!-- Header do Telão -->
    <div class="telao-header">
      <div class="title-wrap">
        <h2>PLACAR OFICIAL EM TEMPO REAL</h2>
        <p>Acompanhe a disputa ponto a ponto das equipes na JENPEX</p>
      </div>

      <div class="header-stats">
        <div class="stat-box glass-panel">
          <span class="stat-label">EQUIPES NA DISPUTA</span>
          <span class="stat-value">{{ ranking.length }}</span>
        </div>
        <div class="stat-box glass-panel">
          <span class="stat-label">PONTOS TOTAIS DISTRIBUÍDOS</span>
          <span class="stat-value text-accent">{{ totalPontosDistribuídos }}</span>
        </div>
      </div>
    </div>

    <!-- PÓDIO (TOP 3) -->
    <section v-if="top3.length > 0" class="podium-section">
      <!-- 2º LUGAR (Prata) -->
      <div v-if="top3[1]" class="podium-card silver glass-panel">
        <div class="podium-badge">🥈 2º LUGAR</div>
        <div class="team-avatar" :style="{ borderColor: top3[1].cor_hex }">
          {{ top3[1].nome.substring(0, 2).toUpperCase() }}
        </div>
        <h3 class="team-name">{{ top3[1].nome }}</h3>
        <span class="team-class">{{ top3[1].curso_turma }}</span>
        <div class="team-points">
          <span class="points-num">{{ top3[1].total_pontos }}</span>
          <span class="points-label">PTS</span>
        </div>
        <div class="pedestal pedestal-silver"></div>
      </div>

      <!-- 1º LUGAR (Ouro) -->
      <div v-if="top3[0]" class="podium-card gold glass-panel">
        <div class="crown-icon">👑</div>
        <div class="podium-badge gold-badge">🥇 LÍDER DA GINCANA</div>
        <div class="team-avatar gold-avatar" :style="{ borderColor: top3[0].cor_hex }">
          {{ top3[0].nome.substring(0, 2).toUpperCase() }}
        </div>
        <h3 class="team-name gold-name">{{ top3[0].nome }}</h3>
        <span class="team-class">{{ top3[0].curso_turma }}</span>
        <div class="team-points gold-points">
          <span class="points-num">{{ top3[0].total_pontos }}</span>
          <span class="points-label">PTS</span>
        </div>
        <div class="pedestal pedestal-gold"></div>
      </div>

      <!-- 3º LUGAR (Bronze) -->
      <div v-if="top3[2]" class="podium-card bronze glass-panel">
        <div class="podium-badge">🥉 3º LUGAR</div>
        <div class="team-avatar" :style="{ borderColor: top3[2].cor_hex }">
          {{ top3[2].nome.substring(0, 2).toUpperCase() }}
        </div>
        <h3 class="team-name">{{ top3[2].nome }}</h3>
        <span class="team-class">{{ top3[2].curso_turma }}</span>
        <div class="team-points">
          <span class="points-num">{{ top3[2].total_pontos }}</span>
          <span class="points-label">PTS</span>
        </div>
        <div class="pedestal pedestal-bronze"></div>
      </div>
    </section>

    <!-- TABELA / LISTA DO 4º EM DIANTE (COM TRANSIÇÃO SUAVE DE REORDENAÇÃO) -->
    <section v-if="demaisEquipes.length > 0" class="leaderboard-section">
      <h3 class="section-title">Classificação Geral (4º colocado em diante)</h3>

      <TransitionGroup name="flip-list" tag="div" class="teams-list">
        <div 
          v-for="equipe in demaisEquipes" 
          :key="equipe.id"
          class="team-row glass-panel"
        >
          <div class="pos-badge">#{{ equipe.posicao }}</div>
          
          <div class="team-indicator" :style="{ backgroundColor: equipe.cor_hex }"></div>

          <div class="team-meta">
            <span class="team-title">{{ equipe.nome }}</span>
            <span class="team-sub">{{ equipe.curso_turma }}</span>
          </div>

          <div class="team-score">
            <span class="score-val">{{ equipe.total_pontos }}</span>
            <span class="score-unit">PTS</span>
          </div>
        </div>
      </TransitionGroup>
    </section>

    <!-- Estado Vazio caso não haja equipes cadastradas -->
    <div v-if="ranking.length === 0" class="empty-state glass-panel">
      <span class="empty-icon">⏳</span>
      <h3>Nenhuma equipe cadastrada ainda</h3>
      <p>Acesse o <strong>Painel do Jurado / Admin</strong> para cadastrar equipes ou execute o script <code>database/seed.sql</code> no MySQL.</p>
    </div>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
import confetti from 'canvas-confetti'

const props = defineProps({
  ranking: {
    type: Array,
    default: () => []
  },
  lastScoreToast: {
    type: Object,
    default: null
  }
})

// Top 3 do pódio
const top3 = computed(() => {
  return props.ranking.slice(0, 3)
})

// Equipes do 4º lugar em diante
const demaisEquipes = computed(() => {
  return props.ranking.slice(3)
})

// Soma de todos os pontos de todas as equipes
const totalPontosDistribuídos = computed(() => {
  return props.ranking.reduce((acc, eq) => acc + (eq.total_pontos || 0), 0)
})

// Efeito Sonoro nativo usando Web Audio API (sem dependência de mp3 externo)
function playBeep(freq = 587.33, type = 'triangle', duration = 0.25) {
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)()
    const osc = audioCtx.createOscillator()
    const gain = audioCtx.createGain()
    osc.type = type
    osc.frequency.setValueAtTime(freq, audioCtx.currentTime)
    gain.gain.setValueAtTime(0.15, audioCtx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration)
    osc.connect(gain)
    gain.connect(audioCtx.destination)
    osc.start()
    osc.stop(audioCtx.currentTime + duration)
  } catch (e) {
    // áudio bloqueado pelo navegador antes do primeiro clique
  }
}

// Disparador de confetes quando uma nota é lançada
watch(() => props.lastScoreToast, (newVal) => {
  if (newVal) {
    playBeep(659.25, 'sine', 0.4) // Efeito sonoro
    
    // Confetes na tela
    try {
      confetti({
        particleCount: 50,
        spread: 60,
        origin: { y: 0.8 },
        colors: ['#3b82f6', '#10b981', '#f59e0b', '#ec4899']
      })
    } catch (e) {
      // Ignora erro se confetti falhar
    }
  }
})
</script>

<style scoped>
.telao-container {
  max-width: 1300px;
  margin: 0 auto;
  padding: 10px 24px 60px;
  position: relative;
}

/* Toast em Tempo Real */
.live-toast {
  position: fixed;
  top: 90px;
  right: 30px;
  z-index: 1000;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 22px;
  background: rgba(16, 24, 39, 0.95);
  border: 1px solid rgba(59, 130, 246, 0.6);
  box-shadow: 0 10px 30px rgba(37, 99, 235, 0.4);
}

.toast-bolt {
  font-size: 1.8rem;
  animation: bounce 1s infinite alternate;
}

@keyframes bounce {
  from { transform: translateY(-3px); }
  to { transform: translateY(3px); }
}

.toast-info {
  font-size: 0.95rem;
}

.highlight-team {
  font-weight: 800;
  color: #60a5fa;
}

.toast-proof {
  display: block;
  font-size: 0.8rem;
  color: var(--text-muted);
}

.toast-slide-enter-active,
.toast-slide-leave-active {
  transition: all 0.4s ease;
}

.toast-slide-enter-from,
.toast-slide-leave-to {
  opacity: 0;
  transform: translateX(60px);
}

/* Header */
.telao-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 28px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 20px;
}

.title-wrap h2 {
  font-size: 1.9rem;
  font-weight: 900;
  letter-spacing: -0.02em;
}

.title-wrap p {
  color: var(--text-muted);
  font-size: 1rem;
}

.header-stats {
  display: flex;
  gap: 16px;
}

.stat-box {
  padding: 12px 20px;
  text-align: right;
  min-width: 170px;
}

.stat-label {
  display: block;
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--text-sub);
  letter-spacing: 0.08em;
}

.stat-value {
  font-size: 1.8rem;
  font-weight: 900;
  font-family: var(--font-mono);
}

.text-accent {
  color: #38bdf8;
}

/* PÓDIO */
.podium-section {
  display: grid;
  grid-template-columns: 1fr 1.2fr 1fr;
  gap: 20px;
  align-items: flex-end;
  margin-bottom: 40px;
}

.podium-card {
  text-align: center;
  padding: 24px 16px 0;
  position: relative;
  overflow: hidden;
  transition: transform 0.3s ease;
}

.podium-card:hover {
  transform: translateY(-4px);
}

.podium-badge {
  display: inline-block;
  padding: 6px 14px;
  border-radius: 9999px;
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  background: rgba(255, 255, 255, 0.08);
  margin-bottom: 12px;
}

.crown-icon {
  font-size: 2.4rem;
  margin-bottom: -8px;
  filter: drop-shadow(0 0 10px rgba(251, 191, 36, 0.8));
  animation: float 2s infinite ease-in-out;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

.gold-badge {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.3), rgba(217, 119, 6, 0.3));
  color: #fbbf24;
  border: 1px solid rgba(251, 191, 36, 0.4);
}

.team-avatar {
  width: 72px;
  height: 72px;
  border-radius: 20px;
  margin: 0 auto 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.6rem;
  font-weight: 900;
  background: #1f2937;
  border: 3px solid #3b82f6;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}

.gold-avatar {
  width: 90px;
  height: 90px;
  font-size: 2rem;
  border-width: 4px;
  box-shadow: 0 0 25px rgba(245, 158, 11, 0.45);
}

.team-name {
  font-size: 1.25rem;
  font-weight: 800;
  margin-bottom: 4px;
}

.gold-name {
  font-size: 1.55rem;
  background: linear-gradient(135deg, #ffffff 40%, #fbbf24);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.team-class {
  display: block;
  font-size: 0.82rem;
  color: var(--text-muted);
  margin-bottom: 14px;
}

.team-points {
  margin-bottom: 18px;
}

.points-num {
  font-size: 2.2rem;
  font-weight: 900;
  font-family: var(--font-mono);
}

.gold-points .points-num {
  font-size: 2.8rem;
  color: #fbbf24;
}

.points-label {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-sub);
  margin-left: 4px;
}

.pedestal {
  height: 12px;
  border-radius: 6px 6px 0 0;
  margin-top: 10px;
}

.pedestal-gold { background: linear-gradient(90deg, #f59e0b, #fbbf24, #f59e0b); height: 18px; }
.pedestal-silver { background: linear-gradient(90deg, #94a3b8, #cbd5e1, #94a3b8); }
.pedestal-bronze { background: linear-gradient(90deg, #b45309, #d97706, #b45309); }

/* LISTA FLIP-LIST ANIMADA */
.leaderboard-section {
  margin-top: 20px;
}

.section-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-muted);
  margin-bottom: 16px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.teams-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: relative;
}

.team-row {
  display: flex;
  align-items: center;
  padding: 14px 24px;
  gap: 18px;
  transition: all 0.5s ease;
}

.team-row:hover {
  background: rgba(31, 41, 55, 0.8);
  border-color: rgba(255, 255, 255, 0.15);
}

.pos-badge {
  font-size: 1.2rem;
  font-weight: 900;
  font-family: var(--font-mono);
  color: var(--text-muted);
  min-width: 44px;
}

.team-indicator {
  width: 12px;
  height: 38px;
  border-radius: 6px;
}

.team-meta {
  flex: 1;
}

.team-title {
  display: block;
  font-size: 1.15rem;
  font-weight: 700;
}

.team-sub {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.team-score {
  text-align: right;
}

.score-val {
  font-size: 1.6rem;
  font-weight: 900;
  font-family: var(--font-mono);
  color: #38bdf8;
}

.score-unit {
  font-size: 0.75rem;
  color: var(--text-sub);
  margin-left: 4px;
  font-weight: 700;
}

/* Animação Vue Flip List */
.flip-list-move {
  transition: transform 0.6s cubic-bezier(0.2, 1, 0.3, 1);
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  margin-top: 40px;
}

.empty-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 12px;
}

@media (max-width: 900px) {
  .podium-section {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}
</style>
