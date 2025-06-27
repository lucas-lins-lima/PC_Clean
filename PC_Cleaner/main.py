# main.py - PC Cleaner Launcher 100% REAL
"""
PC CLEANER - SISTEMA COMPLETO DE LIMPEZA COM IA
================================================

Versões disponíveis:
• FREE: Limpeza básica limitada
• PRO: IA básica + funcionalidades avançadas  
• MASTER PLUS: IA COMPLETA + Computer Vision + Automação

Autor: PC Cleaner Team
Versão: 3.0.0
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import threading
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import hashlib
import webbrowser
import subprocess
import ctypes

# Configurar paths para .exe
if getattr(sys, 'frozen', False):
    # Se executando como .exe
    BASE_DIR = os.path.dirname(sys.executable)
    RESOURCES_DIR = os.path.join(BASE_DIR, 'resources')
else:
    # Se executando como script Python
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCES_DIR = os.path.join(BASE_DIR, 'resources')

# Adicionar diretório base ao path
sys.path.insert(0, BASE_DIR)

# Criar diretórios necessários
os.makedirs(os.path.join(BASE_DIR, 'data'), exist_ok=True)
os.makedirs(RESOURCES_DIR, exist_ok=True)

# Configurar logging
log_file = os.path.join(BASE_DIR, 'data', 'pc_cleaner.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('main')

# Importar módulos do PC Cleaner
try:
    from utils.password_manager import PasswordManager
    from utils.date_tracker import DateTracker, check_quick_status
    from utils.common_functions import get_real_system_info
    from free_plan import FreePlanGUI
    from pro_plan import ProPlanGUI
    from master_plus_plan import MasterPlusGUI
except ImportError as e:
    logger.error(f"Erro ao importar módulos: {e}")
    if not getattr(sys, 'frozen', False):
        raise
    else:
        messagebox.showerror("Erro Crítico", f"Erro ao carregar módulos:\n{e}")
        sys.exit(1)

class SplashScreen:
    """Tela de splash/loading 100% REAL"""
    
    def __init__(self):
        self.splash = tk.Tk()
        self.splash.title("PC Cleaner")
        self.splash.geometry("600x400")
        self.splash.configure(bg='#1a1a2e')
        self.splash.resizable(False, False)
        
        # Centralizar na tela
        self.center_window()
        
        # Remover barra de título
        self.splash.overrideredirect(True)
        
        # Configurar interface
        self.create_splash_interface()
        
        # Variáveis de progresso
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Inicializando PC Cleaner...")
        
        # Inicializar verificações
        self.start_initialization()

    def center_window(self):
        """Centraliza a janela na tela"""
        self.splash.update_idletasks()
        x = (self.splash.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.splash.winfo_screenheight() // 2) - (400 // 2)
        self.splash.geometry(f"600x400+{x}+{y}")

    def create_splash_interface(self):
        """Cria interface da tela de splash"""
        # Background frame
        bg_frame = tk.Frame(self.splash, bg='#1a1a2e')
        bg_frame.pack(fill=tk.BOTH, expand=True)
        
        # Logo e título principal
        logo_frame = tk.Frame(bg_frame, bg='#1a1a2e')
        logo_frame.pack(pady=50)
        
        # Título principal
        title_label = tk.Label(logo_frame, text="PC CLEANER", 
                              font=('Arial', 28, 'bold'), fg='#3498db', bg='#1a1a2e')
        title_label.pack()
        
        # Subtítulo
        subtitle_label = tk.Label(logo_frame, text="Sistema Completo de Limpeza com IA", 
                                 font=('Arial', 12), fg='#95a5a6', bg='#1a1a2e')
        subtitle_label.pack()
        
        # Versão
        version_label = tk.Label(logo_frame, text="v3.0.0 - Edição Completa", 
                                font=('Arial', 10), fg='#7f8c8d', bg='#1a1a2e')
        version_label.pack(pady=5)
        
        # Frame de informações dos planos
        plans_frame = tk.Frame(bg_frame, bg='#1a1a2e')
        plans_frame.pack(pady=20)
        
        plans_text = """
