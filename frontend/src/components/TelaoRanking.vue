<template>
  <div :class="['telao-container', { 'tv-fullscreen-mode': emTelaCheia, 'is-disconnected': !isServerOnline }]">
    <!-- Notificação Flutuante de Pontos em Tempo Real -->
    <transition name="toast-slide">
      <div v-if="lastScoreToast" class="live-toast glass-panel">
        <span class="toast-bolt">⚡</span>
        <div class="toast-info">
          <strong>+{{ lastScoreToast.pontos }} pontos</strong> para
          <span class="highlight-participant">{{ lastScoreToast.participante }}</span>
          <span v-if="lastScoreToast.jogo" class="toast-game">• {{ lastScoreToast.jogo }}</span>
        </div>
      </div>
    </transition>

    <!-- Cabeçalho do Ranking (#E8EDF7 com Títulos em Azul Institucional #20245D) -->
    <header class="telao-header">
      <div class="header-left-brand">
        <div class="tv-brand-emblem" aria-hidden="true">
          <span class="geo-sq geo-green"></span>
          <span class="geo-sq geo-yellow"></span>
          <span class="geo-sq geo-orange"></span>
          <span class="geo-sq geo-navy"></span>
        </div>
        <div class="title-wrap">
          <div class="event-pill">7ª JENPEX 2026 • IFMT CAMPO NOVO DO PARECIS</div>
          <h2>RANKING GERAL TOP 10</h2>
          <p v-if="isServerOnline">Classificação oficial em tempo real • empate: vence quem se cadastrou primeiro</p>
          <p v-else class="subtitle-disconnected">
            Sincronização pausada — aguardando reconexão com o servidor local
          </p>
        </div>
      </div>

      <div class="header-right">
        <!-- Aviso Discreto de Desconexão integrado ao cabeçalho para não parecer tempo real ativo -->
        <div v-if="!isServerOnline" class="tv-offline-pill" role="alert">
          <span class="offline-dot"></span>
          <div class="offline-text">
            <strong>Servidor desconectado</strong>
            <span>Última leitura{{ ultimaAtualizacao ? ` às ${ultimaAtualizacao}` : '' }} (reconectando...)</span>
          </div>
        </div>

        <div class="header-stats">
          <div class="stat-box">
            <span class="stat-label">CLASSIFICADOS NO TOP 10</span>
            <span class="stat-value">{{ top10Ranking.length }} <small>/ 10</small></span>
          </div>
        </div>

        <!-- Botão de Tela Cheia oculto automaticamente quando já estiver no modo TV Tela Cheia -->
        <button
          v-if="!emTelaCheia"
          type="button"
          class="btn-fullscreen-tv"
          title="Ativar Modo Televisão em Tela Cheia"
          @click="alternarTelaCheia"
        >
          ⛶ Modo TV (Tela Cheia)
        </button>
      </div>
    </header>

    <!-- Conteúdo Principal quando há participantes retornados pelo servidor -->
    <div v-if="top10Ranking.length > 0" class="tv-stage">
      <!-- PÓDIO (1º, 2º e 3º Colocados) -->
      <section class="podium-section" aria-label="Pódio Top 3">
        <!-- 2º LUGAR (Prata) -->
        <div v-if="top3[1]" class="podium-card silver">
          <div class="podium-badge">🥈 {{ top3[1].posicao }}º LUGAR</div>
          <div class="participant-avatar silver-avatar">
            {{ obterIniciais(top3[1].nomeExibicao) }}
          </div>
          <h3 class="participant-name">{{ top3[1].nomeExibicao }}</h3>
          <span class="participant-code-tag">#{{ top3[1].participant_code }}</span>
          <div class="game-chips podium-chips">
            <span v-for="jogo in colunasJogos" :key="jogo"
              :class="['game-chip', pontosNoJogo(top3[1], jogo) === null ? 'chip-empty' : '']">
              {{ jogo }} <b>{{ pontosNoJogo(top3[1], jogo) ?? '–' }}</b>
            </span>
          </div>
          <div class="participant-points">
            <span class="points-num">{{ top3[1].total_pontos }}</span>
            <span class="points-label">PTS TOTAL</span>
          </div>
          <div class="pedestal pedestal-silver"></div>
        </div>

        <!-- 1º LUGAR (Ouro) -->
        <div v-if="top3[0]" class="podium-card gold">
          <div class="crown-icon">👑</div>
          <div class="podium-badge gold-badge">🥇 {{ top3[0].posicao }}º LUGAR • LÍDER</div>
          <div class="participant-avatar gold-avatar">
            {{ obterIniciais(top3[0].nomeExibicao) }}
          </div>
          <h3 class="participant-name gold-name">{{ top3[0].nomeExibicao }}</h3>
          <span class="participant-code-tag">#{{ top3[0].participant_code }}</span>
          <div class="game-chips podium-chips">
            <span v-for="jogo in colunasJogos" :key="jogo"
              :class="['game-chip', pontosNoJogo(top3[0], jogo) === null ? 'chip-empty' : '']">
              {{ jogo }} <b>{{ pontosNoJogo(top3[0], jogo) ?? '–' }}</b>
            </span>
          </div>
          <div class="participant-points gold-points">
            <span class="points-num">{{ top3[0].total_pontos }}</span>
            <span class="points-label">PTS TOTAL</span>
          </div>
          <div class="pedestal pedestal-gold"></div>
        </div>

        <!-- 3º LUGAR (Bronze) -->
        <div v-if="top3[2]" class="podium-card bronze">
          <div class="podium-badge">🥉 {{ top3[2].posicao }}º LUGAR</div>
          <div class="participant-avatar bronze-avatar">
            {{ obterIniciais(top3[2].nomeExibicao) }}
          </div>
          <h3 class="participant-name">{{ top3[2].nomeExibicao }}</h3>
          <span class="participant-code-tag">#{{ top3[2].participant_code }}</span>
          <div class="game-chips podium-chips">
            <span v-for="jogo in colunasJogos" :key="jogo"
              :class="['game-chip', pontosNoJogo(top3[2], jogo) === null ? 'chip-empty' : '']">
              {{ jogo }} <b>{{ pontosNoJogo(top3[2], jogo) ?? '–' }}</b>
            </span>
          </div>
          <div class="participant-points">
            <span class="points-num">{{ top3[2].total_pontos }}</span>
            <span class="points-label">PTS TOTAL</span>
          </div>
          <div class="pedestal pedestal-bronze"></div>
        </div>
      </section>

      <!-- CLASSIFICAÇÃO DO 4º AO 10º LUGAR -->
      <section class="leaderboard-section" aria-label="Classificação do 4º ao 10º lugar">
        <div class="leaderboard-header">
          <h3 class="section-title">Classificação — 4º ao 10º Lugar</h3>
          <span v-if="isServerOnline" class="sync-indicator">
            <span class="sync-dot-live"></span>
            Sincronização automática a cada 2s
            <template v-if="ultimaAtualizacao"> • Atualizado às {{ ultimaAtualizacao }}</template>
          </span>
          <span v-else class="sync-indicator sync-paused">
            ⚠️ Dados congelados (última sincronização{{ ultimaAtualizacao ? ` às ${ultimaAtualizacao}` : '' }})
          </span>
        </div>

        <TransitionGroup
          v-if="colocados4a10.length > 0"
          name="flip-list"
          tag="div"
          class="participants-grid"
        >
          <div
            v-for="participante in colocados4a10"
            :key="participante.participant_code || participante.id"
            class="participant-row"
          >
            <div class="pos-badge">{{ participante.posicao }}º</div>
            <div class="row-accent-bar"></div>
            <div class="participant-meta">
              <span class="participant-title">
                {{ participante.nomeExibicao }}
                <small class="code-inline">#{{ participante.participant_code }}</small>
              </span>
              <div class="game-chips">
                <span v-for="jogo in colunasJogos" :key="jogo"
                  :class="['game-chip', pontosNoJogo(participante, jogo) === null ? 'chip-empty' : '']">
                  {{ jogo }} <b>{{ pontosNoJogo(participante, jogo) ?? '–' }}</b>
                </span>
              </div>
            </div>
            <div class="participant-score">
              <span class="score-val">{{ participante.total_pontos }}</span>
              <span class="score-unit">TOTAL</span>
            </div>
          </div>
        </TransitionGroup>

        <div v-else class="partial-ranking-note">
          <span>
            Exibindo os {{ top10Ranking.length }} participantes retornados pelo servidor no momento.
            As posições de 4º a 10º lugar serão preenchidas automaticamente conforme novos dados forem disponibilizados pela API.
          </span>
        </div>
      </section>
    </div>

    <!-- Estado Vazio Real (sem inventar dados fictícios) -->
    <div v-else class="empty-state">
      <span class="empty-icon">🏆</span>
      <h3>Aguardando pontuações confirmadas no servidor</h3>
      <p v-if="isServerOnline">
        O servidor está conectado, mas ainda não há participantes pontuados no ranking oficial (<code>GET /display/ranking</code>).
      </p>
      <p v-else>
        Aguardando conexão com o servidor central da 7ª JENPEX 2026 na rede local...
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import confetti from 'canvas-confetti'

const props = defineProps({
  ranking: {
    type: Array,
    default: () => []
  },
  jogos: {
    type: Array,
    default: () => []
  },
  participantesConhecidos: {
    type: Array,
    default: () => []
  },
  lastScoreToast: {
    type: Object,
    default: null
  },
  isServerOnline: {
    type: Boolean,
    default: false
  },
  ultimaAtualizacao: {
    type: String,
    default: ''
  }
})

const emTelaCheia = ref(false)

// Normaliza e limita estritamente aos 10 melhores reais retornados pelo servidor
const top10Ranking = computed(() => {
  return props.ranking.slice(0, 10).map((entry, idx) => {
    const code = (entry.participant_code || '').toUpperCase()
    const conhecido = props.participantesConhecidos.find(
      (p) => (p.participant_code || '').toUpperCase() === code
    )

    // Prioriza nome completo vindo da API (quando existir) ou do cadastro conhecido;
    // caso o backend retorne apenas participant_code, exibe o código real sem inventar nomes.
    const nomeCompleto =
      entry.username ||
      entry.full_name ||
      entry.nome ||
      conhecido?.nomeExibicao ||
      conhecido?.nome ||
      conhecido?.username ||
      (code ? `Participante #${code}` : `Posição ${idx + 1}`)

    return {
      id: code || idx + 1,
      posicao: entry.position ?? entry.posicao ?? idx + 1,
      participant_code: code || '---',
      nomeExibicao: nomeCompleto,
      total_pontos: entry.total_points ?? entry.total_pontos ?? 0,
      pontosPorJogo: Object.fromEntries((entry.games || []).map((g) => [g.game_name, g.points]))
    }
  })
})

const top3 = computed(() => top10Ranking.value.slice(0, 3))

const colocados4a10 = computed(() => top10Ranking.value.slice(3, 10))

// Colunas de jogos: jogos ativos informados pelo servidor (ou os que aparecem nas notas)
const colunasJogos = computed(() => {
  if (props.jogos.length) return props.jogos
  const nomes = new Set()
  for (const item of top10Ranking.value) {
    Object.keys(item.pontosPorJogo).forEach((n) => nomes.add(n))
  }
  return [...nomes]
})

function pontosNoJogo(participante, jogo) {
  const valor = participante?.pontosPorJogo?.[jogo]
  return valor === undefined ? null : valor
}

function obterIniciais(nome) {
  if (!nome) return 'JP'
  const limpo = nome.replace(/^Participante\s+#/i, '').trim()
  const partes = limpo.split(/\s+/).filter(Boolean)
  if (partes.length >= 2) {
    return (partes[0][0] + partes[partes.length - 1][0]).toUpperCase()
  }
  return limpo.substring(0, 2).toUpperCase()
}

function atualizarEstadoFullscreen() {
  emTelaCheia.value = Boolean(document.fullscreenElement)
}

function alternarTelaCheia() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(() => {})
  } else if (document.exitFullscreen) {
    document.exitFullscreen().catch(() => {})
  }
}

