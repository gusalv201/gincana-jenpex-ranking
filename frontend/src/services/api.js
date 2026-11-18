/**
 * Serviço centralizado de comunicação HTTP para a 7ª JENPEX 2026 — IFMT Campo Novo do Parecis.
 *
 * Projetado para operação em rede local (LAN) sem dependência de internet:
 * - Utiliza URLs relativas (`/api`) encaminhadas pelo proxy do Vite ao backend FastAPI
 *   no computador servidor, evitando dependência de `localhost` nos dispositivos clientes
 *   e evitando bloqueios de CORS ao acessar pelo endereço IP da LAN.
 * - Suporta também configuração explícita via `VITE_API_BASE_URL` quando implantado sem proxy.
 * - Contém exclusivamente os endpoints reais implementados no backend FastAPI.
 */

const DEFAULT_TIMEOUT_MS = 8000

/**
 * Resolve a URL base da API para operação em rede local.
 */
export function resolveApiBaseUrl() {
  const configuredUrl = import.meta.env?.VITE_API_BASE_URL
  if (configuredUrl && typeof configuredUrl === 'string' && configuredUrl.trim() !== '') {
    return configuredUrl.trim().replace(/\/+$/, '')
  }
  return '/api'
}

export const API_BASE_URL = resolveApiBaseUrl()

/**
 * Classe padronizada de erro para chamadas HTTP e falhas de rede/conexão.
 */
export class ApiError extends Error {
  /**
   * @param {object} params
   * @param {string} params.message Mensagem amigável em português
   * @param {number} params.status Código HTTP (0 para erro de rede/timeout)
   * @param {string} params.code Código interno padronizado do erro
   * @param {any} [params.detail] Detalhe original retornado pelo backend
   * @param {string} [params.endpoint] Endpoint requisitado
   */
  constructor({ message, status = 0, code = 'UNKNOWN_ERROR', detail = null, endpoint = '' }) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.detail = detail
    this.endpoint = endpoint
  }
}

/**
 * Traduz mensagens de erro do backend FastAPI e códigos HTTP para mensagens claras em português.
 */
function formatErrorMessage(status, detail) {
  if (typeof detail === 'string' && detail.trim() !== '') {
    const translations = {
      'Username already registered': 'Este participante já está cadastrado no servidor (HTTP 409).',
      'Incorrect username or password': 'Credenciais inválidas (usuário ou senha incorretos).',
      'Participant not found': 'Participante não encontrado no servidor para o código informado (HTTP 404).',
      'Code does not belong to an active participant': 'O código informado não pertence a um participante ativo (HTTP 409).',
      'Participant already has a score for this game': 'Participação bloqueada: este aluno já participou deste jogo (HTTP 409).',
      'No active game assigned to this table master': 'Nenhum jogo ativo está vinculado a este chefe de mesa no servidor (HTTP 404).',
      'Game not found': 'Jogo não encontrado no servidor (HTTP 404).',
      'Master not found': 'Chefe de mesa não encontrado no servidor (HTTP 404).',
      'Master is already assigned to another game': 'Este chefe de mesa já está vinculado a outro jogo (HTTP 409).',
      'A game with scores cannot be reassigned': 'Um jogo que já possui pontuações não pode ter o chefe de mesa alterado (HTTP 409).',
      'Score not found': 'Registro de pontuação não encontrado (HTTP 404).',
      'Participant role required': 'Acesso restrito a participantes (HTTP 403).',
      'Table master role required': 'Autenticação de chefe de mesa necessária para esta operação.',
      'Admin role required': 'Autenticação de administrador necessária para esta operação.',
      'Could not validate credentials': 'Sessão inválida ou expirada (HTTP 401). Faça login novamente.',
      'Not authenticated': 'Não autenticado (HTTP 401). Informe as credenciais do chefe de mesa.',
      'Unable to allocate a unique participant code; try again': 'Não foi possível gerar um código único no momento (HTTP 503). Tente novamente.',
    }
    return translations[detail] || detail
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const messages = detail.map((err) => {
      const field = Array.isArray(err.loc) ? err.loc[err.loc.length - 1] : 'campo'
      if (field === 'password' && err.type === 'missing') {
        return 'password: o endpoint atual /auth/register do backend exige senha (mín. 8 caracteres)'
      }
      return `${field}: ${err.msg}`
    })
    return `Erro de validação no servidor (HTTP ${status}): ${messages.join('; ')}`
  }

  switch (status) {
    case 400:
      return 'Requisição inválida (HTTP 400).'
    case 401:
      return 'Não autorizado (HTTP 401). Verifique as credenciais de acesso.'
    case 403:
      return 'Permissão negada para executar esta ação (HTTP 403).'
    case 404:
      return 'Recurso não encontrado no servidor (HTTP 404).'
    case 409:
      return 'Conflito de dados no servidor: registro ou participação duplicada (HTTP 409).'
    case 422:
      return 'Dados recusados pela validação do servidor (HTTP 422).'
    case 500:
      return 'Erro interno no servidor da gincana (HTTP 500).'
    case 502:
    case 503:
    case 504:
      return 'Servidor FastAPI indisponível ou sem conexão na rede local.'
    default:
      return `Erro HTTP ${status} ao comunicar com o servidor.`
  }
}

