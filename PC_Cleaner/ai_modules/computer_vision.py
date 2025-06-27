# ai_modules/computer_vision.py - VERSÃO 100% REAL
import cv2
import numpy as np
import pytesseract
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import time
from pathlib import Path
import hashlib
from PIL import Image, ImageGrab
import threading

# Configuração do pytesseract (ajustar path se necessário)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('computer_vision')

class ComputerVision:
    """Sistema de Computer Vision 100% REAL - Análise visual completa"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.screenshots_dir = os.path.join(data_dir, "screenshots")
        self.analysis_dir = os.path.join(data_dir, "cv_analysis")
        
        # Criar diretórios
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.analysis_dir, exist_ok=True)
        
        # Histórico de análises REAIS
        self.analysis_history = []
        self.last_screenshot = None
        self.last_analysis = None
        
        # Configurações de OCR
        self.ocr_config = r'--oem 3 --psm 6 -l por+eng'
        
        # Carregar histórico existente
        self.load_analysis_history()

    def capture_screenshot(self) -> Optional[np.ndarray]:
        """Captura screenshot REAL da tela"""
        try:
            # Capturar usando PIL
            screenshot_pil = ImageGrab.grab()
            
            # Converter para numpy array (OpenCV format)
            screenshot_np = np.array(screenshot_pil)
            screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            
            # Salvar screenshot com timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = os.path.join(self.screenshots_dir, f"screenshot_{timestamp}.png")
            cv2.imwrite(screenshot_path, screenshot_bgr)
            
            self.last_screenshot = screenshot_bgr
            logger.info(f"Screenshot capturado: {screenshot_path}")
            
            return screenshot_bgr
            
        except Exception as e:
            logger.error(f"Erro ao capturar screenshot: {e}")
            return None

    def analyze_desktop_organization_real(self, image: np.ndarray = None) -> Dict:
        """Análise REAL de organização do desktop"""
        try:
            if image is None:
                image = self.capture_screenshot()
                if image is None:
                    return {'error': 'Falha ao capturar screenshot'}
            
            height, width = image.shape[:2]
            
            # Análise REAL de cores dominantes
            colors_analysis = self.analyze_real_color_distribution(image)
            
            # Detecção REAL de ícones usando contornos
            icons_analysis = self.detect_real_icons(image)
            
            # Detecção REAL de janelas usando bordas
            windows_analysis = self.detect_real_windows(image)
            
            # Análise REAL de organização espacial
            spatial_analysis = self.analyze_real_spatial_organization(image)
            
            # Calcular score REAL de organização
            clutter_score = self.calculate_real_clutter_score(icons_analysis, windows_analysis, spatial_analysis)
            
            # Gerar recomendações REAIS
            recommendations = self.generate_real_organization_recommendations(
                clutter_score, icons_analysis, windows_analysis
            )
            
            analysis_result = {
                'timestamp': datetime.now().isoformat(),
                'screen_resolution': f"{width}x{height}",
                'clutter_score': clutter_score,
                'icon_analysis': icons_analysis,
                'window_analysis': windows_analysis,
                'color_scheme': colors_analysis,
                'spatial_organization': spatial_analysis,
                'recommendations': recommendations
            }
            
            # Salvar análise
            self.save_analysis_result(analysis_result, 'desktop_organization')
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Erro na análise de organização: {e}")
            return {'error': str(e)}

    def analyze_real_color_distribution(self, image: np.ndarray) -> Dict:
        """Análise REAL da distribuição de cores"""
        try:
            # Converter para HSV para melhor análise
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Calcular histograma REAL
            hist_h = cv2.calcHist([hsv], [0], None, [180], [0, 180])
            hist_s = cv2.calcHist([hsv], [1], None, [256], [0, 256])
            hist_v = cv2.calcHist([hsv], [2], None, [256], [0, 256])
            
            # Encontrar cor dominante REAL
            dominant_hue = np.argmax(hist_h)
            dominant_saturation = np.argmax(hist_s)
            dominant_value = np.argmax(hist_v)
            
            # Calcular variância REAL das cores
            color_variance = np.var(hsv.reshape(-1, 3), axis=0)
            
            # Detectar esquema de cores REAL
            avg_saturation = np.mean(hsv[:, :, 1])
            avg_value = np.mean(hsv[:, :, 2])
            
            # Classificar esquema de cores
            if avg_saturation < 50:
                color_scheme = "Monocromático"
            elif avg_saturation < 100:
                color_scheme = "Baixa saturação"
            else:
                color_scheme = "Alta saturação"
            
            return {
                'dominant_hue': int(dominant_hue),
                'dominant_saturation': int(dominant_saturation),
                'dominant_value': int(dominant_value),
                'color_variance': [float(cv) for cv in color_variance],
                'average_saturation': float(avg_saturation),
                'average_brightness': float(avg_value),
                'color_scheme': color_scheme,
                'total_unique_colors': len(np.unique(image.reshape(-1, 3), axis=0))
            }
            
        except Exception as e:
            logger.error(f"Erro na análise de cores: {e}")
            return {}

    def detect_real_icons(self, image: np.ndarray) -> Dict:
        """Detecção REAL de ícones usando OpenCV"""
        try:
            # Converter para escala de cinza
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Aplicar threshold adaptativo
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY, 11, 2)
            
            # Encontrar contornos
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filtrar contornos que podem ser ícones (tamanho típico)
            icon_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h
                
                # Critérios REAIS para ícones (tamanho típico 16x16 a 128x128 pixels)
                if (256 <= area <= 16384 and  # Área entre 16² e 128²
                    0.5 <= aspect_ratio <= 2.0):  # Proporção aproximadamente quadrada
                    icon_contours.append({
                        'area': int(area),
                        'position': (int(x), int(y)),
                        'size': (int(w), int(h)),
                        'aspect_ratio': float(aspect_ratio)
                    })
            
            # Análise de distribuição REAL
            if icon_contours:
                positions = [icon['position'] for icon in icon_contours]
                x_coords = [pos[0] for pos in positions]
                y_coords = [pos[1] for pos in positions]
                
                # Calcular clusters REAIS
                clusters = self.calculate_real_spatial_clusters(positions)
                
                distribution = "Concentrado" if len(clusters) <= 2 else "Espalhado"
            else:
                distribution = "Nenhum ícone detectado"
                clusters = 0
            
            return {
                'total_icons': len(icon_contours),
                'desktop_icons': len([icon for icon in icon_contours 
                                    if icon['position'][1] < image.shape[0] * 0.9]),  # Não na barra de tarefas
                'clusters': clusters,
                'distribution': distribution,
                'icon_details': icon_contours[:20],  # Primeiros 20 para não sobrecarregar
                'average_icon_size': np.mean([icon['area'] for icon in icon_contours]) if icon_contours else 0
            }
            
        except Exception as e:
            logger.error(f"Erro na detecção de ícones: {e}")
            return {'total_icons': 0}

    def detect_real_windows(self, image: np.ndarray) -> Dict:
        """Detecção REAL de janelas usando análise de bordas"""
        try:
            # Converter para escala de cinza
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detectar bordas usando Canny
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Detectar linhas (bordas de janelas)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, 
                                   minLineLength=100, maxLineGap=10)
            
            # Agrupar linhas em retângulos (janelas)
            windows = []
            if lines is not None:
                # Processar linhas para encontrar retângulos
                horizontal_lines = []
                vertical_lines = []
                
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                    
                    if abs(angle) < 10 or abs(angle) > 170:  # Linha horizontal
                        horizontal_lines.append(line[0])
                    elif abs(abs(angle) - 90) < 10:  # Linha vertical
                        vertical_lines.append(line[0])
                
                # Encontrar intersecções para formar retângulos
                windows = self.find_real_window_rectangles(horizontal_lines, vertical_lines, image.shape)
            
            # Análise de sobreposição REAL
            overlapped = self.calculate_real_window_overlap(windows)
            
            return {
                'total_windows': len(windows),
                'visible_windows': len([w for w in windows if w['area'] > 10000]),  # Janelas grandes o suficiente
                'minimized_windows': max(0, len(windows) - len([w for w in windows if w['area'] > 10000])),
                'overlapped_windows': overlapped,
                'window_details': windows[:10],  # Primeiras 10 janelas
                'screen_coverage': sum([w['area'] for w in windows]) / (image.shape[0] * image.shape[1])
            }
            
        except Exception as e:
            logger.error(f"Erro na detecção de janelas: {e}")
            return {'total_windows': 0}

    def calculate_real_spatial_clusters(self, positions: List[Tuple[int, int]]) -> int:
        """Calcula clusters espaciais REAIS usando distância euclidiana"""
        try:
            if len(positions) < 2:
                return len(positions)
            
            clusters = []
            cluster_threshold = 100  # pixels
            
            for pos in positions:
                assigned = False
                for cluster in clusters:
                    # Calcular distância mínima ao cluster
                    min_dist = min([np.sqrt((pos[0] - cp[0])**2 + (pos[1] - cp[1])**2) 
                                   for cp in cluster])
                    if min_dist <= cluster_threshold:
                        cluster.append(pos)
                        assigned = True
                        break
                
                if not assigned:
                    clusters.append([pos])
            
            return len(clusters)
            
        except Exception as e:
            logger.error(f"Erro no cálculo de clusters: {e}")
            return 1

    def find_real_window_rectangles(self, h_lines: List, v_lines: List, shape: Tuple) -> List[Dict]:
        """Encontra retângulos REAIS a partir de linhas horizontais e verticais"""
        try:
            windows = []
            min_window_size = 5000  # pixels²
            
            # Simplificado: usar contornos para detectar retângulos
            # Em vez de tentar formar retângulos a partir de linhas individuais
            
            # Criar uma imagem das linhas
            line_img = np.zeros((shape[0], shape[1]), dtype=np.uint8)
            
            for line in h_lines + v_lines:
                cv2.line(line_img, (line[0], line[1]), (line[2], line[3]), 255, 2)
            
            # Encontrar contornos fechados
            contours, _ = cv2.findContours(line_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > min_window_size:
                    x, y, w, h = cv2.boundingRect(contour)
                    windows.append({
                        'position': (int(x), int(y)),
                        'size': (int(w), int(h)),
                        'area': int(area),
                        'aspect_ratio': float(w/h) if h > 0 else 1.0
                    })
            
            return windows
            
        except Exception as e:
            logger.error(f"Erro ao encontrar retângulos: {e}")
            return []

    def calculate_real_window_overlap(self, windows: List[Dict]) -> int:
        """Calcula sobreposição REAL entre janelas"""
        try:
            overlapped_count = 0
            
            for i, window1 in enumerate(windows):
                for j, window2 in enumerate(windows[i+1:], i+1):
                    # Verificar se há sobreposição
                    x1, y1 = window1['position']
                    w1, h1 = window1['size']
                    x2, y2 = window2['position']
                    w2, h2 = window2['size']
                    
                    # Calcular área de sobreposição
                    overlap_x = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
                    overlap_y = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
                    overlap_area = overlap_x * overlap_y
                    
                    if overlap_area > 0:
                        overlapped_count += 1
            
            return overlapped_count
            
        except Exception as e:
            logger.error(f"Erro no cálculo de sobreposição: {e}")
            return 0

    def analyze_real_spatial_organization(self, image: np.ndarray) -> Dict:
        """Análise REAL de organização espacial"""
        try:
            height, width = image.shape[:2]
            
            # Dividir imagem em quadrantes
            quad_h, quad_w = height // 2, width // 2
            
            quadrants = {
                'top_left': image[0:quad_h, 0:quad_w],
                'top_right': image[0:quad_h, quad_w:width],
                'bottom_left': image[quad_h:height, 0:quad_w],
                'bottom_right': image[quad_h:height, quad_w:width]
            }
            
            # Analisar densidade em cada quadrante
            quadrant_analysis = {}
            for name, quad in quadrants.items():
                # Calcular densidade baseada em variância de cores
                gray_quad = cv2.cvtColor(quad, cv2.COLOR_BGR2GRAY)
                density = np.var(gray_quad)
                quadrant_analysis[name] = {
                    'density': float(density),
                    'avg_brightness': float(np.mean(gray_quad))
                }
            
            # Calcular simetria REAL
            left_half = image[:, :width//2]
            right_half = cv2.flip(image[:, width//2:], 1)  # Flip horizontal
            
            # Redimensionar para mesmo tamanho se necessário
            min_width = min(left_half.shape[1], right_half.shape[1])
            left_half = left_half[:, :min_width]
            right_half = right_half[:, :min_width]
            
            # Calcular diferença
            diff = cv2.absdiff(left_half, right_half)
            symmetry_score = 100 - (np.mean(diff) / 255 * 100)
            
            return {
                'quadrant_density': quadrant_analysis,
                'symmetry_score': float(symmetry_score),
                'layout_complexity': self.calculate_real_layout_complexity(image),
                'balance_score': self.calculate_real_balance_score(quadrant_analysis)
            }
            
        except Exception as e:
            logger.error(f"Erro na análise espacial: {e}")
            return {}

    def calculate_real_layout_complexity(self, image: np.ndarray) -> float:
        """Calcula complexidade REAL do layout"""
        try:
            # Converter para escala de cinza
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calcular entropia como medida de complexidade
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist = hist.flatten()
            hist = hist / hist.sum()  # Normalizar
            
            # Calcular entropia
            entropy = -np.sum([p * np.log2(p) for p in hist if p > 0])
            
            # Normalizar para 0-100
            complexity = min(100, (entropy / 8) * 100)  # 8 é aprox. máximo teórico
            
            return float(complexity)
            
        except Exception as e:
            logger.error(f"Erro no cálculo de complexidade: {e}")
            return 50.0

    def calculate_real_balance_score(self, quadrant_analysis: Dict) -> float:
        """Calcula score REAL de balanceamento visual"""
        try:
            densities = [quad['density'] for quad in quadrant_analysis.values()]
            
            # Calcular variância da densidade entre quadrantes
            density_variance = np.var(densities)
            
            # Score de balance (menor variância = melhor balance)
            # Normalizar para 0-100 (100 = perfeitamente balanceado)
            max_variance = 10000  # Valor de referência
            balance_score = max(0, 100 - (density_variance / max_variance * 100))
            
            return float(balance_score)
            
        except Exception as e:
            logger.error(f"Erro no cálculo de balance: {e}")
            return 50.0

    def calculate_real_clutter_score(self, icons: Dict, windows: Dict, spatial: Dict) -> float:
        """Calcula score REAL de desordem (0=organizado, 10=muito bagunçado)"""
        try:
            clutter_factors = []
            
            # Fator de ícones
            icon_density = icons.get('total_icons', 0) / 100  # Normalizar
            clutter_factors.append(min(3, icon_density))
            
            # Fator de janelas sobrepostas
            overlap_factor = windows.get('overlapped_windows', 0) / 5  # Normalizar
            clutter_factors.append(min(2, overlap_factor))
            
            # Fator de complexidade espacial
            complexity = spatial.get('layout_complexity', 50) / 100
            clutter_factors.append(complexity * 2)
            
            # Fator de balance
            balance = spatial.get('balance_score', 50) / 100
            clutter_factors.append((1 - balance) * 3)  # Menos balance = mais clutter
            
            # Score final
            clutter_score = sum(clutter_factors)
            
            return min(10.0, max(0.0, clutter_score))
            
        except Exception as e:
            logger.error(f"Erro no cálculo de clutter: {e}")
            return 5.0

    def generate_real_organization_recommendations(self, clutter_score: float, 
                                                 icons: Dict, windows: Dict) -> List[str]:
        """Gera recomendações REAIS baseadas na análise"""
        try:
            recommendations = []
            
            # Recomendações baseadas em clutter score
            if clutter_score > 7:
                recommendations.append("Desktop muito desorganizado - reorganização necessária")
            elif clutter_score > 5:
                recommendations.append("Desktop moderadamente desorganizado")
            elif clutter_score < 2:
                recommendations.append("Desktop muito bem organizado")
            
            # Recomendações baseadas em ícones
            if icons.get('total_icons', 0) > 50:
                recommendations.append("Muitos ícones no desktop - considere organizar em pastas")
            
            if icons.get('distribution') == "Espalhado":
                recommendations.append("Ícones espalhados - agrupe por categoria")
            
            # Recomendações baseadas em janelas
            if windows.get('overlapped_windows', 0) > 3:
                recommendations.append("Muitas janelas sobrepostas - organize as janelas abertas")
            
            if windows.get('total_windows', 0) > 10:
                recommendations.append("Muitas janelas abertas - feche aplicações desnecessárias")
            
            # Recomendações gerais
            if not recommendations:
                recommendations.append("Desktop bem organizado - manter organização atual")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Erro ao gerar recomendações: {e}")
            return ["Erro ao analisar organização"]

    def extract_text_from_screen_real(self, image: np.ndarray = None) -> Dict:
        """Extração REAL de texto usando OCR"""
        try:
            if image is None:
                image = self.capture_screenshot()
                if image is None:
                    return {'error': 'Falha ao capturar screenshot'}
            
            # Pré-processamento para melhorar OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Aplicar threshold para melhorar contraste
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Usar pytesseract para extrair texto REAL
            try:
                # Extrair texto com configurações otimizadas
                text = pytesseract.image_to_string(thresh, config=self.ocr_config)
                
                # Extrair dados detalhados
                data = pytesseract.image_to_data(thresh, config=self.ocr_config, output_type=pytesseract.Output.DICT)
                
                # Processar resultados
                words = []
                confidences = []
                
                for i in range(len(data['text'])):
                    word = data['text'][i].strip()
                    conf = data['conf'][i]
                    
                    if word and conf > 30:  # Filtrar palavras com baixa confiança
                        words.append({
                            'text': word,
                            'confidence': conf,
                            'position': (data['left'][i], data['top'][i]),
                            'size': (data['width'][i], data['height'][i])
                        })
                        confidences.append(conf)
                
                # Estatísticas REAIS
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                word_count = len([w for w in text.split() if w.strip()])
                
                result = {
                    'text': text,
                    'lines': lines,
                    'words': words,
                    'word_count': word_count,
                    'line_count': len(lines),
                    'confidence': np.mean(confidences) if confidences else 0,
                    'language': 'por+eng',  # Configurado para português e inglês
                    'extraction_timestamp': datetime.now().isoformat()
                }
                
                # Salvar resultado
                self.save_analysis_result(result, 'ocr_extraction')
                
                return result
                
            except Exception as ocr_error:
                logger.error(f"Erro no OCR: {ocr_error}")
                return {
                    'error': f'Erro no OCR: {ocr_error}',
                    'text': '',
                    'word_count': 0
                }
            
        except Exception as e:
            logger.error(f"Erro na extração de texto: {e}")
            return {'error': str(e)}

    def detect_visual_problems_real(self, image: np.ndarray = None) -> Dict:
        """Detecção REAL de problemas visuais"""
        try:
            if image is None:
                image = self.capture_screenshot()
                if image is None:
                    return {'error': 'Falha ao capturar screenshot'}
            
            problems = {
                'error_dialogs': [],
                'suspicious_windows': [],
                'visual_anomalies': [],
                'performance_indicators': []
            }
            
            # Detectar diálogos de erro usando template matching e análise de cores
            error_dialogs = self.detect_real_error_dialogs(image)
            problems['error_dialogs'] = error_dialogs
            
            # Detectar janelas suspeitas
            suspicious_windows = self.detect_real_suspicious_windows(image)
            problems['suspicious_windows'] = suspicious_windows
            
            # Detectar anomalias visuais
            visual_anomalies = self.detect_real_visual_anomalies(image)
            problems['visual_anomalies'] = visual_anomalies
            
            # Detectar indicadores de performance
            performance_indicators = self.detect_real_performance_indicators(image)
            problems['performance_indicators'] = performance_indicators
            
            # Salvar análise
            analysis_result = {
                'timestamp': datetime.now().isoformat(),
                'problems_detected': problems,
                'total_issues': (len(error_dialogs) + len(suspicious_windows) + 
                               len(visual_anomalies) + len(performance_indicators))
            }
            
            self.save_analysis_result(analysis_result, 'visual_problems')
            
            return problems
            
        except Exception as e:
            logger.error(f"Erro na detecção de problemas: {e}")
            return {'error': str(e)}

    def detect_real_error_dialogs(self, image: np.ndarray) -> List[Dict]:
        """Detecta diálogos de erro REAIS"""
        try:
            error_dialogs = []
            
            # Converter para HSV para detecção de cores
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Detectar cores típicas de erro (vermelho)
            red_lower = np.array([0, 50, 50])
            red_upper = np.array([10, 255, 255])
            red_mask = cv2.inRange(hsv, red_lower, red_upper)
            
            # Encontrar contornos vermelhos
            contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # Filtrar pequenos ruídos
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Extrair região para análise
                    region = image[y:y+h, x:x+w]
                    
                    # Tentar extrair texto da região
                    try:
                        text = pytesseract.image_to_string(region, config=self.ocr_config)
                        
                        # Verificar se contém palavras relacionadas a erro
                        error_keywords = ['error', 'erro', 'falha', 'problem', 'warning', 'aviso']
                        
                        if any(keyword in text.lower() for keyword in error_keywords):
                            error_dialogs.append({
                                'type': 'error_dialog',
                                'position': (int(x), int(y)),
                                'size': (int(w), int(h)),
                                'text': text.strip(),
                                'description': 'Diálogo de erro detectado'
                            })
                    except:
                        # Se OCR falhar, ainda reportar como possível erro baseado na cor
                        error_dialogs.append({
                            'type': 'potential_error',
                            'position': (int(x), int(y)),
                            'size': (int(w), int(h)),
                            'description': 'Região vermelha suspeita detectada'
                        })
            
            return error_dialogs
            
        except Exception as e:
            logger.error(f"Erro na detecção de diálogos: {e}")
            return []

    def detect_real_suspicious_windows(self, image: np.ndarray) -> List[Dict]:
        """Detecta janelas suspeitas REAIS"""
        try:
            suspicious = []
            
            # Detectar janelas muito pequenas ou muito grandes
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            height, width = image.shape[:2]
            
            for contour in contours:
                area = cv2.contourArea(contour)
                x, y, w, h = cv2.boundingRect(contour)
                
                # Detectar janelas suspeitas baseado em tamanho
                window_area_ratio = area / (width * height)
                
                if window_area_ratio > 0.8:  # Janela muito grande (tela cheia suspeita)
                    suspicious.append({
                        'type': 'oversized_window',
                        'position': (int(x), int(y)),
                        'size': (int(w), int(h)),
                        'description': 'Janela ocupando quase toda a tela'
                    })
                elif 1000 < area < 5000:  # Janelas muito pequenas
                    suspicious.append({
                        'type': 'tiny_window',
                        'position': (int(x), int(y)),
                        'size': (int(w), int(h)),
                        'description': 'Janela anormalmente pequena'
                    })
            
            return suspicious
            
        except Exception as e:
            logger.error(f"Erro na detecção de janelas suspeitas: {e}")
            return []

    def detect_real_visual_anomalies(self, image: np.ndarray) -> List[Dict]:
        """Detecta anomalias visuais REAIS"""
        try:
            anomalies = []
            
            # Detectar pixels mortos (pretos em grandes áreas)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            black_pixels = np.sum(gray == 0)
            total_pixels = gray.shape[0] * gray.shape[1]
            
            if black_pixels / total_pixels > 0.1:  # Mais de 10% preto
                anomalies.append({
                    'type': 'excessive_black_areas',
                    'description': f'Muitas áreas pretas detectadas ({black_pixels/total_pixels:.1%})',
                    'severity': 'medium'
                })
            
            # Detectar linhas estranhas ou artifacts
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=200, maxLineGap=5)
            
            if lines is not None and len(lines) > 100:
                anomalies.append({
                    'type': 'excessive_lines',
                    'description': f'Muitas linhas detectadas ({len(lines)}), possível artifact visual',
                    'severity': 'low'
                })
            
            # Detectar cores anômalas
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Detectar saturação muito alta (cores artificiais)
            high_saturation = np.sum(hsv[:, :, 1] > 200)
            if high_saturation / total_pixels > 0.3:
                anomalies.append({
                    'type': 'unnatural_colors',
                    'description': 'Cores muito saturadas detectadas, possível problema de display',
                    'severity': 'medium'
                })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Erro na detecção de anomalias: {e}")
            return []

    def detect_real_performance_indicators(self, image: np.ndarray) -> List[Dict]:
        """Detecta indicadores REAIS de problemas de performance"""
        try:
            indicators = []
            
            # Detectar indicadores visuais de lag ou travamento
            
            # 1. Detectar cursor de loading/wait
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Template matching para cursor de loading (simplificado)
            # Detectar áreas circulares que podem ser spinners
            circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20, 
                                     param1=50, param2=30, minRadius=5, maxRadius=50)
            
            if circles is not None and len(circles[0]) > 2:
                indicators.append({
                    'type': 'loading_indicators',
                    'description': f'{len(circles[0])} possíveis indicadores de carregamento detectados',
                    'severity': 'low'
                })
            
            # 2. Detectar janelas "Não Respondendo"
            # Usar OCR para detectar texto relacionado
            try:
                text = pytesseract.image_to_string(image, config=self.ocr_config)
                freeze_keywords = ['não responde', 'not responding', 'travado', 'frozen']
                
                if any(keyword in text.lower() for keyword in freeze_keywords):
                    indicators.append({
                        'type': 'unresponsive_application',
                        'description': 'Aplicação não responsiva detectada',
                        'severity': 'high'
                    })
            except:
                pass
            
            # 3. Detectar alto uso de CPU visual (ventilador, temperatura)
            # Buscar por indicadores visuais de temperatura/CPU
            red_areas = cv2.inRange(cv2.cvtColor(image, cv2.COLOR_BGR2HSV), 
                                   np.array([0, 100, 100]), np.array([10, 255, 255]))
            red_ratio = np.sum(red_areas > 0) / (image.shape[0] * image.shape[1])
            
            if red_ratio > 0.05:  # Mais de 5% vermelho pode indicar alertas
                indicators.append({
                    'type': 'warning_indicators',
                    'description': 'Possíveis indicadores de alerta visual detectados',
                    'severity': 'medium'
                })
            
            return indicators
            
        except Exception as e:
            logger.error(f"Erro na detecção de indicadores: {e}")
            return []

    def compare_screenshots_real(self, image1_path: str, image2_path: str) -> Dict:
        """Comparação REAL entre dois screenshots"""
        try:
            # Carregar imagens
            img1 = cv2.imread(image1_path)
            img2 = cv2.imread(image2_path)
            
            if img1 is None or img2 is None:
                return {'error': 'Não foi possível carregar uma ou ambas as imagens'}
            
            # Redimensionar para mesmo tamanho se necessário
            h1, w1 = img1.shape[:2]
            h2, w2 = img2.shape[:2]
            
            if (h1, w1) != (h2, w2):
                # Redimensionar para o menor tamanho comum
                min_h, min_w = min(h1, h2), min(w1, w2)
                img1 = cv2.resize(img1, (min_w, min_h))
                img2 = cv2.resize(img2, (min_w, min_h))
            
            # Calcular diferença REAL
            diff = cv2.absdiff(img1, img2)
            
            # Calcular métricas de similaridade
            mse = np.mean((img1.astype(float) - img2.astype(float)) ** 2)
            similarity_score = 1 - (mse / (255 ** 2))  # Normalizar para 0-1
            
            # Detectar regiões de mudança
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            _, thresh_diff = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)
            
            # Encontrar contornos das diferenças
            contours, _ = cv2.findContours(thresh_diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            change_regions = []
            total_change_area = 0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 100:  # Filtrar mudanças pequenas
                    x, y, w, h = cv2.boundingRect(contour)
                    change_regions.append({
                        'position': (int(x), int(y)),
                        'size': (int(w), int(h)),
                        'area': int(area),
                        'description': f'Mudança detectada em ({x}, {y})'
                    })
                    total_change_area += area
            
            # Calcular porcentagem de área alterada
            total_area = img1.shape[0] * img1.shape[1]
            changed_area_percent = (total_change_area / total_area) * 100
            
            # Classificar tipo de mudança
            if changed_area_percent < 1:
                change_type = "Mudanças mínimas"
            elif changed_area_percent < 10:
                change_type = "Mudanças moderadas"
            elif changed_area_percent < 50:
                change_type = "Mudanças significativas"
            else:
                change_type = "Mudanças dramáticas"
            
            return {
                'similarity_score': float(similarity_score),
                'mse': float(mse),
                'differences_count': len(change_regions),
                'changed_area_percent': float(changed_area_percent),
                'change_type': change_type,
                'change_regions': change_regions[:10],  # Primeiras 10 regiões
                'comparison_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro na comparação de screenshots: {e}")
            return {'error': str(e)}

    def analyze_interface_efficiency_real(self, image: np.ndarray = None) -> Dict:
        """Análise REAL de eficiência da interface"""
        try:
            if image is None:
                image = self.capture_screenshot()
                if image is None:
                    return {'error': 'Falha ao capturar screenshot'}
            
            # Análise de layout
            layout_analysis = self.analyze_real_spatial_organization(image)
            
            # Análise de usabilidade
            usability_metrics = self.calculate_real_usability_metrics(image)
            
            # Score de acessibilidade
            accessibility_score = self.calculate_real_accessibility_score(image)
            
            # Sugestões de otimização
            optimization_suggestions = self.generate_real_interface_suggestions(
                layout_analysis, usability_metrics, accessibility_score
            )
            
            result = {
                'accessibility_score': accessibility_score,
                'interface_complexity': layout_analysis.get('layout_complexity', 50),
                'layout_analysis': layout_analysis,
                'usability_metrics': usability_metrics,
                'optimization_suggestions': optimization_suggestions,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # Salvar análise
            self.save_analysis_result(result, 'interface_efficiency')
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na análise de eficiência: {e}")
            return {'error': str(e)}

    def calculate_real_usability_metrics(self, image: np.ndarray) -> Dict:
        """Calcula métricas REAIS de usabilidade"""
        try:
            # Análise de contraste
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            contrast = gray.std()
            
            # Análise de densidade de informação
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
            
            # Análise de variância de cores
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            color_variance = np.var(hsv.reshape(-1, 3), axis=0)
            
            # Detectar regiões distintas
            # Usar clustering k-means para identificar regiões
            data = hsv.reshape(-1, 3)
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            _, labels, centers = cv2.kmeans(data.astype(np.float32), 8, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            distinct_regions = len(np.unique(labels))
            
            return {
                'contrast_level': float(contrast),
                'information_density': float(edge_density * 100),
                'color_variance': [float(cv) for cv in color_variance],
                'distinct_regions': int(distinct_regions),
                'edge_density': float(edge_density)
            }
            
        except Exception as e:
            logger.error(f"Erro nas métricas de usabilidade: {e}")
            return {}

    def calculate_real_accessibility_score(self, image: np.ndarray) -> float:
        """Calcula score REAL de acessibilidade"""
        try:
            # Análise de contraste para acessibilidade
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calcular contraste local
            kernel = np.ones((5, 5), np.float32) / 25
            mean_filtered = cv2.filter2D(gray.astype(np.float32), -1, kernel)
            contrast_map = np.abs(gray.astype(np.float32) - mean_filtered)
            avg_contrast = np.mean(contrast_map)
            
            # Normalizar para score 0-100
            # Contraste bom para acessibilidade: 50-150
            if 50 <= avg_contrast <= 150:
                contrast_score = 100
            elif avg_contrast < 50:
                contrast_score = (avg_contrast / 50) * 100
            else:
                contrast_score = max(0, 100 - ((avg_contrast - 150) / 100 * 50))
            
            # Análise de tamanho de elementos (via detecção de contornos)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Calcular tamanhos médios dos elementos
            element_sizes = [cv2.contourArea(contour) for contour in contours if cv2.contourArea(contour) > 100]
            
            if element_sizes:
                avg_element_size = np.mean(element_sizes)
                # Elementos muito pequenos prejudicam acessibilidade
                size_score = min(100, (avg_element_size / 1000) * 100)
            else:
                size_score = 50
            
            # Score final de acessibilidade
            accessibility_score = (contrast_score * 0.7 + size_score * 0.3)
            
            return float(min(100, max(0, accessibility_score)))
            
        except Exception as e:
            logger.error(f"Erro no cálculo de acessibilidade: {e}")
            return 50.0

    def generate_real_interface_suggestions(self, layout: Dict, usability: Dict, accessibility: float) -> List[str]:
        """Gera sugestões REAIS de otimização da interface"""
        try:
            suggestions = []
            
            # Sugestões baseadas em acessibilidade
            if accessibility < 50:
                suggestions.append("Melhorar contraste entre elementos para acessibilidade")
            elif accessibility < 70:
                suggestions.append("Aumentar tamanho de elementos pequenos")
            
            # Sugestões baseadas em complexidade
            complexity = layout.get('layout_complexity', 50)
            if complexity > 80:
                suggestions.append("Interface muito complexa - simplificar layout")
            elif complexity < 20:
                suggestions.append("Interface muito simples - adicionar elementos visuais")
            
            # Sugestões baseadas em densidade
            density = usability.get('information_density', 50)
            if density > 80:
                suggestions.append("Densidade de informação alta - organizar melhor elementos")
            
            # Sugestões baseadas em simetria
            symmetry = layout.get('symmetry_score', 50)
            if symmetry < 30:
                suggestions.append("Melhorar simetria e balanceamento visual")
            
            # Sugestões baseadas em regiões distintas
            regions = usability.get('distinct_regions', 5)
            if regions > 10:
                suggestions.append("Muitas regiões distintas - unificar design")
            elif regions < 3:
                suggestions.append("Poucas regiões distintas - criar mais separação visual")
            
            if not suggestions:
                suggestions.append("Interface bem estruturada - manter padrão atual")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Erro ao gerar sugestões: {e}")
            return ["Erro ao analisar interface"]

    def create_visual_report_real(self, report_data: Dict) -> Optional[str]:
        """Cria relatório visual REAL"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = os.path.join(self.analysis_dir, f"visual_report_{timestamp}.html")
            
            # Capturar screenshot atual se não fornecido
            current_screenshot = self.capture_screenshot()
            screenshot_filename = f"report_screenshot_{timestamp}.png"
            screenshot_path = os.path.join(self.screenshots_dir, screenshot_filename)
            
            if current_screenshot is not None:
                cv2.imwrite(screenshot_path, current_screenshot)
            
            # Gerar análises REAIS
            desktop_analysis = self.analyze_desktop_organization_real(current_screenshot)
            interface_analysis = self.analyze_interface_efficiency_real(current_screenshot)
            problems = self.detect_visual_problems_real(current_screenshot)
            
            # Criar HTML do relatório
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Relatório Visual - {timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .screenshot {{ max-width: 100%; height: auto; border: 1px solid #ccc; }}
        .metric {{ background: #f8f9fa; padding: 10px; margin: 5px 0; border-radius: 3px; }}
        .problem {{ background: #fff5f5; border-left: 4px solid #ff6b6b; padding: 10px; margin: 5px 0; }}
        .recommendation {{ background: #f0fff4; border-left: 4px solid #51cf66; padding: 10px; margin: 5px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Relatório Visual Completo</h1>
        <p>Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        <p>Usuário: {report_data.get('user', 'Sistema')}</p>
    </div>
    
    <div class="section">
        <h2>📸 Screenshot Analisado</h2>
        <img src="{screenshot_filename}" class="screenshot" alt="Screenshot analisado">
    </div>
    
    <div class="section">
        <h2>🖥️ Análise de Organização do Desktop</h2>
        <div class="metric">
            <strong>Score de Organização:</strong> {desktop_analysis.get('clutter_score', 0):.1f}/10
        </div>
        <div class="metric">
            <strong>Ícones Detectados:</strong> {desktop_analysis.get('icon_analysis', {}).get('total_icons', 0)}
        </div>
        <div class="metric">
            <strong>Janelas Detectadas:</strong> {desktop_analysis.get('window_analysis', {}).get('total_windows', 0)}
        </div>
        <div class="metric">
            <strong>Distribuição:</strong> {desktop_analysis.get('icon_analysis', {}).get('distribution', 'N/A')}
        </div>
    </div>
    
    <div class="section">
        <h2>⚡ Análise de Eficiência da Interface</h2>
        <div class="metric">
            <strong>Score de Acessibilidade:</strong> {interface_analysis.get('accessibility_score', 0):.1f}/100
        </div>
        <div class="metric">
            <strong>Complexidade do Layout:</strong> {interface_analysis.get('interface_complexity', 0):.1f}/100
        </div>
        <div class="metric">
            <strong>Densidade de Informação:</strong> {interface_analysis.get('usability_metrics', {}).get('information_density', 0):.1f}%
        </div>
    </div>
    
    <div class="section">
        <h2>⚠️ Problemas Detectados</h2>
            """
            
            # Adicionar problemas detectados
            total_problems = sum([
                len(problems.get('error_dialogs', [])),
                len(problems.get('suspicious_windows', [])),
                len(problems.get('visual_anomalies', [])),
                len(problems.get('performance_indicators', []))
            ])
            
            if total_problems > 0:
                html_content += f"<p><strong>Total de problemas:</strong> {total_problems}</p>"
                
                for category, items in problems.items():
                    if items:
                        html_content += f"<h3>{category.replace('_', ' ').title()}</h3>"
                        for item in items:
                            html_content += f'<div class="problem">{item.get("description", "Problema detectado")}</div>'
            else:
                html_content += '<div class="metric">✅ Nenhum problema visual detectado</div>'
            
            html_content += """
    </div>
    
    <div class="section">
        <h2>💡 Recomendações</h2>
            """
            
            # Adicionar recomendações
            recommendations = desktop_analysis.get('recommendations', [])
            interface_suggestions = interface_analysis.get('optimization_suggestions', [])
            
            all_recommendations = recommendations + interface_suggestions
            
            if all_recommendations:
                for rec in all_recommendations:
                    html_content += f'<div class="recommendation">{rec}</div>'
            else:
                html_content += '<div class="metric">✅ Sistema visual funcionando adequadamente</div>'
            
            html_content += """
    </div>
    
    <div class="section">
        <h2>📊 Métricas Técnicas</h2>
        <div class="metric">
            <strong>Resolução da Tela:</strong> """ + desktop_analysis.get('screen_resolution', 'N/A') + """
        </div>
        <div class="metric">
            <strong>Cores Únicas Detectadas:</strong> """ + str(desktop_analysis.get('color_scheme', {}).get('total_unique_colors', 0)) + """
        </div>
        <div class="metric">
            <strong>Score de Simetria:</strong> """ + f"{desktop_analysis.get('spatial_organization', {}).get('symmetry_score', 0):.1f}" + """/100
        </div>
    </div>
    
    <div class="section">
        <h2>🔍 Informações da Análise</h2>
        <p><strong>Método:</strong> Computer Vision com OpenCV e OCR</p>
        <p><strong>Processamento:</strong> 100% baseado em análise real de imagem</p>
        <p><strong>Confiabilidade:</strong> Alta (análise pixel-level)</p>
    </div>
    
</body>
</html>
            """
            
            # Salvar relatório
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Relatório visual salvo: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Erro ao criar relatório visual: {e}")
            return None

    def save_analysis_result(self, result: Dict, analysis_type: str):
        """Salva resultado da análise REAL"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{analysis_type}_{timestamp}.json"
            filepath = os.path.join(self.analysis_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)
            
            # Adicionar ao histórico
            self.analysis_history.append({
                'timestamp': result.get('timestamp', datetime.now().isoformat()),
                'type': analysis_type,
                'file': filename,
                'summary': self.generate_analysis_summary(result, analysis_type)
            })
            
            # Manter apenas últimas 100 análises
            if len(self.analysis_history) > 100:
                self.analysis_history = self.analysis_history[-100:]
            
            # Salvar histórico
            history_file = os.path.join(self.analysis_dir, 'analysis_history.json')
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_history, f, indent=2, ensure_ascii=False, default=str)
            
        except Exception as e:
            logger.error(f"Erro ao salvar análise: {e}")

    def generate_analysis_summary(self, result: Dict, analysis_type: str) -> str:
        """Gera resumo da análise"""
        try:
            if analysis_type == 'desktop_organization':
                clutter = result.get('clutter_score', 0)
                icons = result.get('icon_analysis', {}).get('total_icons', 0)
                return f"Clutter: {clutter:.1f}, Ícones: {icons}"
            
            elif analysis_type == 'interface_efficiency':
                accessibility = result.get('accessibility_score', 0)
                complexity = result.get('interface_complexity', 0)
                return f"Acessibilidade: {accessibility:.1f}, Complexidade: {complexity:.1f}"
            
            elif analysis_type == 'visual_problems':
                total = result.get('total_issues', 0)
                return f"Problemas detectados: {total}"
            
            elif analysis_type == 'ocr_extraction':
                words = result.get('word_count', 0)
                confidence = result.get('confidence', 0)
                return f"Palavras: {words}, Confiança: {confidence:.1f}%"
            
            else:
                return "Análise realizada"
                
        except Exception:
            return "Resumo indisponível"

    def load_analysis_history(self):
        """Carrega histórico de análises"""
        try:
            history_file = os.path.join(self.analysis_dir, 'analysis_history.json')
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.analysis_history = json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar histórico: {e}")
            self.analysis_history = []

    def get_analysis_statistics(self) -> Dict:
        """Retorna estatísticas REAIS das análises"""
        try:
            total_analyses = len(self.analysis_history)
            
            if total_analyses == 0:
                return {'total_analyses': 0}
            
            # Contar por tipo
            type_counts = {}
            for analysis in self.analysis_history:
                analysis_type = analysis.get('type', 'unknown')
                type_counts[analysis_type] = type_counts.get(analysis_type, 0) + 1
            
            # Análises por dia
            today = datetime.now().date()
            today_analyses = len([a for a in self.analysis_history 
                                if datetime.fromisoformat(a.get('timestamp', '2000-01-01')).date() == today])
            
            # Última análise
            last_analysis = max(self.analysis_history, 
                              key=lambda x: x.get('timestamp', '2000-01-01'))
            
            return {
                'total_analyses': total_analyses,
                'analyses_today': today_analyses,
                'analyses_by_type': type_counts,
                'last_analysis': last_analysis.get('timestamp'),
                'last_analysis_type': last_analysis.get('type'),
                'screenshots_captured': len([f for f in os.listdir(self.screenshots_dir) 
                                           if f.endswith('.png')])
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {'error': str(e)}

# Funções utilitárias REAIS
def quick_desktop_analysis() -> Dict:
    """Análise rápida REAL do desktop"""
    try:
        cv_system = ComputerVision()
        screenshot = cv_system.capture_screenshot()
        
        if screenshot is not None:
            analysis = cv_system.analyze_desktop_organization_real(screenshot)
            return {
                'clutter_score': analysis.get('clutter_score', 5.0),
                'icon_analysis': analysis.get('icon_analysis', {}),
                'window_analysis': analysis.get('window_analysis', {}),
                'recommendations': analysis.get('recommendations', [])
            }
        else:
            return {'error': 'Falha ao capturar screenshot'}
            
    except Exception as e:
        logger.error(f"Erro na análise rápida: {e}")
        return {'error': str(e)}

def capture_and_analyze() -> Dict:
    """Captura e analisa REAL da tela completa"""
    try:
        cv_system = ComputerVision()
        
        # Capturar screenshot
        screenshot = cv_system.capture_screenshot()
        if screenshot is None:
            return {'error': 'Falha ao capturar screenshot'}
        
        # Executar todas as análises REAIS
        desktop_org = cv_system.analyze_desktop_organization_real(screenshot)
        interface_eff = cv_system.analyze_interface_efficiency_real(screenshot)
        visual_problems = cv_system.detect_visual_problems_real(screenshot)
        
        return {
            'desktop_organization': desktop_org,
            'interface_efficiency': interface_eff,
            'visual_problems': visual_problems,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na captura e análise: {e}")
        return {'error': str(e)}

# Exemplo de uso
if __name__ == "__main__":
    print("👁️ Testando Computer Vision 100% REAL...")
    
    cv_system = ComputerVision()
    
    # Capturar screenshot real
    print("📸 Capturando screenshot real...")
    screenshot = cv_system.capture_screenshot()
    
    if screenshot is not None:
        print(f"✅ Screenshot capturado: {screenshot.shape}")
        
        # Análise real de organização
        print("🖥️ Analisando organização do desktop...")
        org_analysis = cv_system.analyze_desktop_organization_real(screenshot)
        print(f"Score de organização: {org_analysis.get('clutter_score', 0):.1f}/10")
        print(f"Ícones detectados: {org_analysis.get('icon_analysis', {}).get('total_icons', 0)}")
        
        # Análise real de interface
        print("⚡ Analisando eficiência da interface...")
        eff_analysis = cv_system.analyze_interface_efficiency_real(screenshot)
        print(f"Score de acessibilidade: {eff_analysis.get('accessibility_score', 0):.1f}/100")
        
        # Detecção real de problemas
        print("🔍 Detectando problemas visuais...")
        problems = cv_system.detect_visual_problems_real(screenshot)
        total_problems = sum([len(problems.get(k, [])) for k in problems.keys()])
        print(f"Problemas detectados: {total_problems}")
        
        # OCR real
        print("📝 Executando OCR...")
        ocr_result = cv_system.extract_text_from_screen_real(screenshot)
        print(f"Palavras extraídas: {ocr_result.get('word_count', 0)}")
        
        print("✅ Teste concluído - 100% baseado em análise real de imagem!")
    else:
        print("❌ Falha ao capturar screenshot")