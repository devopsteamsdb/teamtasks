import os
import json
import logging
import requests
from dotenv import load_dotenv

# Ensure .env is loaded
project_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(project_dir, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    load_dotenv()

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.reload_config()

    def reload_config(self):
        # Local airgapped OpenAI-compatible gateway settings
        self.openai_base_url = os.getenv('OPENAI_API_BASE') or os.getenv('AI_BASE_URL')
        self.openai_api_key = os.getenv('OPENAI_API_KEY') or os.getenv('AI_API_KEY') or 'sk-local'
        self.openai_model = os.getenv('OPENAI_MODEL') or os.getenv('AI_MODEL') or 'llama3.3'
        
        # Cloudflare Workers AI settings
        self.cf_account_id = os.getenv('CLOUDFLARE_ACCOUNT_ID')
        self.cf_api_token = os.getenv('CLOUDFLARE_API_TOKEN')
        self.cf_model = os.getenv('CLOUDFLARE_MODEL') or '@cf/meta/llama-3.1-8b-instruct'
        self.cf_fallback_model = '@cf/meta/llama-3.3-70b-instruct-fp8-fast'

        # Explicit provider override: 'local_openai' or 'cloudflare'
        explicit_provider = os.getenv('AI_PROVIDER', '').lower().strip()
        
        if explicit_provider == 'local_openai':
            self.provider = 'local_openai'
        elif explicit_provider == 'cloudflare':
            self.provider = 'cloudflare'
        elif self.openai_base_url:
            self.provider = 'local_openai'
        elif self.cf_account_id and self.cf_api_token:
            self.provider = 'cloudflare'
        else:
            self.provider = 'none'

    def get_status(self):
        self.reload_config()
        if self.provider == 'local_openai':
            return {
                'configured': True,
                'provider': 'local_openai',
                'name': 'Local OpenAI Gateway (Airgapped)',
                'model': self.openai_model,
                'base_url': self.openai_base_url,
                'is_airgapped': True
            }
        elif self.provider == 'cloudflare':
            return {
                'configured': True,
                'provider': 'cloudflare',
                'name': 'Cloudflare Workers AI (Dev)',
                'model': self.cf_model,
                'is_airgapped': False
            }
        else:
            return {
                'configured': False,
                'provider': 'none',
                'name': 'Not Configured',
                'model': None,
                'is_airgapped': False,
                'hint': 'Configure OPENAI_API_BASE in .env for airgapped local, or CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN for Cloudflare'
            }

    def chat(self, messages, system_prompt=None, temperature=0.2, max_tokens=2048):
        self.reload_config()
        if self.provider == 'none':
            raise ValueError(
                "AI service is not configured. Please set OPENAI_API_BASE in .env (for airgapped local gateway) "
                "or set CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN in .env (for Cloudflare Workers AI)."
            )

        full_messages = []
        if system_prompt:
            full_messages.append({'role': 'system', 'content': system_prompt})
        full_messages.extend(messages)

        if self.provider == 'local_openai':
            return self._call_local_openai(full_messages, temperature, max_tokens)
        else:
            return self._call_cloudflare(full_messages, temperature, max_tokens)

    def _call_local_openai(self, messages, temperature, max_tokens):
        base_url = self.openai_base_url.rstrip('/')
        url = f"{base_url}/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {self.openai_api_key}"
        }
        payload = {
            'model': self.openai_model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            choices = data.get('choices', [])
            if choices and 'message' in choices[0]:
                content = choices[0]['message'].get('content', '')
                if isinstance(content, (dict, list)):
                    return json.dumps(content, ensure_ascii=False)
                return str(content)
            resp = data.get('response', '')
            if isinstance(resp, (dict, list)):
                return json.dumps(resp, ensure_ascii=False)
            return str(resp)
        except Exception as e:
            logger.error(f"Error calling local OpenAI gateway: {e}")
            raise RuntimeError(f"Error from Local OpenAI Gateway ({self.openai_base_url}): {str(e)}")

    def _call_cloudflare(self, messages, temperature, max_tokens):
        headers = {
            'Authorization': f'Bearer {self.cf_api_token}',
            'Content-Type': 'application/json'
        }
        payload = {
            'messages': messages,
            'max_tokens': max_tokens
        }
        
        # Try primary model first
        primary_url = f"https://api.cloudflare.com/client/v4/accounts/{self.cf_account_id}/ai/run/{self.cf_model}"
        try:
            response = requests.post(primary_url, headers=headers, json=payload, timeout=45)
            if response.status_code == 200:
                result = response.json().get('result', {})
                resp = result.get('response', '')
                if isinstance(resp, (dict, list)):
                    return json.dumps(resp, ensure_ascii=False)
                return str(resp)
            logger.warning(f"Cloudflare primary model {self.cf_model} returned status {response.status_code}: {response.text}")
        except Exception as e:
            logger.warning(f"Cloudflare primary model failed with error: {e}. Trying fallback model.")

        # Fallback to 8b instruct model
        fallback_url = f"https://api.cloudflare.com/client/v4/accounts/{self.cf_account_id}/ai/run/{self.cf_fallback_model}"
        try:
            response = requests.post(fallback_url, headers=headers, json=payload, timeout=45)
            response.raise_for_status()
            result = response.json().get('result', {})
            resp = result.get('response', '')
            if isinstance(resp, (dict, list)):
                return json.dumps(resp, ensure_ascii=False)
            return str(resp)
        except Exception as e:
            logger.error(f"Error calling Cloudflare Workers AI fallback model: {e}")
            raise RuntimeError(f"Cloudflare Workers AI error: {str(e)}")

ai_service = AIService()