function resolveErrorCode(status) {
  if (status === 401) return 'UNAUTHORIZED'
  if (status === 403) return 'FORBIDDEN'
  if (status === 404) return 'NOT_FOUND'
  if (status === 409) return 'CONFLICT'
  if (status === 422) return 'VALIDATION_ERROR'
  if (status >= 500) return 'SERVER_ERROR'
  return 'HTTP_ERROR'
}

// Token JWT mantido em memória durante a sessão da aba
let authToken = null

export function setAuthToken(token) {
  authToken = token || null
}

export function getAuthToken() {
  return authToken
}

export function clearAuthToken() {
  authToken = null
}

/**
 * Executa uma requisição HTTP padronizada para o backend FastAPI.
 */
export async function apiRequest(path, options = {}) {
  const {
    method = 'GET',
    body = undefined,
    token = authToken,
    timeoutMs = DEFAULT_TIMEOUT_MS,
    signal: externalSignal,
  } = options

  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  const url = `${API_BASE_URL}${normalizedPath}`

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(new Error('TIMEOUT')), timeoutMs)

  if (externalSignal) {
    if (externalSignal.aborted) {
      clearTimeout(timeoutId)
      throw new ApiError({
        message: 'Requisição cancelada.',
        status: 0,
        code: 'ABORTED',
        endpoint: normalizedPath,
      })
    }
    externalSignal.addEventListener('abort', () => controller.abort(externalSignal.reason), { once: true })
  }

  const headers = {
    Accept: 'application/json',
  }

  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  try {
    const response = await fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    })

    const contentType = response.headers.get('content-type') || ''
    const isJson = contentType.includes('application/json')
    const payload = isJson ? await response.json().catch(() => null) : await response.text().catch(() => null)

    if (!response.ok) {
      const detail = payload && typeof payload === 'object' ? payload.detail : payload
      throw new ApiError({
        message: formatErrorMessage(response.status, detail),
        status: response.status,
        code: resolveErrorCode(response.status),
        detail,
        endpoint: normalizedPath,
      })
    }

    return payload
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }

    const isTimeout =
      error?.name === 'AbortError' &&
      (controller.signal.reason?.message === 'TIMEOUT' || !externalSignal?.aborted)

    if (isTimeout) {
      throw new ApiError({
        message: 'Tempo limite esgotado ao comunicar com o servidor local (FastAPI).',
        status: 0,
        code: 'TIMEOUT_ERROR',
        endpoint: normalizedPath,
      })
    }

    throw new ApiError({
      message: 'Servidor local indisponível. Verifique se o backend FastAPI está em execução na rede.',
      status: 0,
      code: 'NETWORK_ERROR',
      detail: error?.message || null,
      endpoint: normalizedPath,
    })
  } finally {
    clearTimeout(timeoutId)
  }
}

// ============================================================================
// ENDPOINTS REAIS DO BACKEND FASTAPI
// ============================================================================

/**
 * Verifica se o backend FastAPI está ativo e respondendo (`GET /`).
 */
export function checkBackendHealth(options = {}) {
  return apiRequest('/', options)
}

/**
 * Cadastra um novo participante (`POST /auth/register`).
 * Não injeta credenciais ou senhas padrão compartilhadas.
 * Envia exatamente os campos fornecidos pela camada de interface.
 */
