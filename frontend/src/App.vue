<template>
  <div class="app-layout">
    <Navbar
      :currentView="currentView"
      :isConnected="isServerOnline"
      @change-view="navegarPara"
    />

    <main class="main-content">
      <!-- Interface 1: Recepção / Cadastro Manual de Participantes (/#cadastro) -->
      <CadastroParticipantes
        v-if="currentView === 'cadastro'"
        :participantes="participantesConhecidos"
        :isServerOnline="isServerOnline"
        @participante-cadastrado="registrarParticipanteEmMemoria"
        @retry-connection="sincronizarComServidor"
      />

      <!-- Interface 2: Painel do Chefe de Mesa (/#mesa) -->
      <PainelChefeMesa
        v-else-if="currentView === 'mesa'"
        :participantesConhecidos="participantesConhecidos"
        :rankingAtual="ranking"
        :isServerOnline="isServerOnline"
        @pontuacao-registrada="aoRegistrarPontuacaoNaMesa"
        @retry-connection="sincronizarComServidor"
      />

      <!-- Interface 4: Área do aluno (/#notas) -->
      <MinhasNotas v-else-if="currentView === 'notas'" />

      <!-- Interface 5: Administração (/#admin) -->
      <PainelAdmin v-else-if="currentView === 'admin'" />

      <!-- Interface 3: Ranking Geral Top 10 para TV (/#ranking) -->
      <TelaoRanking
        v-else
        :ranking="ranking"
        :participantesConhecidos="participantesConhecidos"
        :lastScoreToast="lastScoreToast"
        :isServerOnline="isServerOnline"
        :ultimaAtualizacao="ultimaAtualizacaoRanking"
      />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import Navbar from './components/Navbar.vue'
import CadastroParticipantes from './components/CadastroParticipantes.vue'
import PainelChefeMesa from './components/PainelChefeMesa.vue'
import TelaoRanking from './components/TelaoRanking.vue'
import MinhasNotas from './components/MinhasNotas.vue'
import PainelAdmin from './components/PainelAdmin.vue'
import { getDisplayRanking } from './services/api.js'

const ROTAS_VALIDAS = new Set(['cadastro', 'mesa', 'ranking', 'notas', 'admin'])

function resolverRotaPorHash() {
  const rawHash = (window.location.hash || '').replace(/^#\/?/, '').trim().toLowerCase()
  if (ROTAS_VALIDAS.has(rawHash)) {
    return rawHash
  }
  return 'ranking'
}

const currentView = ref(resolverRotaPorHash())
const isServerOnline = ref(false)
const ranking = ref([])
const participantesConhecidos = ref([])
const lastScoreToast = ref(null)
const ultimaAtualizacaoRanking = ref('')

let pollingInterval = null
const POLLING_INTERVAL_MS = 2000
let requisicaoEmAndamento = false
let mapaPontosAnteriores = new Map()
let primeiraCargaConcluida = false

function navegarPara(view) {
  const destino = ROTAS_VALIDAS.has(view) ? view : 'ranking'
  currentView.value = destino
  if (window.location.hash !== `#${destino}`) {
    window.location.hash = `#${destino}`
  }
}

function aoMudarHash() {
  currentView.value = resolverRotaPorHash()
}

function exibirToastPontuacao(dadosToast) {
  lastScoreToast.value = dadosToast
  setTimeout(() => {
    lastScoreToast.value = null
  }, 4500)
}

function registrarParticipanteEmMemoria(novoParticipante) {
  const existe = participantesConhecidos.value.some(
    (p) => p.participant_code === novoParticipante.participant_code
  )
  if (!existe) {
    participantesConhecidos.value = [novoParticipante, ...participantesConhecidos.value]
  }
}

function aoRegistrarPontuacaoNaMesa(evento) {
  exibirToastPontuacao({
    participante: evento.participant_name || `Participante #${evento.participant_code}`,
    pontos: evento.points,
    jogo: evento.game_name
  })
  sincronizarComServidor()
}

// Consulta periódica ao servidor central a cada 2 segundos (sem substituir por dados simulados em caso de erro)
async function sincronizarComServidor() {
  if (requisicaoEmAndamento) return
  requisicaoEmAndamento = true

  try {
    const data = await getDisplayRanking()
    isServerOnline.value = true
    ultimaAtualizacaoRanking.value = new Date().toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })

    if (data && Array.isArray(data.ranking)) {
      const novaLista = data.ranking

      // Detecta aumento de pontuação no ranking para acionar efeito visual no Telão
      if (primeiraCargaConcluida) {
        for (const item of novaLista) {
          const code = item.participant_code
          const pontosAntigos = mapaPontosAnteriores.get(code)
          if (pontosAntigos !== undefined && item.total_points > pontosAntigos) {
            const diferenca = item.total_points - pontosAntigos
            const conhecido = participantesConhecidos.value.find((p) => p.participant_code === code)
            exibirToastPontuacao({
              participante: item.username || conhecido?.nomeExibicao || `Participante #${code}`,
              pontos: diferenca,
              jogo: 'Pontuação atualizada'
            })
            break
          }
        }
      }

      const novoMapa = new Map()
      for (const item of novaLista) {
        if (item.participant_code) {
          novoMapa.set(item.participant_code, item.total_points)
        }
      }
      mapaPontosAnteriores = novoMapa
      primeiraCargaConcluida = true

      // Preserva exatamente os dados reais enviados pelo servidor (até 10 posições no componente TelaoRanking)
      ranking.value = novaLista
    }
  } catch {
    // Em caso de falha, sinaliza indisponibilidade e preserva os dados já existentes em tela
    isServerOnline.value = false
  } finally {
    requisicaoEmAndamento = false
  }
}

onMounted(() => {
  if (!window.location.hash) {
    window.location.hash = `#${currentView.value}`
  }
  window.addEventListener('hashchange', aoMudarHash)

  sincronizarComServidor()
  pollingInterval = setInterval(() => {
    sincronizarComServidor()
  }, POLLING_INTERVAL_MS)
})

onUnmounted(() => {
  window.removeEventListener('hashchange', aoMudarHash)
  if (pollingInterval) clearInterval(pollingInterval)
})
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
}
</style>
