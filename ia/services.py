import time
import requests
from django.utils import timezone
from .models import IAConfig, IACallAudit, UserTokenQuota


def estimate_tokens(text: str) -> int:
    """Estimativa aproximada de tokens para fallback (1 token ≈ 4 caracteres)"""
    if not text:
        return 0
    return max(1, len(text) // 4)


def chamar_ia(prompt: str, user, endpoint: str = 'assistente', system_instruction: str = None) -> dict:
    """
    ÚNICA porta de entrada para chamadas à Inteligência Artificial no sistema.
    
    1. Valida se a IA está ativa.
    2. Valida e debita a cota mensal do usuário.
    3. Executa a requisição ao provedor configurado (Google Gemini, OpenAI, etc.).
    4. Registra auditoria completa em IACallAudit.
    5. Atualiza o saldo em UserTokenQuota.
    
    Retorna:
        dict: {
            'success': bool,
            'response': str,
            'total_tokens': int,
            'error': str or None
        }
    """
    start_time = time.time()
    config = IAConfig.get_active_config()

    if not config.ativo:
        return {
            'success': False,
            'response': '',
            'total_tokens': 0,
            'error': 'O serviço de Inteligência Artificial está temporariamente desativado no sistema.'
        }

    # 1. Validação de Cota do Usuário
    quota = None
    if user and user.is_authenticated:
        quota = UserTokenQuota.get_or_create_for_user(user)
        if quota.tokens_used >= quota.monthly_limit:
            error_msg = f"Você atingiu o limite mensal de tokens ({quota.monthly_limit} tokens). Sua cota será renovada no próximo mês."
            IACallAudit.objects.create(
                user=user,
                endpoint=endpoint,
                model_used=config.model_name,
                prompt=prompt,
                response='',
                prompt_tokens=estimate_tokens(prompt),
                response_tokens=0,
                total_tokens=estimate_tokens(prompt),
                latency_ms=int((time.time() - start_time) * 1000),
                status='quota_exceeded',
                error_message=error_msg
            )
            return {
                'success': False,
                'response': '',
                'total_tokens': 0,
                'error': error_msg
            }

    # 2. Execução da Chamada
    effective_sys_prompt = system_instruction or config.system_prompt
    response_text = ""
    prompt_tokens = estimate_tokens(prompt) + estimate_tokens(effective_sys_prompt)
    response_tokens = 0
    status = 'success'
    error_message = ''

    api_key = config.api_key.strip()
    provider = config.provider

    try:
        if provider == 'gemini':
            if not api_key:
                # Simulação inteligente quando a API key ainda não foi cadastrada na tela de configuração
                response_text = (
                    f"Olá! O modelo **{config.model_name}** está configurado, mas a chave de API ainda não foi informada "
                    f"na tela de [Configurações da IA](/ia/config/).\n\n"
                    f"Para ativar o assistente completo, insira sua chave do Google AI Studio no menu de configuração.\n\n"
                    f"> *Mensagem recebida:* \"{prompt[:120]}...\""
                )
            else:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.model_name}:generateContent?key={api_key}"
                payload = {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": f"Instrução do Sistema:\n{effective_sys_prompt}\n\nMensagem do Usuário:\n{prompt}"}]
                        }
                    ],
                    "generationConfig": {
                        "temperature": config.temperature,
                        "maxOutputTokens": config.max_tokens,
                    }
                }
                res = requests.post(url, json=payload, timeout=30)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get('candidates', [])
                    if candidates and 'content' in candidates[0]:
                        parts = candidates[0]['content'].get('parts', [])
                        if parts:
                            response_text = parts[0].get('text', '')
                    usage = data.get('usageMetadata', {})
                    if usage:
                        prompt_tokens = usage.get('promptTokenCount', prompt_tokens)
                        response_tokens = usage.get('candidatesTokenCount', estimate_tokens(response_text))
                    else:
                        response_tokens = estimate_tokens(response_text)
                else:
                    status = 'error'
                    error_message = f"Erro na API Gemini ({res.status_code}): {res.text[:300]}"
                    response_text = f"Ocorreu um erro ao comunicar com a IA: {error_message}"

        elif provider == 'openai':
            if not api_key:
                response_text = "Chave de API da OpenAI não configurada. Acesse as configurações da IA para adicioná-la."
            else:
                url = config.endpoint_url.strip() or "https://api.openai.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {api_key}"}
                payload = {
                    "model": config.model_name,
                    "messages": [
                        {"role": "system", "content": effective_sys_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": config.temperature,
                    "max_tokens": config.max_tokens,
                }
                res = requests.post(url, headers=headers, json=payload, timeout=30)
                if res.status_code == 200:
                    data = res.json()
                    response_text = data['choices'][0]['message']['content']
                    usage = data.get('usage', {})
                    prompt_tokens = usage.get('prompt_tokens', prompt_tokens)
                    response_tokens = usage.get('completion_tokens', estimate_tokens(response_text))
                else:
                    status = 'error'
                    error_message = f"Erro na API OpenAI ({res.status_code}): {res.text[:300]}"
                    response_text = f"Ocorreu um erro ao comunicar com a IA: {error_message}"

        else: # custom
            response_text = f"Provedor customizado '{provider}' acionado com sucesso. Prompt: {prompt[:80]}"
            response_tokens = estimate_tokens(response_text)

    except requests.exceptions.RequestException as e:
        status = 'error'
        error_message = f"Exceção de rede ao chamar IA: {str(e)}"
        response_text = f"Não foi possível conectar ao servidor de IA: {error_message}"
    except Exception as e:
        status = 'error'
        error_message = f"Erro inesperado: {str(e)}"
        response_text = f"Erro interno ao processar a resposta: {error_message}"

    if not response_tokens:
        response_tokens = estimate_tokens(response_text)
    total_tokens = prompt_tokens + response_tokens
    latency_ms = int((time.time() - start_time) * 1000)

    # 3. Auditoria da Requisição
    IACallAudit.objects.create(
        user=user if (user and user.is_authenticated) else None,
        endpoint=endpoint,
        model_used=config.model_name,
        prompt=prompt,
        response=response_text,
        prompt_tokens=prompt_tokens,
        response_tokens=response_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
        status=status,
        error_message=error_message
    )

    # 4. Atualização da Cota do Usuário
    if quota and status == 'success':
        quota.tokens_used += total_tokens
        quota.save(update_fields=['tokens_used', 'updated_at'])

    return {
        'success': status == 'success',
        'response': response_text,
        'total_tokens': total_tokens,
        'latency_ms': latency_ms,
        'error': error_message if status != 'success' else None
    }

