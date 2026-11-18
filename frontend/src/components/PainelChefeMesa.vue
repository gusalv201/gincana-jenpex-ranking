<template>
  <div class="mesa-container">
    <!-- Aviso de Servidor Offline -->
    <div v-if="!isServerOnline" class="banner-alert banner-offline" role="alert">
      <div>
        <strong>⚠️ Servidor local indisponível na rede.</strong>
        <p>O registro de pontuações está temporariamente suspenso até que a comunicação com o servidor seja restabelecida.</p>
      </div>
      <button type="button" class="btn-secondary" @click="sincronizarMesa(true)">
        🔄 Tentar Reconectar
      </button>
    </div>

    <!-- Cabeçalho do Painel do Chefe de Mesa -->
    <header class="mesa-header glass-panel">
      <div class="mesa-title-group">
        <span class="section-tag">PAINEL DE OPERAÇÃO • CHEFE DE MESA</span>
        <h2>{{ jogoVinculado ? jogoVinculado.name : 'Painel do Chefe de Mesa' }}</h2>
        <p v-if="jogoVinculado">
          Jogo vinculado pelo servidor (ID #{{ jogoVinculado.id }}) •
          <strong :class="jogoVinculado.is_active ? 'text-green' : 'text-orange'">
            {{ jogoVinculado.is_active ? 'Ativo para partidas' : 'Jogo inativo' }}
          </strong>
        </p>
        <p v-else>
          Autentique-se com sua conta de Chefe de Mesa (<code>table_master</code>) para carregar o jogo vinculado pelo servidor.
        </p>
      </div>

      <div class="mesa-session-controls">
        <div v-if="usuarioLogado" class="master-badge">
          <span class="master-role">CHEFE DE MESA</span>
          <strong>{{ usuarioLogado.username }}</strong>
          <button type="button" class="btn-secondary btn-sm" @click="encerrarSessao">
            Sair
          </button>
        </div>
        <button
          v-else
          type="button"
          class="btn-orange"
          @click="mostrarLoginModal = !mostrarLoginModal"
        >
          🔑 Autenticar Chefe de Mesa
        </button>
      </div>
    </header>

    <!-- Painel de Autenticação do Chefe de Mesa (compatível com /auth/login e vínculo /game-master/game) -->
    <section v-if="!usuarioLogado || mostrarLoginModal" class="login-panel glass-panel">
      <div class="login-panel-header">
        <h3>Autenticação do Chefe de Mesa</h3>
        <p>
          O backend vincula cada Chefe de Mesa a um jogo específico (<code>GET /game-master/game</code>).
          Informe suas credenciais para operar sua mesa.
        </p>
      </div>

      <form class="login-form" @submit.prevent="realizarLoginChefe">
        <div class="form-group">
          <label for="master-user">Usuário do Chefe de Mesa</label>
          <input
            id="master-user"
            v-model="credenciais.username"
            type="text"
            class="input-field"
            placeholder="Ex.: mestre_robotica"
            required
            :disabled="autenticando"
            autocomplete="username"
          />
        </div>
        <div class="form-group">
          <label for="master-pass">Senha</label>
          <input
            id="master-pass"
            v-model="credenciais.password"
            type="password"
            class="input-field"
            placeholder="Informe a senha"
            required
            :disabled="autenticando"
            autocomplete="current-password"
          />
        </div>
        <div class="login-actions">
          <button type="submit" class="btn-primary" :disabled="autenticando">
            <span v-if="autenticando">⏳ Validando...</span>
            <span v-else>Entrar e Carregar Jogo</span>
          </button>
        </div>
      </form>

      <div v-if="erroAutenticacao" class="banner-alert banner-error" role="alert">
        <div>
          <strong>Falha na autenticação</strong>
          <p>{{ erroAutenticacao }}</p>
        </div>
      </div>
    </section>

    <!-- Grade Principal de Operação da Mesa -->
    <div class="mesa-grid">
      <!-- Coluna Esquerda: Pesquisa e Lista Rolável de Participantes -->
      <section class="participantes-card glass-panel">
        <div class="card-header-row">
          <div>
            <h3 class="panel-title">1. Selecionar Aluno Participante</h3>
            <span class="card-subtitle">
              Pesquise pelo nome ou código. Alunos que já jogaram este jogo ficam bloqueados.
            </span>
          </div>
          <button
            type="button"
            class="btn-secondary btn-sm"
            :disabled="sincronizando"
            @click="sincronizarMesa(true)"
          >
            {{ sincronizando ? '⏳...' : '🔄 Atualizar' }}
          </button>
        </div>

        <!-- Campo de Pesquisa -->
        <div class="search-wrap">
          <input
            v-model="termoBusca"
            type="search"
            class="input-field"
            placeholder="🔍 Pesquisar por nome do aluno ou código (ex.: ABC123)..."
            autocomplete="off"
          />
        </div>

        <!-- Filtros rápidos de status -->
        <div class="filter-pills">
          <button
            type="button"
            :class="['pill-btn', filtroStatus === 'todos' ? 'active' : '']"
            @click="filtroStatus = 'todos'"
          >
            Todos ({{ listaCombinadaParticipantes.length }})
          </button>
          <button
            type="button"
            :class="['pill-btn', filtroStatus === 'disponiveis' ? 'active' : '']"
            @click="filtroStatus = 'disponiveis'"
          >
            Disponíveis ({{ totalDisponiveis }})
          </button>
          <button
            type="button"
            :class="['pill-btn', filtroStatus === 'jogaram' ? 'active' : '']"
            @click="filtroStatus = 'jogaram'"
          >
            Já participaram ({{ historicoJogo.length }})
          </button>
        </div>

        <!-- Lista Rolável de Alunos -->
        <div v-if="participantesVisiveis.length > 0" class="scrollable-participants">
          <button
            v-for="item in participantesVisiveis"
            :key="item.participant_code || item.username"
            type="button"
            :class="[
              'participant-row',
              item.jaParticipou ? 'row-played' : 'row-available',
              alunoSelecionado && alunoSelecionado.participant_code === item.participant_code ? 'row-selected' : ''
            ]"
            :disabled="item.jaParticipou"
            @click="selecionarAluno(item)"
          >
            <div class="row-info">
              <strong class="row-name">{{ item.nomeExibicao }}</strong>
              <span class="row-meta">
                Código: <code>{{ item.participant_code || 'Sem código' }}</code>
                <template v-if="item.identificador"> • {{ item.identificador }}</template>
              </span>
            </div>

            <div class="row-status">
              <span v-if="item.jaParticipou" class="badge-played">
                🔒 Já participou ({{ item.pontosObtidos }} pts)
              </span>
              <span v-else class="badge-available">
                ✅ Disponível
              </span>
            </div>
          </button>
        </div>

        <div v-else class="empty-box">
          <p v-if="termoBusca.trim()">
            Nenhum aluno encontrado na lista para <strong>"{{ termoBusca }}"</strong>.
          </p>
          <p v-else>
            Nenhum aluno listado ainda. Assim que o backend fornecer a listagem de participantes ou pontuações forem registradas, eles aparecerão aqui.
          </p>
        </div>

        <!-- Seleção por código direto (caso o participante tenha sido cadastrado em outro PC e a API ainda não liste nomes) -->
        <div class="manual-code-box">
          <label for="codigo-direto-input">
            Informar código do participante (6 caracteres) caso não apareça na lista:
          </label>
          <div class="manual-code-row">
            <input
              id="codigo-direto-input"
              v-model="codigoManual"
              type="text"
              maxlength="6"
              class="input-field code-input-upper"
              placeholder="Ex.: A1B2C3"
              autocomplete="off"
            />
            <button
              type="button"
              class="btn-secondary"
              @click="selecionarPorCodigoManual"
            >
              Verificar Código
            </button>
          </div>
        </div>
      </section>

      <!-- Coluna Direita: Atribuição de Pontos + Confirmação + Histórico do Jogo -->
      <div class="coluna-direita">
        <!-- Card de Lançamento de Pontuação -->
        <section class="pontuacao-card glass-panel">
          <h3 class="panel-title">2. Registrar Pontuação da Partida</h3>

          <!-- Jogo Atual -->
          <div class="active-game-banner">
            <span class="game-banner-label">JOGO SELECIONADO / VINCULADO:</span>
            <strong class="game-banner-name">
              {{ jogoVinculado ? jogoVinculado.name : 'Aguardando autenticação do chefe de mesa' }}
            </strong>
          </div>

          <!-- Aluno Selecionado -->
          <div v-if="alunoSelecionado" class="selected-student-box">
            <div class="selected-student-info">
              <span class="selected-label">PARTICIPANTE EM JOGO</span>
              <strong class="selected-name">{{ alunoSelecionado.nomeExibicao }}</strong>
              <span class="selected-code">Código: {{ alunoSelecionado.participant_code }}</span>
            </div>
            <button
              type="button"
              class="btn-secondary btn-sm"
              :disabled="enviandoPontos"
              @click="cancelarSelecaoAluno"
            >
              Trocar aluno
            </button>
          </div>

          <div v-else class="unselected-student-box">
            Selecione um aluno com status <strong>Disponível</strong> na lista ao lado para iniciar a partida.
          </div>

          <!-- Formulário de Pontos (1 a 100) -->
          <form @submit.prevent="solicitarConfirmacaoPontos" novalidate>
            <div class="form-group">
              <label for="input-pontos-mesa">Pontuação obtida na partida (1 a 100 pontos) *</label>

              <div class="quick-score-buttons">
                <button
                  v-for="valor in [10, 25, 50, 75, 100]"
                  :key="valor"
                  type="button"
                  :class="['q-score-btn', pontosInput === valor ? 'active' : '']"
                  :disabled="!alunoSelecionado || enviandoPontos"
                  @click="definirPontosRapidos(valor)"
                >
                  +{{ valor }} pts
                </button>
              </div>

              <input
                id="input-pontos-mesa"
                v-model.number="pontosInput"
                type="number"
                min="1"
                max="100"
                step="1"
                required
                class="input-field score-number-input"
                placeholder="Digite um valor inteiro entre 1 e 100"
                :disabled="!alunoSelecionado || enviandoPontos"
              />
            </div>

            <!-- Etapa de Confirmação Antes do Envio -->
            <div v-if="aguardandoConfirmacao && alunoSelecionado" class="confirm-dialog-box" role="region" aria-label="Confirmação de pontuação">
              <h4>⚠️ Confirmar registro de pontuação?</h4>
              <p>
                Você está prestes a registrar <strong>{{ pontosInput }} pontos</strong> para
                <strong>{{ alunoSelecionado.nomeExibicao }}</strong>
                (<code>{{ alunoSelecionado.participant_code }}</code>) no jogo
                <strong>{{ jogoVinculado ? jogoVinculado.name : 'atual' }}</strong>.
              </p>
              <p class="confirm-rule-warning">
                Cada participante tem direito a apenas uma participação neste jogo.
              </p>
              <div class="confirm-actions">
                <button
                  type="button"
                  class="btn-primary"
                  :disabled="enviandoPontos"
                  @click="confirmarERegistrarPontuacao"
                >
                  <span v-if="enviandoPontos">⏳ Registrando no servidor...</span>
                  <span v-else>✅ Confirmar e Salvar no Servidor</span>
                </button>
                <button
                  type="button"
                  class="btn-secondary"
                  :disabled="enviandoPontos"
                  @click="aguardandoConfirmacao = false"
                >
                  Revisar Valor
                </button>
              </div>
            </div>

            <button
              v-else
              type="submit"
              class="btn-orange btn-full"
              :disabled="!alunoSelecionado || !jogoVinculado || enviandoPontos"
            >
              Atribuir Pontuação ao Participante
            </button>
          </form>

          <!-- Mensagens de Sucesso e Erro (exclusivamente após resposta do servidor) -->
          <div v-if="mensagemSucesso" class="banner-alert banner-success msg-feedback" role="status">
            <div>
              <strong>✅ Pontuação confirmada pelo servidor!</strong>
              <p>{{ mensagemSucesso }}</p>
            </div>
          </div>

          <div v-if="mensagemErro" class="banner-alert banner-error msg-feedback" role="alert">
            <div>
              <strong>Não foi possível registrar a pontuação</strong>
              <p>{{ mensagemErro }}</p>
            </div>
          </div>
        </section>

        <!-- Card de Histórico de Pontuações do Jogo -->
        <section class="historico-card glass-panel">
          <div class="card-header-row">
            <h3 class="panel-title">📜 Histórico de Pontuações deste Jogo</h3>
            <span class="history-count">{{ historicoOrdenado.length }} partidas</span>
          </div>

          <div v-if="historicoOrdenado.length === 0" class="empty-box">
            Nenhuma pontuação registrada para este jogo no servidor até o momento.
          </div>

          <ul v-else class="history-list">
            <li
              v-for="registro in historicoOrdenado"
              :key="`${registro.participant_code}-${registro.created_at}`"
              class="history-item"
            >
              <div class="history-left">
                <strong class="history-student">{{ resolverNomePorCodigo(registro.participant_code) }}</strong>
                <span class="history-meta">
                  Código: <code>{{ registro.participant_code }}</code> • {{ formatarHorario(registro.created_at) }}
                </span>
              </div>
              <div class="history-right">
                <span class="history-points">+{{ registro.points }} pts</span>
              </div>
            </li>
          </ul>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  login,
  getMyProfile,
  getGameMasterGame,
  getGameMasterScores,
  submitGameMasterScore,
  getAuthToken,
  clearAuthToken
} from '../services/api.js'