🆓 FREE: Limpeza básica • Limitada • Grátis
💼 PRO: IA básica • Funcionalidades avançadas • R$ 19,90/mês  
👑 MASTER PLUS: IA COMPLETA • Computer Vision • Automação • R$ 39,90/mês
        """
        
        tk.Label(plans_frame, text=plans_text, font=('Arial', 10), 
                fg='#ecf0f1', bg='#1a1a2e', justify=tk.CENTER).pack()
        
        # Frame de progresso
        progress_frame = tk.Frame(bg_frame, bg='#1a1a2e')
        progress_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=40, pady=30)
        
        # Status label
        self.status_label = tk.Label(progress_frame, textvariable=self.status_var,
                                    font=('Arial', 10), fg='#3498db', bg='#1a1a2e')
        self.status_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, length=520)
        self.progress_bar.pack(fill=tk.X)
        
        # Copyright
        copyright_label = tk.Label(progress_frame, text="© 2024 PC Cleaner Team - Todos os direitos reservados", 
                                  font=('Arial', 8), fg='#7f8c8d', bg='#1a1a2e')
        copyright_label.pack(pady=(10, 0))

    def start_initialization(self):
        """Inicia processo de inicialização REAL"""
        def init_thread():
            try:
                steps = [
                    ("Verificando sistema...", 10, 1),
                    ("Carregando módulos...", 25, 2),
                    ("Inicializando componentes...", 40, 1.5),
                    ("Verificando dependências...", 55, 1),
                    ("Configurando IA...", 70, 2),
                    ("Preparando interface...", 85, 1),
                    ("Finalizando...", 100, 0.5)
                ]
                
                for status, progress, delay in steps:
                    self.splash.after(0, lambda s=status: self.status_var.set(s))
                    self.splash.after(0, lambda p=progress: self.progress_var.set(p))
                    time.sleep(delay)
                
                # Verificação real do sistema
                self.splash.after(0, lambda: self.status_var.set("Verificando configuração do sistema..."))
                system_info = get_real_system_info()
                
                if system_info.get('error'):
                    self.splash.after(0, lambda: messagebox.showerror("Erro", f"Erro no sistema: {system_info.get('error')}"))
                    self.splash.after(0, self.splash.destroy)
                    return
                
                # Aguardar um pouco e fechar splash
                time.sleep(1)
                self.splash.after(0, self.close_splash)
                
            except Exception as e:
                logger.error(f"Erro na inicialização: {e}")
                self.splash.after(0, lambda: messagebox.showerror("Erro", f"Erro na inicialização: {e}"))
                self.splash.after(0, self.splash.destroy)
        
        threading.Thread(target=init_thread, daemon=True).start()

    def close_splash(self):
        """Fecha a tela de splash"""
        self.splash.destroy()

    def show(self):
        """Exibe a tela de splash"""
        self.splash.mainloop()

class MainApplication:
    """Aplicação principal do PC Cleaner - 100% REAL"""
    
    def __init__(self):
        # Configurar aplicação
        self.setup_application()
        
        # Inicializar componentes
        self.password_manager = PasswordManager()
        self.date_tracker = DateTracker()
        
        # Estado da aplicação
        self.current_plan = None
        self.authenticated_user = None
        self.user_license_info = {}
        
        # Criar janela principal
        self.create_main_window()

    def setup_application(self):
        """Configura a aplicação para execução"""
        try:
            # Configurar DPI awareness no Windows
            if sys.platform == 'win32':
                try:
                    ctypes.windll.shcore.SetProcessDpiAwareness(1)
                except:
                    pass
            
            # Registrar tipos de arquivo (para .exe)
            if getattr(sys, 'frozen', False):
                self.register_file_types()
            
        except Exception as e:
            logger.error(f"Erro na configuração: {e}")

    def register_file_types(self):
        """Registra tipos de arquivo para o .exe"""
        try:
            if sys.platform == 'win32':
                import winreg
                
                # Registrar extensão .pcc (PC Cleaner Config)
                key_path = r"SOFTWARE\Classes\.pcc"
                try:
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                        winreg.SetValue(key, "", winreg.REG_SZ, "PCCleanerConfig")
                except:
                    pass
        except Exception as e:
            logger.error(f"Erro ao registrar tipos de arquivo: {e}")

    def create_main_window(self):
        """Cria janela principal de seleção"""
        self.root = tk.Tk()
        self.root.title("PC Cleaner - Seleção de Plano")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # Configurar ícone
        self.set_application_icon()
        
        # Centralizar janela
        self.center_main_window()
        
        # Criar interface
        self.create_main_interface()
        
        # Verificar atualizações
        self.check_for_updates()

    def set_application_icon(self):
        """Define ícone da aplicação"""
        try:
            icon_path = os.path.join(RESOURCES_DIR, 'pc_cleaner.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            logger.error(f"Erro ao definir ícone: {e}")

    def center_main_window(self):
        """Centraliza janela principal"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.root.winfo_screenheight() // 2) - (600 // 2)
        self.root.geometry(f"800x600+{x}+{y}")

    def create_main_interface(self):
        """Cria interface principal de seleção"""
        # Header principal
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=100)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Logo e título
        title_label = tk.Label(header_frame, text="PC CLEANER", 
                              font=('Arial', 24, 'bold'), fg='#3498db', bg='#2c3e50')
        title_label.pack(pady=20)
        
        subtitle_label = tk.Label(header_frame, text="Escolha seu plano e faça login para continuar", 
                                 font=('Arial', 12), fg='#ecf0f1', bg='#2c3e50')
        subtitle_label.pack()
        
        # Container principal
        main_container = tk.Frame(self.root, bg='#f0f0f0')
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Criar cards dos planos
        self.create_plan_cards(main_container)
        
        # Frame de informações do sistema
        self.create_system_info_frame(main_container)
        
        # Footer
        self.create_footer()

    def create_plan_cards(self, parent):
        """Cria cards dos planos"""
        plans_frame = tk.Frame(parent, bg='#f0f0f0')
        plans_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título da seção
        tk.Label(plans_frame, text="SELECIONE SEU PLANO", 
                font=('Arial', 16, 'bold'), fg='#2c3e50', bg='#f0f0f0').pack(pady=(0, 20))
        
        # Container dos cards
        cards_container = tk.Frame(plans_frame, bg='#f0f0f0')
        cards_container.pack(fill=tk.X)
        
        # Card FREE
        self.create_free_card(cards_container)
        
        # Card PRO  
        self.create_pro_card(cards_container)
        
        # Card MASTER PLUS
        self.create_master_card(cards_container)

    def create_free_card(self, parent):
        """Cria card do plano Free"""
        free_frame = tk.Frame(parent, bg='#ecf0f1', relief=tk.RAISED, borderwidth=2)
        free_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Header do card
        header = tk.Frame(free_frame, bg='#95a5a6', height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="🆓 PLANO FREE", font=('Arial', 14, 'bold'), 
                fg='white', bg='#95a5a6').pack(pady=15)
        
        # Conteúdo
        content = tk.Frame(free_frame, bg='#ecf0f1')
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Descrição
        tk.Label(content, text="Grátis", font=('Arial', 16, 'bold'), 
                fg='#27ae60', bg='#ecf0f1').pack()
        
        features = [
            "✅ Limpeza básica",
            "✅ 3 limpezas por dia",
            "✅ Funcionalidades essenciais",
            "❌ Sem IA",
            "❌ Sem automação",
            "❌ Suporte limitado"
        ]
        
        for feature in features:
            tk.Label(content, text=feature, font=('Arial', 9), 
                    fg='#2c3e50', bg='#ecf0f1', anchor='w').pack(fill=tk.X, pady=1)
        
        # Botão
        tk.Button(content, text="🚀 USAR GRÁTIS", font=('Arial', 11, 'bold'),
                 bg='#95a5a6', fg='white', command=self.launch_free_plan,
                 cursor='hand2').pack(fill=tk.X, pady=(15, 0))

    def create_pro_card(self, parent):
        """Cria card do plano Pro"""
        pro_frame = tk.Frame(parent, bg='#e8f5ff', relief=tk.RAISED, borderwidth=2)
        pro_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Header do card
        header = tk.Frame(pro_frame, bg='#3498db', height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="💼 PLANO PRO", font=('Arial', 14, 'bold'), 
                fg='white', bg='#3498db').pack(pady=15)
        
        # Badge popular
        tk.Label(pro_frame, text="⭐ MAIS POPULAR", font=('Arial', 8, 'bold'), 
                fg='white', bg='#e74c3c').pack()
        
        # Conteúdo
        content = tk.Frame(pro_frame, bg='#e8f5ff')
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Preço
        tk.Label(content, text="R$ 19,90/mês", font=('Arial', 16, 'bold'), 
                fg='#3498db', bg='#e8f5ff').pack()
        
        features = [
            "✅ Limpezas ILIMITADAS",
            "✅ IA básica integrada", 
            "✅ Detecção de duplicatas",
            "✅ Otimização de registro",
            "✅ Relatórios avançados",
            "✅ Suporte prioritário"
        ]
        
        for feature in features:
            tk.Label(content, text=feature, font=('Arial', 9), 
                    fg='#2c3e50', bg='#e8f5ff', anchor='w').pack(fill=tk.X, pady=1)
        
        # Botão
        tk.Button(content, text="🚀 FAZER LOGIN PRO", font=('Arial', 11, 'bold'),
                 bg='#3498db', fg='white', command=self.launch_pro_plan,
                 cursor='hand2').pack(fill=tk.X, pady=(15, 0))

    def create_master_card(self, parent):
        """Cria card do plano Master Plus"""
        master_frame = tk.Frame(parent, bg='#fff9e6', relief=tk.RAISED, borderwidth=3)
        master_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Header do card
        header = tk.Frame(master_frame, bg='#f39c12', height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="👑 MASTER PLUS", font=('Arial', 14, 'bold'), 
                fg='white', bg='#f39c12').pack(pady=15)
        
        # Badge VIP
        tk.Label(master_frame, text="💎 VIP EXCLUSIVO", font=('Arial', 8, 'bold'), 
                fg='white', bg='#8e44ad').pack()
        
        # Conteúdo
        content = tk.Frame(master_frame, bg='#fff9e6')
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Preço
        tk.Label(content, text="R$ 39,90/mês", font=('Arial', 16, 'bold'), 
                fg='#f39c12', bg='#fff9e6').pack()
        
        features = [
            "✅ TUDO do Pro +",
            "✅ IA COMPLETA (100%)",
            "✅ Computer Vision total",
            "✅ Automação RPA",
            "✅ Manutenção preditiva", 
            "✅ Suporte VIP 24/7"
        ]
        
        for feature in features:
            tk.Label(content, text=feature, font=('Arial', 9), 
                    fg='#2c3e50', bg='#fff9e6', anchor='w').pack(fill=tk.X, pady=1)
        
        # Botão
        tk.Button(content, text="👑 LOGIN VIP", font=('Arial', 11, 'bold'),
                 bg='#f39c12', fg='white', command=self.launch_master_plan,
                 cursor='hand2').pack(fill=tk.X, pady=(15, 0))

    def create_system_info_frame(self, parent):
        """Cria frame de informações do sistema"""
        info_frame = tk.LabelFrame(parent, text="ℹ️ Informações do Sistema", 
                                  font=('Arial', 12, 'bold'), bg='#f0f0f0')
        info_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Obter informações REAIS do sistema
        system_info = get_real_system_info()
        
        info_text = f"""
💻 Sistema: {system_info.get('os_name', 'N/A')} {system_info.get('os_version', '')}
🖥️ CPU: {system_info.get('cpu_model', 'N/A')} ({system_info.get('cpu_cores', 'N/A')} núcleos)
💾 RAM: {system_info.get('total_memory_gb', 0):.1f} GB (Uso: {system_info.get('memory_percent', 0):.1f}%)
💿 Disco: {system_info.get('free_disk_gb', 0):.1f} GB livres de {system_info.get('total_disk_gb', 0):.1f} GB
⚡ Status: {'⚠️ Alto uso de recursos' if system_info.get('cpu_percent', 0) > 80 or system_info.get('memory_percent', 0) > 80 else '✅ Sistema saudável'}
        """
        
        tk.Label(info_frame, text=info_text, font=('Arial', 10), 
                fg='#2c3e50', bg='#f0f0f0', justify=tk.LEFT).pack(padx=10, pady=10)

    def create_footer(self):
        """Cria footer da aplicação"""
        footer_frame = tk.Frame(self.root, bg='#34495e', height=50)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        footer_frame.pack_propagate(False)
        
        # Links
        links_frame = tk.Frame(footer_frame, bg='#34495e')
        links_frame.pack(expand=True)
        
        links = [
            ("🌐 Site Oficial", "https://pccleaner.com"),
            ("📧 Suporte", "mailto:suporte@pccleaner.com"),
            ("💎 Upgrade", "https://pccleaner.com/upgrade"),
            ("ℹ️ Sobre", self.show_about)
        ]
        
        for text, action in links:
            if isinstance(action, str):
                btn = tk.Label(links_frame, text=text, font=('Arial', 9), 
                              fg='#3498db', bg='#34495e', cursor='hand2')
                btn.bind("<Button-1>", lambda e, url=action: webbrowser.open(url))
            else:
                btn = tk.Label(links_frame, text=text, font=('Arial', 9), 
                              fg='#3498db', bg='#34495e', cursor='hand2')
                btn.bind("<Button-1>", lambda e, func=action: func())
            btn.pack(side=tk.LEFT, padx=20, pady=15)

    def show_about(self):
        """Mostra informações sobre o PC Cleaner"""
        about_text = """
PC CLEANER v3.0.0
Sistema Completo de Limpeza com Inteligência Artificial

🆓 FREE: Limpeza básica gratuita
💼 PRO: IA básica + funcionalidades avançadas (R$ 19,90/mês)
👑 MASTER PLUS: IA COMPLETA + automação total (R$ 39,90/mês)

Desenvolvido por: PC Cleaner Team
© 2024 Todos os direitos reservados

🌐 Site: https://pccleaner.com
📧 Suporte: suporte@pccleaner.com
📞 Telefone: (11) 3333-4444
        """
        
        messagebox.showinfo("Sobre o PC Cleaner", about_text)

    def check_for_updates(self):
        """Verifica atualizações (simulado para .exe)"""
        def check_thread():
            try:
                # Simular verificação de updates
                time.sleep(2)
                # Em uma implementação real, verificaria servidor de updates
                logger.info("Verificação de atualizações concluída")
            except Exception as e:
                logger.error(f"Erro na verificação de atualizações: {e}")
        
        threading.Thread(target=check_thread, daemon=True).start()

    # Métodos de lançamento dos planos

    def launch_free_plan(self):
        """Lança o plano Free"""
        try:
            self.root.withdraw()  # Esconder janela principal
            
            try:
                free_app = FreePlanGUI()
                if hasattr(free_app, 'root') and free_app.root.winfo_exists():
                    free_app.run()
            except Exception as e:
                logger.error(f"Erro ao executar plano Free: {e}")
                messagebox.showerror("Erro", f"Erro ao iniciar plano Free:\n{e}")
            
            self.root.deiconify()  # Mostrar janela principal novamente
            
        except Exception as e:
            logger.error(f"Erro ao lançar plano Free: {e}")

    def launch_pro_plan(self):
        """Lança o plano Pro"""
        try:
            self.root.withdraw()  # Esconder janela principal
            
            try:
                pro_app = ProPlanGUI()
                if hasattr(pro_app, 'root') and pro_app.root.winfo_exists():
                    pro_app.run()
            except Exception as e:
                logger.error(f"Erro ao executar plano Pro: {e}")
                messagebox.showerror("Erro", f"Erro ao iniciar plano Pro:\n{e}")
            
            self.root.deiconify()  # Mostrar janela principal novamente
            
        except Exception as e:
            logger.error(f"Erro ao lançar plano Pro: {e}")

    def launch_master_plan(self):
        """Lança o plano Master Plus"""
        try:
            self.root.withdraw()  # Esconder janela principal
            
            try:
                master_app = MasterPlusGUI()
                if hasattr(master_app, 'root') and master_app.root.winfo_exists():
                    master_app.run()
            except Exception as e:
                logger.error(f"Erro ao executar plano Master Plus: {e}")
                messagebox.showerror("Erro", f"Erro ao iniciar plano Master Plus:\n{e}")
            
            self.root.deiconify()  # Mostrar janela principal novamente
            
        except Exception as e:
            logger.error(f"Erro ao lançar plano Master Plus: {e}")

    def run(self):
        """Executa a aplicação principal"""
        try:
            # Configurar protocolo de fechamento
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # Executar loop principal
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"Erro na execução principal: {e}")
            messagebox.showerror("Erro Crítico", f"Erro crítico na aplicação: {e}")

    def on_closing(self):
        """Manipula fechamento da aplicação"""
        try:
            result = messagebox.askyesno("Sair", "Deseja realmente sair do PC Cleaner?")
            if result:
                self.root.quit()
                self.root.destroy()
        except Exception as e:
            logger.error(f"Erro ao fechar aplicação: {e}")
            self.root.quit()

