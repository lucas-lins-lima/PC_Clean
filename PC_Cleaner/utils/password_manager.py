# utils/password_manager.py
import json
import hashlib
import secrets
import string
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, List
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

# Configuração de logging específica para passwords
password_logger = logging.getLogger('password_manager')
password_handler = logging.FileHandler('password_manager.log')
password_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
password_handler.setFormatter(password_formatter)
password_logger.addHandler(password_handler)
password_logger.setLevel(logging.INFO)

class PasswordManager:
    """Sistema completo de gerenciamento de senhas para planos Pro e Master Plus"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.passwords_file = os.path.join(data_dir, "passwords.json")
        self.user_data_file = os.path.join(data_dir, "user_data.json")
        self.attempts_file = os.path.join(data_dir, "login_attempts.json")
        
        # Configurações de segurança
        self.max_attempts = 5
        self.lockout_duration = 1800  # 30 minutos em segundos
        self.password_length = 16
        self.salt_length = 32
        
        # Períodos disponíveis (em dias)
        self.available_periods = {
            'trimestre': 90,
            'semestre': 180,
            'ano': 365
        }
        
        # Tipos de planos
        self.plan_types = ['pro', 'master_plus']
        
        # Criar diretório de dados se não existir
        os.makedirs(data_dir, exist_ok=True)
        
        # Inicializar arquivos se não existirem
        self._initialize_files()
        
        # Chave mestra para criptografia
        self.master_key = self._get_or_create_master_key()
        self.cipher_suite = Fernet(self.master_key)

    def _initialize_files(self):
        """Inicializa arquivos JSON necessários"""
        files_to_init = [
            (self.passwords_file, {}),
            (self.user_data_file, {}),
            (self.attempts_file, {})
        ]
        
        for file_path, default_content in files_to_init:
            if not os.path.exists(file_path):
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(default_content, f, indent=2)
                    password_logger.info(f"Arquivo criado: {file_path}")
                except Exception as e:
                    password_logger.error(f"Erro ao criar arquivo {file_path}: {e}")

    def _get_or_create_master_key(self) -> bytes:
        """Obtém ou cria chave mestra para criptografia"""
        key_file = os.path.join(self.data_dir, ".master_key")
        
        if os.path.exists(key_file):
            try:
                with open(key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                password_logger.error(f"Erro ao ler chave mestra: {e}")
        
        # Gerar nova chave mestra
        password = b"PCCleaner2025_MasterKey_SecureEncryption"
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        
        try:
            with open(key_file, 'wb') as f:
                f.write(key)
            # Tornar arquivo oculto (Windows)
            os.system(f'attrib +h "{key_file}"')
            password_logger.info("Nova chave mestra criada")
        except Exception as e:
            password_logger.error(f"Erro ao salvar chave mestra: {e}")
        
        return key

    def generate_secure_password(self, length: int = None) -> str:
        """Gera senha segura com caracteres aleatórios"""
        if length is None:
            length = self.password_length
        
        # Definir conjuntos de caracteres
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        # Garantir pelo menos um caractere de cada tipo
        password_chars = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]
        
        # Preencher o restante aleatoriamente
        all_chars = lowercase + uppercase + digits + special
        for _ in range(length - 4):
            password_chars.append(secrets.choice(all_chars))
        
        # Embaralhar para posição aleatória
        secrets.SystemRandom().shuffle(password_chars)
        
        password = ''.join(password_chars)
        password_logger.info(f"Senha segura gerada com comprimento: {length}")
        
        return password

    def create_password_entry(self, email: str, plan_type: str, period: str) -> Tuple[str, bool]:
        """Cria nova entrada de senha para um usuário"""
        if plan_type not in self.plan_types:
            return "", False
        
        if period not in self.available_periods:
            return "", False
        
        # Verificar se usuário já tem senha ativa
        if self._has_active_password(email, plan_type):
            password_logger.warning(f"Usuário {email} já possui senha ativa para plano {plan_type}")
            return "", False
        
        # Gerar nova senha
        password = self.generate_secure_password()
        password_hash = self._hash_password(password)
        
        # Criar entrada de dados
        password_data = {
            'email': email,
            'plan_type': plan_type,
            'period': period,
            'period_days': self.available_periods[period],
            'password_hash': password_hash,
            'created_at': datetime.now().isoformat(),
            'activated_at': None,
            'expires_at': None,
            'is_active': False,
            'is_expired': False,
            'login_count': 0,
            'last_login': None,
            'ip_addresses': [],
            'device_fingerprint': None
        }
        
        # Salvar dados criptografados
        if self._save_password_data(email, plan_type, password_data):
            password_logger.info(f"Senha criada para {email} - Plano: {plan_type} - Período: {period}")
            return password, True
        
        return "", False

    def validate_password(self, email: str, password: str, plan_type: str, 
                         device_info: Dict = None) -> Tuple[bool, str, Dict]:
        """Valida senha inserida pelo usuário"""
        
        # Verificar tentativas de login
        if self._is_account_locked(email):
            remaining_time = self._get_lockout_remaining_time(email)
            return False, f"Conta bloqueada. Tente novamente em {remaining_time} minutos.", {}
        
        # Carregar dados da senha
        password_data = self._load_password_data(email, plan_type)
        if not password_data:
            self._record_failed_attempt(email)
            return False, "Senha não encontrada para este usuário/plano.", {}
        
        # Verificar se senha está correta
        if not self._verify_password(password, password_data['password_hash']):
            self._record_failed_attempt(email)
            attempts_left = self.max_attempts - self._get_failed_attempts_count(email)
            return False, f"Senha incorreta. Tentativas restantes: {attempts_left}", {}
        
        # Verificar se senha já expirou
        if password_data.get('is_expired', False):
            return False, "Esta senha já expirou. Solicite uma nova senha.", {}
        
        # Primeiro uso - ativar senha
        if not password_data.get('is_active', False):
            password_data = self._activate_password(email, plan_type, password_data, device_info)
        
        # Verificar se não expirou após ativação
        if self._is_password_expired(password_data):
            self._mark_password_as_expired(email, plan_type)
            return False, "Esta senha expirou. Solicite uma nova senha.", {}
        
        # Atualizar informações de login
        password_data = self._update_login_info(email, plan_type, password_data, device_info)
        
        # Limpar tentativas falhadas
        self._clear_failed_attempts(email)
        
        # Calcular dias restantes
        days_remaining = self._calculate_days_remaining(password_data)
        
        user_info = {
            'email': email,
            'plan_type': plan_type,
            'period': password_data['period'],
            'days_remaining': days_remaining,
            'login_count': password_data.get('login_count', 0),
            'activated_at': password_data.get('activated_at'),
            'expires_at': password_data.get('expires_at')
        }
        
        password_logger.info(f"Login bem-sucedido: {email} - Plano: {plan_type}")
        return True, "Login realizado com sucesso!", user_info

    def check_password_status(self, email: str, plan_type: str) -> Dict:
        """Verifica status atual da senha do usuário"""
        password_data = self._load_password_data(email, plan_type)
        
        if not password_data:
            return {
                'exists': False,
                'is_active': False,
                'is_expired': False,
                'days_remaining': 0,
                'message': 'Nenhuma senha encontrada para este usuário/plano.'
            }
        
        is_expired = self._is_password_expired(password_data)
        days_remaining = self._calculate_days_remaining(password_data)
        
        status = {
            'exists': True,
            'is_active': password_data.get('is_active', False),
            'is_expired': is_expired,
            'days_remaining': days_remaining,
            'period': password_data.get('period'),
            'created_at': password_data.get('created_at'),
            'activated_at': password_data.get('activated_at'),
            'expires_at': password_data.get('expires_at'),
            'login_count': password_data.get('login_count', 0),
            'last_login': password_data.get('last_login')
        }
        
        if is_expired:
            status['message'] = 'Senha expirada. Solicite uma nova senha.'
        elif not password_data.get('is_active', False):
            status['message'] = 'Senha criada mas ainda não ativada.'
        elif days_remaining <= 7:
            status['message'] = f'Atenção: Sua senha expira em {days_remaining} dias.'
        else:
            status['message'] = f'Senha ativa. {days_remaining} dias restantes.'
        
        return status

    def revoke_password(self, email: str, plan_type: str) -> bool:
        """Revoga/desativa senha do usuário"""
        password_data = self._load_password_data(email, plan_type)
        
        if not password_data:
            return False
        
        password_data['is_expired'] = True
        password_data['revoked_at'] = datetime.now().isoformat()
        
        if self._save_password_data(email, plan_type, password_data):
            password_logger.info(f"Senha revogada para {email} - Plano: {plan_type}")
            return True
        
        return False

    def get_user_statistics(self, email: str) -> Dict:
        """Obtém estatísticas de uso do usuário"""
        stats = {
            'email': email,
            'plans': {},
            'total_logins': 0,
            'first_login': None,
            'last_login': None,
            'active_plans': []
        }
        
        for plan_type in self.plan_types:
            password_data = self._load_password_data(email, plan_type)
            if password_data:
                plan_stats = {
                    'exists': True,
                    'is_active': password_data.get('is_active', False),
                    'is_expired': self._is_password_expired(password_data),
                    'login_count': password_data.get('login_count', 0),
                    'period': password_data.get('period'),
                    'days_remaining': self._calculate_days_remaining(password_data),
                    'created_at': password_data.get('created_at'),
                    'activated_at': password_data.get('activated_at')
                }
                
                stats['plans'][plan_type] = plan_stats
                stats['total_logins'] += plan_stats['login_count']
                
                if plan_stats['is_active'] and not plan_stats['is_expired']:
                    stats['active_plans'].append(plan_type)
                
                # Atualizar datas globais
                if password_data.get('activated_at'):
                    activated_date = password_data['activated_at']
                    if not stats['first_login'] or activated_date < stats['first_login']:
                        stats['first_login'] = activated_date
                
                if password_data.get('last_login'):
                    last_login = password_data['last_login']
                    if not stats['last_login'] or last_login > stats['last_login']:
                        stats['last_login'] = last_login
        
        return stats

    def cleanup_expired_passwords(self) -> int:
        """Remove senhas expiradas há mais de 30 dias"""
        cleaned_count = 0
        
        try:
            with open(self.passwords_file, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
            
            cutoff_date = datetime.now() - timedelta(days=30)
            
            for user_key in list(all_data.keys()):
                user_data = all_data[user_key]
                
                # Verificar cada plano do usuário
                for plan_key in list(user_data.keys()):
                    plan_data = user_data[plan_key]
                    
                    if plan_data.get('is_expired', False):
                        # Verificar se expirou há mais de 30 dias
                        if plan_data.get('expires_at'):
                            expire_date = datetime.fromisoformat(plan_data['expires_at'])
                            if expire_date < cutoff_date:
                                del user_data[plan_key]
                                cleaned_count += 1
                
                # Remover usuário se não tiver mais planos
                if not user_data:
                    del all_data[user_key]
            
            # Salvar dados limpos
            with open(self.passwords_file, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False)
            
            password_logger.info(f"Limpeza concluída: {cleaned_count} senhas expiradas removidas")
            
        except Exception as e:
            password_logger.error(f"Erro na limpeza de senhas expiradas: {e}")
        
        return cleaned_count

    def generate_usage_report(self) -> Dict:
        """Gera relatório completo de uso do sistema de senhas"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_users': 0,
            'active_users': 0,
            'expired_users': 0,
            'plans_stats': {plan: {'total': 0, 'active': 0, 'expired': 0} for plan in self.plan_types},
            'period_stats': {period: 0 for period in self.available_periods.keys()},
            'recent_logins': [],
            'top_users': []
        }
        
        try:
            with open(self.passwords_file, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
            
            all_users_stats = []
            
            for user_key, user_data in all_data.items():
                user_email = user_key.split('_')[0]  # Extrair email do key
                user_stats = {'email': user_email, 'total_logins': 0, 'plans': []}
                
                for plan_key, plan_data in user_data.items():
                    plan_type = plan_key
                    is_active = plan_data.get('is_active', False)
                    is_expired = self._is_password_expired(plan_data)
                    
                    # Estatísticas por plano
                    report['plans_stats'][plan_type]['total'] += 1
                    if is_active and not is_expired:
                        report['plans_stats'][plan_type]['active'] += 1
                    if is_expired:
                        report['plans_stats'][plan_type]['expired'] += 1
                    
                    # Estatísticas por período
                    period = plan_data.get('period', 'unknown')
                    if period in report['period_stats']:
                        report['period_stats'][period] += 1
                    
                    # Estatísticas do usuário
                    login_count = plan_data.get('login_count', 0)
                    user_stats['total_logins'] += login_count
                    user_stats['plans'].append({
                        'type': plan_type,
                        'logins': login_count,
                        'active': is_active and not is_expired
                    })
                    
                    # Logins recentes
                    if plan_data.get('last_login'):
                        report['recent_logins'].append({
                            'email': user_email,
                            'plan': plan_type,
                            'login_time': plan_data['last_login'],
                            'login_count': login_count
                        })
                
                all_users_stats.append(user_stats)
                report['total_users'] += 1
                
                # Verificar se tem planos ativos
                has_active = any(plan['active'] for plan in user_stats['plans'])
                if has_active:
                    report['active_users'] += 1
                else:
                    report['expired_users'] += 1
            
            # Top usuários por login
            report['top_users'] = sorted(all_users_stats, 
                                       key=lambda x: x['total_logins'], 
                                       reverse=True)[:10]
            
            # Logins recentes ordenados
            report['recent_logins'] = sorted(report['recent_logins'], 
                                           key=lambda x: x['login_time'], 
                                           reverse=True)[:20]
            
        except Exception as e:
            password_logger.error(f"Erro ao gerar relatório: {e}")
        
        return report

    # Métodos privados auxiliares
    def _hash_password(self, password: str) -> str:
        """Gera hash seguro da senha"""
        salt = os.urandom(self.salt_length)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return base64.b64encode(salt + pwd_hash).decode('ascii')

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verifica se senha corresponde ao hash armazenado"""
        try:
            decoded_hash = base64.b64decode(stored_hash.encode('ascii'))
            salt = decoded_hash[:self.salt_length]
            stored_pwd_hash = decoded_hash[self.salt_length:]
            pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            return pwd_hash == stored_pwd_hash
        except Exception:
            return False

    def _has_active_password(self, email: str, plan_type: str) -> bool:
        """Verifica se usuário já tem senha ativa para o plano"""
        password_data = self._load_password_data(email, plan_type)
        if password_data:
            return password_data.get('is_active', False) and not self._is_password_expired(password_data)
        return False

    def _load_password_data(self, email: str, plan_type: str) -> Optional[Dict]:
        """Carrega dados da senha do arquivo"""
        try:
            with open(self.passwords_file, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
            
            user_key = f"{email}_{plan_type}"
            
            if user_key in all_data and plan_type in all_data[user_key]:
                encrypted_data = all_data[user_key][plan_type]
                # Descriptografar dados sensíveis se necessário
                return encrypted_data
            
        except Exception as e:
            password_logger.error(f"Erro ao carregar dados da senha: {e}")
        
        return None

    def _save_password_data(self, email: str, plan_type: str, password_data: Dict) -> bool:
        """Salva dados da senha no arquivo"""
        try:
            # Carregar dados existentes
            try:
                with open(self.passwords_file, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                all_data = {}
            
            user_key = f"{email}_{plan_type}"
            
            if user_key not in all_data:
                all_data[user_key] = {}
            
            # Criptografar dados sensíveis se necessário
            all_data[user_key][plan_type] = password_data
            
            # Salvar dados atualizados
            with open(self.passwords_file, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            password_logger.error(f"Erro ao salvar dados da senha: {e}")
            return False

    def _activate_password(self, email: str, plan_type: str, password_data: Dict, device_info: Dict = None) -> Dict:
        """Ativa senha no primeiro uso"""
        now = datetime.now()
        expire_date = now + timedelta(days=password_data['period_days'])
        
        password_data['is_active'] = True
        password_data['activated_at'] = now.isoformat()
        password_data['expires_at'] = expire_date.isoformat()
        password_data['login_count'] = 1
        password_data['last_login'] = now.isoformat()
        
        if device_info:
            password_data['device_fingerprint'] = device_info.get('fingerprint')
            password_data['ip_addresses'] = [device_info.get('ip_address', 'unknown')]
        
        self._save_password_data(email, plan_type, password_data)
        password_logger.info(f"Senha ativada para {email} - Plano: {plan_type} - Expira em: {expire_date}")
        
        return password_data

    def _update_login_info(self, email: str, plan_type: str, password_data: Dict, device_info: Dict = None) -> Dict:
        """Atualiza informações de login"""
        password_data['login_count'] = password_data.get('login_count', 0) + 1
        password_data['last_login'] = datetime.now().isoformat()
        
        if device_info and device_info.get('ip_address'):
            ip_addresses = password_data.get('ip_addresses', [])
            new_ip = device_info['ip_address']
            if new_ip not in ip_addresses:
                ip_addresses.append(new_ip)
                password_data['ip_addresses'] = ip_addresses[-10:]  # Manter apenas os 10 últimos IPs
        
        self._save_password_data(email, plan_type, password_data)
        return password_data

    def _is_password_expired(self, password_data: Dict) -> bool:
        """Verifica se senha está expirada"""
        if password_data.get('is_expired', False):
            return True
        
        if not password_data.get('expires_at'):
            return False
        
        try:
            expire_date = datetime.fromisoformat(password_data['expires_at'])
            return datetime.now() > expire_date
        except Exception:
            return True

    def _mark_password_as_expired(self, email: str, plan_type: str):
        """Marca senha como expirada"""
        password_data = self._load_password_data(email, plan_type)
        if password_data:
            password_data['is_expired'] = True
            password_data['expired_at'] = datetime.now().isoformat()
            self._save_password_data(email, plan_type, password_data)

    def _calculate_days_remaining(self, password_data: Dict) -> int:
        """Calcula dias restantes da senha"""
        if not password_data.get('expires_at') or password_data.get('is_expired', False):
            return 0
        
        try:
            expire_date = datetime.fromisoformat(password_data['expires_at'])
            remaining = expire_date - datetime.now()
            return max(0, remaining.days)
        except Exception:
            return 0

    def _is_account_locked(self, email: str) -> bool:
        """Verifica se conta está bloqueada por tentativas falhadas"""
        try:
            with open(self.attempts_file, 'r', encoding='utf-8') as f:
                attempts_data = json.load(f)
            
            if email in attempts_data:
                user_attempts = attempts_data[email]
                if user_attempts.get('failed_count', 0) >= self.max_attempts:
                    last_attempt = datetime.fromisoformat(user_attempts['last_attempt'])
                    if (datetime.now() - last_attempt).seconds < self.lockout_duration:
                        return True
            
        except Exception:
            pass
        
        return False

    def _get_lockout_remaining_time(self, email: str) -> int:
        """Obtém tempo restante de bloqueio em minutos"""
        try:
            with open(self.attempts_file, 'r', encoding='utf-8') as f:
                attempts_data = json.load(f)
            
            if email in attempts_data:
                last_attempt = datetime.fromisoformat(attempts_data[email]['last_attempt'])
                elapsed = (datetime.now() - last_attempt).seconds
                remaining = (self.lockout_duration - elapsed) // 60
                return max(0, remaining)
        except Exception:
            pass
        
        return 0

    def _record_failed_attempt(self, email: str):
        """Registra tentativa de login falhada"""
        try:
            try:
                with open(self.attempts_file, 'r', encoding='utf-8') as f:
                    attempts_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                attempts_data = {}
            
            if email not in attempts_data:
                attempts_data[email] = {'failed_count': 0, 'last_attempt': None}
            
            attempts_data[email]['failed_count'] += 1
            attempts_data[email]['last_attempt'] = datetime.now().isoformat()
            
            with open(self.attempts_file, 'w', encoding='utf-8') as f:
                json.dump(attempts_data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            password_logger.error(f"Erro ao registrar tentativa falhada: {e}")

    def _get_failed_attempts_count(self, email: str) -> int:
        """Obtém número de tentativas falhadas"""
        try:
            with open(self.attempts_file, 'r', encoding='utf-8') as f:
                attempts_data = json.load(f)
            
            return attempts_data.get(email, {}).get('failed_count', 0)
        except Exception:
            return 0

    def _clear_failed_attempts(self, email: str):
        """Limpa tentativas falhadas após login bem-sucedido"""
        try:
            with open(self.attempts_file, 'r', encoding='utf-8') as f:
                attempts_data = json.load(f)
            
            if email in attempts_data:
                del attempts_data[email]
            
            with open(self.attempts_file, 'w', encoding='utf-8') as f:
                json.dump(attempts_data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            password_logger.error(f"Erro ao limpar tentativas falhadas: {e}")

# Função auxiliar para validação de força de senha
def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """Valida força da senha gerada"""
    issues = []
    
    if len(password) < 12:
        issues.append("Senha deve ter pelo menos 12 caracteres")
    
    if not any(c.isupper() for c in password):
        issues.append("Senha deve conter pelo menos uma letra maiúscula")
    
    if not any(c.islower() for c in password):
        issues.append("Senha deve conter pelo menos uma letra minúscula")
    
    if not any(c.isdigit() for c in password):
        issues.append("Senha deve conter pelo menos um número")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        issues.append("Senha deve conter pelo menos um caractere especial")
    
    return len(issues) == 0, issues

# Função para gerar device fingerprint
def generate_device_fingerprint() -> str:
    """Gera fingerprint único do dispositivo"""
    import platform
    import uuid
    
    device_info = {
        'platform': platform.platform(),
        'processor': platform.processor(),
        'machine': platform.machine(),
        'node': platform.node(),
        'mac_address': ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                                for elements in range(0,2*6,2)][::-1])
    }
    
    fingerprint_string = json.dumps(device_info, sort_keys=True)
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()