const props = defineProps({
  participantesConhecidos: {
    type: Array,
    default: () => []
  },
  rankingAtual: {
    type: Array,
    default: () => []
  },
  isServerOnline: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['pontuacao-registrada', 'retry-connection'])

const credenciais = ref({
  username: '',
  password: ''
})

const usuarioLogado = ref(null)
const jogoVinculado = ref(null)
const historicoJogo = ref([])

const mostrarLoginModal = ref(false)
const autenticando = ref(false)
const erroAutenticacao = ref('')
const sincronizando = ref(false)

const termoBusca = ref('')
const filtroStatus = ref('todos')
const codigoManual = ref('')

const alunoSelecionado = ref(null)
const pontosInput = ref(50)
const aguardandoConfirmacao = ref(false)
const enviandoPontos = ref(false)
const mensagemSucesso = ref('')
const mensagemErro = ref('')

let pollingMesaInterval = null
const MESA_POLLING_MS = 4000

function normalizarTexto(valor) {
  return (valor || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase()
}

// Mapa rápido de códigos que já jogaram este jogo no servidor
const mapaJaParticipou = computed(() => {
  const mapa = new Map()
  for (const item of historicoJogo.value) {
    if (item.participant_code) {
      mapa.set(item.participant_code.toUpperCase(), item.points)
    }
  }
  return mapa
})

function resolverNomePorCodigo(codigo) {
  if (!codigo) return 'Participante'
  const codeUpper = codigo.toUpperCase()
  const conhecido = props.participantesConhecidos.find(
    (p) => (p.participant_code || '').toUpperCase() === codeUpper
  )
  if (conhecido) {
    return conhecido.nomeExibicao || conhecido.nome || conhecido.username
  }
  return `Participante #${codeUpper}`
}

// Combina participantes conhecidos na sessão + códigos vindos do ranking e do histórico do jogo
const listaCombinadaParticipantes = computed(() => {
  const porCodigo = new Map()

  for (const p of props.participantesConhecidos) {
    const code = (p.participant_code || '').toUpperCase()
    if (!code) continue
    const jaJogouPontos = mapaJaParticipou.value.get(code)
    porCodigo.set(code, {
      participant_code: code,
      nomeExibicao: p.nomeExibicao || p.nome || p.username || `Participante #${code}`,
      identificador: p.identificador || null,
      jaParticipou: jaJogouPontos !== undefined,
      pontosObtidos: jaJogouPontos ?? null
    })
  }

  for (const r of props.rankingAtual) {
    const code = (r.participant_code || '').toUpperCase()
    if (!code || porCodigo.has(code)) continue
    const jaJogouPontos = mapaJaParticipou.value.get(code)
    porCodigo.set(code, {
      participant_code: code,
      nomeExibicao: r.username || r.nome || `Participante #${code}`,
      identificador: null,
      jaParticipou: jaJogouPontos !== undefined,
      pontosObtidos: jaJogouPontos ?? null
    })
  }

  for (const s of historicoJogo.value) {
    const code = (s.participant_code || '').toUpperCase()
    if (!code || porCodigo.has(code)) continue
    porCodigo.set(code, {
      participant_code: code,
      nomeExibicao: `Participante #${code}`,
      identificador: null,
      jaParticipou: true,
      pontosObtidos: s.points
    })
  }

  return Array.from(porCodigo.values()).sort((a, b) => {
    if (a.jaParticipou !== b.jaParticipou) {
      return a.jaParticipou ? 1 : -1
    }
    return a.nomeExibicao.localeCompare(b.nomeExibicao, 'pt-BR')
  })
})

const totalDisponiveis = computed(() => {
  return listaCombinadaParticipantes.value.filter((p) => !p.jaParticipou).length
})

const participantesVisiveis = computed(() => {
  const busca = normalizarTexto(termoBusca.value)
  return listaCombinadaParticipantes.value.filter((item) => {
    if (filtroStatus.value === 'disponiveis' && item.jaParticipou) return false
    if (filtroStatus.value === 'jogaram' && !item.jaParticipou) return false
    if (!busca) return true
    const nome = normalizarTexto(item.nomeExibicao)
    const codigo = normalizarTexto(item.participant_code)
    const ident = normalizarTexto(item.identificador)
    return nome.includes(busca) || codigo.includes(busca) || ident.includes(busca)
  })
})

const historicoOrdenado = computed(() => {
  return [...historicoJogo.value].sort((a, b) => {
    const tA = a.created_at ? new Date(a.created_at).getTime() : 0
    const tB = b.created_at ? new Date(b.created_at).getTime() : 0
    return tB - tA
  })
})

function formatarHorario(isoString) {
  if (!isoString) return ''
  try {
    return new Date(isoString).toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return ''
  }
}

async function realizarLoginChefe() {
  if (autenticando.value) return
  erroAutenticacao.value = ''
  autenticando.value = true

  try {
    await login({
      username: credenciais.value.username.trim(),
      password: credenciais.value.password
    })

    const perfil = await getMyProfile()
    usuarioLogado.value = perfil
    credenciais.value.password = ''
    mostrarLoginModal.value = false

    await sincronizarMesa(false)
  } catch (error) {
    erroAutenticacao.value = error.message || 'Não foi possível autenticar o chefe de mesa.'
  } finally {
    autenticando.value = false
  }
}

function encerrarSessao() {
  clearAuthToken()
  usuarioLogado.value = null
  jogoVinculado.value = null
  historicoJogo.value = []
  alunoSelecionado.value = null
  aguardandoConfirmacao.value = false
}

async function sincronizarMesa(emitirRetry = false) {
  if (emitirRetry) {
    emit('retry-connection')
  }
  if (!getAuthToken() || sincronizando.value) return

  sincronizando.value = true
  try {
    if (!usuarioLogado.value) {
      usuarioLogado.value = await getMyProfile()
    }
    const [gameData, scoresData] = await Promise.all([
      getGameMasterGame(),
      getGameMasterScores()
    ])
    jogoVinculado.value = gameData
    if (Array.isArray(scoresData)) {
      historicoJogo.value = scoresData
    }

    // Se o aluno selecionado acabou de jogar em outra atualização, bloqueia seleção
    if (
      alunoSelecionado.value &&
      mapaJaParticipou.value.has(alunoSelecionado.value.participant_code)
    ) {
      alunoSelecionado.value = null
      aguardandoConfirmacao.value = false
    }
  } catch (error) {
    if (error.status === 401) {
      encerrarSessao()
      erroAutenticacao.value = 'Sua sessão expirou (HTTP 401). Faça login novamente.'
    } else if (error.status === 404) {
      jogoVinculado.value = null
      mensagemErro.value = error.message
    }
  } finally {
    sincronizando.value = false
  }
}

function selecionarAluno(item) {
  mensagemErro.value = ''
  mensagemSucesso.value = ''
  aguardandoConfirmacao.value = false

  if (item.jaParticipou || mapaJaParticipou.value.has(item.participant_code)) {
    mensagemErro.value = `O participante "${item.nomeExibicao}" já participou deste jogo e não pode jogar uma segunda vez.`
    return
  }

  alunoSelecionado.value = item
}

function selecionarPorCodigoManual() {
  mensagemErro.value = ''
  mensagemSucesso.value = ''
  aguardandoConfirmacao.value = false

  const code = codigoManual.value.trim().toUpperCase()
  if (code.length !== 6) {
    mensagemErro.value = 'O código do participante deve possuir exatamente 6 caracteres.'
    return
  }

  if (mapaJaParticipou.value.has(code)) {
    mensagemErro.value = `O participante de código #${code} já participou deste jogo (${mapaJaParticipou.value.get(code)} pts registrados).`
    return
  }

  const existente = listaCombinadaParticipantes.value.find((p) => p.participant_code === code)
  alunoSelecionado.value = existente || {
    participant_code: code,
    nomeExibicao: resolverNomePorCodigo(code),
    identificador: null,
    jaParticipou: false,
    pontosObtidos: null
  }
  codigoManual.value = ''
}

function cancelarSelecaoAluno() {
  alunoSelecionado.value = null
  aguardandoConfirmacao.value = false
  mensagemErro.value = ''
}

function definirPontosRapidos(valor) {
  pontosInput.value = valor
  aguardandoConfirmacao.value = false
}

function solicitarConfirmacaoPontos() {
  mensagemErro.value = ''
  mensagemSucesso.value = ''

  if (!usuarioLogado.value || !jogoVinculado.value) {
    mensagemErro.value = 'Autentique-se como Chefe de Mesa vinculado a um jogo ativo antes de lançar pontos.'
    return
  }

  if (!alunoSelecionado.value || !alunoSelecionado.value.participant_code) {
    mensagemErro.value = 'Selecione um participante disponível antes de atribuir a pontuação.'
    return
  }

  const code = alunoSelecionado.value.participant_code.toUpperCase()
  if (mapaJaParticipou.value.has(code)) {
    mensagemErro.value = 'Este aluno já participou deste jogo. Cada aluno tem direito a apenas uma participação por jogo.'
    alunoSelecionado.value = null
    return
  }

  const pts = Number(pontosInput.value)
  if (!Number.isInteger(pts) || pts < 1 || pts > 100) {
    mensagemErro.value = 'A pontuação deve ser um número inteiro entre 1 e 100.'
    return
  }

  aguardandoConfirmacao.value = true
}

async function confirmarERegistrarPontuacao() {
  if (enviandoPontos.value || !alunoSelecionado.value) return

  const code = alunoSelecionado.value.participant_code.toUpperCase()
  const nomeAluno = alunoSelecionado.value.nomeExibicao
  const pts = Number(pontosInput.value)

  enviandoPontos.value = true
  mensagemErro.value = ''
  mensagemSucesso.value = ''

  try {
    // Envia pontuação para validação e persistência definitiva no servidor central
    const resultado = await submitGameMasterScore({
      participant_code: code,
      points: pts
    })

    // Atualiza histórico local imediatamente após confirmação 201 do servidor
    historicoJogo.value = [
      {
        participant_code: resultado.participant_code || code,
        points: resultado.points ?? pts,
        created_at: resultado.created_at || new Date().toISOString()
      },
      ...historicoJogo.value.filter((i) => i.participant_code !== code)
    ]

    mensagemSucesso.value = `Foram registrados ${resultado.points ?? pts} pontos para ${nomeAluno} (#${code}) no jogo "${jogoVinculado.value?.name || ''}".`

    emit('pontuacao-registrada', {
      participant_code: code,
      participant_name: nomeAluno,
      points: resultado.points ?? pts,
      game_name: jogoVinculado.value?.name || 'Jogo'
    })

    // Limpa seleção e fecha confirmação; o aluno passa a aparecer como "Já participou"
    alunoSelecionado.value = null
    aguardandoConfirmacao.value = false
  } catch (error) {
    aguardandoConfirmacao.value = false

    if (error.status === 409) {
      mensagemErro.value = error.message
      // Sincroniza lista de pontuações para refletir o bloqueio no estado visual
      await sincronizarMesa(false)
    } else if (error.status === 404) {
      mensagemErro.value = error.message
    } else if (error.status === 401) {
      encerrarSessao()
      erroAutenticacao.value = 'Sessão expirada ou não autorizada (HTTP 401). Faça login novamente.'
    } else if (error.status === 422) {
      mensagemErro.value = error.message
    } else {
      mensagemErro.value = error.message || 'Erro de comunicação ao registrar a pontuação.'
    }
  } finally {
    enviandoPontos.value = false
  }
}

onMounted(() => {
  if (getAuthToken()) {
    sincronizarMesa(false)
  }

  pollingMesaInterval = setInterval(() => {
    if (getAuthToken()) {
      sincronizarMesa(false)
    }
  }, MESA_POLLING_MS)
})

onUnmounted(() => {
  if (pollingMesaInterval) clearInterval(pollingMesaInterval)
})
</script>

<style scoped>
.mesa-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 8px 24px 48px;
}

.mesa-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 26px;
  margin-bottom: 20px;
  background: #FFFFFF;
  border-left: 6px solid var(--jenpex-orange);
}