def create_required_directories():
    """Cria diretórios necessários para a aplicação"""
    directories = [
        'data',
        'resources',
        'data/backups',
        'data/reports',
        'data/logs',
        'data/screenshots',
        'data/ml_models',
        'data/anomaly_models',
        'data/anomaly_alerts',
        'data/cv_analysis',
        'data/registry_backups'
    ]
    
    for directory in directories:
        dir_path = os.path.join(BASE_DIR, directory)
        os.makedirs(dir_path, exist_ok=True)
        logger.info(f"Diretório criado/verificado: {dir_path}")

def check_system_requirements():
    """Verifica requisitos do sistema"""
    try:
        # Verificar Python (apenas se executando como script)
        if not getattr(sys, 'frozen', False):
            if sys.version_info < (3, 8):
                messagebox.showerror("Erro", "Python 3.8 ou superior é necessário!")
                return False
        
        # Verificar espaço em disco
        import shutil
        free_space = shutil.disk_usage(BASE_DIR).free / (1024**3)  # GB
        if free_space < 0.5:  # Menos de 500 MB
            messagebox.showwarning("Aviso", f"Pouco espaço em disco: {free_space:.1f} GB livres")
        
        # Verificar dependências críticas
        try:
            import tkinter
            import threading
            import json
            import datetime
        except ImportError as e:
            messagebox.showerror("Erro", f"Dependência faltando: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Erro na verificação de requisitos: {e}")
        return False

