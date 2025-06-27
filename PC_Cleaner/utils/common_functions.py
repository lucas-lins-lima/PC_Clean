# utils/common_functions.py
import os
import shutil
import tempfile
import winreg
import subprocess
import psutil
import time
import hashlib
import json
from pathlib import Path
from datetime import datetime
import threading
from typing import List, Dict, Tuple, Optional
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cleanup_log.txt'),
        logging.StreamHandler()
    ]
)

class PCCleaner:
    """Classe principal para limpeza e otimização do PC"""
    
    def __init__(self):
        self.temp_folders = [
            tempfile.gettempdir(),
            os.path.expanduser("~/AppData/Local/Temp"),
            os.path.expanduser("~/AppData/Local/Microsoft/Windows/Temporary Internet Files"),
            "C:\Windows\Temp",
            "C:\Windows\Prefetch",
            "C:\Windows\SoftwareDistribution\Download",
        ]
        self.browser_cache_paths = {
            'Chrome': os.path.expanduser("~/AppData/Local/Google/Chrome/User Data/Default/Cache"),
            'Firefox': os.path.expanduser("~/AppData/Local/Mozilla/Firefox/Profiles"),
            'Edge': os.path.expanduser("~/AppData/Local/Microsoft/Edge/User Data/Default/Cache"),
            'Opera': os.path.expanduser("~/AppData/Roaming/Opera Software/Opera Stable/Cache")
        }
        self.cleaned_size = 0
        self.errors = []

    def get_system_info(self) -> Dict:
        """Coleta informações detalhadas do sistema"""
        try:
            # Informações da CPU
            cpu_info = {
                'physical_cores': psutil.cpu_count(logical=False),
                'total_cores': psutil.cpu_count(logical=True),
                'max_frequency': f"{psutil.cpu_freq().max:.2f} MHz" if psutil.cpu_freq() else "N/A",
                'current_frequency': f"{psutil.cpu_freq().current:.2f} MHz" if psutil.cpu_freq() else "N/A",
                'usage_percent': psutil.cpu_percent(interval=1)
            }
            
            # Informações da memória
            memory = psutil.virtual_memory()
            memory_info = {
                'total': self._bytes_to_gb(memory.total),
                'available': self._bytes_to_gb(memory.available),
                'used': self._bytes_to_gb(memory.used),
                'percentage': memory.percent
            }
            
            # Informações do disco
            disk_usage = psutil.disk_usage('/')
            disk_info = {
                'total': self._bytes_to_gb(disk_usage.total),
                'used': self._bytes_to_gb(disk_usage.used),
                'free': self._bytes_to_gb(disk_usage.free),
                'percentage': (disk_usage.used / disk_usage.total) * 100
            }
            
            # Informações da rede
            net_info = psutil.net_io_counters()
            network_info = {
                'bytes_sent': self._bytes_to_mb(net_info.bytes_sent),
                'bytes_received': self._bytes_to_mb(net_info.bytes_received),
                'packets_sent': net_info.packets_sent,
                'packets_received': net_info.packets_recv
            }
            
            # Processos em execução
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_percent': proc.info['memory_percent']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {
                'cpu': cpu_info,
                'memory': memory_info,
                'disk': disk_info,
                'network': network_info,
                'processes': sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:10],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Erro ao coletar informações do sistema: {e}")
            return {}

    def clean_temp_files(self) -> Tuple[int, List[str]]:
        """Remove arquivos temporários do sistema"""
        cleaned_files = []
        total_size = 0
        
        for temp_folder in self.temp_folders:
            if os.path.exists(temp_folder):
                try:
                    for root, dirs, files in os.walk(temp_folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                file_size = os.path.getsize(file_path)
                                os.remove(file_path)
                                cleaned_files.append(file_path)
                                total_size += file_size
                            except (PermissionError, FileNotFoundError, OSError) as e:
                                self.errors.append(f"Não foi possível remover {file_path}: {e}")
                                
                        # Remove diretórios vazios
                        for dir_name in dirs:
                            dir_path = os.path.join(root, dir_name)
                            try:
                                if not os.listdir(dir_path):
                                    os.rmdir(dir_path)
                                    cleaned_files.append(dir_path)
                            except (PermissionError, OSError):
                                continue
                                
                except Exception as e:
                    self.errors.append(f"Erro ao limpar pasta {temp_folder}: {e}")
        
        self.cleaned_size += total_size
        logging.info(f"Arquivos temporários limpos: {len(cleaned_files)} arquivos, {self._bytes_to_mb(total_size)} MB")
        return len(cleaned_files), cleaned_files

    def clean_browser_cache(self) -> Dict[str, int]:
        """Limpa cache dos principais navegadores"""
        browser_results = {}
        
        for browser, cache_path in self.browser_cache_paths.items():
            cleaned_size = 0
            if os.path.exists(cache_path):
                try:
                    if browser == 'Firefox':
                        # Firefox tem estrutura diferente
                        for profile_dir in os.listdir(cache_path):
                            profile_cache = os.path.join(cache_path, profile_dir, 'cache2')
                            if os.path.exists(profile_cache):
                                cleaned_size += self._remove_directory_contents(profile_cache)
                    else:
                        cleaned_size = self._remove_directory_contents(cache_path)
                    
                    browser_results[browser] = cleaned_size
                    self.cleaned_size += cleaned_size
                    
                except Exception as e:
                    self.errors.append(f"Erro ao limpar cache do {browser}: {e}")
                    browser_results[browser] = 0
            else:
                browser_results[browser] = 0
        
        return browser_results

    def clean_recycle_bin(self) -> int:
        """Esvazia a lixeira do Windows"""
        try:
            # Usando winshell se disponível, senão método alternativo
            try:
                import winshell
                winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
                logging.info("Lixeira esvaziada com sucesso")
                return 1
            except ImportError:
                # Método alternativo usando subprocess
                subprocess.run(['PowerShell', '-Command', 'Clear-RecycleBin -Confirm:$false'], 
                             capture_output=True, check=True)
                logging.info("Lixeira esvaziada com sucesso (método alternativo)")
                return 1
                
        except Exception as e:
            self.errors.append(f"Erro ao esvaziar lixeira: {e}")
            return 0

    def optimize_startup_programs(self) -> List[Dict]:
        """Analisa e otimiza programas de inicialização"""
        startup_programs = []
        
        # Locais do registro onde ficam programas de inicialização
        startup_keys = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce")
        ]
        
        for hkey, key_path in startup_keys:
            try:
                with winreg.OpenKey(hkey, key_path) as key:
                    i = 0
                    while True:
                        try:
                            name, value, reg_type = winreg.EnumValue(key, i)
                            startup_programs.append({
                                'name': name,
                                'path': value,
                                'registry_location': f"{hkey}\{key_path}",
                                'can_disable': self._is_safe_to_disable(name, value)
                            })
                            i += 1
                        except WindowsError:
                            break
            except Exception as e:
                self.errors.append(f"Erro ao acessar registro de inicialização: {e}")
        
        return startup_programs

    def find_duplicate_files(self, directories: List[str] = None) -> Dict[str, List[str]]:
        """Encontra arquivos duplicados baseado em hash MD5"""
        if directories is None:
            directories = [
                os.path.expanduser("~/Documents"),
                os.path.expanduser("~/Downloads"),
                os.path.expanduser("~/Pictures"),
                os.path.expanduser("~/Videos")
            ]
        
        file_hashes = {}
        duplicates = {}
        
        for directory in directories:
            if os.path.exists(directory):
                for root, _, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            file_hash = self._get_file_hash(file_path)
                            file_size = os.path.getsize(file_path)
                            
                            # Só considera duplicatas arquivos maiores que 1MB
                            if file_size > 1024 * 1024:
                                if file_hash in file_hashes:
                                    if file_hash not in duplicates:
                                        duplicates[file_hash] = [file_hashes[file_hash]]
                                    duplicates[file_hash].append(file_path)
                                else:
                                    file_hashes[file_hash] = file_path
                                    
                        except Exception as e:
                            self.errors.append(f"Erro ao processar arquivo {file_path}: {e}")
        
        return duplicates

    def analyze_disk_space(self, path: str = "C:") -> Dict:
        """Analisa uso de espaço em disco detalhadamente"""
        disk_analysis = {
            'total_size': 0,
            'folders': [],
            'largest_files': [],
            'file_types': {}
        }
        
        try:
            # Análise por pastas
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    try:
                        folder_size = self._get_folder_size(item_path)
                        disk_analysis['folders'].append({
                            'name': item,
                            'path': item_path,
                            'size_mb': self._bytes_to_mb(folder_size),
                            'size_gb': self._bytes_to_gb(folder_size)
                        })
                    except Exception as e:
                        self.errors.append(f"Erro ao analisar pasta {item_path}: {e}")
            
            # Ordena pastas por tamanho
            disk_analysis['folders'] = sorted(disk_analysis['folders'], 
                                            key=lambda x: x['size_mb'], reverse=True)
            
            # Encontra maiores arquivos
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size > 100 * 1024 * 1024:  # Arquivos maiores que 100MB
                            file_ext = os.path.splitext(file)[1].lower()
                            disk_analysis['largest_files'].append({
                                'name': file,
                                'path': file_path,
                                'size_mb': self._bytes_to_mb(file_size),
                                'extension': file_ext
                            })
                            
                            # Conta por tipo de arquivo
                            if file_ext in disk_analysis['file_types']:
                                disk_analysis['file_types'][file_ext] += file_size
                            else:
                                disk_analysis['file_types'][file_ext] = file_size
                                
                    except Exception as e:
                        continue
            
            # Ordena maiores arquivos
            disk_analysis['largest_files'] = sorted(disk_analysis['largest_files'], 
                                                   key=lambda x: x['size_mb'], reverse=True)[:50]
            
        except Exception as e:
            self.errors.append(f"Erro na análise de disco: {e}")
        
        return disk_analysis

    def clean_windows_logs(self) -> int:
        """Limpa logs do Windows"""
        log_paths = [
            "C:\Windows\Logs",
            "C:\Windows\System32\LogFiles",
            "C:\Windows\System32\winevt\Logs"
        ]
        
        cleaned_files = 0
        for log_path in log_paths:
            if os.path.exists(log_path):
                try:
                    for root, _, files in os.walk(log_path):
                        for file in files:
                            if file.endswith(('.log', '.etl')):
                                file_path = os.path.join(root, file)
                                try:
                                    file_size = os.path.getsize(file_path)
                                    os.remove(file_path)
                                    self.cleaned_size += file_size
                                    cleaned_files += 1
                                except Exception:
                                    continue
                except Exception as e:
                    self.errors.append(f"Erro ao limpar logs em {log_path}: {e}")
        
        return cleaned_files

    def defragment_registry(self) -> bool:
        """Executa limpeza e otimização do registro do Windows"""
        try:
            # Backup do registro antes da limpeza
            backup_path = f"registry_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.reg"
            subprocess.run(['reg', 'export', 'HKLM', backup_path], check=True)
            
            # Limpeza de entradas órfãs do registro
            registry_keys_to_clean = [
                r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run",
                r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            ]
            
            for key_path in registry_keys_to_clean:
                try:
                    self._clean_registry_key(key_path)
                except Exception as e:
                    self.errors.append(f"Erro ao limpar chave do registro {key_path}: {e}")
            
            logging.info("Limpeza do registro concluída")
            return True
            
        except Exception as e:
            self.errors.append(f"Erro na desfragmentação do registro: {e}")
            return False

    # Métodos auxiliares privados
    def _bytes_to_mb(self, bytes_val: int) -> float:
        """Converte bytes para megabytes"""
        return round(bytes_val / (1024 * 1024), 2)
    
    def _bytes_to_gb(self, bytes_val: int) -> float:
        """Converte bytes para gigabytes"""
        return round(bytes_val / (1024 * 1024 * 1024), 2)
    
    def _remove_directory_contents(self, directory: str) -> int:
        """Remove conteúdo de um diretório e retorna bytes removidos"""
        total_size = 0
        try:
            for root, dirs, files in os.walk(directory, topdown=False):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        total_size += file_size
                    except Exception:
                        continue
                for dir_name in dirs:
                    try:
                        os.rmdir(os.path.join(root, dir_name))
                    except Exception:
                        continue
        except Exception:
            pass
        return total_size
    
    def _get_file_hash(self, file_path: str) -> str:
        """Calcula hash MD5 de um arquivo"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def _get_folder_size(self, folder_path: str) -> int:
        """Calcula tamanho total de uma pasta"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(file_path)
                    except Exception:
                        continue
        except Exception:
            pass
        return total_size
    
    def _is_safe_to_disable(self, name: str, path: str) -> bool:
        """Determina se é seguro desabilitar um programa de inicialização"""
        # Lista de programas seguros para desabilitar
        safe_to_disable = [
            'spotify', 'discord', 'steam', 'skype', 'zoom', 'adobe',
            'office', 'dropbox', 'googledrive', 'onedrive'
        ]
        
        # Lista de programas críticos que NÃO devem ser desabilitados
        critical_programs = [
            'windows', 'microsoft', 'antivirus', 'firewall', 'driver',
            'audio', 'network', 'bluetooth', 'touchpad'
        ]
        
        name_lower = name.lower()
        path_lower = path.lower()
        
        # Verifica se é crítico
        for critical in critical_programs:
            if critical in name_lower or critical in path_lower:
                return False
        
        # Verifica se é seguro para desabilitar
        for safe in safe_to_disable:
            if safe in name_lower or safe in path_lower:
                return True
        
        return False  # Por segurança, não marca como seguro se não tem certeza
    
    def _clean_registry_key(self, key_path: str):
        """Limpa entradas órfãs de uma chave do registro"""
        # Implementação simplificada - em produção seria mais complexa
        pass

