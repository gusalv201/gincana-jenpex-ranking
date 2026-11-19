<template>
  <div class="cadastro-container">
    <!-- Aviso de Servidor Offline -->
    <div v-if="!isServerOnline" class="banner-alert banner-offline" role="alert">
      <div>
        <strong>⚠️ Servidor local indisponível na rede.</strong>
        <p>Não é possível confirmar novos cadastros até que a conexão com o servidor FastAPI seja restabelecida.</p>
      </div>
      <button type="button" class="btn-secondary" @click="$emit('retry-connection')">
        🔄 Tentar Reconectar
      </button>
    </div>

    <!-- Cabeçalho da Interface de Recepção -->
    <header class="section-header glass-panel">
      <div class="header-title-block">
        <span class="section-tag">RECEPÇÃO • ENTRADA DA SALA</span>
        <h2>Cadastro de Participantes</h2>
        <p>Cadastre o aluno na entrada para liberá-lo nos jogos da 7ª JENPEX 2026.</p>
      </div>

      <div class="counter-card">
        <span class="counter-label">TOTAL DE PARTICIPANTES</span>
        <span class="counter-value">{{ totalParticipantesExibido }}</span>
      </div>
    </header>

    <!-- Login obrigatório do administrador (recepção) -->
    <section v-if="!adminLogado" class="form-panel glass-panel admin-login-panel">
      <h3 class="panel-title">🔒 Acesso da Recepção</h3>
      <p class="field-hint">Somente o administrador pode cadastrar participantes.</p>
      <form @submit.prevent="entrarComoAdmin">
        <div class="form-group">
          <label for="admin-user">Usuário administrador</label>
          <input id="admin-user" v-model="credenciaisAdmin.username" type="text" class="input-field"
            autocomplete="username" required :disabled="autenticando" />
        </div>
        <div class="form-group">
          <label for="admin-pass">Senha</label>
          <input id="admin-pass" v-model="credenciaisAdmin.password" type="password" class="input-field"
            autocomplete="current-password" required :disabled="autenticando" />
        </div>
        <div v-if="erroLogin" class="banner-alert banner-error" role="alert">
          <div><p>{{ erroLogin }}</p></div>
        </div>
        <button type="submit" class="btn-primary btn-submit-cadastro" :disabled="autenticando">
          {{ autenticando ? '⏳ Validando...' : 'Entrar' }}
        </button>
      </form>
    </section>

    <div v-else class="cadastro-grid">
      <!-- Coluna 1: Formulário de Cadastro -->
      <section class="form-panel glass-panel">
        <h3 class="panel-title">Novo Cadastro de Aluno</h3>

        <form @submit.prevent="confirmarCadastro" novalidate>
          <div class="form-group">
            <label for="input-nome-aluno">Nome completo do aluno *</label>
            <input
              id="input-nome-aluno"
              ref="nomeInputRef"
              v-model="form.nome"
              type="text"
              class="input-field"
              placeholder="Ex.: Ana Beatriz Souza"
              maxlength="80"
              :disabled="enviando"
              autocomplete="off"
              @input="limparAvisosValidacao"
            />
          </div>

          <div class="form-group">
            <label for="input-identificador">
              Identificador adicional / Turma
              <span class="label-optional">(opcional — obrigatório em caso de homônimo)</span>
            </label>
            <input
              id="input-identificador"
              ref="identificadorInputRef"
              v-model="form.identificador"
              type="text"
              class="input-field"
              :class="{ 'highlight-field': exigirIdentificadorHomonimo }"
              placeholder="Ex.: 2º Info A, Manhã, agro-1..."
              maxlength="30"
              :disabled="enviando"
              autocomplete="off"
              @input="limparAvisosValidacao"
            />
            <small class="field-hint">
              Permite diferenciar dois alunos com o mesmo nome sem exigir matrícula ou senha.
            </small>
          </div>

          <div class="form-group">
            <label for="input-pin">
              Senha / PIN do aluno
              <span class="label-optional">(opcional — em branco gera um PIN de 6 dígitos)</span>
            </label>
            <input
              id="input-pin"
              v-model="form.senha"
              type="text"
              class="input-field"
              placeholder="Mínimo 6 caracteres"
              maxlength="128"
              :disabled="enviando"
              autocomplete="off"
              @input="limparAvisosValidacao"
            />
            <small class="field-hint">
              O aluno usa o código + esta senha na aba "Minhas Notas" para ver a própria pontuação.
            </small>
          </div>

          <!-- Mensagem de Erro / Validação -->
          <div v-if="erroMensagem" class="banner-alert banner-error" role="alert">
            <div>
              <strong>Não foi possível concluir o cadastro</strong>
              <p>{{ erroMensagem }}</p>
            </div>
          </div>

          <!-- Botão Destacado de Confirmação -->
          <button
            type="submit"
            class="btn-primary btn-submit-cadastro"
            :disabled="enviando"
          >
            <span v-if="enviando">⏳ Registrando no servidor...</span>
            <span v-else>✅ Confirmar Cadastro do Participante</span>
          </button>
        </form>

        <!-- Confirmação Visual (exibida somente após resposta 201 do servidor) -->
        <div v-if="ultimoCadastrado" class="confirmacao-card banner-success" role="status">
          <div class="confirmacao-header">
            <span class="confirmacao-badge">🎉 CADASTRO CONFIRMADO PELO SERVIDOR</span>
          </div>
          <div class="confirmacao-body">
            <div class="confirmacao-info">
              <span class="confirmacao-label">Participante</span>
              <strong class="confirmacao-nome">{{ ultimoCadastrado.nomeExibicao }}</strong>
              <span v-if="ultimoCadastrado.identificador" class="confirmacao-ident">
                Identificador: {{ ultimoCadastrado.identificador }}
              </span>
            </div>
            <div v-if="ultimoCadastrado.participant_code" class="confirmacao-codigo">
              <span class="codigo-label">CÓDIGO GERADO</span>
              <span class="codigo-valor">{{ ultimoCadastrado.participant_code }}</span>
            </div>
            <div v-if="ultimoCadastrado.senha" class="confirmacao-codigo">
              <span class="codigo-label">SENHA / PIN</span>
              <span class="codigo-valor">{{ ultimoCadastrado.senha }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Coluna 2: Lista e Pesquisa de Alunos Cadastrados -->
      <section class="list-panel glass-panel">
        <div class="list-panel-header">
          <div>
            <h3 class="panel-title">Alunos Cadastrados</h3>
            <span class="list-subtitle">
              Exibindo {{ participantesFiltrados.length }} de {{ participantes.length }} registros carregados
            </span>
          </div>
        </div>

        <!-- Barra de Pesquisa por Nome -->
        <div class="search-box">
          <input
            v-model="termoPesquisa"
            type="search"
            class="input-field"
            placeholder="🔍 Pesquisar aluno pelo nome, identificador ou código..."
            autocomplete="off"
          />
        </div>

        <!-- Lista de Participantes -->
        <div v-if="participantesFiltrados.length > 0" class="participantes-list">
          <div
            v-for="aluno in participantesFiltrados"
            :key="aluno.id || aluno.participant_code || aluno.username"
            class="participante-item"
          >
            <div class="participante-main">
              <strong class="participante-nome">{{ aluno.nome || aluno.username }}</strong>
              <span v-if="aluno.identificador" class="participante-tag">
                {{ aluno.identificador }}
              </span>
            </div>
            <div class="participante-meta">
              <span v-if="aluno.participant_code" class="code-pill">
                #{{ aluno.participant_code }}
              </span>
              <span class="status-pill">Disponível</span>
            </div>
          </div>
        </div>

        <div v-else class="empty-list-state">
          <p v-if="termoPesquisa.trim()">
            Nenhum participante encontrado para <strong>"{{ termoPesquisa }}"</strong>.
          </p>
          <p v-else>
            Nenhum participante confirmado listado no momento.
          </p>
        </div>

        <!-- Nota Técnica Transparente sobre Limitação Atual do Backend -->
        <div class="banner-alert banner-limitation limitation-note">
          <div>
            <strong>ℹ️ Status da integração com o servidor:</strong>
            <p>
              O backend atual (<code>POST /auth/register</code>) ainda exige o campo <code>password</code> e não expõe um endpoint <code>GET</code> para listar todos os participantes cadastrados em outros dispositivos. Somente cadastros confirmados pelo servidor são exibidos acima.
            </p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { registerParticipant, login, getMyProfile, clearAuthToken } from '../services/api.js'

const props = defineProps({
  participantes: {
    type: Array,
    default: () => []
  },
  totalServidor: {
    type: Number,
    default: null
  },
  isServerOnline: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['participante-cadastrado', 'retry-connection'])

const form = ref({
  nome: '',
  identificador: '',
  senha: ''
})

const adminLogado = ref(false)
const autenticando = ref(false)
const erroLogin = ref('')
const credenciaisAdmin = ref({ username: '', password: '' })

async function entrarComoAdmin() {
  if (autenticando.value) return
  erroLogin.value = ''
  autenticando.value = true
  try {
    await login({
      username: credenciaisAdmin.value.username.trim(),
      password: credenciaisAdmin.value.password
    })
    const perfil = await getMyProfile()
    if (perfil?.role !== 'admin') {
      clearAuthToken()
      erroLogin.value = 'Este usuário não é administrador.'
      return
    }
    credenciaisAdmin.value.password = ''
    adminLogado.value = true
  } catch (error) {
    erroLogin.value = error.message || 'Falha na autenticação.'
  } finally {
    autenticando.value = false
  }
}

const termoPesquisa = ref('')
const enviando = ref(false)
const erroMensagem = ref('')
const exigirIdentificadorHomonimo = ref(false)
const ultimoCadastrado = ref(null)

const nomeInputRef = ref(null)
const identificadorInputRef = ref(null)

function normalizarTexto(valor) {
  return (valor || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, ' ')
}

function montarUsernameServidor(nome, identificador) {
  const nomeLimpo = nome.trim().replace(/\s+/g, ' ')
  const identLimpo = identificador.trim().replace(/\s+/g, ' ')
  return identLimpo ? `${nomeLimpo} (${identLimpo})` : nomeLimpo
}

const totalParticipantesExibido = computed(() => {
  if (typeof props.totalServidor === 'number' && props.totalServidor > props.participantes.length) {
    return props.totalServidor
  }
  return props.participantes.length
})

const participantesFiltrados = computed(() => {
  const busca = normalizarTexto(termoPesquisa.value)
  if (!busca) {
    return props.participantes
  }
  return props.participantes.filter((p) => {
    const nome = normalizarTexto(p.nome || p.username)
    const ident = normalizarTexto(p.identificador)
    const codigo = normalizarTexto(p.participant_code)
    return nome.includes(busca) || ident.includes(busca) || codigo.includes(busca)
  })
})

function limparAvisosValidacao() {
  if (erroMensagem.value) {
    erroMensagem.value = ''
  }
}

async function confirmarCadastro() {
  if (enviando.value) return

  erroMensagem.value = ''
  const nomeLimpo = form.value.nome.trim().replace(/\s+/g, ' ')
  const identLimpo = form.value.identificador.trim().replace(/\s+/g, ' ')

  // 1. Validação de campo vazio
  if (!nomeLimpo) {
    erroMensagem.value = 'Informe o nome completo do aluno para realizar o cadastro.'
    nomeInputRef.value?.focus()
    return
  }

  if (nomeLimpo.length < 3) {
    erroMensagem.value = 'O nome do aluno deve conter pelo menos 3 caracteres.'
    nomeInputRef.value?.focus()
    return
  }

  // 2. Verificação de duplicidade ou homônimo na lista conhecida
  const nomeNorm = normalizarTexto(nomeLimpo)
  const identNorm = normalizarTexto(identLimpo)

  const mesmoNomeExistente = props.participantes.find(
    (p) => normalizarTexto(p.nome || p.username) === nomeNorm
  )

  if (mesmoNomeExistente) {
    const identExistenteNorm = normalizarTexto(mesmoNomeExistente.identificador || '')
    if (identExistenteNorm === identNorm) {
      exigirIdentificadorHomonimo.value = true
      erroMensagem.value = identLimpo
        ? `O aluno "${nomeLimpo} (${identLimpo})" já consta na lista de participantes cadastrados.`
        : `Já existe um aluno cadastrado com o nome "${nomeLimpo}". Se for outro aluno homônimo, preencha o campo "Identificador adicional / Turma" para diferenciá-los.`
      identificadorInputRef.value?.focus()
      return
    }
  }

  const usernameParaServidor = montarUsernameServidor(nomeLimpo, identLimpo)

  enviando.value = true
  try {
    // 3. Chamada real ao servidor central (sem senha compartilhada e sem simulação)
    const senhaInformada = form.value.senha.trim()
    if (senhaInformada && senhaInformada.length < 6) {
      erroMensagem.value = 'A senha do aluno deve ter pelo menos 6 caracteres (ou deixe em branco para gerar um PIN).'
      return
    }
    const resposta = await registerParticipant({
      username: usernameParaServidor,
      password: senhaInformada
    })

    // Só confirma se o servidor respondeu com sucesso
    const registroConfirmado = {
      id: resposta.id,
      username: resposta.username || usernameParaServidor,
      nome: nomeLimpo,
      identificador: identLimpo || null,
      nomeExibicao: usernameParaServidor,
      participant_code: resposta.participant_code,
      senha: resposta.password || senhaInformada,
      is_active: resposta.is_active ?? true,
      created_at: new Date().toISOString()
    }

    ultimoCadastrado.value = registroConfirmado
    exigirIdentificadorHomonimo.value = false
    emit('participante-cadastrado', registroConfirmado)

    // Limpa os campos após confirmação do servidor
    form.value.nome = ''
    form.value.identificador = ''
    form.value.senha = ''
    nomeInputRef.value?.focus()
  } catch (error) {
    if (error.status === 409) {
      exigirIdentificadorHomonimo.value = true
      erroMensagem.value =
        'Este nome já está cadastrado no servidor (HTTP 409). Caso trate-se de um aluno homônimo, informe um Identificador adicional / Turma para diferenciá-lo.'
      identificadorInputRef.value?.focus()
    } else if (error.status === 422) {
      erroMensagem.value = error.message
    } else if (error.status === 401 || error.status === 403) {
      clearAuthToken()
      adminLogado.value = false
      erroLogin.value = 'Sessão expirada. Entre novamente como administrador.'
    } else {
      erroMensagem.value = error.message || 'Falha ao comunicar com o servidor central.'
    }
  } finally {
    enviando.value = false
  }
}
</script>

<style scoped>
.admin-login-panel {
  max-width: 480px;
  margin: 24px auto;
}

.cadastro-container {
  max-width: 1240px;
  margin: 0 auto;
  padding: 8px 24px 48px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 26px;
  margin-bottom: 22px;
  background: #FFFFFF;
  border-left: 6px solid var(--jenpex-green);
}

.section-tag {
  display: inline-block;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: var(--jenpex-green);
  margin-bottom: 4px;
}

.header-title-block h2 {
  font-size: 1.7rem;
  font-weight: 900;
  color: var(--jenpex-navy);
}

.header-title-block p {
  color: var(--text-muted);
  font-size: 0.96rem;
  margin-top: 2px;
}

.counter-card {
  background: #E6F6F4;
  border: 1.5px solid #99DCD6;
  border-radius: 12px;
  padding: 12px 22px;
  text-align: right;
  min-width: 195px;
}

.counter-label {
  display: block;
  font-size: 0.73rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: #006B62;
}

.counter-value {
  font-size: 2.1rem;
  font-weight: 900;
  font-family: var(--font-mono);
  color: var(--jenpex-navy);
}

.cadastro-grid {
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  gap: 22px;
  align-items: start;
}

.form-panel,
.list-panel {
  padding: 26px;
  background: #FFFFFF;
}

.panel-title {
  font-size: 1.24rem;
  font-weight: 800;
  margin-bottom: 18px;
  padding-bottom: 10px;
  border-bottom: 1.5px solid var(--border-color);
  color: var(--jenpex-navy);
}

.form-group {
  margin-bottom: 18px;
}

.form-group label {
  display: block;
  font-size: 0.95rem;
  font-weight: 700;
  margin-bottom: 8px;
  color: var(--jenpex-navy);
}

.label-optional {
  font-weight: 600;
  font-size: 0.82rem;
  color: var(--text-muted);
  margin-left: 4px;
}

.field-hint {
  display: block;
  margin-top: 6px;
  font-size: 0.84rem;
  color: var(--text-muted);
}

.highlight-field {
  border-color: var(--jenpex-orange) !important;
  box-shadow: 0 0 0 3px rgba(255, 100, 31, 0.2) !important;
}

.btn-submit-cadastro {
  width: 100%;
  padding: 15px 20px;
  font-size: 1.06rem;
  margin-top: 6px;
}

.confirmacao-card {
  margin-top: 20px;
  padding: 16px 18px;
  border-radius: 12px;
}

.confirmacao-badge {
  display: inline-block;
  font-size: 0.78rem;
  font-weight: 900;
  letter-spacing: 0.06em;
  color: #006B62;
  margin-bottom: 8px;
}

.confirmacao-body {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.confirmacao-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 700;
  color: #065F46;
}

.confirmacao-nome {
  display: block;
  font-size: 1.22rem;
  color: var(--jenpex-navy);
}

.confirmacao-ident {
  display: block;
  font-size: 0.86rem;
  color: #065F46;
  margin-top: 2px;
}

.confirmacao-codigo {
  background: #FFFFFF;
  border: 1.5px solid var(--jenpex-green);
  padding: 8px 16px;
  border-radius: 10px;
  text-align: center;
}

.codigo-label {
  display: block;
  font-size: 0.68rem;
  font-weight: 800;
  color: var(--text-muted);
}

.codigo-valor {
  font-family: var(--font-mono);
  font-size: 1.38rem;
  font-weight: 900;
  color: var(--jenpex-navy);
  letter-spacing: 0.08em;
}

.list-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 12px;
}

.list-subtitle {
  display: block;
  font-size: 0.86rem;
  color: var(--text-muted);
  margin-top: -10px;
  margin-bottom: 12px;
}

.search-box {
  margin-bottom: 14px;
}

.participantes-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 360px;
  overflow-y: auto;
  padding-right: 4px;
}

