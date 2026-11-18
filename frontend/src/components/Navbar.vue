<template>
  <div>
    <!-- Faixa Geométrica Oficial 7ª JENPEX 2026 -->
    <div class="jenpex-geometric-bar" aria-hidden="true"></div>

    <header v-if="!isFullscreen" class="navbar-header glass-panel">
      <div class="brand">
        <div class="geometric-emblem" aria-hidden="true">
          <span class="geo-sq geo-green"></span>
          <span class="geo-sq geo-yellow"></span>
          <span class="geo-sq geo-orange"></span>
          <span class="geo-sq geo-white"></span>
        </div>
        <div class="brand-text">
          <h1>7ª JENPEX 2026 • GINCANA</h1>
          <span class="sub-brand">IFMT — CAMPUS CAMPO NOVO DO PARECIS</span>
        </div>
      </div>

      <!-- Navegação entre as 3 Interfaces Independentes -->
      <nav class="nav-links" aria-label="Interfaces do sistema">
        <a
          href="#cadastro"
          :class="['nav-btn', currentView === 'cadastro' ? 'active' : '']"
          @click.prevent="$emit('change-view', 'cadastro')"
        >
          📝 Recepção (#cadastro)
        </a>
        <a
          href="#mesa"
          :class="['nav-btn', currentView === 'mesa' ? 'active' : '']"
          @click.prevent="$emit('change-view', 'mesa')"
        >
          🎮 Chefe de Mesa (#mesa)
        </a>
        <a
          href="#ranking"
          :class="['nav-btn', currentView === 'ranking' ? 'active' : '']"
          @click.prevent="$emit('change-view', 'ranking')"
        >
          🖥️ Ranking Top 10 (#ranking)
        </a>
      </nav>

      <!-- Indicador de Conexão com o Servidor Central na Rede Local -->
      <div class="nav-actions">
        <div :class="['badge-live', isConnected ? 'online' : 'offline']">
          <span :class="['pulse-dot', isConnected ? 'green' : 'red']"></span>
          <span>{{ isConnected ? 'Servidor LAN Conectado' : 'Servidor Indisponível' }}</span>
        </div>

        <button
          type="button"
          class="btn-icon"
          title="Alternar Modo Tela Cheia (F11)"
          @click="toggleFullscreen"
        >
          ⛶
        </button>
      </div>
    </header>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

defineProps({
  currentView: {
    type: String,
    required: true
  },
  isConnected: {
    type: Boolean,
    default: false
  }
})

defineEmits(['change-view'])

const isFullscreen = ref(false)

function syncFullscreenState() {
  isFullscreen.value = Boolean(document.fullscreenElement)
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(() => {})
  } else if (document.exitFullscreen) {
    document.exitFullscreen().catch(() => {})
  }
}

onMounted(() => {
  document.addEventListener('fullscreenchange', syncFullscreenState)
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', syncFullscreenState)
})
</script>

<style scoped>
.navbar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  margin: 12px 24px;
  border-radius: 14px;
  background: #FFFFFF;
  border: 1px solid #D9E1EB;
  box-shadow: 0 3px 10px rgba(32, 36, 93, 0.05);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.geometric-emblem {
  display: grid;
  grid-template-columns: repeat(2, 14px);
  grid-template-rows: repeat(2, 14px);
  gap: 3px;
  transform: rotate(45deg);
  margin: 4px 6px 4px 4px;
}

.geo-sq {
  display: block;
  width: 14px;
  height: 14px;
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
.geo-white {
  background: #20245D;
}

.brand-text h1 {
  font-size: 1.2rem;
  font-weight: 900;
  letter-spacing: 0.02em;
  color: #20245D;
  line-height: 1.15;
}

.sub-brand {
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: #008F83;
  text-transform: uppercase;
}

/* Container do menu com fundo claro e borda discreta #D9E1EB */
.nav-links {
  display: flex;
  gap: 8px;
  background: #F0F4F9;
  padding: 6px;
  border-radius: 12px;
  border: 1px solid #D9E1EB;
}

/* Botões brancos com textos em azul institucional #20245D e alta legibilidade */
.nav-btn {
  text-decoration: none;
  background: #FFFFFF;
  border: 1px solid #D9E1EB;
  color: #20245D;
  padding: 9px 18px;
  border-radius: 9px;
  font-size: 0.95rem;
  font-weight: 700;
  font-family: var(--font-display);
  cursor: pointer;
  transition: all 0.16s ease;
  box-shadow: 0 1px 3px rgba(32, 36, 93, 0.04);
}

.nav-btn:hover {
  border-color: #008F83;
  color: #008F83;
  background: #FFFFFF;
}

/* Opção selecionada destacada em verde #008F83 com texto branco */
.nav-btn.active {
  background: #008F83;
  color: #FFFFFF;
  border-color: #008F83;
  box-shadow: 0 3px 8px rgba(0, 143, 131, 0.25);
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-icon {
  background: #FFFFFF;
  border: 1px solid #D9E1EB;
  color: #20245D;
  font-size: 1.05rem;
  font-weight: 700;
  padding: 8px 13px;
  border-radius: 9px;
  cursor: pointer;
  transition: all 0.16s;
}

.btn-icon:hover {
  background: #F0F4F9;
  border-color: #008F83;
  color: #008F83;
}

@media (max-width: 960px) {
  .navbar-header {
    flex-direction: column;
    gap: 12px;
    margin: 10px 14px;
  }
  .nav-links {
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>
