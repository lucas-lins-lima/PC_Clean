# utils/email_sender.py
import smtplib
import ssl
import json
import os
import time
import threading
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Tuple
import logging
import queue
import re
from pathlib import Path
import html

# Configuração de logging específica para emails
email_logger = logging.getLogger('email_sender')
email_handler = logging.FileHandler('email_sender.log')
email_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
email_handler.setFormatter(email_formatter)
email_logger.addHandler(email_handler)
email_logger.setLevel(logging.INFO)

class EmailSender:
    """Sistema completo de envio de emails para o PC Cleaner"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.config_file = os.path.join(data_dir, "email_config.json")
        self.queue_file = os.path.join(data_dir, "email_queue.json")
        self.templates_dir = os.path.join("resources", "email_templates")
        
        # Configurações SMTP para diferentes provedores
        self.smtp_configs = {
            'gmail': {
                'server': 'smtp.gmail.com',
                'port': 587,
                'use_tls': True,
                'requires_app_password': True
            },
            'outlook': {
                'server': 'smtp-mail.outlook.com',
                'port': 587,
                'use_tls': True,
                'requires_app_password': False
            },
            'yahoo': {
                'server': 'smtp.mail.yahoo.com',
                'port': 587,
                'use_tls': True,
                'requires_app_password': True
            },
            'hotmail': {
                'server': 'smtp-mail.outlook.com',
                'port': 587,
                'use_tls': True,
                'requires_app_password': False
            }
        }
        
        # Configurações padrão
        self.default_config = {
            'sender_name': 'PC Cleaner Pro',
            'sender_email': '',
            'sender_password': '',
            'provider': 'gmail',
            'max_retries': 3,
            'retry_delay': 5,
            'rate_limit': 10,  # emails por minuto
            'queue_enabled': True,
            'auto_queue_processing': True
        }
        
        # Sistema de fila de emails
        self.email_queue = queue.Queue()
        self.queue_processor_running = False
        self.sent_count = 0
        self.last_reset_time = datetime.now()
        
        # Inicializar sistema
        self._initialize_system()
        self._load_configuration()
        self._start_queue_processor()

    def _initialize_system(self):
        """Inicializa diretórios e arquivos necessários"""
        # Criar diretórios
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Criar arquivo de configuração se não existir
        if not os.path.exists(self.config_file):
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.default_config, f, indent=2)
        
        # Criar templates de email padrão
        self._create_default_templates()

    def _load_configuration(self):
        """Carrega configurações do arquivo"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # Mesclar com configurações padrão para garantir completude
            for key, value in self.default_config.items():
                if key not in self.config:
                    self.config[key] = value
            
            email_logger.info("Configurações de email carregadas com sucesso")
            
        except Exception as e:
            email_logger.error(f"Erro ao carregar configurações: {e}")
            self.config = self.default_config.copy()

    def _create_default_templates(self):
        """Cria templates HTML padrão para emails"""
        templates = {
            'password_pro': {
                'subject': '🔐 Sua Senha do PC Cleaner Pro',
                'template': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PC Cleaner Pro - Senha de Acesso</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: white; padding: 30px; border: 1px solid #ddd; }
        .password-box { background: #f8f9fa; border: 2px solid #007bff; padding: 20px; margin: 20px 0; text-align: center; border-radius: 8px; }
        .password { font-size: 24px; font-weight: bold; color: #007bff; font-family: 'Courier New', monospace; letter-spacing: 2px; }
        .info-box { background: #e7f3ff; border-left: 4px solid #007bff; padding: 15px; margin: 15px 0; }
        .warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; }
        .footer { background: #6c757d; color: white; padding: 20px; text-align: center; font-size: 12px; border-radius: 0 0 10px 10px; }
        .button { background: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 PC Cleaner Pro</h1>
            <h2>Sua Senha de Acesso</h2>
        </div>
        
        <div class="content">
            <p>Olá <strong>{user_name}</strong>,</p>
            
            <p>Parabéns! Sua senha para o <strong>PC Cleaner Pro</strong> foi gerada com sucesso.</p>
            
            <div class="password-box">
                <p><strong>Sua Senha Exclusiva:</strong></p>
                <div class="password">{password}</div>
            </div>
            
            <div class="info-box">
                <h3>📋 Informações do Seu Plano:</h3>
                <ul>
                    <li><strong>Plano:</strong> PC Cleaner Pro</li>
                    <li><strong>Período:</strong> {period_name} ({period_days} dias)</li>
                    <li><strong>Válido até:</strong> {expires_at}</li>
                    <li><strong>Gerada em:</strong> {created_at}</li>
                </ul>
            </div>
            
            <div class="warning">
                <h3>⚠️ Instruções Importantes:</h3>
                <ul>
                    <li>Guarde esta senha em local seguro</li>
                    <li>Não compartilhe com outras pessoas</li>
                    <li>A contagem de dias inicia no <strong>primeiro uso</strong></li>
                    <li>Você receberá notificações próximo ao vencimento</li>
                </ul>
            </div>
            
            <h3>🎯 Funcionalidades do PC Cleaner Pro:</h3>
            <ul>
                <li>✅ Limpeza avançada de sistema</li>
                <li>✅ Análise preditiva com IA</li>
                <li>✅ Otimização inteligente</li>
                <li>✅ Chatbot de suporte</li>
                <li>✅ Relatórios detalhados</li>
                <li>✅ Detecção avançada de malware</li>
            </ul>
            
            <p>Precisa de ajuda? Nossa equipe está sempre disponível!</p>
        </div>
        
        <div class="footer">
            <p>© 2025 PC Cleaner Pro. Todos os direitos reservados.</p>
            <p>Este email foi enviado automaticamente. Não responda este email.</p>
        </div>
    </div>
</body>
</html>
                '''
            },
            
            'password_master_plus': {
                'subject': '👑 Sua Senha do PC Cleaner Master Plus',
                'template': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PC Cleaner Master Plus - Senha de Acesso VIP</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #ff6b6b 0%, #feca57 50%, #48dbfb 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: white; padding: 30px; border: 1px solid #ddd; }
        .password-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; margin: 20px 0; text-align: center; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
        .password { font-size: 28px; font-weight: bold; font-family: 'Courier New', monospace; letter-spacing: 3px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .vip-badge { background: #ffd700; color: #333; padding: 10px 20px; border-radius: 20px; display: inline-block; font-weight: bold; margin: 10px 0; }
        .info-box { background: #f8f9fa; border: 2px solid #ffd700; padding: 20px; margin: 15px 0; border-radius: 8px; }
        .feature-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0; }
        .feature-item { background: #e7f3ff; padding: 10px; border-radius: 5px; text-align: center; }
        .footer { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; font-size: 12px; border-radius: 0 0 10px 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>👑 PC Cleaner Master Plus</h1>
            <div class="vip-badge">🌟 PLANO VIP 🌟</div>
            <h2>Sua Senha de Acesso Exclusiva</h2>
        </div>
        
        <div class="content">
            <p>Olá <strong>{user_name}</strong>,</p>
            
            <p>🎉 <strong>Bem-vindo ao PC Cleaner Master Plus!</strong> 🎉</p>
            <p>Você agora tem acesso às mais avançadas tecnologias de limpeza e otimização com Inteligência Artificial!</p>
            
            <div class="password-box">
                <p><strong>🔐 Sua Senha VIP:</strong></p>
                <div class="password">{password}</div>
            </div>
            
            <div class="info-box">
                <h3>📋 Informações do Seu Plano VIP:</h3>
                <ul>
                    <li><strong>Plano:</strong> PC Cleaner Master Plus 👑</li>
                    <li><strong>Período:</strong> {period_name} ({period_days} dias)</li>
                    <li><strong>Válido até:</strong> {expires_at}</li>
                    <li><strong>Gerada em:</strong> {created_at}</li>
                    <li><strong>Status:</strong> <span style="color: #28a745; font-weight: bold;">PREMIUM ATIVO</span></li>
                </ul>
            </div>
            
            <h3>🚀 Funcionalidades Exclusivas Master Plus:</h3>
            <div class="feature-grid">
                <div class="feature-item">🧠 IA Avançada</div>
                <div class="feature-item">👁️ Computer Vision</div>
                <div class="feature-item">🗣️ Assistente de Voz</div>
                <div class="feature-item">🤖 Automação RPA</div>
                <div class="feature-item">🔍 Deep Learning</div>
                <div class="feature-item">📊 Analytics Completo</div>
                <div class="feature-item">🛡️ Proteção Máxima</div>
                <div class="feature-item">⚡ Performance Max</div>
            </div>
            
            <div style="background: #d4edda; border: 2px solid #28a745; padding: 20px; margin: 20px 0; border-radius: 8px;">
                <h3>💎 Diferenciais Exclusivos:</h3>
                <ul>
                    <li>🎯 Análise preditiva de performance</li>
                    <li>🖼️ Detecção visual de problemas</li>
                    <li>💬 Chatbot com NLP avançado</li>
                    <li>🔧 Automação completa de tarefas</li>
                    <li>📈 Relatórios com IA</li>
                    <li>🌐 Suporte prioritário 24/7</li>
                </ul>
            </div>
            
            <p><strong>Sua experiência premium começa agora!</strong> 🌟</p>
        </div>
        
        <div class="footer">
            <p>© 2025 PC Cleaner Master Plus. Experiência Premium Garantida.</p>
            <p>Suporte VIP: support@pccleaner.pro | WhatsApp: (11) 99999-9999</p>
        </div>
    </div>
</body>
</html>
                '''
            },
            
            'expiration_warning': {
                'subject': '⏰ Sua senha do PC Cleaner expira em breve',
                'template': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PC Cleaner - Aviso de Expiração</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #ff6b6b; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: white; padding: 30px; border: 1px solid #ddd; }
        .warning-box { background: #fff3cd; border: 2px solid #ffc107; padding: 20px; margin: 20px 0; border-radius: 8px; text-align: center; }
        .days-remaining { font-size: 36px; font-weight: bold; color: #dc3545; }
        .action-button { background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 15px 0; font-weight: bold; }
        .footer { background: #6c757d; color: white; padding: 20px; text-align: center; font-size: 12px; border-radius: 0 0 10px 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⏰ Aviso Importante</h1>
            <h2>Sua senha expira em breve</h2>
        </div>
        
        <div class="content">
            <p>Olá <strong>{user_name}</strong>,</p>
            
            <div class="warning-box">
                <h3>🚨 Atenção: Sua senha do PC Cleaner {plan_type} expira em:</h3>
                <div class="days-remaining">{days_remaining} dias</div>
            </div>
            
            <p>Para continuar aproveitando todos os benefícios do PC Cleaner {plan_type}, renove sua senha antes do vencimento.</p>
            
            <div style="background: #e7f3ff; padding: 15px; margin: 15px 0; border-radius: 5px;">
                <h3>📋 Informações da sua conta:</h3>
                <ul>
                    <li><strong>Plano:</strong> {plan_type}</li>
                    <li><strong>Data de expiração:</strong> {expires_at}</li>
                    <li><strong>Total de logins:</strong> {login_count}</li>
                </ul>
            </div>
            
            <p>Entre em contato conosco para renovar sua senha e continuar com acesso total!</p>
            
            <div style="text-align: center;">
                <a href="mailto:support@pccleaner.pro" class="action-button">💬 Renovar Agora</a>
            </div>
        </div>
        
        <div class="footer">
            <p>© 2025 PC Cleaner. Não perca seus benefícios premium!</p>
        </div>
    </div>
</body>
</html>
                '''
            }
        }
        
        # Salvar templates
        for template_name, template_data in templates.items():
            template_path = os.path.join(self.templates_dir, f"{template_name}.html")
            subject_path = os.path.join(self.templates_dir, f"{template_name}_subject.txt")
            
            if not os.path.exists(template_path):
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(template_data['template'])
                
                with open(subject_path, 'w', encoding='utf-8') as f:
                    f.write(template_data['subject'])

    def configure_email(self, sender_email: str, sender_password: str, 
                       sender_name: str = None, provider: str = 'gmail') -> bool:
        """Configura credenciais de email"""
        try:
            # Validar email
            if not self._validate_email(sender_email):
                email_logger.error(f"Email inválido: {sender_email}")
                return False
            
            # Testar conexão SMTP
            if not self._test_smtp_connection(sender_email, sender_password, provider):
                email_logger.error("Falha na conexão SMTP")
                return False
            
            # Salvar configurações
            self.config.update({
                'sender_email': sender_email,
                'sender_password': sender_password,
                'sender_name': sender_name or 'PC Cleaner Pro',
                'provider': provider
            })
            
            # Salvar no arquivo
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            
            email_logger.info(f"Configurações de email salvas para: {sender_email}")
            return True
            
        except Exception as e:
            email_logger.error(f"Erro ao configurar email: {e}")
            return False

    def send_password_email(self, recipient_email: str, password: str, 
                           plan_type: str, period: str, period_days: int,
                           user_name: str = None) -> Tuple[bool, str]:
        """Envia email com senha para o usuário"""
        try:
            if not self._validate_email(recipient_email):
                return False, "Email do destinatário inválido"
            
            if not self._check_rate_limit():
                return False, "Limite de envio de emails atingido. Tente novamente em alguns minutos."
            
            # Preparar dados do template
            template_data = {
                'user_name': user_name or recipient_email.split('@')[0],
                'password': password,
                'plan_type': plan_type.title(),
                'period_name': period.title(),
                'period_days': period_days,
                'created_at': datetime.now().strftime('%d/%m/%Y às %H:%M:%S'),
                'expires_at': (datetime.now() + timedelta(days=period_days)).strftime('%d/%m/%Y')
            }
            
            # Determinar template
            template_name = f"password_{plan_type.lower().replace(' ', '_')}"
            
            # Enviar email
            success, message = self._send_templated_email(
                recipient_email, 
                template_name, 
                template_data
            )
            
            if success:
                email_logger.info(f"Email de senha enviado para: {recipient_email} - Plano: {plan_type}")
                self._record_sent_email(recipient_email, 'password', plan_type)
            
            return success, message
            
        except Exception as e:
            error_msg = f"Erro ao enviar email de senha: {e}"
            email_logger.error(error_msg)
            return False, error_msg

    def send_expiration_warning(self, recipient_email: str, plan_type: str, 
                               days_remaining: int, expires_at: str,
                               login_count: int, user_name: str = None) -> Tuple[bool, str]:
        """Envia aviso de expiração de senha"""
        try:
            template_data = {
                'user_name': user_name or recipient_email.split('@')[0],
                'plan_type': plan_type.title(),
                'days_remaining': days_remaining,
                'expires_at': expires_at,
                'login_count': login_count
            }
            
            success, message = self._send_templated_email(
                recipient_email,
                'expiration_warning',
                template_data
            )
            
            if success:
                email_logger.info(f"Aviso de expiração enviado para: {recipient_email}")
                self._record_sent_email(recipient_email, 'expiration_warning', plan_type)
            
            return success, message
            
        except Exception as e:
            error_msg = f"Erro ao enviar aviso de expiração: {e}"
            email_logger.error(error_msg)
            return False, error_msg

    def send_custom_email(self, recipient_email: str, subject: str, 
                         html_content: str, plain_content: str = None,
                         attachments: List[str] = None) -> Tuple[bool, str]:
        """Envia email personalizado"""
        try:
            if not self._validate_email(recipient_email):
                return False, "Email do destinatário inválido"
            
            if not self._check_rate_limit():
                return False, "Limite de envio atingido"
            
            success, message = self._send_email(
                recipient_email,
                subject,
                html_content,
                plain_content,
                attachments
            )
            
            if success:
                self._record_sent_email(recipient_email, 'custom', 'none')
            
            return success, message
            
        except Exception as e:
            error_msg = f"Erro ao enviar email personalizado: {e}"
            email_logger.error(error_msg)
            return False, error_msg

    def queue_email(self, email_data: Dict) -> bool:
        """Adiciona email à fila de envio"""
        try:
            email_data['queued_at'] = datetime.now().isoformat()
            email_data['attempts'] = 0
            
            self.email_queue.put(email_data)
            
            # Salvar fila em arquivo
            self._save_queue_to_file()
            
            email_logger.info(f"Email adicionado à fila: {email_data.get('recipient_email', 'unknown')}")
            return True
            
        except Exception as e:
            email_logger.error(f"Erro ao adicionar email à fila: {e}")
            return False

    def get_email_statistics(self) -> Dict:
        """Obtém estatísticas de envio de emails"""
        try:
            stats_file = os.path.join(self.data_dir, "email_stats.json")
            
            if os.path.exists(stats_file):
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
            else:
                stats = {
                    'total_sent': 0,
                    'total_failed': 0,
                    'sent_by_type': {},
                    'sent_by_plan': {},
                    'daily_stats': {},
                    'last_updated': datetime.now().isoformat()
                }
            
            # Adicionar estatísticas da sessão atual
            stats['session_sent'] = self.sent_count
            stats['queue_size'] = self.email_queue.qsize()
            stats['rate_limit_remaining'] = self.config['rate_limit'] - self.sent_count
            
            return stats
            
        except Exception as e:
            email_logger.error(f"Erro ao obter estatísticas: {e}")
            return {}

    def _send_templated_email(self, recipient_email: str, template_name: str, 
                             template_data: Dict) -> Tuple[bool, str]:
        """Envia email usando template HTML"""
        try:
            # Carregar template HTML
            template_path = os.path.join(self.templates_dir, f"{template_name}.html")
            subject_path = os.path.join(self.templates_dir, f"{template_name}_subject.txt")
            
            if not os.path.exists(template_path):
                return False, f"Template não encontrado: {template_name}"
            
            with open(template_path, 'r', encoding='utf-8') as f:
                html_template = f.read()
            
            # Carregar assunto
            if os.path.exists(subject_path):
                with open(subject_path, 'r', encoding='utf-8') as f:
                    subject = f.read().strip()
            else:
                subject = f"PC Cleaner - {template_name.replace('_', ' ').title()}"
            
            # Substituir variáveis no template
            html_content = html_template.format(**template_data)
            subject = subject.format(**template_data)
            
            # Gerar versão texto plano
            plain_content = self._html_to_plain(html_content)
            
            return self._send_email(recipient_email, subject, html_content, plain_content)
            
        except KeyError as e:
            return False, f"Variável não encontrada no template: {e}"
        except Exception as e:
            return False, f"Erro ao processar template: {e}"

    def _send_email(self, recipient_email: str, subject: str, 
                   html_content: str, plain_content: str = None,
                   attachments: List[str] = None) -> Tuple[bool, str]:
        """Envia email usando SMTP"""
        max_retries = self.config.get('max_retries', 3)
        retry_delay = self.config.get('retry_delay', 5)
        
        for attempt in range(max_retries):
            try:
                # Configurar servidor SMTP
                smtp_config = self.smtp_configs.get(self.config['provider'])
                if not smtp_config:
                    return False, f"Provedor não suportado: {self.config['provider']}"
                
                # Criar conexão SMTP
                if smtp_config['use_tls']:
                    server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
                    server.starttls(context=ssl.create_default_context())
                else:
                    server = smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port'])
                
                # Fazer login
                server.login(self.config['sender_email'], self.config['sender_password'])
                
                # Criar mensagem
                message = MIMEMultipart('related')
                message['From'] = f"{self.config['sender_name']} <{self.config['sender_email']}>"
                message['To'] = recipient_email
                message['Subject'] = subject
                
                # Criar parte alternativa para HTML e texto
                msg_alternative = MIMEMultipart('alternative')
                message.attach(msg_alternative)
                
                # Adicionar versão texto plano
                if plain_content:
                    part_text = MIMEText(plain_content, 'plain', 'utf-8')
                    msg_alternative.attach(part_text)
                
                # Adicionar versão HTML
                part_html = MIMEText(html_content, 'html', 'utf-8')
                msg_alternative.attach(part_html)
                
                # Adicionar anexos se houver
                if attachments:
                    for file_path in attachments:
                        if os.path.exists(file_path):
                            self._attach_file(message, file_path)
                
                # Enviar email
                server.send_message(message)
                server.quit()
                
                # Incrementar contador
                self.sent_count += 1
                
                email_logger.info(f"Email enviado com sucesso para: {recipient_email}")
                return True, "Email enviado com sucesso"
                
            except smtplib.SMTPAuthenticationError:
                return False, "Erro de autenticação. Verifique email e senha."
            except smtplib.SMTPRecipientsRefused:
                return False, "Email do destinatário foi recusado pelo servidor."
            except smtplib.SMTPException as e:
                if attempt < max_retries - 1:
                    email_logger.warning(f"Tentativa {attempt + 1} falhou, tentando novamente em {retry_delay}s: {e}")
                    time.sleep(retry_delay)
                    continue
                else:
                    return False, f"Erro SMTP após {max_retries} tentativas: {e}"
            except Exception as e:
                if attempt < max_retries - 1:
                    email_logger.warning(f"Tentativa {attempt + 1} falhou: {e}")
                    time.sleep(retry_delay)
                    continue
                else:
                    return False, f"Erro inesperado: {e}"
        
        return False, "Todas as tentativas de envio falharam"

    def _start_queue_processor(self):
        """Inicia processador de fila de emails em thread separada"""
        if self.config.get('auto_queue_processing', True) and not self.queue_processor_running:
            def process_queue():
                self.queue_processor_running = True
                while self.queue_processor_running:
                    try:
                        if not self.email_queue.empty():
                            email_data = self.email_queue.get(timeout=1)
                            self._process_queued_email(email_data)
                        else:
                            time.sleep(5)  # Aguardar novos emails
                    except queue.Empty:
                        continue
                    except Exception as e:
                        email_logger.error(f"Erro no processador de fila: {e}")
            
            queue_thread = threading.Thread(target=process_queue, daemon=True)
            queue_thread.start()
            email_logger.info("Processador de fila de emails iniciado")

    def _process_queued_email(self, email_data: Dict):
        """Processa email da fila"""
        try:
            email_type = email_data.get('type', 'custom')
            
            if email_type == 'password':
                success, message = self.send_password_email(
                    email_data['recipient_email'],
                    email_data['password'],
                    email_data['plan_type'],
                    email_data['period'],
                    email_data['period_days'],
                    email_data.get('user_name')
                )
            elif email_type == 'expiration_warning':
                success, message = self.send_expiration_warning(
                    email_data['recipient_email'],
                    email_data['plan_type'],
                    email_data['days_remaining'],
                    email_data['expires_at'],
                    email_data['login_count'],
                    email_data.get('user_name')
                )
            else:
                success, message = self.send_custom_email(
                    email_data['recipient_email'],
                    email_data['subject'],
                    email_data['html_content'],
                    email_data.get('plain_content'),
                    email_data.get('attachments')
                )
            
            if success:
                email_logger.info(f"Email da fila processado com sucesso: {email_data['recipient_email']}")
            else:
                email_data['attempts'] = email_data.get('attempts', 0) + 1
                if email_data['attempts'] < self.config.get('max_retries', 3):
                    # Recolocar na fila para nova tentativa
                    self.email_queue.put(email_data)
                    email_logger.warning(f"Email falhou, tentativa {email_data['attempts']}: {message}")
                else:
                    email_logger.error(f"Email falhou definitivamente após {email_data['attempts']} tentativas: {message}")
            
        except Exception as e:
            email_logger.error(f"Erro ao processar email da fila: {e}")

    def _validate_email(self, email: str) -> bool:
        """Valida formato do email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _test_smtp_connection(self, email: str, password: str, provider: str) -> bool:
        """Testa conexão SMTP"""
        try:
            smtp_config = self.smtp_configs.get(provider)
            if not smtp_config:
                return False
            
            if smtp_config['use_tls']:
                server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port'])
            
            server.login(email, password)
            server.quit()
            return True
            
        except Exception as e:
            email_logger.error(f"Erro ao testar conexão SMTP: {e}")
            return False

    def _check_rate_limit(self) -> bool:
        """Verifica limite de envio de emails por minuto"""
        now = datetime.now()
        
        # Reset contador se passou mais de 1 minuto
        if (now - self.last_reset_time).seconds >= 60:
            self.sent_count = 0
            self.last_reset_time = now
        
        return self.sent_count < self.config.get('rate_limit', 10)

    def _record_sent_email(self, recipient: str, email_type: str, plan_type: str):
        """Registra estatísticas de email enviado"""
        try:
            stats_file = os.path.join(self.data_dir, "email_stats.json")
            
            # Carregar estatísticas existentes
            if os.path.exists(stats_file):
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
            else:
                stats = {
                    'total_sent': 0,
                    'total_failed': 0,
                    'sent_by_type': {},
                    'sent_by_plan': {},
                    'daily_stats': {}
                }
            
            # Atualizar estatísticas
            stats['total_sent'] += 1
            stats['sent_by_type'][email_type] = stats['sent_by_type'].get(email_type, 0) + 1
            stats['sent_by_plan'][plan_type] = stats['sent_by_plan'].get(plan_type, 0) + 1
            
            # Estatísticas diárias
            today = datetime.now().strftime('%Y-%m-%d')
            if today not in stats['daily_stats']:
                stats['daily_stats'][today] = 0
            stats['daily_stats'][today] += 1
            
            stats['last_updated'] = datetime.now().isoformat()
            
            # Salvar estatísticas
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            email_logger.error(f"Erro ao registrar estatística de email: {e}")

    def _html_to_plain(self, html_content: str) -> str:
        """Converte HTML para texto plano"""
        try:
            # Remoção básica de tags HTML
            import re
            
            # Remover scripts e styles
            html_content = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<style.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            
            # Substituir quebras de linha
            html_content = re.sub(r'<br\s*/?>', '\n', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'</p>', '\n\n', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'</div>', '\n', html_content, flags=re.IGNORECASE)
            
            # Remover todas as tags HTML
            plain_text = re.sub(r'<[^>]+>', '', html_content)
            
            # Decodificar entidades HTML
            plain_text = html.unescape(plain_text)
            
            # Limpar espaços extras
            plain_text = re.sub(r'\n\s*\n', '\n\n', plain_text)
            plain_text = re.sub(r'[ \t]+', ' ', plain_text)
            
            return plain_text.strip()
            
        except Exception:
            return "Conteúdo do email (versão HTML não pôde ser convertida)"

    def _attach_file(self, message: MIMEMultipart, file_path: str):
        """Anexa arquivo ao email"""
        try:
            with open(file_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(file_path)}'
            )
            
            message.attach(part)
            
        except Exception as e:
            email_logger.error(f"Erro ao anexar arquivo {file_path}: {e}")

    def _save_queue_to_file(self):
        """Salva fila de emails em arquivo para persistência"""
        try:
            queue_items = []
            temp_queue = queue.Queue()
            
            # Extrair items da fila
            while not self.email_queue.empty():
                item = self.email_queue.get()
                queue_items.append(item)
                temp_queue.put(item)
            
            # Restaurar fila
            self.email_queue = temp_queue
            
            # Salvar em arquivo
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(queue_items, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            email_logger.error(f"Erro ao salvar fila: {e}")

    def stop_queue_processor(self):
        """Para o processador de fila"""
        self.queue_processor_running = False
        email_logger.info("Processador de fila parado")

# Função utilitária para envio rápido
def send_quick_password_email(recipient_email: str, password: str, plan_type: str, 
                             period: str, sender_config: Dict) -> Tuple[bool, str]:
    """Função utilitária para envio rápido de email com senha"""
    try:
        email_sender = EmailSender()
        
        # Configurar credenciais rapidamente
        if not email_sender.configure_email(
            sender_config['email'],
            sender_config['password'],
            sender_config.get('name', 'PC Cleaner'),
            sender_config.get('provider', 'gmail')
        ):
            return False, "Erro na configuração do email"
        
        # Mapear período para dias
        period_days_map = {'trimestre': 90, 'semestre': 180, 'ano': 365}
        period_days = period_days_map.get(period, 90)
        
        return email_sender.send_password_email(
            recipient_email, password, plan_type, period, period_days
        )
        
    except Exception as e:
        return False, f"Erro no envio rápido: {e}"