// Efeito Sonoro nativo usando Web Audio API (100% offline, sem dependência de arquivos externos)
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
  } catch {
    // Áudio aguardando interação na página
  }
}

watch(
  () => props.lastScoreToast,
  (newVal) => {
    if (newVal) {
      playBeep(659.25, 'sine', 0.4)
      try {
        confetti({
          particleCount: 55,
          spread: 65,
          origin: { y: 0.8 },
          colors: ['#008F83', '#FF641F', '#F59E0B', '#20245D']
        })
      } catch {
        // Ignora caso canvas-confetti não possa renderizar
      }
    }
  }
)

onMounted(() => {
  atualizarEstadoFullscreen()
  document.addEventListener('fullscreenchange', atualizarEstadoFullscreen)
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', atualizarEstadoFullscreen)
})
</script>

<style scoped>
.game-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}
.podium-chips {
  justify-content: center;
  margin: 6px 0;
}
.game-chip {
  font-size: 0.72rem;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(32, 36, 93, 0.1);
  color: #20245D;
  white-space: nowrap;
}
.game-chip b {
  margin-left: 2px;
}
.chip-empty {
  opacity: 0.45;
}
.code-inline {
  font-size: 0.7em;
  opacity: 0.6;
  font-weight: 500;
  margin-left: 6px;
  letter-spacing: 1px;
}