.section-tag {
  display: inline-block;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: var(--jenpex-orange);
  margin-bottom: 4px;
}

.mesa-title-group h2 {
  font-size: 1.7rem;
  font-weight: 900;
  color: var(--jenpex-navy);
}

.mesa-title-group p {
  color: var(--text-muted);
  font-size: 0.96rem;
  margin-top: 2px;
}

.text-green {
  color: var(--jenpex-green);
}

.text-orange {
  color: var(--jenpex-orange);
}

.master-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #F5F7FA;
  border: 1px solid var(--border-color);
  padding: 8px 14px;
  border-radius: 10px;
  color: var(--jenpex-navy);
}

.master-role {
  font-size: 0.72rem;
  font-weight: 800;
  padding: 4px 8px;
  border-radius: 6px;
  background: #FFF1EB;
  color: #C2410C;
  border: 1px solid #FDBA8C;
}

.btn-sm {
  padding: 7px 13px;
  font-size: 0.84rem;
}

.login-panel {
  padding: 24px 26px;
  margin-bottom: 22px;
  background: #FFFFFF;
  border: 1.5px solid #FDBA8C;
}

.login-panel-header h3 {
  font-size: 1.2rem;
  color: var(--jenpex-navy);
  margin-bottom: 4px;
}

.login-panel-header p {
  font-size: 0.92rem;
  color: var(--text-muted);
  margin-bottom: 16px;
}

