# ai_modules/anomaly_detector.py - VERSÃO 100% REAL
import psutil
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
import threading
import pickle
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('anomaly_detector')

class AnomalyDetector:
    """Sistema de Detecção de Anomalias 100% REAL"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.models_dir = os.path.join(data_dir, "anomaly_models")
        self.alerts_dir = os.path.join(data_dir, "anomaly_alerts")
        self.monitoring_data_file = os.path.join(data_dir, "monitoring_data.json")
        
        # Criar diretórios
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.alerts_dir, exist_ok=True)
        
        # Modelos de detecção
        self.system_anomaly_model = IsolationForest(contamination=0.1, random_state=42)
        self.process_anomaly_model = IsolationForest(contamination=0.05, random_state=42)
        self.network_anomaly_model = IsolationForest(contamination=0.08, random_state=42)
        self.scaler = StandardScaler()
        
        # Dados de monitoramento REAIS
        self.monitoring_data = []
        self.baseline_established = False
        self.monitoring_active = False
        self.alert_thresholds = self.load_default_thresholds()
        
        # Histórico de anomalias REAIS
        self.anomaly_history = []
        self.behavioral_patterns = {}
        
        # Carregar dados existentes
        self.load_monitoring_data()
        self.load_models()
        
        # Iniciar coleta de dados
        self.start_monitoring()

    def load_default_thresholds(self) -> Dict:
        """Carrega limites padrão para detecção"""
        return {
            'cpu_threshold': 90.0,
            'memory_threshold': 85.0,
            'disk_threshold': 95.0,
            'network_threshold_mbps': 100.0,
            'process_cpu_threshold': 50.0,
            'process_memory_threshold': 1024,  # MB
            'disk_io_threshold': 100,  # MB/s
            'network_connections_threshold': 100
        }

    def collect_real_system_metrics(self) -> Dict:
        """Coleta métricas REAIS do sistema"""
        try:
            timestamp = datetime.now()
            
            # Métricas REAIS de sistema
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_freq = psutil.cpu_freq()
            cpu_count = psutil.cpu_count()
            
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Métricas REAIS de disco
            disk_usage = psutil.disk_usage('/')
            try:
                disk_io = psutil.disk_io_counters()
                disk_io_data = {
                    'read_bytes_per_sec': disk_io.read_bytes,
                    'write_bytes_per_sec': disk_io.write_bytes,
                    'read_count': disk_io.read_count,
                    'write_count': disk_io.write_count
                } if disk_io else {}
            except:
                disk_io_data = {}
            
            # Métricas REAIS de rede
            try:
                net_io = psutil.net_io_counters()
                network_data = {
                    'bytes_sent_per_sec': net_io.bytes_sent,
                    'bytes_recv_per_sec': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv,
                    'err_in': net_io.errin,
                    'err_out': net_io.errout,
                    'drop_in': net_io.dropin,
                    'drop_out': net_io.dropout
                }
                
                # Conexões de rede REAIS
                connections = psutil.net_connections(kind='inet')
                active_connections = len([c for c in connections if c.status == 'ESTABLISHED'])
                
            except:
                network_data = {}
                active_connections = 0
            
            # Métricas REAIS de processos
            processes_data = []
            total_processes = 0
            high_cpu_processes = 0
            high_memory_processes = 0
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'status']):
                try:
                    proc_info = proc.info
                    total_processes += 1
                    
                    if proc_info['cpu_percent'] and proc_info['cpu_percent'] > self.alert_thresholds['process_cpu_threshold']:
                        high_cpu_processes += 1
                    
                    if (proc_info['memory_info'] and 
                        proc_info['memory_info'].rss / (1024*1024) > self.alert_thresholds['process_memory_threshold']):
                        high_memory_processes += 1
                    
                    # Guardar processos problemáticos
                    if (proc_info['cpu_percent'] and proc_info['cpu_percent'] > 25) or \
                       (proc_info['memory_percent'] and proc_info['memory_percent'] > 10):
                        processes_data.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cpu_percent': proc_info['cpu_percent'] or 0,
                            'memory_percent': proc_info['memory_percent'] or 0,
                            'memory_mb': (proc_info['memory_info'].rss / (1024*1024)) if proc_info['memory_info'] else 0,
                            'status': proc_info['status']
                        })
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Métricas REAIS de temperatura (se disponível)
            temperature_data = {}
            try:
                temps = psutil.sensors_temperatures()
                for name, entries in temps.items():
                    temp_values = [temp.current for temp in entries if temp.current]
                    if temp_values:
                        temperature_data[name] = {
                            'current': max(temp_values),
                            'average': sum(temp_values) / len(temp_values)
                        }
            except:
                pass
            
            # Métricas REAIS de bateria (se disponível)
            battery_data = {}
            try:
                battery = psutil.sensors_battery()
                if battery:
                    battery_data = {
                        'percent': battery.percent,
                        'plugged': battery.power_plugged,
                        'time_left': battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
                    }
            except:
                pass
            
            metrics = {
                'timestamp': timestamp.isoformat(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'cpu_frequency': cpu_freq.current if cpu_freq else 0,
                    'cpu_count': cpu_count,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'memory_used_gb': memory.used / (1024**3),
                    'swap_percent': swap.percent,
                    'disk_percent': disk_usage.percent,
                    'disk_free_gb': disk_usage.free / (1024**3)
                },
                'disk_io': disk_io_data,
                'network': network_data,
                'network_connections': active_connections,
                'processes': {
                    'total': total_processes,
                    'high_cpu': high_cpu_processes,
                    'high_memory': high_memory_processes,
                    'problematic': processes_data[:20]  # Top 20 processos problemáticos
                },
                'temperatures': temperature_data,
                'battery': battery_data,
                'boot_time': psutil.boot_time(),
                'uptime_seconds': time.time() - psutil.boot_time()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Erro ao coletar métricas: {e}")
            return {}

    def extract_features_for_anomaly_detection(self, metrics: Dict) -> List[float]:
        """Extrai features REAIS para detecção de anomalias"""
        try:
            system = metrics.get('system', {})
            disk_io = metrics.get('disk_io', {})
            network = metrics.get('network', {})
            processes = metrics.get('processes', {})
            
            features = [
                system.get('cpu_percent', 0),
                system.get('memory_percent', 0),
                system.get('disk_percent', 0),
                system.get('swap_percent', 0),
                system.get('cpu_frequency', 0) / 1000,  # Normalizar
                disk_io.get('read_bytes_per_sec', 0) / (1024*1024),  # MB/s
                disk_io.get('write_bytes_per_sec', 0) / (1024*1024),  # MB/s
                network.get('bytes_sent_per_sec', 0) / (1024*1024),  # MB/s
                network.get('bytes_recv_per_sec', 0) / (1024*1024),  # MB/s
                network.get('err_in', 0),
                network.get('err_out', 0),
                metrics.get('network_connections', 0),
                processes.get('total', 0),
                processes.get('high_cpu', 0),
                processes.get('high_memory', 0),
                metrics.get('uptime_seconds', 0) / 3600  # Horas
            ]
            
            # Adicionar features de temperatura se disponível
            temps = metrics.get('temperatures', {})
            if temps:
                avg_temp = np.mean([data['current'] for data in temps.values()])
                features.append(avg_temp)
            else:
                features.append(0)
            
            # Adicionar features de bateria se disponível
            battery = metrics.get('battery', {})
            if battery:
                features.extend([
                    battery.get('percent', 100),
                    1 if battery.get('plugged', True) else 0
                ])
            else:
                features.extend([100, 1])  # Valores padrão para desktop
            
            return features
            
        except Exception as e:
            logger.error(f"Erro ao extrair features: {e}")
            return [0] * 19

    def detect_real_system_anomalies(self, metrics: Dict = None) -> Dict:
        """Detecta anomalias REAIS do sistema"""
        try:
            if metrics is None:
                metrics = self.collect_real_system_metrics()
            
            anomalies = {
                'system_anomalies': [],
                'process_anomalies': [],
                'network_anomalies': [],
                'performance_anomalies': [],
                'security_anomalies': []
            }
            
            timestamp = metrics.get('timestamp', datetime.now().isoformat())
            system = metrics.get('system', {})
            processes = metrics.get('processes', {})
            network = metrics.get('network', {})
            
            # Detecção de anomalias de sistema baseada em limites REAIS
            if system.get('cpu_percent', 0) > self.alert_thresholds['cpu_threshold']:
                anomalies['system_anomalies'].append({
                    'type': 'high_cpu_usage',
                    'severity': 'high',
                    'value': system.get('cpu_percent'),
                    'threshold': self.alert_thresholds['cpu_threshold'],
                    'description': f"Uso de CPU muito alto: {system.get('cpu_percent', 0):.1f}%",
                    'timestamp': timestamp
                })
            
            if system.get('memory_percent', 0) > self.alert_thresholds['memory_threshold']:
                anomalies['system_anomalies'].append({
                    'type': 'high_memory_usage',
                    'severity': 'high',
                    'value': system.get('memory_percent'),
                    'threshold': self.alert_thresholds['memory_threshold'],
                    'description': f"Uso de memória muito alto: {system.get('memory_percent', 0):.1f}%",
                    'timestamp': timestamp
                })
            
            if system.get('disk_percent', 0) > self.alert_thresholds['disk_threshold']:
                anomalies['system_anomalies'].append({
                    'type': 'high_disk_usage',
                    'severity': 'critical',
                    'value': system.get('disk_percent'),
                    'threshold': self.alert_thresholds['disk_threshold'],
                    'description': f"Espaço em disco crítico: {system.get('disk_percent', 0):.1f}%",
                    'timestamp': timestamp
                })
            
            # Detecção de anomalias de processos REAIS
            problematic_processes = processes.get('problematic', [])
            for proc in problematic_processes:
                if proc['cpu_percent'] > self.alert_thresholds['process_cpu_threshold']:
                    anomalies['process_anomalies'].append({
                        'type': 'high_cpu_process',
                        'severity': 'medium',
                        'process_name': proc['name'],
                        'pid': proc['pid'],
                        'cpu_percent': proc['cpu_percent'],
                        'description': f"Processo {proc['name']} usando {proc['cpu_percent']:.1f}% de CPU",
                        'timestamp': timestamp
                    })
                
                if proc['memory_mb'] > self.alert_thresholds['process_memory_threshold']:
                    anomalies['process_anomalies'].append({
                        'type': 'high_memory_process',
                        'severity': 'medium',
                        'process_name': proc['name'],
                        'pid': proc['pid'],
                        'memory_mb': proc['memory_mb'],
                        'description': f"Processo {proc['name']} usando {proc['memory_mb']:.1f} MB de memória",
                        'timestamp': timestamp
                    })
            
            # Detecção de anomalias de rede REAIS
            if metrics.get('network_connections', 0) > self.alert_thresholds['network_connections_threshold']:
                anomalies['network_anomalies'].append({
                    'type': 'excessive_connections',
                    'severity': 'medium',
                    'value': metrics.get('network_connections'),
                    'threshold': self.alert_thresholds['network_connections_threshold'],
                    'description': f"Muitas conexões de rede: {metrics.get('network_connections', 0)}",
                    'timestamp': timestamp
                })
            
            # Detecção de anomalias de performance REAIS
            if system.get('swap_percent', 0) > 50:
                anomalies['performance_anomalies'].append({
                    'type': 'high_swap_usage',
                    'severity': 'medium',
                    'value': system.get('swap_percent'),
                    'description': f"Alto uso de swap: {system.get('swap_percent', 0):.1f}%",
                    'timestamp': timestamp
                })
            
            # Detecção de temperatura alta
            temps = metrics.get('temperatures', {})
            for sensor, temp_data in temps.items():
                if temp_data['current'] > 80:  # Temperatura alta
                    anomalies['system_anomalies'].append({
                        'type': 'high_temperature',
                        'severity': 'high',
                        'sensor': sensor,
                        'temperature': temp_data['current'],
                        'description': f"Temperatura alta em {sensor}: {temp_data['current']:.1f}°C",
                        'timestamp': timestamp
                    })
            
            # Detecção de anomalias usando ML (se modelos estão treinados)
            if self.baseline_established:
                ml_anomalies = self.detect_ml_anomalies(metrics)
                for category, ml_anom in ml_anomalies.items():
                    anomalies[category].extend(ml_anom)
            
            # Salvar anomalias detectadas
            if any(anomalies.values()):
                self.save_anomaly_alert(anomalies)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Erro na detecção de anomalias: {e}")
            return {'error': str(e)}

    def detect_ml_anomalies(self, metrics: Dict) -> Dict:
        """Detecta anomalias usando ML treinado com dados REAIS"""
        try:
            ml_anomalies = {
                'system_anomalies': [],
                'process_anomalies': [],
                'network_anomalies': []
            }
            
            if not self.baseline_established:
                return ml_anomalies
            
            # Extrair features
            features = self.extract_features_for_anomaly_detection(metrics)
            features_scaled = self.scaler.transform([features])
            
            # Detectar anomalia do sistema
            system_prediction = self.system_anomaly_model.predict(features_scaled)[0]
            if system_prediction == -1:  # Anomalia detectada
                anomaly_score = self.system_anomaly_model.decision_function(features_scaled)[0]
                ml_anomalies['system_anomalies'].append({
                    'type': 'ml_system_anomaly',
                    'severity': 'medium',
                    'anomaly_score': float(anomaly_score),
                    'description': 'Comportamento anômalo do sistema detectado por ML',
                    'timestamp': metrics.get('timestamp')
                })
            
            # Análise de padrões comportamentais
            behavioral_anomaly = self.detect_behavioral_anomaly(metrics)
            if behavioral_anomaly:
                ml_anomalies['system_anomalies'].append(behavioral_anomaly)
            
            return ml_anomalies
            
        except Exception as e:
            logger.error(f"Erro na detecção ML: {e}")
            return {}

    def detect_behavioral_anomaly(self, metrics: Dict) -> Optional[Dict]:
        """Detecta anomalias comportamentais REAIS"""
        try:
            current_hour = datetime.now().hour
            
            # Analisar padrão de uso por hora
            if str(current_hour) not in self.behavioral_patterns:
                return None
            
            expected_pattern = self.behavioral_patterns[str(current_hour)]
            current_cpu = metrics.get('system', {}).get('cpu_percent', 0)
            current_memory = metrics.get('system', {}).get('memory_percent', 0)
            
            # Comparar com padrão esperado
            cpu_deviation = abs(current_cpu - expected_pattern.get('avg_cpu', current_cpu))
            memory_deviation = abs(current_memory - expected_pattern.get('avg_memory', current_memory))
            
            # Se desvio for muito grande, é anomalia comportamental
            if cpu_deviation > 30 or memory_deviation > 25:
                return {
                    'type': 'behavioral_anomaly',
                    'severity': 'medium',
                    'cpu_deviation': cpu_deviation,
                    'memory_deviation': memory_deviation,
                    'description': f'Comportamento fora do padrão para {current_hour}:00h',
                    'timestamp': metrics.get('timestamp')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Erro na detecção comportamental: {e}")
            return None

    def update_behavioral_patterns(self, metrics: Dict):
        """Atualiza padrões comportamentais REAIS"""
        try:
            hour = str(datetime.now().hour)
            cpu_percent = metrics.get('system', {}).get('cpu_percent', 0)
            memory_percent = metrics.get('system', {}).get('memory_percent', 0)
            
            if hour not in self.behavioral_patterns:
                self.behavioral_patterns[hour] = {
                    'samples': [],
                    'avg_cpu': 0,
                    'avg_memory': 0
                }
            
            # Adicionar amostra
            self.behavioral_patterns[hour]['samples'].append({
                'cpu': cpu_percent,
                'memory': memory_percent,
                'timestamp': metrics.get('timestamp')
            })
            
            # Manter apenas últimas 30 amostras por hora
            if len(self.behavioral_patterns[hour]['samples']) > 30:
                self.behavioral_patterns[hour]['samples'] = self.behavioral_patterns[hour]['samples'][-30:]
            
            # Recalcular médias
            samples = self.behavioral_patterns[hour]['samples']
            self.behavioral_patterns[hour]['avg_cpu'] = np.mean([s['cpu'] for s in samples])
            self.behavioral_patterns[hour]['avg_memory'] = np.mean([s['memory'] for s in samples])
            
        except Exception as e:
            logger.error(f"Erro ao atualizar padrões: {e}")

    def start_monitoring(self):
        """Inicia monitoramento REAL em tempo real"""
        try:
            def monitoring_loop():
                self.monitoring_active = True
                logger.info("Iniciando monitoramento de anomalias em tempo real")
                
                while self.monitoring_active:
                    try:
                        # Coletar métricas REAIS
                        metrics = self.collect_real_system_metrics()
                        
                        if metrics:
                            # Adicionar aos dados de monitoramento
                            self.monitoring_data.append(metrics)
                            
                            # Manter apenas últimas 1440 amostras (24h se coletando a cada minuto)
                            if len(self.monitoring_data) > 1440:
                                self.monitoring_data = self.monitoring_data[-1440:]
                            
                            # Detectar anomalias
                            anomalies = self.detect_real_system_anomalies(metrics)
                            
                            # Atualizar padrões comportamentais
                            self.update_behavioral_patterns(metrics)
                            
                            # Treinar modelos se tiver dados suficientes
                            if len(self.monitoring_data) >= 100 and not self.baseline_established:
                                self.establish_baseline()
                            
                            # Salvar dados periodicamente
                            if len(self.monitoring_data) % 10 == 0:
                                self.save_monitoring_data()
                        
                        # Aguardar próxima coleta (1 minuto)
                        time.sleep(60)
                        
                    except Exception as e:
                        logger.error(f"Erro no loop de monitoramento: {e}")
                        time.sleep(60)
            
            # Executar em thread separada
            threading.Thread(target=monitoring_loop, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Erro ao iniciar monitoramento: {e}")

    def establish_baseline(self):
        """Estabelece baseline REAL baseado em dados coletados"""
        try:
            if len(self.monitoring_data) < 50:
                return False
            
            logger.info("Estabelecendo baseline de comportamento normal...")
            
            # Preparar dados para treinamento
            features_list = []
            for metrics in self.monitoring_data:
                features = self.extract_features_for_anomaly_detection(metrics)
                features_list.append(features)
            
            X = np.array(features_list)
            
            # Normalizar features
            X_scaled = self.scaler.fit_transform(X)
            
            # Treinar modelos de detecção de anomalias
            self.system_anomaly_model.fit(X_scaled)
            
            # Marcar como estabelecido
            self.baseline_established = True
            
            # Salvar modelos
            self.save_models()
            
            logger.info(f"Baseline estabelecido com {len(self.monitoring_data)} amostras")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao estabelecer baseline: {e}")
            return False

    def save_anomaly_alert(self, anomalies: Dict):
        """Salva alerta de anomalia REAL"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            alert_file = os.path.join(self.alerts_dir, f"anomaly_alert_{timestamp}.json")
            
            alert_data = {
                'timestamp': datetime.now().isoformat(),
                'anomalies': anomalies,
                'total_anomalies': sum(len(v) for v in anomalies.values() if isinstance(v, list)),
                'severity_levels': self.calculate_severity_summary(anomalies)
            }
            
            with open(alert_file, 'w', encoding='utf-8') as f:
                json.dump(alert_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Adicionar ao histórico
            self.anomaly_history.append({
                'timestamp': alert_data['timestamp'],
                'total_anomalies': alert_data['total_anomalies'],
                'severity_levels': alert_data['severity_levels'],
                'file': alert_file
            })
            
            # Manter apenas últimos 100 alertas
            if len(self.anomaly_history) > 100:
                self.anomaly_history = self.anomaly_history[-100:]
            
            logger.info(f"Alerta de anomalia salvo: {alert_file}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar alerta: {e}")

    def calculate_severity_summary(self, anomalies: Dict) -> Dict:
        """Calcula resumo de severidade das anomalias"""
        try:
            severity_count = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
            
            for category, anomaly_list in anomalies.items():
                if isinstance(anomaly_list, list):
                    for anomaly in anomaly_list:
                        severity = anomaly.get('severity', 'medium')
                        severity_count[severity] = severity_count.get(severity, 0) + 1
            
            return severity_count
            
        except Exception as e:
            logger.error(f"Erro no cálculo de severidade: {e}")
            return {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}

    def get_real_anomaly_statistics(self) -> Dict:
        """Retorna estatísticas REAIS de anomalias"""
        try:
            if not self.anomaly_history:
                return {
                    'total_alerts': 0,
                    'last_24h_alerts': 0,
                    'severity_distribution': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0},
                    'monitoring_active': self.monitoring_active,
                    'baseline_established': self.baseline_established
                }
            
            # Alertas nas últimas 24 horas
            last_24h = datetime.now() - timedelta(hours=24)
            recent_alerts = [
                alert for alert in self.anomaly_history
                if datetime.fromisoformat(alert['timestamp']) > last_24h
            ]
            
            # Distribuição de severidade total
            total_severity = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
            for alert in self.anomaly_history:
                for severity, count in alert.get('severity_levels', {}).items():
                    total_severity[severity] += count
            
            # Último alerta
            last_alert = max(self.anomaly_history, key=lambda x: x['timestamp']) if self.anomaly_history else None
            
            return {
                'total_alerts': len(self.anomaly_history),
                'last_24h_alerts': len(recent_alerts),
                'severity_distribution': total_severity,
                'last_alert': last_alert['timestamp'] if last_alert else None,
                'monitoring_active': self.monitoring_active,
                'baseline_established': self.baseline_established,
                'data_points_collected': len(self.monitoring_data),
                'behavioral_patterns_learned': len(self.behavioral_patterns)
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {'error': str(e)}

    def create_anomaly_report_real(self, hours: int = 24) -> Dict:
        """Cria relatório REAL de anomalias"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # Filtrar alertas do período
            period_alerts = [
                alert for alert in self.anomaly_history
                if start_time <= datetime.fromisoformat(alert['timestamp']) <= end_time
            ]
            
            # Carregar detalhes dos alertas
            detailed_anomalies = []
            for alert in period_alerts:
                try:
                    with open(alert['file'], 'r', encoding='utf-8') as f:
                        alert_data = json.load(f)
                        detailed_anomalies.append(alert_data)
                except:
                    continue
            
            # Análise estatística
            total_anomalies = sum(alert['total_anomalies'] for alert in period_alerts)
            
            # Análise por categoria
            category_stats = {}
            severity_stats = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
            
            for alert_data in detailed_anomalies:
                for category, anomaly_list in alert_data.get('anomalies', {}).items():
                    if isinstance(anomaly_list, list):
                        category_stats[category] = category_stats.get(category, 0) + len(anomaly_list)
                        
                        for anomaly in anomaly_list:
                            severity = anomaly.get('severity', 'medium')
                            severity_stats[severity] += 1
            
            # Tendências (comparar com período anterior)
            prev_start = start_time - timedelta(hours=hours)
            prev_alerts = [
                alert for alert in self.anomaly_history
                if prev_start <= datetime.fromisoformat(alert['timestamp']) < start_time
            ]
            
            prev_total = sum(alert['total_anomalies'] for alert in prev_alerts)
            trend = "stable"
            if total_anomalies > prev_total * 1.2:
                trend = "increasing"
            elif total_anomalies < prev_total * 0.8:
                trend = "decreasing"
            
            # Análise de ameaças
            threat_level = "low"
            if severity_stats['critical'] > 0:
                threat_level = "critical"
            elif severity_stats['high'] > 5:
                threat_level = "high"
            elif severity_stats['medium'] > 10:
                threat_level = "medium"
            
            return {
                'report_period': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'hours': hours
                },
                'summary': {
                    'total_anomalies': total_anomalies,
                    'total_alerts': len(period_alerts),
                    'trend': trend,
                    'threat_level': threat_level
                },
                'distribution': {
                    'by_category': category_stats,
                    'by_severity': severity_stats
                },
                'threat_analysis': {
                    'threat_level': threat_level,
                    'risk_score': min(100, (severity_stats['critical'] * 10 + 
                                           severity_stats['high'] * 5 + 
                                           severity_stats['medium'] * 2 + 
                                           severity_stats['low'])),
                    'recommendations': self.generate_threat_recommendations(severity_stats)
                },
                'system_health': self.calculate_system_health_score(),
                'detailed_anomalies': detailed_anomalies[-10:],  # Últimas 10 para não sobrecarregar
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar relatório: {e}")
            return {'error': str(e)}

    def generate_threat_recommendations(self, severity_stats: Dict) -> List[str]:
        """Gera recomendações REAIS baseadas em ameaças detectadas"""
        try:
            recommendations = []
            
            if severity_stats['critical'] > 0:
                recommendations.append("Ação imediata necessária - anomalias críticas detectadas")
                recommendations.append("Verificar logs de sistema detalhadamente")
                recommendations.append("Considerar reinicialização do sistema")
            
            if severity_stats['high'] > 3:
                recommendations.append("Investigar processos com alto uso de recursos")
                recommendations.append("Verificar integridade do sistema")
            
            if severity_stats['medium'] > 10:
                recommendations.append("Monitoramento mais frequente recomendado")
                recommendations.append("Otimizar configurações do sistema")
            
            if severity_stats['low'] > 20:
                recommendations.append("Ajustar limites de detecção")
                recommendations.append("Revisar padrões de uso normal")
            
            if not any(severity_stats.values()):
                recommendations.append("Sistema funcionando dentro dos parâmetros normais")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Erro ao gerar recomendações: {e}")
            return ["Erro ao analisar ameaças"]

    def calculate_system_health_score(self) -> float:
        """Calcula score REAL de saúde do sistema"""
        try:
            if not self.monitoring_data:
                return 50.0
            
            # Pegar últimas métricas
            latest_metrics = self.monitoring_data[-1]
            system = latest_metrics.get('system', {})
            
            # Calcular score baseado em métricas reais
            cpu_score = max(0, 100 - system.get('cpu_percent', 0))
            memory_score = max(0, 100 - system.get('memory_percent', 0))
            disk_score = max(0, 100 - system.get('disk_percent', 0))
            swap_score = max(0, 100 - system.get('swap_percent', 0))
            
            # Penalizar se há muitas anomalias recentes
            recent_anomalies = len([
                alert for alert in self.anomaly_history[-10:]  # Últimos 10 alertas
            ])
            anomaly_penalty = min(30, recent_anomalies * 3)
            
            # Score final
            health_score = (cpu_score * 0.25 + memory_score * 0.25 + 
                          disk_score * 0.25 + swap_score * 0.25 - anomaly_penalty)
            
            return max(0, min(100, health_score))
            
        except Exception as e:
            logger.error(f"Erro no cálculo de saúde: {e}")
            return 50.0

    def save_monitoring_data(self):
        """Salva dados de monitoramento REAIS"""
        try:
            with open(self.monitoring_data_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'monitoring_data': self.monitoring_data,
                    'behavioral_patterns': self.behavioral_patterns,
                    'alert_thresholds': self.alert_thresholds,
                    'baseline_established': self.baseline_established
                }, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Erro ao salvar dados de monitoramento: {e}")

    def load_monitoring_data(self):
        """Carrega dados de monitoramento REAIS"""
        try:
            if os.path.exists(self.monitoring_data_file):
                with open(self.monitoring_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.monitoring_data = data.get('monitoring_data', [])
                    self.behavioral_patterns = data.get('behavioral_patterns', {})
                    self.alert_thresholds.update(data.get('alert_thresholds', {}))
                    self.baseline_established = data.get('baseline_established', False)
                
                logger.info(f"Carregados {len(self.monitoring_data)} pontos de monitoramento")
        except Exception as e:
            logger.error(f"Erro ao carregar dados de monitoramento: {e}")

    def save_models(self):
        """Salva modelos treinados"""
        try:
            model_files = {
                'system_anomaly_model.pkl': self.system_anomaly_model,
                'process_anomaly_model.pkl': self.process_anomaly_model,
                'network_anomaly_model.pkl': self.network_anomaly_model,
                'scaler.pkl': self.scaler
            }
            
            for filename, model in model_files.items():
                filepath = os.path.join(self.models_dir, filename)
                with open(filepath, 'wb') as f:
                    pickle.dump(model, f)
            
            logger.info("Modelos de detecção salvos")
            
        except Exception as e:
            logger.error(f"Erro ao salvar modelos: {e}")

    def load_models(self):
        """Carrega modelos treinados"""
        try:
            model_files = {
                'system_anomaly_model.pkl': 'system_anomaly_model',
                'process_anomaly_model.pkl': 'process_anomaly_model', 
                'network_anomaly_model.pkl': 'network_anomaly_model',
                'scaler.pkl': 'scaler'
            }
            
            all_exist = all(
                os.path.exists(os.path.join(self.models_dir, filename))
                for filename in model_files.keys()
            )
            
            if all_exist:
                for filename, attr_name in model_files.items():
                    filepath = os.path.join(self.models_dir, filename)
                    with open(filepath, 'rb') as f:
                        setattr(self, attr_name, pickle.load(f))
                
                self.baseline_established = True
                logger.info("Modelos de detecção carregados")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelos: {e}")
            return False

    def stop_monitoring(self):
        """Para o monitoramento"""
        self.monitoring_active = False
        logger.info("Monitoramento de anomalias parado")

# Funções utilitárias REAIS
def quick_anomaly_scan() -> Dict:
    """Scan rápido REAL de anomalias"""
    try:
        detector = AnomalyDetector()
        metrics = detector.collect_real_system_metrics()
        anomalies = detector.detect_real_system_anomalies(metrics)
        
        # Contar anomalias
        total_anomalies = sum(len(v) for v in anomalies.values() if isinstance(v, list))
        
        # Determinar nível de ameaça
        critical_count = sum(1 for category in anomalies.values() 
                           if isinstance(category, list)
                           for anomaly in category 
                           if anomaly.get('severity') == 'critical')
        
        if critical_count > 0:
            threat_level = 'crítico'
        elif total_anomalies > 5:
            threat_level = 'alto'
        elif total_anomalies > 0:
            threat_level = 'médio'
        else:
            threat_level = 'baixo'
        
        # Gerar recomendações
        recommendations = []
        if total_anomalies == 0:
            recommendations.append("Sistema funcionando normalmente")
        else:
            if any(a.get('type') == 'high_cpu_usage' for cat in anomalies.values() 
                   if isinstance(cat, list) for a in cat):
                recommendations.append("Verificar processos com alto uso de CPU")
            
            if any(a.get('type') == 'high_memory_usage' for cat in anomalies.values() 
                   if isinstance(cat, list) for a in cat):
                recommendations.append("Liberar memória RAM")
            
            if any(a.get('type') == 'high_disk_usage' for cat in anomalies.values() 
                   if isinstance(cat, list) for a in cat):
                recommendations.append("Liberar espaço em disco urgentemente")
        
        return {
            'anomalies_detected': total_anomalies,
            'threat_level': threat_level,
            'risk_score': min(100, total_anomalies * 10 + critical_count * 20),
            'anomalies': anomalies,
            'recommendations': recommendations,
            'scan_timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro no scan rápido: {e}")
        return {'error': str(e)}

def start_anomaly_monitoring() -> bool:
    """Inicia monitoramento REAL de anomalias"""
    try:
        detector = AnomalyDetector()
        detector.start_monitoring()
        return True
    except Exception as e:
        logger.error(f"Erro ao iniciar monitoramento: {e}")
        return False

# Exemplo de uso
if __name__ == "__main__":
    print("🔍 Testando Anomaly Detector 100% REAL...")
    
    detector = AnomalyDetector()
    
    # Coletar métricas reais
    print("📊 Coletando métricas reais do sistema...")
    metrics = detector.collect_real_system_metrics()
    print(f"CPU: {metrics['system']['cpu_percent']:.1f}%")
    print(f"Memória: {metrics['system']['memory_percent']:.1f}%")
    print(f"Disco: {metrics['system']['disk_percent']:.1f}%")
    print(f"Processos: {metrics['processes']['total']}")
    
    # Detectar anomalias reais
    print("🔍 Detectando anomalias...")
    anomalies = detector.detect_real_system_anomalies(metrics)
    
    total = sum(len(v) for v in anomalies.values() if isinstance(v, list))
    print(f"Anomalias detectadas: {total}")
    
    for category, anomaly_list in anomalies.items():
        if isinstance(anomaly_list, list) and anomaly_list:
            print(f"- {category}: {len(anomaly_list)} anomalia(s)")
    
    print("✅ Teste concluído - 100% baseado em dados reais do sistema!")