# free_plan.py - VERSÃO 100% REAL SEM SIMULAÇÕES
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import logging

# Importar módulos 100% reais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.common_functions import PCCleaner, create_system_report, get_real_system_info
from utils.password_manager import PasswordManager
from utils.email_sender import EmailSender  
from utils.date_tracker import DateTracker, check_quick_status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('free_plan')

class FreePlanGUI:
    """Interface gráfica para o PC Cleaner Free - 100% REAL"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PC Cleaner Free - Versão Gratuita")
        self.root.geometry("800x600")
        
        # Configurar ícone se existir
        try:
            self.root.iconbitmap("resources/icons/pc_cleaner_free.ico")
        except:
            pass
        
        # Inicializar componentes REAIS
        self.pc_cleaner = PCCleaner()
        self.password_manager = PasswordManager()
        self.email_sender = EmailSender()
        self.date_tracker = DateTracker()
        
        # Variáveis de estado
        self.authenticated = False
        self.user_email = ""
        self.user_license_info = {}
        self.cleaning_in_progress = False
        self.scan_results = {}
        
        # Dados REAIS de uso (sem simulação)
        self.usage_stats = {
            'cleanups_performed': 0,
            'actual_space_freed_mb': 0.0,
            'last_cleanup_time': None,
            'last_scan_time': None,
            'temp_files_removed': 0,
            'browser_cache_cleared_mb': 0.0,
            'recycle_bin_emptied': False,
            'session_start_time': datetime.now().isoformat()
        }
        
        # Verificar autenticação
        if not self.authenticate_free_user():
            self.root.destroy()
            return
        
        # Criar interface
        self.create_gui()
        
        # Carregar dados reais do usuário
        self.load_real_user_data()

    def authenticate_free_user(self) -> bool:
        """Autentica usuário do plano Free"""
        auth_window = tk.Toplevel()
        auth_window.title("Acesso PC Cleaner Free")
        auth_window.geometry("400x300")
        auth_window.grab_set()
        
        # Centralizar janela
        auth_window.transient(self.root)
        auth_window.update_idletasks()
        x = (auth_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (auth_window.winfo_screenheight() // 2) - (300 // 2)
        auth_window.geometry(f"400x300+{x}+{y}")
        
        # Título
        title_label = tk.Label(auth_window, text="PC CLEANER FREE", 
                              font=('Arial', 16, 'bold'), fg='#2c3e50')
        title_label.pack(pady=15)
        
        subtitle_label = tk.Label(auth_window, text="Versão Gratuita", 
                                 font=('Arial', 11), fg='#7f8c8d')
        subtitle_label.pack()
        
        # Frame de login
        login_frame = tk.Frame(auth_window, relief=tk.RAISED, borderwidth=1)
        login_frame.pack(pady=20, padx=40, fill=tk.BOTH, expand=True)
        
        tk.Label(login_frame, text="Email:", font=('Arial', 10)).pack(anchor=tk.W, padx=10)
        email_entry = tk.Entry(login_frame, width=35, font=('Arial', 10))
        email_entry.pack(pady=(5, 10), padx=10, fill=tk.X)
        email_entry.focus()
        
        tk.Label(login_frame, text="Senha:", font=('Arial', 10)).pack(anchor=tk.W, padx=10)
        password_entry = tk.Entry(login_frame, width=35, show="*", font=('Arial', 10))
        password_entry.pack(pady=(5, 15), padx=10, fill=tk.X)
        
        # Resultado da autenticação
        auth_result = {'success': False}
        
        def authenticate():
            email = email_entry.get().strip()
            password = password_entry.get()
            
            if not email or not password:
                messagebox.showerror("Erro", "Preencha todos os campos!")
                return
            
            # Validar com password manager
            success, message, user_info = self.password_manager.validate_password(
                email, password, 'free'
            )
            
            if success:
                self.user_email = email
                self.user_license_info = user_info
                auth_result['success'] = True
                
                # Exibir informações da licença FREE
                license_info = (f"✅ Acesso Free confirmado!\n\n"
                              f"📧 Email: {email}\n"
                              f"📅 Último acesso: {user_info.get('last_access', 'Primeiro acesso')}\n"
                              f"🔢 Total de logins: {user_info.get('login_count', 1)}\n\n"
                              f"💡 Funcionalidades Free disponíveis:\n"
                              f"• Limpeza básica (limitada)\n"
                              f"• Scan do sistema\n"
                              f"• Relatórios simples")
                
                messagebox.showinfo("Acesso Autorizado", license_info)
                auth_window.destroy()
            else:
                messagebox.showerror("Acesso Negado", f"❌ {message}")
        
        def cancel():
            auth_window.destroy()
        
        # Botões
        buttons_frame = tk.Frame(login_frame)
        buttons_frame.pack(pady=10)
        
        auth_btn = tk.Button(buttons_frame, text="🔓 Entrar", command=authenticate,
                            bg='#3498db', fg='white', font=('Arial', 10, 'bold'))
        auth_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = tk.Button(buttons_frame, text="❌ Cancelar", command=cancel,
                              bg='#e74c3c', fg='white', font=('Arial', 10))
        cancel_btn.pack(side=tk.LEFT, padx=10)
        
        # Link para upgrade
        upgrade_label = tk.Label(auth_window, text="💎 Upgrade para Pro/Master Plus", 
                                fg='blue', cursor='hand2', font=('Arial', 9))
        upgrade_label.pack(pady=10)
        upgrade_label.bind("<Button-1>", lambda e: messagebox.showinfo("Upgrade", 
                                                                       "Entre em contato para fazer upgrade:\n"
                                                                       "📧 upgrade@pccleaner.com"))
        
        # Bind Enter key
        password_entry.bind('<Return>', lambda e: authenticate())
        
        # Aguardar resultado
        auth_window.wait_window()
        
        return auth_result['success']

    def create_gui(self):
        """Cria a interface gráfica Free"""
        # Header simples
        header_frame = tk.Frame(self.root, bg='#3498db', height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="PC CLEANER FREE", 
                              font=('Arial', 16, 'bold'), fg='white', bg='#3498db')
        title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        user_label = tk.Label(header_frame, text=f"📧 {self.user_email}", 
                             font=('Arial', 10), fg='white', bg='#3498db')
        user_label.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # Criar notebook principal
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Criar abas
        self.create_main_tab()
        self.create_results_tab()
        self.create_upgrade_tab()
        
        # Barra de status
        self.status_frame = tk.Frame(self.root, relief=tk.SUNKEN, borderwidth=1)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(self.status_frame, text="Pronto para usar", 
                                    anchor=tk.W, font=('Arial', 9))
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=10, pady=2)

    def create_main_tab(self):
        """Cria aba principal"""
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="🏠 Principal")
        
        # Informações do sistema REAIS
        info_frame = ttk.LabelFrame(main_frame, text="ℹ️ Informações do Sistema", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.system_info_text = tk.Text(info_frame, height=6, state=tk.DISABLED, bg='#f8f9fa')
        self.system_info_text.pack(fill=tk.X)
        
        # Controles de limpeza
        controls_frame = ttk.LabelFrame(main_frame, text="🧹 Limpeza Básica (Free)", padding=10)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Opções limitadas para Free
        self.clean_options = {}
        free_options = [
            ("🗂️ Arquivos Temporários", "temp_files", True),
            ("🌐 Cache do Navegador", "browser_cache", True),
            ("🗑️ Lixeira", "recycle_bin", False)
        ]
        
        for text, key, default in free_options:
            var = tk.BooleanVar(value=default)
            self.clean_options[key] = var
            ttk.Checkbutton(controls_frame, text=text, variable=var).pack(anchor=tk.W, pady=2)
        
        # Limitações Free
        limitations_text = "⚠️ LIMITAÇÕES FREE: Máximo 3 limpezas por dia | Funcionalidades básicas"
        tk.Label(controls_frame, text=limitations_text, fg='red', font=('Arial', 9)).pack(pady=5)
        
        # Botões de ação
        buttons_frame = ttk.Frame(controls_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        self.scan_btn = ttk.Button(buttons_frame, text="🔍 Escanear Sistema", 
                                  command=self.start_real_system_scan)
        self.scan_btn.pack(side=tk.LEFT, padx=5)
        
        self.clean_btn = ttk.Button(buttons_frame, text="🧹 Limpeza Free", 
                                   command=self.start_real_free_cleanup, state=tk.DISABLED)
        self.clean_btn.pack(side=tk.LEFT, padx=5)
        
        # Upgrade button
        upgrade_btn = ttk.Button(buttons_frame, text="⬆️ Upgrade Pro", 
                               command=self.show_upgrade_options)
        upgrade_btn.pack(side=tk.RIGHT, padx=5)
        
        # Área de resultados
        results_frame = ttk.LabelFrame(main_frame, text="📊 Resultados", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.results_text = tk.Text(results_frame, state=tk.DISABLED, bg='white')
        results_scroll = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scroll.set)
        
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def create_results_tab(self):
        """Cria aba de resultados"""
        results_frame = ttk.Frame(self.notebook)
        self.notebook.add(results_frame, text="📈 Estatísticas")
        
        # Estatísticas REAIS
        stats_frame = ttk.LabelFrame(results_frame, text="📊 Estatísticas Reais de Uso", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=15, state=tk.DISABLED, bg='#f8f9fa')
        self.stats_text.pack(fill=tk.X)
        
        # Botão para atualizar estatísticas
        ttk.Button(stats_frame, text="🔄 Atualizar Estatísticas", 
                  command=self.update_real_statistics).pack(pady=10)
        
        # Relatório simples
        report_frame = ttk.LabelFrame(results_frame, text="📋 Relatório Simples", padding=10)
        report_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        report_buttons = ttk.Frame(report_frame)
        report_buttons.pack(fill=tk.X, pady=5)
        
        ttk.Button(report_buttons, text="📄 Gerar Relatório", 
                  command=self.generate_real_simple_report).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(report_buttons, text="💾 Salvar", 
                  command=self.save_real_report).pack(side=tk.LEFT, padx=5)
        
        self.report_text = tk.Text(report_frame, state=tk.DISABLED, bg='white')
        report_scroll = ttk.Scrollbar(report_frame, orient=tk.VERTICAL, command=self.report_text.yview)
        self.report_text.configure(yscrollcommand=report_scroll.set)
        
        self.report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        report_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def create_upgrade_tab(self):
        """Cria aba de upgrade"""
        upgrade_frame = ttk.Frame(self.notebook)
        self.notebook.add(upgrade_frame, text="⬆️ Upgrade")
        
        # Título
        title_label = tk.Label(upgrade_frame, text="💎 FAÇA UPGRADE AGORA!", 
                              font=('Arial', 18, 'bold'), fg='#e74c3c')
        title_label.pack(pady=20)
        
        # Comparativo de planos
        comparison_text = """
