# utils/date_tracker.py
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Union
import logging
import threading
import time
from pathlib import Path
import calendar
from enum import Enum
import pytz

# Configuração de logging específica para date_tracker
date_logger = logging.getLogger('date_tracker')
date_handler = logging.FileHandler('date_tracker.log')
date_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
date_handler.setFormatter(date_formatter)
date_logger.addHandler(date_handler)
date_logger.setLevel(logging.INFO)

class PeriodType(Enum):
    """Tipos de períodos disponíveis"""
    TRIMESTRE = "trimestre"
    SEMESTRE = "semestre"
    ANO = "ano"

class LicenseStatus(Enum):
    """Status possíveis de uma licença"""
    CREATED = "created"          # Criada mas não ativada
    ACTIVE = "active"            # Ativa e dentro do prazo
    EXPIRING_SOON = "expiring_soon"  # Expira em menos de 7 dias
    EXPIRED = "expired"          # Expirada
    REVOKED = "revoked"          # Revogada manualmente
    SUSPENDED = "suspended"      # Suspensa temporariamente

class DateTracker:
    """Sistema completo de controle de datas e períodos para licenças"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.tracker_file = os.path.join(data_dir, "date_tracker.json")
        self.alerts_file = os.path.join(data_dir, "date_alerts.json")
        self.usage_patterns_file = os.path.join(data_dir, "usage_patterns.json")
        
        # Configurações de período
        self.period_days = {
            PeriodType.TRIMESTRE: 90,
            PeriodType.SEMESTRE: 180,
            PeriodType.ANO: 365
        }
        
        # Configurações de alertas
        self.alert_days = [30, 14, 7, 3, 1]  # Dias antes da expiração para alertar
        self.timezone = pytz.timezone('America/Sao_Paulo')  # Timezone padrão
        
        # Sistema de monitoramento automático
        self.monitoring_active = False
        self.monitoring_interval = 3600  # 1 hora em segundos
        
        # Inicializar sistema
        self._initialize_system()
        self._start_automatic_monitoring()

    def _initialize_system(self):
        """Inicializa o sistema de controle de datas"""
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Inicializar arquivos se não existirem
        default_files = [
            (self.tracker_file, {}),
            (self.alerts_file, {'pending_alerts': [], 'sent_alerts': []}),
            (self.usage_patterns_file, {'daily_usage': {}, 'weekly_patterns': {}, 'monthly_stats': {}})
        ]
        
        for file_path, default_content in default_files:
            if not os.path.exists(file_path):
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(default_content, f, indent=2, ensure_ascii=False)
                    date_logger.info(f"Arquivo inicializado: {file_path}")
                except Exception as e:
                    date_logger.error(f"Erro ao inicializar arquivo {file_path}: {e}")

    def create_license_period(self, user_email: str, plan_type: str, 
                             period_type: Union[str, PeriodType],
                             custom_days: Optional[int] = None) -> Tuple[bool, Dict]:
        """Cria um novo período de licença para um usuário"""
        try:
            # Normalizar period_type
            if isinstance(period_type, str):
                period_type = PeriodType(period_type.lower())
            
            # Calcular dias do período
            if custom_days:
                period_days = custom_days
            else:
                period_days = self.period_days[period_type]
            
            # Gerar ID único para a licença
            license_id = self._generate_license_id(user_email, plan_type)
            
            # Criar registro de licença
            now = self._get_current_datetime()
            license_data = {
                'license_id': license_id,
                'user_email': user_email,
                'plan_type': plan_type,
                'period_type': period_type.value,
                'period_days': period_days,
                'status': LicenseStatus.CREATED.value,
                'created_at': now.isoformat(),
                'activated_at': None,
                'expires_at': None,
                'last_access': None,
                'access_count': 0,
                'timezone': str(self.timezone),
                'alerts_sent': [],
                'extensions': [],
                'suspension_history': [],
                'usage_stats': {
                    'total_sessions': 0,
                    'total_duration_minutes': 0,
                    'peak_usage_day': None,
                    'average_session_duration': 0
                }
            }
            
            # Salvar licença
            if self._save_license_data(license_id, license_data):
                date_logger.info(f"Licença criada: {license_id} para {user_email}")
                return True, license_data
            else:
                return False, {}
                
        except Exception as e:
            error_msg = f"Erro ao criar período de licença: {e}"
            date_logger.error(error_msg)
            return False, {'error': error_msg}

    def activate_license(self, user_email: str, plan_type: str, 
                        activation_datetime: Optional[datetime] = None) -> Tuple[bool, Dict]:
        """Ativa uma licença iniciando a contagem de tempo"""
        try:
            license_id = self._generate_license_id(user_email, plan_type)
            license_data = self._load_license_data(license_id)
            
            if not license_data:
                return False, {'error': 'Licença não encontrada'}
            
            if license_data['status'] != LicenseStatus.CREATED.value:
                return False, {'error': f'Licença já foi ativada ou está em status: {license_data["status"]}'}
            
            # Usar datetime fornecido ou atual
            activation_time = activation_datetime or self._get_current_datetime()
            expire_time = activation_time + timedelta(days=license_data['period_days'])
            
            # Atualizar dados da licença
            license_data.update({
                'status': LicenseStatus.ACTIVE.value,
                'activated_at': activation_time.isoformat(),
                'expires_at': expire_time.isoformat(),
                'last_access': activation_time.isoformat(),
                'access_count': 1
            })
            
            # Salvar dados atualizados
            if self._save_license_data(license_id, license_data):
                # Agendar alertas de expiração
                self._schedule_expiration_alerts(license_id, expire_time)
                
                # Registrar padrão de uso
                self._record_usage_pattern(user_email, plan_type, 'activation')
                
                date_logger.info(f"Licença ativada: {license_id} - Expira em: {expire_time}")
                return True, license_data
            else:
                return False, {'error': 'Erro ao salvar dados da licença'}
                
        except Exception as e:
            error_msg = f"Erro ao ativar licença: {e}"
            date_logger.error(error_msg)
            return False, {'error': error_msg}

    def check_license_status(self, user_email: str, plan_type: str) -> Dict:
        """Verifica status atual de uma licença"""
        try:
            license_id = self._generate_license_id(user_email, plan_type)
            license_data = self._load_license_data(license_id)
            
            if not license_data:
                return {
                    'exists': False,
                    'status': 'not_found',
                    'message': 'Licença não encontrada'
                }
            
            current_time = self._get_current_datetime()
            
            # Calcular informações de tempo
            time_info = self._calculate_time_info(license_data, current_time)
            
            # Determinar status atual
            current_status = self._determine_current_status(license_data, current_time)
            
            # Atualizar status se necessário
            if current_status != license_data['status']:
                license_data['status'] = current_status
                self._save_license_data(license_id, license_data)
            
            return {
                'exists': True,
                'license_id': license_id,
                'status': current_status,
                'plan_type': license_data['plan_type'],
                'period_type': license_data['period_type'],
                'period_days': license_data['period_days'],
                'created_at': license_data['created_at'],
                'activated_at': license_data.get('activated_at'),
                'expires_at': license_data.get('expires_at'),
                'last_access': license_data.get('last_access'),
                'access_count': license_data.get('access_count', 0),
                'days_remaining': time_info['days_remaining'],
                'hours_remaining': time_info['hours_remaining'],
                'minutes_remaining': time_info['minutes_remaining'],
                'usage_percentage': time_info['usage_percentage'],
                'is_active': current_status == LicenseStatus.ACTIVE.value,
                'is_expired': current_status == LicenseStatus.EXPIRED.value,
                'is_expiring_soon': current_status == LicenseStatus.EXPIRING_SOON.value,
                'message': self._get_status_message(current_status, time_info),
                'usage_stats': license_data.get('usage_stats', {})
            }
            
        except Exception as e:
            error_msg = f"Erro ao verificar status da licença: {e}"
            date_logger.error(error_msg)
            return {'exists': False, 'status': 'error', 'message': error_msg}

    def record_access(self, user_email: str, plan_type: str, 
                     session_duration_minutes: int = 0) -> bool:
        """Registra um acesso à licença"""
        try:
            license_id = self._generate_license_id(user_email, plan_type)
            license_data = self._load_license_data(license_id)
            
            if not license_data:
                return False
            
            current_time = self._get_current_datetime()
            
            # Atualizar informações de acesso
            license_data['last_access'] = current_time.isoformat()
            license_data['access_count'] = license_data.get('access_count', 0) + 1
            
            # Atualizar estatísticas de uso
            usage_stats = license_data.get('usage_stats', {})
            usage_stats['total_sessions'] = usage_stats.get('total_sessions', 0) + 1
            usage_stats['total_duration_minutes'] = usage_stats.get('total_duration_minutes', 0) + session_duration_minutes
            
            if usage_stats['total_sessions'] > 0:
                usage_stats['average_session_duration'] = usage_stats['total_duration_minutes'] / usage_stats['total_sessions']
            
            license_data['usage_stats'] = usage_stats
            
            # Registrar padrão de uso
            self._record_usage_pattern(user_email, plan_type, 'access', session_duration_minutes)
            
            # Salvar dados atualizados
            result = self._save_license_data(license_id, license_data)
            
            if result:
                date_logger.info(f"Acesso registrado: {license_id} - Total: {license_data['access_count']}")
            
            return result
            
        except Exception as e:
            date_logger.error(f"Erro ao registrar acesso: {e}")
            return False

    def extend_license(self, user_email: str, plan_type: str, 
                      extension_days: int, reason: str = "Manual extension") -> Tuple[bool, Dict]:
        """Estende o período de uma licença ativa"""
        try:
            license_id = self._generate_license_id(user_email, plan_type)
            license_data = self._load_license_data(license_id)
            
            if not license_data:
                return False, {'error': 'Licença não encontrada'}
            
            if not license_data.get('expires_at'):
                return False, {'error': 'Licença não foi ativada ainda'}
            
            current_expire_time = datetime.fromisoformat(license_data['expires_at'])
            new_expire_time = current_expire_time + timedelta(days=extension_days)
            
            # Registrar extensão
            extension_record = {
                'extended_at': self._get_current_datetime().isoformat(),
                'extension_days': extension_days,
                'reason': reason,
                'previous_expire_date': license_data['expires_at'],
                'new_expire_date': new_expire_time.isoformat()
            }
            
            # Atualizar dados da licença
            license_data['expires_at'] = new_expire_time.isoformat()
            license_data['period_days'] += extension_days
            
            if 'extensions' not in license_data:
                license_data['extensions'] = []
            license_data['extensions'].append(extension_record)
            
            # Reagendar alertas
            self._schedule_expiration_alerts(license_id, new_expire_time)
            
            # Salvar dados
            if self._save_license_data(license_id, license_data):
                date_logger.info(f"Licença estendida: {license_id} por {extension_days} dias")
                return True, {
                    'new_expire_date': new_expire_time.isoformat(),
                    'total_days_added': extension_days,
                    'extension_history': license_data['extensions']
                }
            else:
                return False, {'error': 'Erro ao salvar extensão'}
                
        except Exception as e:
            error_msg = f"Erro ao estender licença: {e}"
            date_logger.error(error_msg)
            return False, {'error': error_msg}

    def suspend_license(self, user_email: str, plan_type: str, 
                       reason: str = "Manual suspension") -> Tuple[bool, Dict]:
        """Suspende temporariamente uma licença"""
        try:
            license_id = self._generate_license_id(user_email, plan_type)
            license_data = self._load_license_data(license_id)
            
            if not license_data:
                return False, {'error': 'Licença não encontrada'}
            
            current_time = self._get_current_datetime()
            
            # Registrar suspensão
            suspension_record = {
                'suspended_at': current_time.isoformat(),
                'reason': reason,
                'previous_status': license_data['status'],
                'expires_at_suspension': license_data.get('expires_at')
            }
            
            # Atualizar status
            license_data['status'] = LicenseStatus.SUSPENDED.value
            
            if 'suspension_history' not in license_data:
                license_data['suspension_history'] = []
            license_data['suspension_history'].append(suspension_record)
            
            if self._save_license_data(license_id, license_data):
                date_logger.info(f"Licença suspensa: {license_id} - Razão: {reason}")
                return True, {'suspended_at': current_time.isoformat(), 'reason': reason}
            else:
                return False, {'error': 'Erro ao suspender licença'}
                
        except Exception as e:
            error_msg = f"Erro ao suspender licença: {e}"
            date_logger.error(error_msg)
            return False, {'error': error_msg}

    def reactivate_license(self, user_email: str, plan_type: str, 
                          add_suspension_time: bool = True) -> Tuple[bool, Dict]:
        """Reativa uma licença suspensa"""
        try:
            license_id = self._generate_license_id(user_email, plan_type)
            license_data = self._load_license_data(license_id)
            
            if not license_data:
                return False, {'error': 'Licença não encontrada'}
            
            if license_data['status'] != LicenseStatus.SUSPENDED.value:
                return False, {'error': 'Licença não está suspensa'}
            
            current_time = self._get_current_datetime()
            
            # Recuperar última suspensão
            if not license_data.get('suspension_history'):
                return False, {'error': 'Histórico de suspensão não encontrado'}
            
            last_suspension = license_data['suspension_history'][-1]
            suspended_at = datetime.fromisoformat(last_suspension['suspended_at'])
            suspension_duration = current_time - suspended_at
            
            # Atualizar suspensão com data de reativação
            last_suspension['reactivated_at'] = current_time.isoformat()
            last_suspension['suspension_duration_days'] = suspension_duration.days
            
            # Restaurar status anterior
            previous_status = last_suspension.get('previous_status', LicenseStatus.ACTIVE.value)
            license_data['status'] = previous_status
            
            # Adicionar tempo de suspensão ao período se solicitado
            if add_suspension_time and license_data.get('expires_at'):
                current_expire_time = datetime.fromisoformat(license_data['expires_at'])
                new_expire_time = current_expire_time + suspension_duration
                license_data['expires_at'] = new_expire_time.isoformat()
                license_data['period_days'] += suspension_duration.days
                
                # Reagendar alertas
                self._schedule_expiration_alerts(license_id, new_expire_time)
            
            if self._save_license_data(license_id, license_data):
                date_logger.info(f"Licença reativada: {license_id}")
                return True, {
                    'reactivated_at': current_time.isoformat(),
                    'suspension_duration_days': suspension_duration.days,
                    'time_added_back': add_suspension_time
                }
            else:
                return False, {'error': 'Erro ao reativar licença'}
                
        except Exception as e:
            error_msg = f"Erro ao reativar licença: {e}"
            date_logger.error(error_msg)
            return False, {'error': error_msg}

    def get_user_licenses(self, user_email: str) -> List[Dict]:
        """Obtém todas as licenças de um usuário"""
        try:
            user_licenses = []
            
            # Carregar todos os dados de licenças
            with open(self.tracker_file, 'r', encoding='utf-8') as f:
                all_licenses = json.load(f)
            
            # Filtrar licenças do usuário
            for license_id, license_data in all_licenses.items():
                if license_data.get('user_email') == user_email:
                    # Verificar status atual
                    status_info = self.check_license_status(user_email, license_data['plan_type'])
                    user_licenses.append(status_info)
            
            # Ordenar por data de criação (mais recente primeiro)
            user_licenses.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return user_licenses
            
        except Exception as e:
            date_logger.error(f"Erro ao obter licenças do usuário {user_email}: {e}")
            return []

    def get_expiring_licenses(self, days_ahead: int = 7) -> List[Dict]:
        """Obtém licenças que expiram nos próximos N dias"""
        try:
            expiring_licenses = []
            current_time = self._get_current_datetime()
            cutoff_time = current_time + timedelta(days=days_ahead)
            
            with open(self.tracker_file, 'r', encoding='utf-8') as f:
                all_licenses = json.load(f)
            
            for license_id, license_data in all_licenses.items():
                if license_data.get('expires_at') and license_data['status'] == LicenseStatus.ACTIVE.value:
                    expire_time = datetime.fromisoformat(license_data['expires_at'])
                    
                    if current_time <= expire_time <= cutoff_time:
                        status_info = self.check_license_status(
                            license_data['user_email'], 
                            license_data['plan_type']
                        )
                        expiring_licenses.append(status_info)
            
            # Ordenar por dias restantes (menos tempo primeiro)
            expiring_licenses.sort(key=lambda x: x.get('days_remaining', 999))
            
            return expiring_licenses
            
        except Exception as e:
            date_logger.error(f"Erro ao obter licenças expirando: {e}")
            return []

    def get_usage_statistics(self, user_email: Optional[str] = None, 
                           plan_type: Optional[str] = None) -> Dict:
        """Obtém estatísticas detalhadas de uso"""
        try:
            stats = {
                'total_licenses': 0,
                'active_licenses': 0,
                'expired_licenses': 0,
                'suspended_licenses': 0,
                'created_licenses': 0,
                'total_access_count': 0,
                'average_session_duration': 0,
                'plan_distribution': {},
                'period_distribution': {},
                'monthly_activations': {},
                'user_activity': {},
                'peak_usage_patterns': {}
            }
            
            # Carregar dados de licenças
            with open(self.tracker_file, 'r', encoding='utf-8') as f:
                all_licenses = json.load(f)
            
            # Carregar padrões de uso
            with open(self.usage_patterns_file, 'r', encoding='utf-8') as f:
                usage_patterns = json.load(f)
            
            total_duration = 0
            total_sessions = 0
            
            for license_id, license_data in all_licenses.items():
                # Filtrar por usuário/plano se especificado
                if user_email and license_data.get('user_email') != user_email:
                    continue
                if plan_type and license_data.get('plan_type') != plan_type:
                    continue
                
                stats['total_licenses'] += 1
                
                # Contar por status
                status = license_data.get('status', 'unknown')
                if status == LicenseStatus.ACTIVE.value:
                    stats['active_licenses'] += 1
                elif status == LicenseStatus.EXPIRED.value:
                    stats['expired_licenses'] += 1
                elif status == LicenseStatus.SUSPENDED.value:
                    stats['suspended_licenses'] += 1
                elif status == LicenseStatus.CREATED.value:
                    stats['created_licenses'] += 1
                
                # Estatísticas de acesso
                access_count = license_data.get('access_count', 0)
                stats['total_access_count'] += access_count
                
                # Distribuição por plano
                plan = license_data.get('plan_type', 'unknown')
                stats['plan_distribution'][plan] = stats['plan_distribution'].get(plan, 0) + 1
                
                # Distribuição por período
                period = license_data.get('period_type', 'unknown')
                stats['period_distribution'][period] = stats['period_distribution'].get(period, 0) + 1
                
                # Ativações mensais
                if license_data.get('activated_at'):
                    activate_date = datetime.fromisoformat(license_data['activated_at'])
                    month_key = activate_date.strftime('%Y-%m')
                    stats['monthly_activations'][month_key] = stats['monthly_activations'].get(month_key, 0) + 1
                
                # Estatísticas de uso
                usage_stats = license_data.get('usage_stats', {})
                session_duration = usage_stats.get('total_duration_minutes', 0)
                session_count = usage_stats.get('total_sessions', 0)
                
                total_duration += session_duration
                total_sessions += session_count
                
                # Atividade por usuário
                user = license_data.get('user_email', 'unknown')
                if user not in stats['user_activity']:
                    stats['user_activity'][user] = {
                        'total_licenses': 0,
                        'total_accesses': 0,
                        'total_duration_minutes': 0,
                        'plans': []
                    }
                
                stats['user_activity'][user]['total_licenses'] += 1
                stats['user_activity'][user]['total_accesses'] += access_count
                stats['user_activity'][user]['total_duration_minutes'] += session_duration
                if plan not in stats['user_activity'][user]['plans']:
                    stats['user_activity'][user]['plans'].append(plan)
            
            # Calcular médias
            if total_sessions > 0:
                stats['average_session_duration'] = round(total_duration / total_sessions, 2)
            
            # Adicionar padrões de uso do arquivo de padrões
            stats['daily_usage_patterns'] = usage_patterns.get('daily_usage', {})
            stats['weekly_patterns'] = usage_patterns.get('weekly_patterns', {})
            stats['monthly_stats'] = usage_patterns.get('monthly_stats', {})
            
            # Timestamp do relatório
            stats['generated_at'] = self._get_current_datetime().isoformat()
            
            return stats
            
        except Exception as e:
            date_logger.error(f"Erro ao gerar estatísticas: {e}")
            return {}

    def cleanup_expired_licenses(self, days_since_expiration: int = 30) -> int:
        """Remove licenças expiradas há mais de N dias"""
        try:
            cleaned_count = 0
            current_time = self._get_current_datetime()
            cutoff_time = current_time - timedelta(days=days_since_expiration)
            
            with open(self.tracker_file, 'r', encoding='utf-8') as f:
                all_licenses = json.load(f)
            
            licenses_to_remove = []
            
            for license_id, license_data in all_licenses.items():
                if license_data.get('status') == LicenseStatus.EXPIRED.value:
                    if license_data.get('expires_at'):
                        expire_time = datetime.fromisoformat(license_data['expires_at'])
                        if expire_time < cutoff_time:
                            licenses_to_remove.append(license_id)
            
            # Remover licenças
            for license_id in licenses_to_remove:
                del all_licenses[license_id]
                cleaned_count += 1
                date_logger.info(f"Licença expirada removida: {license_id}")
            
            # Salvar dados limpos
            if cleaned_count > 0:
                with open(self.tracker_file, 'w', encoding='utf-8') as f:
                    json.dump(all_licenses, f, indent=2, ensure_ascii=False)
            
            date_logger.info(f"Limpeza concluída: {cleaned_count} licenças removidas")
            return cleaned_count
            
        except Exception as e:
            date_logger.error(f"Erro na limpeza de licenças: {e}")
            return 0

    def _start_automatic_monitoring(self):
        """Inicia monitoramento automático de licenças"""
        def monitor_licenses():
            self.monitoring_active = True
            while self.monitoring_active:
                try:
                    # Verificar licenças expirando
                    expiring_licenses = self.get_expiring_licenses(7)
                    
                    for license_info in expiring_licenses:
                        self._process_expiration_alert(license_info)
                    
                    # Atualizar status de licenças expiradas
                    self._update_expired_licenses()
                    
                    # Aguardar próximo ciclo
                    time.sleep(self.monitoring_interval)
                    
                except Exception as e:
                    date_logger.error(f"Erro no monitoramento automático: {e}")
                    time.sleep(60)  # Aguardar 1 minuto em caso de erro
        
        monitor_thread = threading.Thread(target=monitor_licenses, daemon=True)
        monitor_thread.start()
        date_logger.info("Monitoramento automático de licenças iniciado")

    def _generate_license_id(self, user_email: str, plan_type: str) -> str:
        """Gera ID único para uma licença"""
        import hashlib
        unique_string = f"{user_email}_{plan_type}_{datetime.now().timestamp()}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:16]

    def _get_current_datetime(self) -> datetime:
        """Obtém datetime atual no timezone configurado"""
        return datetime.now(self.timezone)

    def _load_license_data(self, license_id: str) -> Optional[Dict]:
        """Carrega dados de uma licença específica"""
        try:
            with open(self.tracker_file, 'r', encoding='utf-8') as f:
                all_licenses = json.load(f)
            
            return all_licenses.get(license_id)
            
        except Exception as e:
            date_logger.error(f"Erro ao carregar licença {license_id}: {e}")
            return None

    def _save_license_data(self, license_id: str, license_data: Dict) -> bool:
        """Salva dados de uma licença"""
        try:
            # Carregar dados existentes
            try:
                with open(self.tracker_file, 'r', encoding='utf-8') as f:
                    all_licenses = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                all_licenses = {}
            
            # Atualizar licença específica
            all_licenses[license_id] = license_data
            
            # Salvar dados
            with open(self.tracker_file, 'w', encoding='utf-8') as f:
                json.dump(all_licenses, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            date_logger.error(f"Erro ao salvar licença {license_id}: {e}")
            return False

    def _calculate_time_info(self, license_data: Dict, current_time: datetime) -> Dict:
        """Calcula informações de tempo de uma licença"""
        time_info = {
            'days_remaining': 0,
            'hours_remaining': 0,
            'minutes_remaining': 0,
            'usage_percentage': 0
        }
        
        if not license_data.get('expires_at'):
            return time_info
        
        try:
            expire_time = datetime.fromisoformat(license_data['expires_at'])
            
            if current_time < expire_time:
                remaining = expire_time - current_time
                time_info['days_remaining'] = remaining.days
                time_info['hours_remaining'] = remaining.seconds // 3600
                time_info['minutes_remaining'] = (remaining.seconds % 3600) // 60
            
            # Calcular porcentagem de uso
            if license_data.get('activated_at'):
                activated_time = datetime.fromisoformat(license_data['activated_at'])
                total_duration = expire_time - activated_time
                used_duration = current_time - activated_time
                
                if total_duration.total_seconds() > 0:
                    time_info['usage_percentage'] = min(100, 
                        (used_duration.total_seconds() / total_duration.total_seconds()) * 100
                    )
            
        except Exception as e:
            date_logger.error(f"Erro ao calcular informações de tempo: {e}")
        
        return time_info

    def _determine_current_status(self, license_data: Dict, current_time: datetime) -> str:
        """Determina o status atual de uma licença"""
        current_status = license_data.get('status', LicenseStatus.CREATED.value)
        
        # Se não foi ativada ainda
        if not license_data.get('activated_at'):
            return LicenseStatus.CREATED.value
        
        # Se foi suspensa ou revogada, manter status
        if current_status in [LicenseStatus.SUSPENDED.value, LicenseStatus.REVOKED.value]:
            return current_status
        
        # Verificar expiração
        if license_data.get('expires_at'):
            expire_time = datetime.fromisoformat(license_data['expires_at'])
            
            if current_time > expire_time:
                return LicenseStatus.EXPIRED.value
            
            # Verificar se está próximo da expiração (7 dias)
            days_remaining = (expire_time - current_time).days
            if days_remaining <= 7:
                return LicenseStatus.EXPIRING_SOON.value
        
        return LicenseStatus.ACTIVE.value

    def _get_status_message(self, status: str, time_info: Dict) -> str:
        """Gera mensagem descritiva para o status"""
        if status == LicenseStatus.CREATED.value:
            return "Licença criada mas ainda não ativada"
        elif status == LicenseStatus.ACTIVE.value:
            days = time_info.get('days_remaining', 0)
            return f"Licença ativa - {days} dias restantes"
        elif status == LicenseStatus.EXPIRING_SOON.value:
            days = time_info.get('days_remaining', 0)
            return f"⚠️ Licença expira em {days} dias"
        elif status == LicenseStatus.EXPIRED.value:
            return "❌ Licença expirada"
        elif status == LicenseStatus.SUSPENDED.value:
            return "⏸️ Licença suspensa temporariamente"
        elif status == LicenseStatus.REVOKED.value:
            return "🚫 Licença revogada"
        else:
            return f"Status: {status}"

    def _schedule_expiration_alerts(self, license_id: str, expire_time: datetime):
        """Agenda alertas de expiração"""
        try:
            # Carregar alertas existentes
            with open(self.alerts_file, 'r', encoding='utf-8') as f:
                alerts_data = json.load(f)
            
            # Remover alertas antigos desta licença
            alerts_data['pending_alerts'] = [
                alert for alert in alerts_data.get('pending_alerts', [])
                if alert.get('license_id') != license_id
            ]
            
            # Agendar novos alertas
            for days_before in self.alert_days:
                alert_time = expire_time - timedelta(days=days_before)
                
                # Só agendar se a data de alerta é no futuro
                if alert_time > self._get_current_datetime():
                    alert = {
                        'license_id': license_id,
                        'alert_time': alert_time.isoformat(),
                        'days_before_expiration': days_before,
                        'created_at': self._get_current_datetime().isoformat()
                    }
                    alerts_data['pending_alerts'].append(alert)
            
            # Salvar alertas
            with open(self.alerts_file, 'w', encoding='utf-8') as f:
                json.dump(alerts_data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            date_logger.error(f"Erro ao agendar alertas: {e}")

    def _process_expiration_alert(self, license_info: Dict):
        """Processa alerta de expiração"""
        try:
            # Verificar se já foi enviado alerta para este usuário/plano
            with open(self.alerts_file, 'r', encoding='utf-8') as f:
                alerts_data = json.load(f)
            
            alert_key = f"{license_info['user_email']}_{license_info['plan_type']}"
            sent_alerts = alerts_data.get('sent_alerts', [])
            
            # Verificar se já foi enviado alerta para os dias restantes atuais
            days_remaining = license_info.get('days_remaining', 0)
            already_sent = any(
                alert.get('alert_key') == alert_key and 
                alert.get('days_remaining') == days_remaining
                for alert in sent_alerts
            )
            
            if not already_sent:
                # Registrar que o alerta foi "enviado" (aqui seria integrado com o email_sender)
                sent_alert = {
                    'alert_key': alert_key,
                    'user_email': license_info['user_email'],
                    'plan_type': license_info['plan_type'],
                    'days_remaining': days_remaining,
                    'sent_at': self._get_current_datetime().isoformat()
                }
                
                sent_alerts.append(sent_alert)
                alerts_data['sent_alerts'] = sent_alerts
                
                # Salvar alertas atualizados
                with open(self.alerts_file, 'w', encoding='utf-8') as f:
                    json.dump(alerts_data, f, indent=2, ensure_ascii=False)
                
                date_logger.info(f"Alerta de expiração processado: {alert_key} - {days_remaining} dias")
            
        except Exception as e:
            date_logger.error(f"Erro ao processar alerta de expiração: {e}")

    def _update_expired_licenses(self):
        """Atualiza status de licenças que expiraram"""
        try:
            current_time = self._get_current_datetime()
            
            with open(self.tracker_file, 'r', encoding='utf-8') as f:
                all_licenses = json.load(f)
            
            updated_count = 0
            
            for license_id, license_data in all_licenses.items():
                if (license_data.get('status') in [LicenseStatus.ACTIVE.value, LicenseStatus.EXPIRING_SOON.value] and
                    license_data.get('expires_at')):
                    
                    expire_time = datetime.fromisoformat(license_data['expires_at'])
                    
                    if current_time > expire_time:
                        license_data['status'] = LicenseStatus.EXPIRED.value
                        updated_count += 1
            
            if updated_count > 0:
                with open(self.tracker_file, 'w', encoding='utf-8') as f:
                    json.dump(all_licenses, f, indent=2, ensure_ascii=False)
                
                date_logger.info(f"{updated_count} licenças marcadas como expiradas")
            
        except Exception as e:
            date_logger.error(f"Erro ao atualizar licenças expiradas: {e}")

    def _record_usage_pattern(self, user_email: str, plan_type: str, 
                             action: str, duration_minutes: int = 0):
        """Registra padrão de uso para análise"""
        try:
            with open(self.usage_patterns_file, 'r', encoding='utf-8') as f:
                patterns = json.load(f)
            
            current_time = self._get_current_datetime()
            today = current_time.strftime('%Y-%m-%d')
            hour = current_time.hour
            weekday = current_time.strftime('%A')
            month = current_time.strftime('%Y-%m')
            
            # Padrões diários
            if 'daily_usage' not in patterns:
                patterns['daily_usage'] = {}
            
            if today not in patterns['daily_usage']:
                patterns['daily_usage'][today] = {'total_sessions': 0, 'total_duration': 0, 'users': []}
            
            patterns['daily_usage'][today]['total_sessions'] += 1
            patterns['daily_usage'][today]['total_duration'] += duration_minutes
            
            if user_email not in patterns['daily_usage'][today]['users']:
                patterns['daily_usage'][today]['users'].append(user_email)
            
            # Padrões semanais
            if 'weekly_patterns' not in patterns:
                patterns['weekly_patterns'] = {}
            
            if weekday not in patterns['weekly_patterns']:
                patterns['weekly_patterns'][weekday] = {'sessions': 0, 'hours': {}}
            
            patterns['weekly_patterns'][weekday]['sessions'] += 1
            
            if str(hour) not in patterns['weekly_patterns'][weekday]['hours']:
                patterns['weekly_patterns'][weekday]['hours'][str(hour)] = 0
            patterns['weekly_patterns'][weekday]['hours'][str(hour)] += 1
            
            # Estatísticas mensais
            if 'monthly_stats' not in patterns:
                patterns['monthly_stats'] = {}
            
            if month not in patterns['monthly_stats']:
                patterns['monthly_stats'][month] = {
                    'total_sessions': 0,
                    'unique_users': [],
                    'plan_usage': {}
                }
            
            patterns['monthly_stats'][month]['total_sessions'] += 1
            
            if user_email not in patterns['monthly_stats'][month]['unique_users']:
                patterns['monthly_stats'][month]['unique_users'].append(user_email)
            
            if plan_type not in patterns['monthly_stats'][month]['plan_usage']:
                patterns['monthly_stats'][month]['plan_usage'][plan_type] = 0
            patterns['monthly_stats'][month]['plan_usage'][plan_type] += 1
            
            # Salvar padrões atualizados
            with open(self.usage_patterns_file, 'w', encoding='utf-8') as f:
                json.dump(patterns, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            date_logger.error(f"Erro ao registrar padrão de uso: {e}")

    def stop_monitoring(self):
        """Para o monitoramento automático"""
        self.monitoring_active = False
        date_logger.info("Monitoramento automático parado")

# Funções utilitárias
def create_quick_license(user_email: str, plan_type: str, period_type: str) -> Tuple[bool, Dict]:
    """Função utilitária para criação rápida de licença"""
    tracker = DateTracker()
    return tracker.create_license_period(user_email, plan_type, period_type)

def check_quick_status(user_email: str, plan_type: str) -> Dict:
    """Função utilitária para verificação rápida de status"""
    tracker = DateTracker()
    return tracker.check_license_status(user_email, plan_type)

def get_system_overview() -> Dict:
    """Obtém visão geral do sistema de licenças"""
    tracker = DateTracker()
    return {
        'statistics': tracker.get_usage_statistics(),
        'expiring_soon': tracker.get_expiring_licenses(7),
        'expiring_month': tracker.get_expiring_licenses(30),
        'system_health': {
            'monitoring_active': tracker.monitoring_active,
            'timezone': str(tracker.timezone),
            'last_check': tracker._get_current_datetime().isoformat()
        }
    }