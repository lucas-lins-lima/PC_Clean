# build_exe.py - Script para gerar executável
"""
Script para compilar PC Cleaner em executável (.exe)
Uso: python build_exe.py
"""

import os
import sys
import subprocess
import shutil
from datetime import datetime

def install_pyinstaller():
    """Instala PyInstaller se necessário"""
    try:
        import PyInstaller
        print("✅ PyInstaller já instalado")
        return True
    except ImportError:
        print("📦 Instalando PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✅ PyInstaller instalado com sucesso")
            return True
        except subprocess.CalledProcessError:
            print("❌ Erro ao instalar PyInstaller")
            return False

def create_exe():
    """Cria o executável do PC Cleaner"""
    if not install_pyinstaller():
        return False
    
    print("🚀 Iniciando compilação do PC Cleaner...")
    
    # Configurações do PyInstaller
    app_name = "PC_Cleaner"
    main_script = "main.py"
    
    # Comando PyInstaller
    cmd = [
        "pyinstaller",
        "--onefile",                    # Arquivo único
        "--windowed",                   # Sem console
        f"--name={app_name}",          # Nome do executável
        "--icon=resources/pc_cleaner.ico",  # Ícone (se existir)
        "--add-data=utils;utils",       # Incluir pasta utils
        "--add-data=ai_modules;ai_modules",  # Incluir pasta ai_modules
        "--add-data=resources;resources",    # Incluir recursos
        "--hidden-import=tkinter",      # Imports ocultos
        "--hidden-import=threading",
        "--hidden-import=json",
        "--hidden-import=datetime",
        "--hidden-import=hashlib",
        "--hidden-import=webbrowser",
        "--hidden-import=subprocess",
        "--hidden-import=ctypes",
        "--hidden-import=psutil",
        "--hidden-import=numpy",
        "--hidden-import=sklearn",
        "--hidden-import=cv2",
        "--hidden-import=PIL",
        "--hidden-import=matplotlib",
        "--hidden-import=seaborn",
        "--clean",                      # Limpar build anterior
        main_script
    ]
    
    try:
        # Executar PyInstaller
        print("⚙️ Executando PyInstaller...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Compilação concluída com sucesso!")
            
            # Verificar se arquivo foi criado
            exe_path = os.path.join("dist", f"{app_name}.exe")
            if os.path.exists(exe_path):
                size_mb = os.path.getsize(exe_path) / (1024 * 1024)
                print(f"📁 Executável criado: {exe_path}")
                print(f"📊 Tamanho: {size_mb:.1f} MB")
                print(f"⏰ Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
                
                # Criar pasta de distribuição
                dist_folder = f"PC_Cleaner_v3.0.0_{datetime.now().strftime('%Y%m%d')}"
                if os.path.exists(dist_folder):
                    shutil.rmtree(dist_folder)
                os.makedirs(dist_folder)
                
                # Copiar executável
                shutil.copy2(exe_path, dist_folder)
                
                # Copiar arquivos necessários
                files_to_copy = [
                    "README.md",
                    "LICENSE",
                    "requirements.txt"
                ]
                
                for file in files_to_copy:
                    if os.path.exists(file):
                        shutil.copy2(file, dist_folder)
                
                # Criar pastas necessárias no executável
                necessary_folders = ['data', 'resources']
                for folder in necessary_folders:
                    folder_path = os.path.join(dist_folder, folder)
                    os.makedirs(folder_path, exist_ok=True)
                
                print(f"📦 Pasta de distribuição criada: {dist_folder}")
                print("🎉 Build concluído com sucesso!")
                
                return True
            else:
                print("❌ Executável não foi criado")
                return False
        else:
            print("❌ Erro na compilação:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Erro durante compilação: {e}")
        return False

def main():
    print("🛠️ PC CLEANER - GERADOR DE EXECUTÁVEL")
    print("=" * 40)
    
    if not os.path.exists("main.py"):
        print("❌ Arquivo main.py não encontrado!")
        return 1
    
    if create_exe():
        print("\n✅ PC Cleaner compilado com sucesso!")
        print("📁 Verifique a pasta dist/ para o executável")
        return 0
    else:
        print("\n❌ Falha na compilação")
        return 1

if __name__ == "__main__":
    exit_code = main()
    input("\nPressione Enter para fechar...")
    sys.exit(exit_code)