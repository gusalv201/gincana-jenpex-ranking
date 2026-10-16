<template>
  <div class="app-layout">
    <Navbar 
      :currentView="currentView" 
      :isConnected="isWsConnected"
      @change-view="currentView = $event"
    />

    <main class="main-content">
      <!-- Visão 1: Telão Oficial do Ranking -->
      <TelaoRanking 
        v-if="currentView === 'telao'"
        :ranking="ranking"
        :lastScoreToast="lastScoreToast"
      />

      <!-- Visão 2: Painel do Jurado / Lançamento de Notas -->
      <PainelJurado 
        v-if="currentView === 'jurado'"
        :equipes="equipes"
        :provas="provas"
        :apiBaseUrl="apiBaseUrl"
        @pontuacao-enviada="handlePontuacaoLocal"
        @dados-atualizados="carregarDadosIniciais"
      />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import Navbar from './components/Navbar.vue'
import TelaoRanking from './components/TelaoRanking.vue'
import PainelJurado from './components/PainelJurado.vue'

// Detecta automaticamente o host (seja localhost ou IP na rede local)
const host = window.location.hostname || 'localhost'
const apiBaseUrl = `http://${host}:8000`
const wsUrl = `ws://${host}:8000/ws/ranking`

const currentView = ref('telao')
const isWsConnected = ref(false)
const ranking = ref([])
const equipes = ref([])
const provas = ref([])
const lastScoreToast = ref(null)

let socket = null
let reconnectInterval = null

// DADOS DIDÁTICOS DE CONTINGÊNCIA (Caso o backend ainda não esteja rodando no 1º dia de aula)
const fallbackRanking = [
  { id: 1, posicao: 1, nome: "CyberPantanal", curso_turma: "Técnico em Informática 3º Ano", cor_hex: "#3B82F6", total_pontos: 320 },
  { id: 2, posicao: 2, nome: "Binários do Cerrado", curso_turma: "Técnico em Informática 2º Ano", cor_hex: "#10B981", total_pontos: 290 },
  { id: 3, posicao: 3, nome: "Algoritmos da Chapada", curso_turma: "Engenharia / Sistemas", cor_hex: "#F59E0B", total_pontos: 250 },
  { id: 4, posicao: 4, nome: "ByteMat Tech", curso_turma: "Técnico em Redes 1º Ano", cor_hex: "#8B5CF6", total_pontos: 210 },
  { id: 5, posicao: 5, nome: "Hackers do Vale", curso_turma: "Análise e Des. Sistemas", cor_hex: "#EC4899", total_pontos: 180 },
  { id: 6, posicao: 6, nome: "NullPointer Masters", curso_turma: "Técnico em Informática 1º Ano", cor_hex: "#6366F1", total_pontos: 150 }
]

const fallbackProvas = [
  { id: 1, titulo: "Quiz de Hardware & Arquitetura", pontos_padrao: 50 },
  { id: 2, titulo: "Desafio de Robótica & Sensores", pontos_padrao: 100 },
  { id: 3, titulo: "Caça ao Bug (Debugging Relâmpago)", pontos_padrao: 80 },
  { id: 4, titulo: "Arrecadação de Lixo Eletrônico", pontos_padrao: 150 },
  { id: 5, titulo: "Torta na Cara Tech", pontos_padrao: 60 }
]

// Carrega os dados iniciais do banco via REST API
async function carregarDadosIniciais() {
  try {
    const resRank = await fetch(`${apiBaseUrl}/api/ranking`)
    if (resRank.ok) {
      const data = await resRank.json()
      ranking.value = data.ranking
    } else {
      ranking.value = fallbackRanking
    }

    const resEq = await fetch(`${apiBaseUrl}/api/equipes`)
    if (resEq.ok) {
      equipes.value = await resEq.json()
    } else {
      equipes.value = fallbackRanking
    }

    const resPr = await fetch(`${apiBaseUrl}/api/provas`)
    if (resPr.ok) {
      provas.value = await resPr.json()
    } else {
      provas.value = fallbackProvas
    }
  } catch (error) {
    console.warn("Backend ainda não conectado. Utilizando dados didáticos de exemplo.", error)
    ranking.value = fallbackRanking
    equipes.value = fallbackRanking
    provas.value = fallbackProvas
  }
}

// Conexão WebSocket em Tempo Real com Reconexão Automática
function conectarWebSocket() {
  try {
    socket = new WebSocket(wsUrl)

    socket.onopen = () => {
      console.log("⚡ [WebSocket] Conectado ao servidor de tempo real da Jenpex!")
      isWsConnected.value = true
    }

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        console.log("📡 [WebSocket] Evento recebido:", payload)

        if (payload.ranking && payload.ranking.ranking) {
          ranking.value = payload.ranking.ranking
        }

        if (payload.evento === 'PONTOS_ATUALIZADOS') {
          lastScoreToast.value = {
            equipe: payload.equipe_nome,
            pontos: payload.pontos_adicionados,
            prova: payload.prova_titulo
          }
          // Fecha o toast após 4.5 segundos
          setTimeout(() => {
            lastScoreToast.value = null
          }, 4500)
        }
      } catch (err) {
        console.error("Erro ao processar mensagem do WebSocket:", err)
      }
    }

    socket.onclose = () => {
      console.warn("🔌 [WebSocket] Conexão encerrada. Tentando reconectar em 3s...")
      isWsConnected.value = false
    }

    socket.onerror = (err) => {
      console.warn("⚠️ [WebSocket] Erro na conexão:", err)
      isWsConnected.value = false
    }
  } catch (e) {
    isWsConnected.value = false
  }
}

function handlePontuacaoLocal(dados) {
  lastScoreToast.value = dados
  setTimeout(() => {
    lastScoreToast.value = null
  }, 4500)
}

onMounted(() => {
  carregarDadosIniciais()
  conectarWebSocket()

  // Loop de reconexão preventiva caso o servidor reinicie
  reconnectInterval = setInterval(() => {
    if (!isWsConnected.value) {
      conectarWebSocket()
    }
  }, 4000)
})

onUnmounted(() => {
  if (socket) socket.close()
  if (reconnectInterval) clearInterval(reconnectInterval)
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