.participante-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  border-radius: 10px;
  background: #F8FAFC;
  border: 1px solid var(--border-color);
}

.participante-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.participante-nome {
  font-size: 1rem;
  color: var(--jenpex-navy);
}

.participante-tag {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-muted);
}

.participante-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.code-pill {
  font-family: var(--font-mono);
  font-size: 0.84rem;
  font-weight: 800;
  padding: 4px 9px;
  border-radius: 6px;
  background: #EEF2F7;
  border: 1px solid var(--border-color);
  color: var(--jenpex-navy);
}

.status-pill {
  font-size: 0.78rem;
  font-weight: 800;
  padding: 4px 10px;
  border-radius: 999px;
  background: #E6F6F4;
  color: #006B62;
  border: 1px solid #99DCD6;
}

.empty-list-state {
  text-align: center;
  padding: 32px 16px;
  color: var(--text-muted);
  background: #F8FAFC;
  border: 1.5px dashed var(--border-color);
  border-radius: 10px;
  margin-bottom: 14px;
}

.limitation-note {
  margin-top: 16px;
  margin-bottom: 0;
  font-size: 0.85rem;
}

@media (max-width: 900px) {
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 14px;
  }
  .cadastro-grid {
    grid-template-columns: 1fr;
  }
}
</style>