export function registerParticipant(payload, options = {}) {
  const body = { username: payload.username }
  if (payload.password !== undefined && payload.password !== '') {
    body.password = payload.password
  }
  return apiRequest('/auth/register', {
    ...options,
    method: 'POST',
    body,
  })
}

/**
 * Autentica um usuário (`POST /auth/login`).
 * Retorna `{ access_token, token_type }`.
 */
export async function login({ username, password }, options = {}) {
  const tokenData = await apiRequest('/auth/login', {
    ...options,
    method: 'POST',
    body: { username, password },
  })
  if (tokenData?.access_token && options.persistInMemory !== false) {
    setAuthToken(tokenData.access_token)
  }
  return tokenData
}

/**
 * Obtém o perfil do usuário autenticado (`GET /me`).
 */
export function getMyProfile(options = {}) {
  return apiRequest('/me', options)
}

/**
 * Obtém as pontuações individuais do participante autenticado (`GET /me/scores`).
 */
export function getMyScores(options = {}) {
  return apiRequest('/me/scores', options)
}

/**
 * Obtém o ranking público para o Telão/TV (`GET /display/ranking`).
 * Retorna `{ ranking: [{ position, participant_code, total_points }] }`.
 */
export function getDisplayRanking(options = {}) {
  return apiRequest('/display/ranking', options)
}

/**
 * Obtém o jogo ativo vinculado ao chefe de mesa autenticado (`GET /game-master/game`).
 * Retorna `{ id, name, is_active }`.
 */
export function getGameMasterGame(options = {}) {
  return apiRequest('/game-master/game', options)
}

/**
 * Lista todas as pontuações já registradas no jogo do chefe de mesa (`GET /game-master/scores`).
 * Retorna `[{ participant_code, points, created_at }]`.
 */
export function getGameMasterScores(options = {}) {
  return apiRequest('/game-master/scores', options)
}

/**
 * Registra a pontuação de um participante no jogo do chefe de mesa (`POST /game-master/scores`).
 * Requer `participant_code` (6 caracteres) e `points` (inteiro de 1 a 100).
 */
export function submitGameMasterScore({ participant_code, points }, options = {}) {
  return apiRequest('/game-master/scores', {
    ...options,
    method: 'POST',
    body: { participant_code, points },
  })
}

/**
 * Lista os jogos cadastrados (`GET /admin/games` - requer perfil `admin`).
 */
export function listAdminGames(options = {}) {
  return apiRequest('/admin/games', options)
}

/**
 * Cria um novo jogo (`POST /admin/games` - requer perfil `admin`).
 */
export function createAdminGame({ name }, options = {}) {
  return apiRequest('/admin/games', {
    ...options,
    method: 'POST',
    body: { name },
  })
}

/**
 * Lista os chefes de mesa cadastrados (`GET /admin/masters` - requer perfil `admin`).
 */
export function listAdminMasters(options = {}) {
  return apiRequest('/admin/masters', options)
}

/**
 * Cadastra um novo chefe de mesa (`POST /admin/masters` - requer perfil `admin`).
 */
export function createAdminMaster({ username, password }, options = {}) {
  return apiRequest('/admin/masters', {
    ...options,
    method: 'POST',
    body: { username, password },
  })
}

/**
 * Vincula um chefe de mesa a um jogo (`PUT /admin/games/{gameId}/master` - requer perfil `admin`).
 */
export function assignMasterToGame(gameId, { master_id }, options = {}) {
  return apiRequest(`/admin/games/${gameId}/master`, {
    ...options,
    method: 'PUT',
    body: { master_id },
  })
}

/**
 * Corrige uma pontuação existente (`PATCH /admin/scores/{scoreId}` - requer perfil `admin`).
 */
export function correctAdminScore(scoreId, { points }, options = {}) {
  return apiRequest(`/admin/scores/${scoreId}`, {
    ...options,
    method: 'PATCH',
    body: { points },
  })
}

/**
 * Obtém o ranking geral administrativo com total de participantes (`GET /admin/ranking` - requer perfil `admin`).
 */
export function getAdminRanking(options = {}) {
  return apiRequest('/admin/ranking', options)
}