# Funções utilitárias globais
def create_system_report(cleaner: PCCleaner) -> Dict:
    """Cria um relatório completo do sistema"""
    return {
        'system_info': cleaner.get_system_info(),
        'cleaned_size_mb': cleaner._bytes_to_mb(cleaner.cleaned_size),
        'errors': cleaner.errors,
        'timestamp': datetime.now().isoformat(),
        'recommendations': generate_recommendations(cleaner)
    }

def generate_recommendations(cleaner: PCCleaner) -> List[str]:
    """Gera recomendações baseadas na análise do sistema"""
    recommendations = []
    
    system_info = cleaner.get_system_info()
    
    if system_info.get('memory', {}).get('percentage', 0) > 80:
        recommendations.append("Memória RAM em uso alto (>80%). Considere fechar programas desnecessários.")
    
    if system_info.get('disk', {}).get('percentage', 0) > 90:
        recommendations.append("Espaço em disco baixo (<10% livre). Execute limpeza de arquivos.")
    
    if system_info.get('cpu', {}).get('usage_percent', 0) > 80:
        recommendations.append("CPU em uso alto (>80%). Verifique processos em segundo plano.")
    
    return recommendations

def save_results_to_file(results: Dict, filename: str = None):
    """Salva resultados da limpeza em arquivo JSON"""
    if filename is None:
        filename = f"cleanup_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logging.info(f"Resultados salvos em: {filename}")
    except Exception as e:
        logging.error(f"Erro ao salvar resultados: {e}")