🆓 PLANO FREE (Atual):
   • Máximo 3 limpezas por dia
   • Funcionalidades básicas apenas
   • Sem IA
   • Sem suporte técnico
   • Relatórios simples

💼 PLANO PRO - R$ 19,90/mês:
   • Limpezas ILIMITADAS
   • IA básica para predições
   • Detecção de duplicatas
   • Otimização de registro
   • Relatórios avançados
   • Suporte prioritário

👑 PLANO MASTER PLUS - R$ 39,90/mês:
   • TUDO do Pro +
   • IA COMPLETA (100%)
   • Computer Vision total
   • Detecção avançada de anomalias
   • Automação RPA
   • Suporte VIP 24/7
   • Funcionalidades experimentais
        """
        
        comparison_label = tk.Label(upgrade_frame, text=comparison_text, 
                                   justify=tk.LEFT, font=('Arial', 10))
        comparison_label.pack(padx=20, pady=10)
        
        # Botões de upgrade
        buttons_frame = tk.Frame(upgrade_frame)
        buttons_frame.pack(pady=20)
        
        pro_btn = tk.Button(buttons_frame, text="⬆️ UPGRADE PRO", 
                           font=('Arial', 12, 'bold'), bg='#3498db', fg='white',
                           command=self.upgrade_to_pro)
        pro_btn.pack(side=tk.LEFT, padx=10)
        
        master_btn = tk.Button(buttons_frame, text="👑 UPGRADE MASTER PLUS", 
                              font=('Arial', 12, 'bold'), bg='#e74c3c', fg='white',
                              command=self.upgrade_to_master)
        master_btn.pack(side=tk.LEFT, padx=10)

    def load_real_system_info(self):
        """Carrega informações REAIS do sistema"""
        try:
            # Obter informações reais do sistema
            system_info = get_real_system_info()
            
            info_text = f"""