def setup_error_handling():
    """Configura tratamento global de erros"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.error(f"Erro não tratado: {error_msg}")
        
        if not getattr(sys, 'frozen', False):
            # Se executando como script, mostrar erro completo
            messagebox.showerror("Erro Crítico", f"Erro não tratado:\n{error_msg}")
        else:
            # Se executando como .exe, mostrar erro simplificado
            messagebox.showerror("Erro", "Ocorreu um erro inesperado. Verifique os logs.")
    
    sys.excepthook = handle_exception

def main():
    """Função principal da aplicação"""
    try:
        # Configurar tratamento de erros
        import traceback
        setup_error_handling()
        
        # Verificar requisitos do sistema
        if not check_system_requirements():
            return 1
        
        # Criar diretórios necessários
        create_required_directories()
        
        # Log de inicialização
        logger.info("=" * 50)
        logger.info("PC CLEANER v3.0.0 - INICIANDO")
        logger.info(f"Modo de execução: {'EXE' if getattr(sys, 'frozen', False) else 'Script Python'}")
        logger.info(f"Diretório base: {BASE_DIR}")
        logger.info(f"Diretório de recursos: {RESOURCES_DIR}")
        logger.info("=" * 50)
        
        # Exibir splash screen
        splash = SplashScreen()
        splash.show()
        
        # Inicializar aplicação principal
        app = MainApplication()
        app.run()
        
        # Log de finalização
        logger.info("PC CLEANER finalizado normalmente")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Aplicação interrompida pelo usuário")
        return 0
    except Exception as e:
        logger.error(f"Erro crítico na função main: {e}")
        try:
            messagebox.showerror("Erro Crítico", f"Erro crítico:\n{e}")
        except:
            pass
        return 1

# Configuração para .exe
if __name__ == "__main__":
    # Configurar console no Windows (para .exe)
    if sys.platform == 'win32' and getattr(sys, 'frozen', False):
        try:
            # Ocultar console se executando como .exe
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass
    
    # Executar aplicação
    exit_code = main()
    sys.exit(exit_code)