<template>
  <header class="navbar-header glass-panel">
    <div class="brand">
      <span class="trophy-icon">🏆</span>
      <div class="brand-text">
        <h1>GINCANA TECNOLÓGICA</h1>
        <span class="sub-brand">JENPEX • IFMT</span>
      </div>
    </div>

    <!-- Navegação de Abas -->
    <nav class="nav-links">
      <button 
        :class="['nav-btn', currentView === 'telao' ? 'active' : '']"
        @click="$emit('change-view', 'telao')"
      >
        🖥️ Telão do Ranking
      </button>
      <button 
        :class="['nav-btn', currentView === 'jurado' ? 'active' : '']"
        @click="$emit('change-view', 'jurado')"
      >
        📱 Painel do Jurado
      </button>
    </nav>

    <!-- Indicador de Status do WebSocket e Tela Cheia -->
    <div class="nav-actions">
      <div :class="['badge-live', isConnected ? 'online' : 'offline']">
        <span :class="['pulse-dot', isConnected ? 'green' : 'red']"></span>
        <span>{{ isConnected ? 'Tempo Real Ativo' : 'Reconectando...' }}</span>
      </div>

      <button class="btn-icon" @click="toggleFullscreen" title="Tela Cheia (F11)">
        ⛶
      </button>
    </div>
  </header>
</template>

<script setup>
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

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(err => {
      console.warn("Tela cheia indisponível:", err)
    })
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen()
    }
  }
}
</script>

<style scoped>
.navbar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 28px;
  margin: 16px 24px;
  border-radius: 20px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.trophy-icon {
  font-size: 2.2rem;
  filter: drop-shadow(0 0 12px rgba(251, 191, 36, 0.5));
}

.brand-text h1 {
  font-size: 1.25rem;
  font-weight: 900;
  letter-spacing: 0.05em;
  background: linear-gradient(135deg, #ffffff 40%, #94a3b8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1.1;
}

.sub-brand {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  color: #38bdf8;
  text-transform: uppercase;
}

.nav-links {
  display: flex;
  gap: 8px;
  background: rgba(0, 0, 0, 0.3);
  padding: 4px;
  border-radius: 14px;
  border: 1px solid var(--border-color);
}

.nav-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  padding: 8px 18px;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 600;
  font-family: var(--font-display);
  cursor: pointer;
  transition: all 0.2s ease;
}

.nav-btn:hover {
  color: var(--text-main);
}

.nav-btn.active {
  background: rgba(59, 130, 246, 0.25);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.4);
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.badge-live.offline {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
  border-color: rgba(239, 68, 68, 0.3);
}

.pulse-dot.red {
  background-color: #ef4444;
  animation: pulse-red 1.8s infinite;
}

@keyframes pulse-red {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

.btn-icon {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  font-size: 1.1rem;
  padding: 8px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-icon:hover {
  background: rgba(255, 255, 255, 0.12);
}

@media (max-width: 768px) {
  .navbar-header {
    flex-direction: column;
    gap: 14px;
    margin: 10px;
  }
}
</style>