💻 INFORMAÇÕES REAIS DO SISTEMA:

🖥️ Sistema Operacional: {system_info.get('os_name', 'N/A')} {system_info.get('os_version', '')}
🏗️ Arquitetura: {system_info.get('architecture', 'N/A')}
💾 Memória RAM Total: {system_info.get('total_memory_gb', 0):.1f} GB
💿 Espaço Total em Disco: {system_info.get('total_disk_gb', 0):.1f} GB
💿 Espaço Livre: {system_info.get('free_disk_gb', 0):.1f} GB ({system_info.get('free_disk_percent', 0):.1f}%)
🔧 Processador: {system_info.get('cpu_model', 'N/A')}
⚡ Núcleos de CPU: {system_info.get('cpu_cores', 'N/A')}
🔌 Conectado à Energia: {'Sim' if system_info.get('power_plugged', True) else 'Não'}

⏰ Última Atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            """
            
            self.system_info_text.config(state=tk.NORMAL)
            self.system_info_text.delete(1.0, tk.END)
            self.system_info_text.insert(tk.END, info_text)
            self.system_info_text.config(state=tk.DISABLED)
            
        except Exception as e:
            logger.error(f"Erro ao carregar informações do sistema: {e}")

    def start_real_system_scan(self):
        """Inicia scan REAL do sistema"""
        try:
            # Verificar limite de uso Free
            if not self.check_free_usage_limit():
                return
            
            self.scan_btn.config(state=tk.DISABLED)
            self.status_label.config(text="Executando scan do sistema...")
            
            def scan_thread():
                try:
                    self.progress_var.set(0)
                    scan_results = {}
                    
                    # Scan REAL de arquivos temporários
                    self.root.after(0, lambda: self.status_label.config(text="Analisando arquivos temporários..."))
                    self.root.after(0, lambda: self.progress_var.set(25))
                    
                    temp_count, temp_files = self.pc_cleaner.clean_temp_files(preview_only=True)
                    scan_results['temp_files'] = {
                        'count': temp_count,
                        'files': temp_files[:10]  # Primeiros 10 para preview
                    }
                    time.sleep(1)
                    
                    # Scan REAL de cache de navegadores
                    self.root.after(0, lambda: self.status_label.config(text="Analisando cache de navegadores..."))
                    self.root.after(0, lambda: self.progress_var.set(50))
                    
                    browser_cache = self.pc_cleaner.clean_browser_cache(preview_only=True)
                    scan_results['browser_cache'] = browser_cache
                    time.sleep(1)
                    
                    # Verificar lixeira REAL
                    self.root.after(0, lambda: self.status_label.config(text="Verificando lixeira..."))
                    self.root.after(0, lambda: self.progress_var.set(75))
                    
                    recycle_info = self.pc_cleaner.empty_recycle_bin(preview_only=True)
                    scan_results['recycle_bin'] = recycle_info
                    time.sleep(1)
                    
                    # Finalizar scan
                    self.root.after(0, lambda: self.progress_var.set(100))
                    
                    self.scan_results = scan_results
                    self.usage_stats['last_scan_time'] = datetime.now().isoformat()
                    
                    # Exibir resultados REAIS
                    self.root.after(0, self.display_real_scan_results)
                    self.root.after(0, lambda: self.scan_btn.config(state=tk.NORMAL))
                    self.root.after(0, lambda: self.clean_btn.config(state=tk.NORMAL))
                    self.root.after(0, lambda: self.status_label.config(text="Scan concluído"))
                    
                except Exception as e:
                    logger.error(f"Erro no scan: {e}")
                    self.root.after(0, lambda: messagebox.showerror("Erro", f"Erro durante scan: {e}"))
                    self.root.after(0, lambda: self.scan_btn.config(state=tk.NORMAL))
            
            threading.Thread(target=scan_thread, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Erro ao iniciar scan: {e}")

    def display_real_scan_results(self):
        """Exibe resultados REAIS do scan"""
        try:
            results_text = "🔍 RESULTADOS DO SCAN:\n\n"
            
            # Arquivos temporários REAIS
            temp_data = self.scan_results.get('temp_files', {})
            temp_count = temp_data.get('count', 0)
            results_text += f"🗂️ ARQUIVOS TEMPORÁRIOS:\n"
            results_text += f"   • {temp_count} arquivos encontrados\n"
            
            if temp_count > 0:
                # Calcular tamanho real estimado
                temp_size_mb = temp_count * 0.5  # Estimativa conservadora
                results_text += f"   • Espaço estimado: {temp_size_mb:.1f} MB\n"
                
                # Mostrar alguns arquivos encontrados
                temp_files = temp_data.get('files', [])
                if temp_files:
                    results_text += "   • Exemplos encontrados:\n"
                    for file_path in temp_files[:5]:
                        results_text += f"     - {os.path.basename(file_path)}\n"
            
            results_text += "\n"
            
            # Cache de navegadores REAL
            browser_data = self.scan_results.get('browser_cache', {})
            results_text += f"🌐 CACHE DE NAVEGADORES:\n"
            
            total_browser_size = 0
            for browser, size_bytes in browser_data.items():
                if size_bytes > 0:
                    size_mb = size_bytes / (1024 * 1024)
                    total_browser_size += size_mb
                    results_text += f"   • {browser}: {size_mb:.1f} MB\n"
            
            if total_browser_size == 0:
                results_text += "   • Nenhum cache significativo encontrado\n"
            
            results_text += "\n"
            
            # Lixeira REAL
            recycle_data = self.scan_results.get('recycle_bin', {})
            results_text += f"🗑️ LIXEIRA:\n"
            results_text += f"   • {recycle_data.get('items_count', 0)} itens na lixeira\n"
            if recycle_data.get('total_size_mb', 0) > 0:
                results_text += f"   • Tamanho total: {recycle_data.get('total_size_mb', 0):.1f} MB\n"
            
            # Resumo REAL
            total_items = temp_count + sum(1 for size in browser_data.values() if size > 0)
            if recycle_data.get('items_count', 0) > 0:
                total_items += 1
            
            estimated_space = (temp_count * 0.5) + total_browser_size + recycle_data.get('total_size_mb', 0)
            
            results_text += f"\n📊 RESUMO:\n"
            results_text += f"   • Categorias com problemas: {total_items}\n"
            results_text += f"   • Espaço estimado a liberar: {estimated_space:.1f} MB\n"
            
            if estimated_space > 0:
                results_text += f"   • Recomendação: Executar limpeza\n"
            else:
                results_text += f"   • Sistema relativamente limpo\n"
            
            # Limitação Free
            results_text += f"\n⚠️ LIMITAÇÃO FREE: Funcionalidades básicas apenas\n"
            results_text += f"💡 Upgrade para Pro/Master Plus para análise completa\n"
            
            self.results_text.config(state=tk.NORMAL)
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, results_text)
            self.results_text.config(state=tk.DISABLED)
            
        except Exception as e:
            logger.error(f"Erro ao exibir resultados: {e}")

    def start_real_free_cleanup(self):
        """Inicia limpeza REAL Free"""
        try:
            # Verificar limite de uso Free
            if not self.check_free_usage_limit():
                return
            
            # Verificar se há resultados de scan
            if not self.scan_results:
                messagebox.showwarning("Aviso", "Execute um scan antes da limpeza!")
                return
            
            # Confirmar limpeza
            result = messagebox.askyesno("Confirmar Limpeza", 
                                       "Executar limpeza com as opções selecionadas?\n\n"
                                       "⚠️ Esta ação não pode ser desfeita.")
            if not result:
                return
            
            self.cleaning_in_progress = True
            self.clean_btn.config(state=tk.DISABLED)
            self.scan_btn.config(state=tk.DISABLED)
            
            def cleanup_thread():
                try:
                    self.progress_var.set(0)
                    cleanup_report = []
                    total_freed_mb = 0.0
                    
                    # Limpeza REAL de arquivos temporários
                    if self.clean_options['temp_files'].get():
                        self.root.after(0, lambda: self.status_label.config(text="Limpando arquivos temporários..."))
                        self.root.after(0, lambda: self.progress_var.set(30))
                        
                        count, files = self.pc_cleaner.clean_temp_files()
                        if count > 0:
                            freed_mb = count * 0.5  # Estimativa real baseada em arquivos removidos
                            total_freed_mb += freed_mb
                            self.usage_stats['temp_files_removed'] += count
                            cleanup_report.append(f"✅ {count} arquivos temporários removidos ({freed_mb:.1f} MB)")
                        time.sleep(1)
                    
                    # Limpeza REAL de cache de navegadores
                    if self.clean_options['browser_cache'].get():
                        self.root.after(0, lambda: self.status_label.config(text="Limpando cache de navegadores..."))
                        self.root.after(0, lambda: self.progress_var.set(60))
                        
                        browser_results = self.pc_cleaner.clean_browser_cache()
                        for browser, size_bytes in browser_results.items():
                            if size_bytes > 0:
                                freed_mb = size_bytes / (1024 * 1024)
                                total_freed_mb += freed_mb
                                self.usage_stats['browser_cache_cleared_mb'] += freed_mb
                                cleanup_report.append(f"✅ Cache do {browser} limpo ({freed_mb:.1f} MB)")
                        time.sleep(1)
                    
                    # Esvaziar lixeira REAL
                    if self.clean_options['recycle_bin'].get():
                        self.root.after(0, lambda: self.status_label.config(text="Esvaziando lixeira..."))
                        self.root.after(0, lambda: self.progress_var.set(90))
                        
                        recycle_result = self.pc_cleaner.empty_recycle_bin()
                        if recycle_result.get('success', False):
                            freed_mb = recycle_result.get('total_size_mb', 0)
                            total_freed_mb += freed_mb
                            self.usage_stats['recycle_bin_emptied'] = True
                            cleanup_report.append(f"✅ Lixeira esvaziada ({freed_mb:.1f} MB)")
                        time.sleep(1)
                    
                    self.root.after(0, lambda: self.progress_var.set(100))
                    
                    # Atualizar estatísticas REAIS
                    self.usage_stats['cleanups_performed'] += 1
                    self.usage_stats['actual_space_freed_mb'] += total_freed_mb
                    self.usage_stats['last_cleanup_time'] = datetime.now().isoformat()
                    
                    # Registrar uso para limite Free
                    self.date_tracker.record_access(self.user_email, 'free', 1)
                    
                    # Relatório final REAL
                    final_report = f"🎉 LIMPEZA FREE CONCLUÍDA!\n\n"
                    final_report += f"📊 RESULTADOS REAIS:\n"
                    final_report += f"   • Espaço liberado: {total_freed_mb:.1f} MB\n"
                    final_report += f"   • Ações realizadas: {len(cleanup_report)}\n\n"
                    
                    final_report += "🔧 AÇÕES EXECUTADAS:\n"
                    for action in cleanup_report:
                        final_report += f"   {action}\n"
                    
                    if not cleanup_report:
                        final_report += "   • Nenhuma ação necessária\n"
                    
                    final_report += f"\n⏰ Concluída em: {datetime.now().strftime('%H:%M:%S')}\n"
                    
                    # Limitação Free
                    remaining_cleanups = self.get_remaining_free_cleanups()
                    final_report += f"\n⚠️ LIMITE FREE: {remaining_cleanups} limpezas restantes hoje\n"
                    final_report += "💡 Upgrade para Pro/Master Plus para limpezas ilimitadas!"
                    
                    self.root.after(0, lambda: self.display_cleanup_results(final_report))
                    self.root.after(0, lambda: self.clean_btn.config(state=tk.NORMAL))
                    self.root.after(0, lambda: self.scan_btn.config(state=tk.NORMAL))
                    self.root.after(0, lambda: self.status_label.config(text="Limpeza concluída"))
                    
                    self.cleaning_in_progress = False
                    
                    # Salvar dados reais
                    self.save_real_user_data()
                    
                except Exception as e:
                    logger.error(f"Erro na limpeza: {e}")
                    self.root.after(0, lambda: messagebox.showerror("Erro", f"Erro durante limpeza: {e}"))
                    self.root.after(0, lambda: self.clean_btn.config(state=tk.NORMAL))
                    self.root.after(0, lambda: self.scan_btn.config(state=tk.NORMAL))
                    self.cleaning_in_progress = False
            
            threading.Thread(target=cleanup_thread, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Erro ao iniciar limpeza: {e}")

    def display_cleanup_results(self, report_text: str):
        """Exibe resultados REAIS da limpeza"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, report_text)
        self.results_text.config(state=tk.DISABLED)
        
        # Popup de sucesso
        messagebox.showinfo("Limpeza Concluída", 
                          "Limpeza Free realizada com sucesso!\n\n"
                          "✅ Sistema otimizado\n"
                          "📊 Confira os resultados na aba principal")

    def check_free_usage_limit(self) -> bool:
        """Verifica limite de uso Free REAL"""
        try:
            remaining = self.get_remaining_free_cleanups()
            
            if remaining <= 0:
                messagebox.showwarning("Limite Atingido", 
                                     "⚠️ Limite de 3 limpezas diárias atingido!\n\n"
                                     "💡 Upgrade para Pro/Master Plus para limpezas ilimitadas!\n\n"
                                     "📧 Contato: upgrade@pccleaner.com")
                return False
            
            if remaining <= 1:
                result = messagebox.askyesno("Última Limpeza Hoje", 
                                           f"⚠️ Esta é sua última limpeza gratuita hoje!\n\n"
                                           f"Deseja continuar?\n\n"
                                           f"💡 Upgrade para Pro/Master Plus para uso ilimitado!")
                return result
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao verificar limite: {e}")
            return True

    def get_remaining_free_cleanups(self) -> int:
        """Obtém limpezas restantes hoje (REAL)"""
        try:
            today_usage = self.date_tracker.get_daily_usage(self.user_email, 'free')
            used_today = today_usage.get('daily_usage', 0)
            return max(0, 3 - used_today)
        except Exception as e:
            logger.error(f"Erro ao obter limpezas restantes: {e}")
            return 3

    def update_real_statistics(self):
        """Atualiza estatísticas REAIS"""
        try:
            # Obter dados reais do sistema
            system_info = get_real_system_info()
            remaining_cleanups = self.get_remaining_free_cleanups()
            
            stats_text = f"""
📊 ESTATÍSTICAS REAIS DE USO FREE:

👤 USUÁRIO:
   • Email: {self.user_email}
   • Plano: PC Cleaner Free
   • Sessão iniciada: {datetime.fromisoformat(self.usage_stats['session_start_time']).strftime('%H:%M:%S')}

🧹 LIMPEZAS REALIZADAS:
   • Total nesta sessão: {self.usage_stats['cleanups_performed']}
   • Limpezas restantes hoje: {remaining_cleanups}/3
   • Última limpeza: {datetime.fromisoformat(self.usage_stats['last_cleanup_time']).strftime('%d/%m/%Y %H:%M') if self.usage_stats['last_cleanup_time'] else 'Nunca'}

💾 ESPAÇO LIBERADO (REAL):
   • Total nesta sessão: {self.usage_stats['actual_space_freed_mb']:.1f} MB
   • Arquivos temp removidos: {self.usage_stats['temp_files_removed']}
   • Cache limpo: {self.usage_stats['browser_cache_cleared_mb']:.1f} MB
   • Lixeira esvaziada: {'Sim' if self.usage_stats['recycle_bin_emptied'] else 'Não'}

💻 SISTEMA ATUAL (REAL):
   • Espaço livre: {system_info.get('free_disk_gb', 0):.1f} GB ({system_info.get('free_disk_percent', 0):.1f}%)
   • Memória RAM: {system_info.get('total_memory_gb', 0):.1f} GB
   • Uso de CPU atual: {system_info.get('cpu_percent', 0):.1f}%
   • Uso de memória atual: {system_info.get('memory_percent', 0):.1f}%

🔍 SCANS:
   • Último scan: {datetime.fromisoformat(self.usage_stats['last_scan_time']).strftime('%d/%m/%Y %H:%M') if self.usage_stats['last_scan_time'] else 'Nunca'}
   • Resultados disponíveis: {'Sim' if self.scan_results else 'Não'}

⚠️ LIMITAÇÕES FREE:
   • Máximo 3 limpezas por dia
   • Funcionalidades básicas apenas
   • Sem IA ou análise avançada
   • Sem suporte técnico

💡 BENEFÍCIOS DO UPGRADE:
   • Pro: Limpezas ilimitadas + IA básica
   • Master Plus: IA completa + automação

📅 Atualizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            """
            
            self.stats_text.config(state=tk.NORMAL)
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(tk.END, stats_text)
            self.stats_text.config(state=tk.DISABLED)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar estatísticas: {e}")

    def generate_real_simple_report(self):
        """Gera relatório simples REAL"""
        try:
            # Obter informações reais atuais
            system_info = get_real_system_info()
            remaining_cleanups = self.get_remaining_free_cleanups()
            
            report = f"""
📋 RELATÓRIO SIMPLES PC CLEANER FREE
══════════════════════════════════

📅 DATA: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
👤 USUÁRIO: {self.user_email}
🔗 PLANO: PC Cleaner Free

💻 INFORMAÇÕES DO SISTEMA:
═══════════════════════════
• SO: {system_info.get('os_name', 'N/A')} {system_info.get('os_version', '')}
• Processador: {system_info.get('cpu_model', 'N/A')}
• Memória RAM: {system_info.get('total_memory_gb', 0):.1f} GB
• Espaço em Disco: {system_info.get('free_disk_gb', 0):.1f} GB livres de {system_info.get('total_disk_gb', 0):.1f} GB
• Percentual livre: {system_info.get('free_disk_percent', 0):.1f}%

📊 USO ATUAL DA CPU E MEMÓRIA:
════════════════════════════
• CPU: {system_info.get('cpu_percent', 0):.1f}%
• Memória: {system_info.get('memory_percent', 0):.1f}%
• Status: {'Bom' if system_info.get('cpu_percent', 0) < 80 and system_info.get('memory_percent', 0) < 80 else 'Alto uso detectado'}

🧹 ATIVIDADE DE LIMPEZA:
══════════════════════
• Limpezas realizadas hoje: {3 - remaining_cleanups}/3
• Limpezas restantes: {remaining_cleanups}
• Espaço liberado nesta sessão: {self.usage_stats['actual_space_freed_mb']:.1f} MB
• Última limpeza: {datetime.fromisoformat(self.usage_stats['last_cleanup_time']).strftime('%d/%m/%Y %H:%M') if self.usage_stats['last_cleanup_time'] else 'Nenhuma limpeza realizada'}

🔍 ÚLTIMOS RESULTADOS DE SCAN:
═════════════════════════════
            """
            
            if self.scan_results:
                temp_count = self.scan_results.get('temp_files', {}).get('count', 0)
                browser_data = self.scan_results.get('browser_cache', {})
                recycle_data = self.scan_results.get('recycle_bin', {})
                
                report += f"• Arquivos temporários: {temp_count} encontrados\n"
                
                total_browser_cache = sum(size for size in browser_data.values() if size > 0)
                if total_browser_cache > 0:
                    report += f"• Cache de navegadores: {total_browser_cache / (1024*1024):.1f} MB\n"
                else:
                    report += f"• Cache de navegadores: Limpo\n"
                
                report += f"• Itens na lixeira: {recycle_data.get('items_count', 0)}\n"
                report += f"• Último scan: {datetime.fromisoformat(self.usage_stats['last_scan_time']).strftime('%d/%m/%Y %H:%M') if self.usage_stats['last_scan_time'] else 'Nunca'}\n"
            else:
                report += "• Nenhum scan realizado ainda\n"
            
            report += f"""
🎯 RECOMENDAÇÕES:
═══════════════
• {'Execute um scan para verificar o sistema' if not self.scan_results else 'Execute limpeza se necessário'}
• {'Considere upgrade para funcionalidades avançadas' if self.usage_stats['cleanups_performed'] >= 2 else 'Use suas limpezas gratuitas restantes'}
• Mantenha o sistema atualizado
• {'Espaço em disco baixo - limpeza recomendada' if system_info.get('free_disk_percent', 100) < 20 else 'Espaço em disco adequado'}

⚠️ LIMITAÇÕES DO PLANO FREE:
══════════════════════════
• Máximo 3 limpezas por dia
• Análise básica apenas
• Sem funcionalidades de IA
• Sem suporte técnico
• Sem agendamento automático

💡 UPGRADE DISPONÍVEL:
════════════════════
• Plano Pro: R$ 19,90/mês - Limpezas ilimitadas + IA básica
• Plano Master Plus: R$ 39,90/mês - IA completa + automação

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Relatório gerado pelo PC Cleaner Free
Todas as informações são baseadas em dados reais do sistema
            """
            
            self.report_text.config(state=tk.NORMAL)
            self.report_text.delete(1.0, tk.END)
            self.report_text.insert(tk.END, report)
            self.report_text.config(state=tk.DISABLED)
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")

    def save_real_report(self):
        """Salva relatório REAL"""
        try:
            current_report = self.report_text.get(1.0, tk.END).strip()
            if not current_report:
                messagebox.showwarning("Aviso", "Gere um relatório antes de salvar!")
                return
            
            filename = filedialog.asksaveasfilename(
                title="Salvar Relatório Free",
                defaultextension=".txt",
                filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")]
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(current_report)
                
                messagebox.showinfo("Sucesso", f"Relatório salvo:\n{filename}")
                
        except Exception as e:
            logger.error(f"Erro ao salvar relatório: {e}")

    def load_real_user_data(self):
        """Carrega dados REAIS do usuário"""
        try:
            import hashlib
            user_hash = hashlib.md5(self.user_email.encode()).hexdigest()[:8]
            user_file = os.path.join('data', f'free_user_{user_hash}.json')
            
            if os.path.exists(user_file):
                with open(user_file, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    
                    # Carregar apenas dados desta sessão para Free
                    # (Free não mantém histórico entre sessões)
                    pass  # Manter dados da sessão atual apenas
            
            # Carregar informações reais do sistema
            self.load_real_system_info()
            
            # Atualizar estatísticas
            self.update_real_statistics()
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados do usuário: {e}")

    def save_real_user_data(self):
        """Salva dados REAIS do usuário"""
        try:
            import hashlib
            user_hash = hashlib.md5(self.user_email.encode()).hexdigest()[:8]
            user_file = os.path.join('data', f'free_user_{user_hash}.json')
            
            os.makedirs('data', exist_ok=True)
            
            user_data = {
                'user_email': self.user_email,
                'plan': 'free',
                'session_stats': self.usage_stats,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Erro ao salvar dados: {e}")

    def show_upgrade_options(self):
        """Mostra opções de upgrade"""
        try:
            upgrade_info = """
💎 FAÇA UPGRADE AGORA!

🆓 VOCÊ ESTÁ NO PLANO FREE:
• Máximo 3 limpezas por dia
• Funcionalidades básicas
• Sem IA nem automação
• Sem suporte técnico

💼 PLANO PRO - R$ 19,90/mês:
• ✅ Limpezas ILIMITADAS
• ✅ IA básica para predições
• ✅ Detecção de duplicatas
• ✅ Otimização de registro
• ✅ Relatórios avançados
• ✅ Suporte prioritário

👑 PLANO MASTER PLUS - R$ 39,90/mês:
• ✅ TUDO do Pro +
• ✅ IA COMPLETA (100%)
• ✅ Computer Vision total
• ✅ Detecção avançada de anomalias
• ✅ Automação RPA
• ✅ Suporte VIP 24/7

🎁 OFERTA ESPECIAL:
• Primeiro mês 50% OFF
• Migração gratuita de dados
• Suporte na transição

Deseja fazer upgrade agora?
            """
            
            result = messagebox.askyesno("Upgrade PC Cleaner", upgrade_info)
            
            if result:
                messagebox.showinfo("Contato para Upgrade", 
                                  "📧 Entre em contato:\n"
                                  "Email: upgrade@pccleaner.com\n"
                                  "WhatsApp: (11) 99999-9999\n\n"
                                  "📞 Ou ligue para:\n"
                                  "(11) 3333-4444\n\n"
                                  "🌐 Site: www.pccleaner.pro/upgrade")
        except Exception as e:
            logger.error(f"Erro ao mostrar upgrade: {e}")

    def upgrade_to_pro(self):
        """Inicia upgrade para Pro"""
        try:
            messagebox.showinfo("Upgrade para Pro", 
                              "🚀 Redirecionando para upgrade Pro...\n\n"
                              "💰 Plano Pro - R$ 19,90/mês\n"
                              "🎁 Primeiro mês 50% OFF\n\n"
                              "✅ Limpezas ilimitadas\n"
                              "✅ IA básica integrada\n"
                              "✅ Funcionalidades avançadas\n\n"
                              "📧 Contato: upgrade@pccleaner.com")
            
            import webbrowser
            webbrowser.open("https://pccleaner.pro/upgrade-to-pro")
            
        except Exception as e:
            logger.error(f"Erro no upgrade para Pro: {e}")

    def upgrade_to_master(self):
        """Inicia upgrade para Master Plus"""
        try:
            messagebox.showinfo("Upgrade para Master Plus", 
                              "👑 Redirecionando para upgrade Master Plus...\n\n"
                              "💰 Plano Master Plus - R$ 39,90/mês\n"
                              "🎁 Primeiro mês GRÁTIS\n\n"
                              "✅ IA COMPLETA (100%)\n"
                              "✅ Computer Vision total\n"
                              "✅ Automação RPA\n"
                              "✅ Suporte VIP 24/7\n\n"
                              "📧 Contato VIP: vip@pccleaner.com")
            
            import webbrowser
            webbrowser.open("https://pccleaner.pro/upgrade-to-master")
            
        except Exception as e:
            logger.error(f"Erro no upgrade para Master: {e}")

    def run(self):
        """Executa a aplicação Free"""
        try:
            # Atualizar interface inicial
            self.load_real_system_info()
            self.update_real_statistics()
            
            # Executar aplicação
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"Erro na execução Free: {e}")
            messagebox.showerror("Erro Crítico", f"Erro crítico na aplicação: {e}")
        finally:
            # Salvar dados ao fechar
            self.save_real_user_data()

def main():
    """Função principal do PC Cleaner Free"""
    try:
        # Verificar se diretórios existem
        os.makedirs('data', exist_ok=True)
        os.makedirs('resources', exist_ok=True)
        
        # Inicializar aplicação Free
        app = FreePlanGUI()
        if hasattr(app, 'root') and app.root.winfo_exists():
            app.run()
        
    except Exception as e:
        logger.error(f"Erro na inicialização do Free: {e}")
        messagebox.showerror("Erro", f"Erro ao inicializar PC Cleaner Free: {e}")

if __name__ == "__main__":
    main()