/* Container do Ranking com tom azul-acinzentado suave para TV */
.telao-container {
  max-width: 1760px;
  margin: 0 auto;
  padding: 12px 24px 24px;
  position: relative;
  background-color: #E2E8F4;
  border-radius: 16px;
}

/* Modo Televisão em Tela Cheia: utiliza 100% da área útil da TV Full HD */
.telao-container.tv-fullscreen-mode {
  max-width: 100%;
  width: 100vw;
  min-height: calc(100vh - 6px);
  margin: 0;
  padding: 18px 36px 24px;
  border-radius: 0;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}

/* Cabeçalho do Ranking em #E8EDF7 com Títulos em #20245D */
.telao-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  margin-bottom: 18px;
  background: #E8EDF7;
  padding: 16px 24px;
  border-radius: 14px;
  border: 1.5px solid #D9E1EB;
  border-left: 6px solid #008F83;
  box-shadow: 0 3px 10px rgba(32, 36, 93, 0.05);
}

.header-left-brand {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* Emblema Geométrico da JENPEX visível inclusive no Modo TV Tela Cheia */
.tv-brand-emblem {
  display: grid;
  grid-template-columns: repeat(2, 15px);
  grid-template-rows: repeat(2, 15px);
  gap: 3px;
  transform: rotate(45deg);
  margin: 6px 8px 6px 6px;
  flex-shrink: 0;
}

.geo-sq {
  display: block;
  width: 15px;
  height: 15px;
  border-radius: 3px;
}

.geo-green {
  background: #008F83;
}
.geo-yellow {
  background: #F59E0B;
}
.geo-orange {
  background: #FF641F;
}
.geo-navy {
  background: #20245D;
}

.event-pill {
  display: inline-block;
  font-size: 0.78rem;
  font-weight: 900;
  letter-spacing: 0.1em;
  color: #008F83;
  margin-bottom: 2px;
}

.title-wrap h2 {
  font-size: 2.1rem;
  font-weight: 900;
  letter-spacing: -0.01em;
  color: #20245D;
  line-height: 1.1;
}

.title-wrap p {
  color: #526078;
  font-size: 0.96rem;
  font-weight: 600;
  margin-top: 2px;
}

.subtitle-disconnected {
  color: #C2410C !important;
  font-weight: 700 !important;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

/* Aviso discreto e legível de desconexão */
.tv-offline-pill {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #FFF4ED;
  border: 1.5px solid #FDBA8C;
  color: #9A3412;
  padding: 8px 14px;
  border-radius: 10px;
}

.offline-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #FF641F;
  flex-shrink: 0;
}

.offline-text {
  display: flex;
  flex-direction: column;
  font-size: 0.78rem;
  line-height: 1.25;
}

.offline-text strong {
  font-size: 0.84rem;
  color: #9A3412;
}

.header-stats {
  display: flex;
  gap: 12px;
}

/* Cartões brancos para os indicadores do cabeçalho */
.stat-box {
  padding: 10px 18px;
  text-align: right;
  min-width: 165px;
  background: #FFFFFF;
  border: 1.5px solid #D9E1EB;
  border-top: 3px solid #008F83;
  border-radius: 12px;
  box-shadow: 0 2px 6px rgba(32, 36, 93, 0.04);
}

.stat-box-accent {
  border-top-color: #FF641F;
}

.stat-label {
  display: block;
  font-size: 0.7rem;
  font-weight: 800;
  color: #526078;
  letter-spacing: 0.06em;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 900;
  font-family: var(--font-mono);
  color: #20245D;
}

.stat-value small {
  font-size: 0.95rem;
  color: #526078;
}

.text-orange {
  color: #FF641F;
}

.btn-fullscreen-tv {
  background: #008F83;
  border: 1px solid #007369;
  color: #FFFFFF;
  padding: 12px 18px;
  border-radius: 10px;
  font-family: var(--font-display);
  font-weight: 800;
  font-size: 0.92rem;
  cursor: pointer;
  transition: background-color 0.16s ease;
  white-space: nowrap;
}

.btn-fullscreen-tv:hover {
  background: #007369;
}

/* Toast em Tempo Real */
.live-toast {
  position: fixed;
  top: 24px;
  right: 28px;
  z-index: 1000;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 22px;
  background: #20245D;
  color: #FFFFFF;
  border: 2px solid #FF641F;
  border-radius: 12px;
  box-shadow: 0 10px 26px rgba(32, 36, 93, 0.25);
}

.toast-bolt {
  font-size: 1.7rem;
}

.toast-info {
  font-size: 1.02rem;
  color: #FFFFFF;
}

.highlight-participant {
  font-weight: 900;
  color: #FDE047;
}

.toast-game {
  display: block;
  font-size: 0.85rem;
  color: #CBD5E1;
}

.toast-slide-enter-active,
.toast-slide-leave-active {
  transition: opacity 0.35s ease, transform 0.35s ease;
}

.toast-slide-enter-from,
.toast-slide-leave-to {
  opacity: 0;
  transform: translateX(40px);
}

/* PÓDIO TOP 3 — Superfícies suaves (#F8FAFD) para evitar branco excessivamente brilhante na TV */
.podium-section {
  display: grid;
  grid-template-columns: 1fr 1.15fr 1fr;
  gap: 18px;
  align-items: stretch;
  margin-bottom: 18px;
}

.podium-card {
  text-align: center;
  padding: 16px 18px 0;
  position: relative;
  overflow: hidden;
  background: #F8FAFD;
  border: 1.5px solid #D9E1EB;
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 4px 14px rgba(32, 36, 93, 0.06);
}

.podium-card.gold {
  background: #FFFFFF;
  border: 2px solid #FF641F;
  box-shadow: 0 6px 20px rgba(255, 100, 31, 0.14);
}

.podium-card.silver {
  border-color: #94A3B8;
}

.podium-card.bronze {
  border-color: #008F83;
}

.podium-badge {
  display: inline-block;
  align-self: center;
  padding: 5px 14px;
  border-radius: 9999px;
  font-size: 0.84rem;
  font-weight: 900;
  letter-spacing: 0.04em;
  background: #E8EDF7;
  color: #20245D;
  border: 1px solid #D9E1EB;
  margin-bottom: 8px;
}

.crown-icon {
  font-size: 1.85rem;
  margin-bottom: 2px;
}

.gold-badge {
  background: #FFF1EB;
  color: #C2410C;
  border: 1.5px solid #FF641F;
}

.participant-avatar {
  width: 58px;
  height: 58px;
  border-radius: 15px;
  margin: 0 auto 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.35rem;
  font-weight: 900;
  background: #E8EDF7;
  color: #20245D;
  border: 2.5px solid #008F83;
}

.gold-avatar {
  width: 68px;
  height: 68px;
  font-size: 1.65rem;
  border-width: 3px;
  background: #20245D;
  color: #FFFFFF;
  border-color: #FF641F;
}

.silver-avatar {
  border-color: #64748B;
}

.bronze-avatar {
  border-color: #008F83;
}

.participant-name {
  font-size: 1.36rem;
  font-weight: 900;
  margin-bottom: 2px;
  color: #20245D;
}

.gold-name {
  font-size: 1.6rem;
  color: #20245D;
}

.participant-code-tag {
  display: block;
  font-size: 0.72rem;
  font-weight: 600;
  opacity: 0.75;
  font-family: var(--font-mono);
  color: #526078;
  margin-bottom: 6px;
}

.participant-points {
  margin-bottom: 10px;
}

.points-num {
  font-size: 2.2rem;
  font-weight: 900;
  font-family: var(--font-mono);
  color: #008F83;
}

.gold-points .points-num {
  font-size: 2.65rem;
  color: #FF641F;
}

.points-label {
  font-size: 0.85rem;
  font-weight: 800;
  color: #526078;
  margin-left: 4px;
}

.pedestal {
  height: 10px;
  border-radius: 6px 6px 0 0;
  margin-top: auto;
}

.pedestal-gold {
  background: linear-gradient(90deg, #FF641F, #F59E0B, #FF641F);
  height: 13px;
}

.pedestal-silver {
  background: linear-gradient(90deg, #64748B, #94A3B8, #64748B);
}

.pedestal-bronze {
  background: linear-gradient(90deg, #008F83, #00A698, #008F83);
}

/* LISTA 4º AO 10º LUGAR EM GRADE OTIMIZADA PARA TV 1920x1080 */
.leaderboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding: 0 4px;
}

.section-title {
  font-size: 1.05rem;
  font-weight: 900;
  color: #20245D;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.sync-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.86rem;
  font-weight: 700;
  color: #526078;
}

.sync-dot-live {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #008F83;
}

.sync-paused {
  color: #9A3412;
  background: #FFF4ED;
  border: 1px solid #FDBA8C;
  padding: 3px 10px;
  border-radius: 999px;
}

.participants-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px 14px;
}

.participant-row {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  gap: 16px;
  background: #F8FAFD;
  border: 1.5px solid #D9E1EB;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(32, 36, 93, 0.04);
}

.pos-badge {
  font-size: 1.38rem;
  font-weight: 900;
  font-family: var(--font-mono);
  color: #20245D;
  min-width: 46px;
}

.row-accent-bar {
  width: 6px;
  height: 36px;
  border-radius: 4px;
  background: linear-gradient(180deg, #008F83, #FF641F);
}

.participant-meta {
  flex: 1;
  min-width: 0;
}

.participant-title {
  display: block;
  font-size: 1.24rem;
  font-weight: 800;
  color: #20245D;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.participant-sub {
  font-size: 0.86rem;
  font-weight: 600;
  font-family: var(--font-mono);
  color: #526078;
}

.participant-score {
  text-align: right;
}

.score-val {
  font-size: 1.8rem;
  font-weight: 900;
  font-family: var(--font-mono);
  color: #008F83;
}

.score-unit {
  font-size: 0.8rem;
  color: #526078;
  margin-left: 4px;
  font-weight: 800;
}

/* Quando desconectado, reduz levemente o destaque das pontuações antigas para não simular tempo real */
.is-disconnected .tv-stage {
  opacity: 0.92;
}

.partial-ranking-note {
  padding: 16px 20px;
  text-align: center;
  background: #F8FAFD;
  border: 1.5px solid #D9E1EB;
  border-radius: 12px;
  color: #526078;
  font-size: 0.96rem;
  font-weight: 600;
}

.flip-list-move {
  transition: transform 0.45s cubic-bezier(0.2, 1, 0.3, 1);
}

.empty-state {
  text-align: center;
  padding: 60px 24px;
  margin-top: 16px;
  background: #F8FAFD;
  border: 1.5px solid #D9E1EB;
  border-radius: 14px;
}

.empty-icon {
  font-size: 3.2rem;
  display: block;
  margin-bottom: 12px;
}

.empty-state h3 {
  font-size: 1.55rem;
  color: #20245D;
  margin-bottom: 8px;
}

.empty-state p {
  color: #526078;
  font-size: 1.02rem;
}

@media (max-width: 1024px) {
  .telao-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .podium-section,
  .participants-grid {
    grid-template-columns: 1fr;
  }
}
</style>