.login-form {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 14px;
  align-items: end;
}

.login-actions {
  padding-bottom: 2px;
}

.mesa-grid {
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  gap: 22px;
  align-items: start;
}

.coluna-direita {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.participantes-card,
.pontuacao-card,
.historico-card {
  padding: 24px 26px;
  background: #FFFFFF;
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
}

.panel-title {
  font-size: 1.22rem;
  font-weight: 800;
  color: var(--jenpex-navy);
}

.card-subtitle {
  display: block;
  font-size: 0.88rem;
  color: var(--text-muted);
  margin-top: 2px;
}

/* Barra de pesquisa destacada */
.search-wrap {
  margin-bottom: 14px;
}

.search-wrap .input-field {
  font-size: 1.05rem;
  padding: 14px 16px;
  border-width: 2px;
  border-color: #C2CDD9;
  background: #F8FAFC;
}

.search-wrap .input-field:focus {
  background: #FFFFFF;
  border-color: var(--jenpex-green);
}

.filter-pills {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.pill-btn {
  background: #F5F7FA;
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  padding: 7px 14px;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  font-family: var(--font-display);
  transition: all 0.15s ease;
}

.pill-btn:hover {
  color: var(--jenpex-navy);
  border-color: var(--border-strong);
}

.pill-btn.active {
  background: var(--jenpex-navy);
  color: #FFFFFF;
  border-color: var(--jenpex-navy);
}

.scrollable-participants {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 380px;
  overflow-y: auto;
  padding-right: 4px;
  margin-bottom: 16px;
}

.participant-row {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 13px 16px;
  border-radius: 10px;
  text-align: left;
  font-family: var(--font-display);
  transition: all 0.15s ease;
}

.row-available {
  background: #FFFFFF;
  border: 1.5px solid var(--border-color);
  color: var(--jenpex-navy);
  cursor: pointer;
}

.row-available:hover {
  border-color: var(--jenpex-green);
  background: #F2FBF9;
}

.row-selected {
  border-color: var(--jenpex-orange) !important;
  background: #FFF7F2 !important;
  box-shadow: 0 0 0 3px rgba(255, 100, 31, 0.18);
}

.row-played {
  background: #F1F5F9;
  border: 1px solid #E2E8F0;
  color: var(--text-muted);
  opacity: 0.82;
  cursor: not-allowed;
}

.row-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.row-name {
  font-size: 1.04rem;
  font-weight: 800;
  color: var(--jenpex-navy);
}

.row-played .row-name {
  color: var(--text-muted);
}

.row-meta {
  font-size: 0.84rem;
  color: var(--text-muted);
}

.badge-available {
  font-size: 0.8rem;
  font-weight: 800;
  padding: 5px 12px;
  border-radius: 999px;
  background: #E6F6F4;
  color: #006B62;
  border: 1px solid #99DCD6;
  white-space: nowrap;
}

.badge-played {
  font-size: 0.8rem;
  font-weight: 800;
  padding: 5px 12px;
  border-radius: 999px;
  background: #FFF1EB;
  color: #C2410C;
  border: 1px solid #FDBA8C;
  white-space: nowrap;
}

.manual-code-box {
  border-top: 1px solid var(--border-color);
  padding-top: 14px;
}

.manual-code-box label {
  display: block;
  font-size: 0.86rem;
  font-weight: 700;
  color: var(--jenpex-navy);
  margin-bottom: 8px;
}

.manual-code-row {
  display: flex;
  gap: 8px;
}

.code-input-upper {
  text-transform: uppercase;
  font-family: var(--font-mono);
  font-weight: 800;
  font-size: 1.08rem;
  letter-spacing: 0.08em;
}

.active-game-banner {
  background: #F5F7FA;
  border: 1.5px solid var(--border-color);
  border-radius: 10px;
  padding: 12px 16px;
  margin: 12px 0 14px;
}

.game-banner-label {
  display: block;
  font-size: 0.73rem;
  font-weight: 800;
  color: var(--text-muted);
}

.game-banner-name {
  font-size: 1.12rem;
  font-weight: 900;
  color: var(--jenpex-navy);
}

.selected-student-box {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 10px;
  background: #E6F6F4;
  border: 1.5px solid #5EEAD4;
  margin-bottom: 16px;
}

.selected-label {
  display: block;
  font-size: 0.73rem;
  font-weight: 800;
  color: #006B62;
}

.selected-name {
  display: block;
  font-size: 1.14rem;
  color: var(--jenpex-navy);
}

.selected-code {
  font-size: 0.86rem;
  font-weight: 700;
  font-family: var(--font-mono);
  color: #065F46;
}

.unselected-student-box {
  padding: 15px;
  border-radius: 10px;
  background: #F8FAFC;
  border: 1.5px dashed var(--border-color);
  color: var(--text-muted);
  font-size: 0.92rem;
  margin-bottom: 16px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 0.94rem;
  font-weight: 700;
  margin-bottom: 8px;
  color: var(--jenpex-navy);
}

.quick-score-buttons {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.q-score-btn {
  flex: 1;
  min-width: 72px;
  background: #F5F7FA;
  border: 1.5px solid var(--border-color);
  color: var(--jenpex-navy);
  padding: 10px 12px;
  border-radius: 8px;
  font-family: var(--font-mono);
  font-weight: 800;
  font-size: 0.94rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.q-score-btn:hover:not(:disabled) {
  border-color: var(--jenpex-orange);
  background: #FFF7F2;
}

.q-score-btn.active {
  background: var(--jenpex-orange);
  border-color: var(--jenpex-orange-deep);
  color: #FFFFFF;
}

.q-score-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.score-number-input {
  font-family: var(--font-mono);
  font-size: 1.25rem;
  font-weight: 800;
  padding: 14px 16px;
}

.confirm-dialog-box {
  background: #FFF7F2;
  border: 1.5px solid #FDBA8C;
  border-radius: 12px;
  padding: 16px 18px;
  margin-top: 12px;
}

.confirm-dialog-box h4 {
  font-size: 1.05rem;
  color: #9A3412;
  margin-bottom: 6px;
}

.confirm-dialog-box p {
  font-size: 0.94rem;
  color: var(--jenpex-navy);
  margin-bottom: 8px;
}

.confirm-rule-warning {
  font-size: 0.84rem !important;
  font-weight: 700;
  color: #C2410C !important;
}

.confirm-actions {
  display: flex;
  gap: 10px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.btn-full {
  width: 100%;
  padding: 15px;
  font-size: 1.05rem;
}

.msg-feedback {
  margin-top: 14px;
  margin-bottom: 0;
}

.history-count {
  font-size: 0.85rem;
  font-weight: 800;
  color: var(--jenpex-green);
  font-family: var(--font-mono);
}

.history-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 260px;
  overflow-y: auto;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 11px 15px;
  border-radius: 9px;
  background: #F8FAFC;
  border: 1px solid var(--border-color);
}

.history-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.history-student {
  font-size: 0.96rem;
  color: var(--jenpex-navy);
}

.history-meta {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.history-points {
  font-family: var(--font-mono);
  font-size: 1.05rem;
  font-weight: 900;
  color: var(--jenpex-green);
}

.empty-box {
  text-align: center;
  padding: 24px 14px;
  color: var(--text-muted);
  background: #F8FAFC;
  border: 1.5px dashed var(--border-color);
  border-radius: 10px;
  font-size: 0.9rem;
  margin-bottom: 14px;
}

@media (max-width: 960px) {
  .mesa-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 14px;
  }
  .login-form,
  .mesa-grid {
    grid-template-columns: 1fr;
  }
}
</style>
