# ai_modules/nlp_assistant.py
import re
import json
import os
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
import threading
from collections import Counter, defaultdict
import string
from pathlib import Path
import unicodedata
import difflib

# Configuração de logging específica para NLP
nlp_logger = logging.getLogger('nlp_assistant')
nlp_handler = logging.FileHandler('nlp_assistant.log')
nlp_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
nlp_handler.setFormatter(nlp_formatter)
nlp_logger.addHandler(nlp_handler)
nlp_logger.setLevel(logging.INFO)

class NLPAssistant:
    """Sistema completo de Processamento de Linguagem Natural e Assistente Inteligente"""
    
    def __init__(self, data_dir: str = "data", knowledge_dir: str = "resources/knowledge"):
        self.data_dir = data_dir
        self.knowledge_dir = knowledge_dir
        self.conversations_file = os.path.join(data_dir, "conversations.json")
        self.knowledge_base_file = os.path.join(knowledge_dir, "knowledge_base.json")
        self.intents_file = os.path.join(knowledge_dir, "intents.json")
        self.responses_file = os.path.join(knowledge_dir, "responses.json")
        
        # Configurações do assistente
        self.assistant_name = "Clara"
        self.supported_languages = ['pt', 'en']
        self.default_language = 'pt'
        self.confidence_threshold = 0.6
        
        # Dados de conversas
        self.conversation_history = []
        self.user_profiles = {}
        
        # Base de conhecimento
        self.knowledge_base = {}
        self.intents = {}
        self.responses = {}
        
        # Processamento de texto
        self.stop_words_pt = {
            'a', 'o', 'e', 'é', 'de', 'do', 'da', 'em', 'um', 'uma', 'para', 'com', 'não', 'na', 'no',
            'que', 'se', 'por', 'mais', 'como', 'mas', 'foi', 'ao', 'ele', 'das', 'tem', 'à', 'seu',
            'sua', 'ou', 'ser', 'quando', 'muito', 'há', 'nos', 'já', 'está', 'eu', 'também', 'só',
            'pelo', 'pela', 'até', 'isso', 'ela', 'entre', 'era', 'depois', 'sem', 'mesmo', 'aos',
            'ter', 'seus', 'suas', 'numa', 'pelos', 'pelas', 'esse', 'esses', 'essa', 'essas'
        }
        
        self.stop_words_en = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he', 'in', 'is',
            'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were', 'will', 'with', 'the', 'this',
            'but', 'they', 'have', 'had', 'what', 'said', 'each', 'which', 'she', 'do', 'how', 'their',
            'if', 'up', 'out', 'many', 'then', 'them', 'these', 'so', 'some', 'her', 'would', 'make',
            'like', 'into', 'him', 'time', 'two', 'more', 'go', 'no', 'way', 'could', 'my', 'than',
            'first', 'been', 'call', 'who', 'oil', 'its', 'now', 'find', 'long', 'down', 'day', 'did',
            'get', 'has', 'his', 'had', 'let', 'put', 'say', 'she', 'too', 'old', 'any', 'app', 'may',
            'new', 'try', 'us', 'an', 'as', 'boy', 'did', 'its', 'let', 'old', 'see', 'two', 'way',
            'ago', 'are', 'boy', 'did', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old',
            'see', 'two', 'way', 'who', 'boy', 'did', 'get', 'has', 'him', 'his', 'how', 'man', 'new',
            'now', 'old', 'see', 'two', 'way', 'who'
        }
        
        # Padrões de análise
        self.sentiment_patterns = {
            'positive': [
                'bom', 'boa', 'ótimo', 'ótima', 'excelente', 'perfeito', 'perfeita', 'maravilhoso',
                'fantastic', 'great', 'excellent', 'perfect', 'wonderful', 'amazing', 'awesome',
                'love', 'like', 'happy', 'satisfied', 'pleased', 'good', 'best', 'better'
            ],
            'negative': [
                'ruim', 'péssimo', 'péssima', 'terrível', 'horrível', 'problema', 'erro', 'falha',
                'bad', 'terrible', 'horrible', 'awful', 'worst', 'hate', 'dislike', 'angry',
                'frustrated', 'annoyed', 'disappointed', 'upset', 'sad', 'poor', 'worse'
            ],
            'neutral': [
                'ok', 'normal', 'regular', 'comum', 'padrão', 'médio', 'média',
                'okay', 'fine', 'normal', 'average', 'standard', 'typical', 'usual'
            ]
        }
        
        # Estatísticas de uso
        self.interaction_stats = {
            'total_interactions': 0,
            'successful_responses': 0,
            'failed_responses': 0,
            'average_response_time': 0,
            'most_common_intents': {},
            'user_satisfaction_scores': [],
            'language_usage': {'pt': 0, 'en': 0}
        }
        
        # Inicializar sistema
        self._initialize_system()
        self._load_knowledge_base()
        self._load_conversation_history()

    def _initialize_system(self):
        """Inicializa o sistema NLP"""
        # Criar diretórios
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.knowledge_dir, exist_ok=True)
        
        # Criar base de conhecimento padrão
        self._create_default_knowledge_base()
        self._create_default_intents()
        self._create_default_responses()
        
        nlp_logger.info("Sistema NLP inicializado")

    def _create_default_knowledge_base(self):
        """Cria base de conhecimento padrão"""
        if not os.path.exists(self.knowledge_base_file):
            default_knowledge = {
                "pc_cleaner": {
                    "description": "PC Cleaner é um software avançado de limpeza e otimização de computadores",
                    "features": [
                        "Limpeza de arquivos temporários",
                        "Otimização de registro",
                        "Gerenciamento de programas de inicialização",
                        "Análise de disco",
                        "Detecção de malware",
                        "Inteligência artificial para predição de performance"
                    ],
                    "plans": {
                        "free": "Funcionalidades básicas de limpeza",
                        "pro": "Funcionalidades avançadas + IA básica",
                        "master_plus": "Todas as funcionalidades + IA avançada"
                    }
                },
                "troubleshooting": {
                    "slow_computer": [
                        "Execute limpeza de arquivos temporários",
                        "Desabilite programas de inicialização desnecessários",
                        "Execute desfragmentação do disco",
                        "Verifique uso de memória RAM",
                        "Faça scan de malware"
                    ],
                    "disk_space": [
                        "Use o analisador de espaço em disco",
                        "Remova arquivos duplicados",
                        "Limpe cache dos navegadores",
                        "Desinstale programas não utilizados",
                        "Use compressão de arquivos"
                    ],
                    "startup_issues": [
                        "Verifique programas de inicialização",
                        "Execute limpeza do registro",
                        "Verifique integridade dos arquivos do sistema",
                        "Desabilite serviços desnecessários"
                    ]
                },
                "commands": {
                    "clean": "Inicia processo de limpeza do sistema",
                    "scan": "Executa varredura completa do sistema",
                    "optimize": "Otimiza configurações do sistema",
                    "report": "Gera relatório de análise",
                    "help": "Mostra ajuda e comandos disponíveis"
                }
            }
            
            with open(self.knowledge_base_file, 'w', encoding='utf-8') as f:
                json.dump(default_knowledge, f, indent=2, ensure_ascii=False)

    def _create_default_intents(self):
        """Cria intenções padrão"""
        if not os.path.exists(self.intents_file):
            default_intents = {
                "greeting": {
                    "patterns": [
                        "olá", "oi", "ola", "hey", "hello", "hi", "bom dia", "boa tarde", "boa noite",
                        "good morning", "good afternoon", "good evening", "greetings"
                    ],
                    "context": "saudação inicial"
                },
                "help": {
                    "patterns": [
                        "ajuda", "help", "socorro", "como", "what", "que", "preciso", "need",
                        "como usar", "how to", "tutorial", "guia", "guide", "instructions"
                    ],
                    "context": "solicitação de ajuda"
                },
                "clean_request": {
                    "patterns": [
                        "limpar", "limpeza", "clean", "cleanup", "remover", "remove", "delete",
                        "apagar", "temporary", "temp", "cache", "lixo", "trash", "junk"
                    ],
                    "context": "solicitação de limpeza"
                },
                "performance": {
                    "patterns": [
                        "lento", "slow", "performance", "velocidade", "speed", "otimizar", "optimize",
                        "acelerar", "faster", "melhorar", "improve", "boost", "turbo"
                    ],
                    "context": "problemas de performance"
                },
                "disk_space": {
                    "patterns": [
                        "espaço", "space", "disco", "disk", "storage", "armazenamento", "cheio",
                        "full", "capacidade", "capacity", "memory", "memoria"
                    ],
                    "context": "problemas de espaço em disco"
                },
                "malware": {
                    "patterns": [
                        "virus", "malware", "trojan", "spyware", "adware", "infected", "infectado",
                        "security", "segurança", "proteção", "protection", "scan", "varredura"
                    ],
                    "context": "problemas de segurança"
                },
                "startup": {
                    "patterns": [
                        "inicialização", "startup", "boot", "iniciar", "start", "liga", "turn on",
                        "demora", "slow boot", "demorado"
                    ],
                    "context": "problemas de inicialização"
                },
                "plans": {
                    "patterns": [
                        "plano", "plan", "preço", "price", "custo", "cost", "gratis", "free",
                        "pro", "master", "premium", "upgrade", "atualizar"
                    ],
                    "context": "informações sobre planos"
                },
                "satisfaction": {
                    "patterns": [
                        "obrigado", "thanks", "thank you", "valeu", "excelente", "excellent",
                        "perfeito", "perfect", "ótimo", "great", "bom", "good", "ruim", "bad"
                    ],
                    "context": "feedback do usuário"
                },
                "goodbye": {
                    "patterns": [
                        "tchau", "bye", "goodbye", "até logo", "see you", "adeus", "farewell",
                        "obrigado", "thanks", "valeu"
                    ],
                    "context": "despedida"
                }
            }
            
            with open(self.intents_file, 'w', encoding='utf-8') as f:
                json.dump(default_intents, f, indent=2, ensure_ascii=False)

    def _create_default_responses(self):
        """Cria respostas padrão"""
        if not os.path.exists(self.responses_file):
            default_responses = {
                "greeting": [
                    "Olá! 👋 Eu sou a Clara, sua assistente do PC Cleaner. Como posso ajudá-lo hoje?",
                    "Oi! 😊 Sou a Clara e estou aqui para ajudar com qualquer dúvida sobre o PC Cleaner!",
                    "Hello! I'm Clara, your PC Cleaner assistant. How can I help you today?",
                    "Bom dia! Como posso tornar seu PC mais rápido e limpo hoje?"
                ],
                "help": [
                    "Posso ajudar você com:\n🧹 Limpeza do sistema\n⚡ Otimização de performance\n🛡️ Análise de segurança\n📊 Relatórios detalhados\n\nQue tipo de ajuda você precisa?",
                    "Aqui estão as principais funcionalidades:\n• Limpeza de arquivos temporários\n• Otimização de registro\n• Gerenciamento de inicialização\n• Análise de espaço em disco\n\nSobre o que gostaria de saber mais?",
                    "Estou aqui para ajudar! Você pode me perguntar sobre limpeza, otimização, problemas de performance, ou qualquer dúvida sobre o PC Cleaner."
                ],
                "clean_request": [
                    "Vou iniciar a limpeza do seu sistema! 🧹\n\nO PC Cleaner irá:\n✓ Remover arquivos temporários\n✓ Limpar cache dos navegadores\n✓ Otimizar registro\n✓ Analisar duplicatas\n\nDeseja continuar?",
                    "Perfeito! A limpeza inteligente do PC Cleaner pode liberar vários GB de espaço. Você gostaria de fazer uma limpeza completa ou específica?",
                    "Ótima escolha! Nossa IA irá analisar seu sistema e recomendar as melhores ações de limpeza. Iniciando análise..."
                ],
                "performance": [
                    "Para melhorar a performance do seu PC, recomendo:\n\n🚀 Otimização de inicialização\n💾 Limpeza de memória\n🔧 Correção de registro\n📈 Análise preditiva com IA\n\nQual problema específico você está enfrentando?",
                    "Problemas de lentidão são muito comuns! Nossa IA pode identificar os gargalos do seu sistema. Você notou lentidão em algum momento específico?",
                    "Vou executar uma análise completa de performance! O PC Cleaner usa machine learning para identificar e corrigir problemas automaticamente."
                ],
                "disk_space": [
                    "Problemas de espaço em disco? Posso ajudar! 💽\n\n📁 Análise de uso de disco\n🗑️ Remoção de arquivos duplicados\n📦 Limpeza de downloads antigos\n🧹 Cache e arquivos temporários\n\nVamos começar com uma análise?",
                    "O analisador inteligente do PC Cleaner pode mostrar exatamente onde seu espaço está sendo usado. Seria útil ver um relatório detalhado?",
                    "Liberação de espaço é nossa especialidade! Nossa IA encontra arquivos seguros para remover sem afetar o funcionamento do sistema."
                ],
                "malware": [
                    "Segurança é fundamental! 🛡️\n\nO PC Cleaner inclui:\n🔍 Scan inteligente de malware\n🚫 Detecção de ameaças\n🧹 Remoção segura\n📊 Relatório de segurança\n\nVamos fazer uma verificação completa?",
                    "Preocupações com segurança são válidas. Nossa tecnologia de IA detecta padrões suspeitos que antivírus tradicionais podem perder.",
                    "Vou executar uma varredura completa! O sistema usa análise comportamental para identificar ameaças avançadas."
                ],
                "startup": [
                    "Inicialização lenta é frustrante! 🐌➡️⚡\n\nPosso otimizar:\n⚙️ Programas de inicialização\n🔧 Serviços do sistema\n📁 Arquivos de boot\n🧠 Análise com IA\n\nQuer que eu analise sua inicialização?",
                    "O PC Cleaner pode reduzir significativamente o tempo de boot! Nossa IA identifica quais programas são realmente necessários na inicialização.",
                    "Problemas de inicialização podem ter várias causas. Vou executar um diagnóstico completo para identificar os gargalos."
                ],
                "plans": [
                    "Temos três planos para você:\n\n🆓 **Gratuito**: Limpeza básica\n⚡ **Pro**: IA básica + funcionalidades avançadas\n👑 **Master Plus**: IA completa + todas as funcionalidades\n\nQual se adequa melhor às suas necessidades?",
                    "Nossos planos são flexíveis:\n• Gratuito: Perfeito para uso básico\n• Pro: Ideal para usuários avançados\n• Master Plus: Máxima performance com IA\n\nPosso explicar os detalhes de algum específico?",
                    "Cada plano oferece valor único! O que é mais importante para você: economia, funcionalidades avançadas ou máxima performance?"
                ],
                "satisfaction": [
                    "Fico feliz em ajudar! 😊 Se tiver mais dúvidas, estarei sempre aqui. Sua experiência é muito importante para nós!",
                    "Que bom que consegui ajudar! 🌟 Não hesite em me procurar sempre que precisar. Estou aqui 24/7!",
                    "Obrigada pelo feedback! Sua opinião nos ajuda a melhorar constantemente. Há algo mais em que posso ajudar?"
                ],
                "goodbye": [
                    "Até logo! 👋 Foi um prazer ajudar. Lembre-se: estou sempre aqui quando precisar!",
                    "Tchau! 😊 Espero ter ajudado. Volte sempre que tiver dúvidas sobre o PC Cleaner!",
                    "Goodbye! Thanks for using PC Cleaner. Have a great day! 🌟"
                ],
                "default": [
                    "Interessante pergunta! 🤔 Pode reformular ou ser mais específico? Estou aqui para ajudar com qualquer dúvida sobre o PC Cleaner.",
                    "Não tenho certeza se entendi completamente. Você poderia explicar de outra forma? Quero garantir que vou ajudar da melhor maneira!",
                    "Hmm, essa é nova para mim! 😅 Você poderia dar mais detalhes? Ou talvez perguntar sobre limpeza, otimização ou funcionalidades do PC Cleaner?"
                ],
                "command_clean": [
                    "🚀 Iniciando limpeza inteligente...\n\n✓ Analisando sistema\n✓ Identificando arquivos desnecessários\n✓ Calculando espaço a ser liberado\n\nAguarde enquanto otimizo seu PC!",
                    "Comando de limpeza recebido! Executando análise preditiva para maximizar os resultados...",
                    "Limpeza iniciada com IA! O sistema está aprendendo os padrões do seu uso para uma limpeza mais eficiente."
                ],
                "command_scan": [
                    "🔍 Iniciando varredura completa...\n\n📊 Analisando performance\n🛡️ Verificando segurança\n💾 Checando integridade\n🧠 Aplicando machine learning\n\nResultados em breve!",
                    "Scan inteligente em andamento! Nossa IA está analisando milhares de arquivos e configurações...",
                    "Varredura avançada iniciada! Usando computer vision e análise comportamental para detecção completa."
                ]
            }
            
            with open(self.responses_file, 'w', encoding='utf-8') as f:
                json.dump(default_responses, f, indent=2, ensure_ascii=False)

    def process_user_input(self, user_input: str, user_id: str = "anonymous", 
                          context: Dict = None) -> Dict:
        """Processa entrada do usuário e retorna resposta inteligente"""
        start_time = time.time()
        
        try:
            # Limpar e normalizar entrada
            cleaned_input = self._clean_text(user_input)
            
            # Detectar idioma
            detected_language = self._detect_language(cleaned_input)
            
            # Análise de sentimento
            sentiment = self._analyze_sentiment(cleaned_input)
            
            # Classificar intenção
            intent, confidence = self._classify_intent(cleaned_input)
            
            # Extrair entidades
            entities = self._extract_entities(cleaned_input)
            
            # Gerar resposta
            response = self._generate_response(intent, entities, sentiment, detected_language, context)
            
            # Registrar interação
            interaction = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'user_input': user_input,
                'cleaned_input': cleaned_input,
                'detected_language': detected_language,
                'intent': intent,
                'confidence': confidence,
                'sentiment': sentiment,
                'entities': entities,
                'response': response,
                'processing_time': round(time.time() - start_time, 3),
                'context': context or {}
            }
            
            self._save_interaction(interaction)
            self._update_stats(interaction)
            
            # Atualizar perfil do usuário
            self._update_user_profile(user_id, interaction)
            
            nlp_logger.info(f"Processamento NLP concluído - Intent: {intent} (confiança: {confidence:.3f})")
            
            return {
                'response': response,
                'intent': intent,
                'confidence': confidence,
                'sentiment': sentiment,
                'language': detected_language,
                'entities': entities,
                'processing_time': interaction['processing_time'],
                'suggestions': self._get_suggestions(intent, entities),
                'follow_up_questions': self._get_follow_up_questions(intent)
            }
            
        except Exception as e:
            error_msg = f"Erro no processamento NLP: {e}"
            nlp_logger.error(error_msg)
            
            return {
                'response': "Desculpe, houve um erro ao processar sua mensagem. Pode tentar novamente?",
                'intent': 'error',
                'confidence': 0.0,
                'sentiment': 'neutral',
                'language': 'pt',
                'entities': [],
                'processing_time': round(time.time() - start_time, 3),
                'error': error_msg
            }

    def chat_conversation(self, user_input: str, conversation_id: str = None, 
                         user_id: str = "anonymous") -> Dict:
        """Mantém conversa contínua com contexto"""
        try:
            # Recuperar ou criar contexto da conversa
            if conversation_id:
                context = self._get_conversation_context(conversation_id)
            else:
                conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
                context = {'conversation_id': conversation_id, 'history': [], 'topics': []}
            
            # Processar entrada atual
            result = self.process_user_input(user_input, user_id, context)
            
            # Atualizar contexto da conversa
            context['history'].append({
                'timestamp': datetime.now().isoformat(),
                'user_input': user_input,
                'assistant_response': result['response'],
                'intent': result['intent'],
                'sentiment': result['sentiment']
            })
            
            # Manter apenas últimas 10 interações
            if len(context['history']) > 10:
                context['history'] = context['history'][-10:]
            
            # Atualizar tópicos da conversa
            if result['intent'] not in context['topics']:
                context['topics'].append(result['intent'])
            
            # Salvar contexto atualizado
            self._save_conversation_context(conversation_id, context)
            
            # Adicionar informações de conversa ao resultado
            result['conversation_id'] = conversation_id
            result['conversation_context'] = {
                'topics_discussed': context['topics'],
                'interaction_count': len(context['history']),
                'conversation_sentiment': self._analyze_conversation_sentiment(context['history'])
            }
            
            return result
            
        except Exception as e:
            nlp_logger.error(f"Erro na conversa: {e}")
            return {
                'response': "Desculpe, houve um problema na conversa. Pode tentar novamente?",
                'error': str(e)
            }

    def analyze_text_sentiment(self, text: str) -> Dict:
        """Analisa sentimento de um texto"""
        try:
            sentiment_analysis = {
                'text': text,
                'sentiment': self._analyze_sentiment(text),
                'confidence': 0.0,
                'emotions': {},
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # Análise mais detalhada
            clean_text = self._clean_text(text)
            words = clean_text.split()
            
            # Contar palavras positivas, negativas e neutras
            positive_count = sum(1 for word in words if word in self.sentiment_patterns['positive'])
            negative_count = sum(1 for word in words if word in self.sentiment_patterns['negative'])
            neutral_count = sum(1 for word in words if word in self.sentiment_patterns['neutral'])
            
            total_sentiment_words = positive_count + negative_count + neutral_count
            
            if total_sentiment_words > 0:
                sentiment_analysis['confidence'] = total_sentiment_words / len(words)
                sentiment_analysis['emotions'] = {
                    'positive_ratio': positive_count / total_sentiment_words,
                    'negative_ratio': negative_count / total_sentiment_words,
                    'neutral_ratio': neutral_count / total_sentiment_words
                }
            
            # Análise de intensidade
            sentiment_analysis['intensity'] = self._calculate_sentiment_intensity(clean_text)
            
            return sentiment_analysis
            
        except Exception as e:
            nlp_logger.error(f"Erro na análise de sentimento: {e}")
            return {'error': str(e)}

    def extract_information(self, text: str) -> Dict:
        """Extrai informações estruturadas de texto"""
        try:
            clean_text = self._clean_text(text)
            
            information = {
                'original_text': text,
                'cleaned_text': clean_text,
                'language': self._detect_language(clean_text),
                'entities': self._extract_entities(clean_text),
                'keywords': self._extract_keywords(clean_text),
                'summary': self._generate_summary(clean_text),
                'topics': self._extract_topics(clean_text),
                'statistics': self._calculate_text_statistics(clean_text),
                'extraction_timestamp': datetime.now().isoformat()
            }
            
            return information
            
        except Exception as e:
            nlp_logger.error(f"Erro na extração de informações: {e}")
            return {'error': str(e)}

    def generate_smart_response(self, user_query: str, knowledge_context: Dict = None) -> Dict:
        """Gera resposta inteligente baseada em contexto"""
        try:
            # Processar query
            result = self.process_user_input(user_query)
            
            # Enriquecer com contexto de conhecimento
            if knowledge_context:
                enriched_response = self._enrich_response_with_context(
                    result['response'], 
                    result['intent'], 
                    knowledge_context
                )
                result['response'] = enriched_response
                result['knowledge_used'] = True
            
            # Adicionar recursos inteligentes
            result['smart_features'] = {
                'auto_complete_suggestions': self._get_auto_complete_suggestions(user_query),
                'related_questions': self._get_related_questions(result['intent']),
                'action_buttons': self._get_action_buttons(result['intent']),
                'quick_responses': self._get_quick_responses(result['intent'])
            }
            
            return result
            
        except Exception as e:
            nlp_logger.error(f"Erro na geração de resposta inteligente: {e}")
            return {'error': str(e)}

    def analyze_user_feedback(self, feedback_text: str, rating: int = None) -> Dict:
        """Analisa feedback do usuário"""
        try:
            analysis = {
                'feedback_text': feedback_text,
                'rating': rating,
                'sentiment': self._analyze_sentiment(feedback_text),
                'key_points': self._extract_feedback_points(feedback_text),
                'improvement_suggestions': [],
                'category': self._categorize_feedback(feedback_text),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # Gerar sugestões de melhoria
            analysis['improvement_suggestions'] = self._generate_improvement_suggestions(analysis)
            
            # Salvar feedback para análise posterior
            self._save_user_feedback(analysis)
            
            return analysis
            
        except Exception as e:
            nlp_logger.error(f"Erro na análise de feedback: {e}")
            return {'error': str(e)}

    def generate_system_report(self, system_data: Dict) -> str:
        """Gera relatório em linguagem natural sobre o sistema"""
        try:
            # Analisar dados do sistema
            performance_score = system_data.get('performance_score', 0)
            cleaned_files = system_data.get('cleaned_files', 0)
            disk_freed = system_data.get('disk_freed_mb', 0)
            
            # Gerar relatório narrativo
            report_parts = []
            
            # Introdução
            report_parts.append("## 📊 Relatório de Análise do Sistema\n")
            report_parts.append(f"*Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}*\n")
            
            # Performance
            if performance_score > 80:
                report_parts.append("🚀 **Excelente!** Seu sistema está funcionando muito bem.")
            elif performance_score > 60:
                report_parts.append("⚡ **Bom desempenho** detectado, com pequenas oportunidades de melhoria.")
            else:
                report_parts.append("🔧 **Atenção necessária** - seu sistema pode se beneficiar de otimização.")
            
            # Limpeza
            if cleaned_files > 0:
                report_parts.append(f"\n🧹 **Limpeza realizada:** {cleaned_files} arquivos processados")
                if disk_freed > 0:
                    if disk_freed > 1024:
                        disk_freed_gb = disk_freed / 1024
                        report_parts.append(f"💾 **Espaço liberado:** {disk_freed_gb:.2f} GB")
                    else:
                        report_parts.append(f"💾 **Espaço liberado:** {disk_freed} MB")
            
            # Recomendações
            report_parts.append("\n## 💡 Recomendações Inteligentes\n")
            recommendations = self._generate_system_recommendations(system_data)
            for rec in recommendations:
                report_parts.append(f"• {rec}")
            
            # Próximos passos
            report_parts.append("\n## 🎯 Próximos Passos\n")
            next_steps = self._generate_next_steps(system_data)
            for step in next_steps:
                report_parts.append(f"1. {step}")
            
            return "\n".join(report_parts)
            
        except Exception as e:
            nlp_logger.error(f"Erro na geração de relatório: {e}")
            return "Erro ao gerar relatório do sistema."

    def get_conversation_statistics(self) -> Dict:
        """Obtém estatísticas das conversas"""
        try:
            stats = self.interaction_stats.copy()
            
            # Adicionar estatísticas calculadas
            if stats['total_interactions'] > 0:
                stats['success_rate'] = (stats['successful_responses'] / stats['total_interactions']) * 100
                stats['average_satisfaction'] = np.mean(stats['user_satisfaction_scores']) if stats['user_satisfaction_scores'] else 0
            else:
                stats['success_rate'] = 0
                stats['average_satisfaction'] = 0
            
            # Top intents
            if stats['most_common_intents']:
                sorted_intents = sorted(stats['most_common_intents'].items(), key=lambda x: x[1], reverse=True)
                stats['top_intents'] = sorted_intents[:10]
            
            # Estatísticas por idioma
            total_lang_usage = sum(stats['language_usage'].values())
            if total_lang_usage > 0:
                stats['language_percentages'] = {
                    lang: (count / total_lang_usage) * 100 
                    for lang, count in stats['language_usage'].items()
                }
            
            stats['generated_at'] = datetime.now().isoformat()
            
            return stats
            
        except Exception as e:
            nlp_logger.error(f"Erro ao obter estatísticas: {e}")
            return {'error': str(e)}

    # Métodos privados auxiliares
    def _clean_text(self, text: str) -> str:
        """Limpa e normaliza texto"""
        try:
            # Converter para minúsculas
            text = text.lower()
            
            # Remover acentos
            text = unicodedata.normalize('NFD', text)
            text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
            
            # Remover pontuação excessiva
            text = re.sub(r'[^\w\s]', ' ', text)
            
            # Remover espaços extras
            text = ' '.join(text.split())
            
            return text.strip()
            
        except Exception as e:
            nlp_logger.error(f"Erro na limpeza de texto: {e}")
            return text

    def _detect_language(self, text: str) -> str:
        """Detecta idioma do texto"""
        try:
            # Palavras características do português
            pt_indicators = ['que', 'nao', 'com', 'para', 'uma', 'ser', 'tem', 'mais', 'ja', 'pode']
            # Palavras características do inglês
            en_indicators = ['the', 'and', 'that', 'have', 'for', 'not', 'with', 'you', 'this', 'but']
            
            words = text.split()
            pt_count = sum(1 for word in words if word in pt_indicators)
            en_count = sum(1 for word in words if word in en_indicators)
            
            # Também verificar caracteres específicos
            if 'ç' in text or 'ã' in text or 'õ' in text:
                pt_count += 2
            
            if pt_count > en_count:
                return 'pt'
            elif en_count > pt_count:
                return 'en'
            else:
                return self.default_language
                
        except Exception as e:
            nlp_logger.error(f"Erro na detecção de idioma: {e}")
            return self.default_language

    def _analyze_sentiment(self, text: str) -> str:
        """Analisa sentimento do texto"""
        try:
            words = text.split()
            
            positive_count = sum(1 for word in words if word in self.sentiment_patterns['positive'])
            negative_count = sum(1 for word in words if word in self.sentiment_patterns['negative'])
            
            if positive_count > negative_count:
                return 'positive'
            elif negative_count > positive_count:
                return 'negative'
            else:
                return 'neutral'
                
        except Exception as e:
            nlp_logger.error(f"Erro na análise de sentimento: {e}")
            return 'neutral'

    def _classify_intent(self, text: str) -> Tuple[str, float]:
        """Classifica intenção do texto"""
        try:
            best_intent = 'default'
            best_score = 0.0
            
            words = set(text.split())
            
            for intent, data in self.intents.items():
                patterns = data.get('patterns', [])
                
                # Calcular score baseado em correspondências
                matches = sum(1 for pattern in patterns if pattern in text)
                word_matches = sum(1 for pattern in patterns if pattern in words)
                
                # Score combinado
                score = (matches * 0.6) + (word_matches * 0.4)
                
                # Normalizar pelo número de padrões
                if patterns:
                    score = score / len(patterns)
                
                if score > best_score:
                    best_score = score
                    best_intent = intent
            
            # Verificar se atinge threshold mínimo
            if best_score < self.confidence_threshold:
                best_intent = 'default'
                best_score = 0.5
            
            return best_intent, min(1.0, best_score)
            
        except Exception as e:
            nlp_logger.error(f"Erro na classificação de intenção: {e}")
            return 'default', 0.0

    def _extract_entities(self, text: str) -> List[Dict]:
        """Extrai entidades do texto"""
        try:
            entities = []
            
            # Extrair números
            numbers = re.findall(r'\d+', text)
            for num in numbers:
                entities.append({
                    'type': 'number',
                    'value': int(num),
                    'text': num
                })
            
            # Extrair emails
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
            for email in emails:
                entities.append({
                    'type': 'email',
                    'value': email,
                    'text': email
                })
            
            # Extrair URLs
            urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\$\$,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
            for url in urls:
                entities.append({
                    'type': 'url',
                    'value': url,
                    'text': url
                })
            
            # Extrair menções de planos
            plan_keywords = {'gratis', 'free', 'pro', 'master', 'plus', 'premium'}
            words = text.split()
            for word in words:
                if word in plan_keywords:
                    entities.append({
                        'type': 'plan',
                        'value': word,
                        'text': word
                    })
            
            return entities
            
        except Exception as e:
            nlp_logger.error(f"Erro na extração de entidades: {e}")
            return []

    def _generate_response(self, intent: str, entities: List[Dict], 
                          sentiment: str, language: str, context: Dict = None) -> str:
        """Gera resposta baseada em intenção e contexto"""
        try:
            # Buscar respostas para a intenção
            possible_responses = self.responses.get(intent, self.responses.get('default', []))
            
            if not possible_responses:
                return "Desculpe, não tenho uma resposta adequada para isso."
            
            # Selecionar resposta baseada no contexto
            response = self._select_contextual_response(possible_responses, sentiment, language, context)
            
            # Personalizar resposta com entidades
            response = self._personalize_response(response, entities, context)
            
            return response
            
        except Exception as e:
            nlp_logger.error(f"Erro na geração de resposta: {e}")
            return "Desculpe, houve um erro ao gerar a resposta."

    def _select_contextual_response(self, responses: List[str], sentiment: str, 
                                   language: str, context: Dict = None) -> str:
        """Seleciona resposta mais apropriada ao contexto"""
        try:
            # Filtrar por idioma se possível
            language_appropriate = []
            for response in responses:
                if language == 'en' and any(en_word in response.lower() for en_word in ['hello', 'thank', 'help', 'clean']):
                    language_appropriate.append(response)
                elif language == 'pt' and any(pt_word in response.lower() for pt_word in ['olá', 'obrigad', 'ajud', 'limpe']):
                    language_appropriate.append(response)
            
            # Se não encontrou respostas apropriadas ao idioma, usar todas
            if not language_appropriate:
                language_appropriate = responses
            
            # Selecionar baseado no sentimento
            if sentiment == 'positive':
                # Preferir respostas mais entusiasmadas
                positive_responses = [r for r in language_appropriate if any(emoji in r for emoji in ['😊', '🌟', '🚀', '✓'])]
                if positive_responses:
                    return random.choice(positive_responses)
            elif sentiment == 'negative':
                # Preferir respostas mais empáticas
                empathetic_responses = [r for r in language_appropriate if any(word in r.lower() for word in ['desculp', 'sorry', 'compreend', 'understand'])]
                if empathetic_responses:
                    return random.choice(empathetic_responses)
            
            # Selecionar aleatoriamente se não houver critério específico
            return random.choice(language_appropriate)
            
        except Exception as e:
            nlp_logger.error(f"Erro na seleção contextual: {e}")
            return random.choice(responses) if responses else "Resposta não disponível."

    def _personalize_response(self, response: str, entities: List[Dict], context: Dict = None) -> str:
        """Personaliza resposta com informações específicas"""
        try:
            # Substituir placeholders com entidades
            for entity in entities:
                if entity['type'] == 'plan':
                    plan_info = self.knowledge_base.get('pc_cleaner', {}).get('plans', {})
                    plan_description = plan_info.get(entity['value'], f"plano {entity['value']}")
                    response = response.replace('{plan}', plan_description)
            
            # Adicionar informações contextuais
            if context and 'conversation_id' in context:
                history = context.get('history', [])
                if len(history) > 1:
                    response += "\n\n*Baseado em nossa conversa anterior*"
            
            return response
            
        except Exception as e:
            nlp_logger.error(f"Erro na personalização de resposta: {e}")
            return response

    def _get_suggestions(self, intent: str, entities: List[Dict]) -> List[str]:
        """Obtém sugestões baseadas na intenção"""
        suggestions_map = {
            'clean_request': [
                "Executar limpeza completa",
                "Apenas arquivos temporários",
                "Limpeza personalizada",
                "Ver espaço a ser liberado"
            ],
            'performance': [
                "Analisar inicialização",
                "Verificar uso de memória",
                "Otimizar registro",
                "Executar diagnóstico completo"
            ],
            'help': [
                "Ver tutorial",
                "Falar com suporte",
                "Consultar FAQ",
                "Agendar demonstração"
            ],
            'plans': [
                "Comparar planos",
                "Testar grátis",
                "Ver preços",
                "Falar com vendas"
            ]
        }
        
        return suggestions_map.get(intent, [
            "Como posso ajudar?",
            "Ver funcionalidades",
            "Suporte técnico",
            "Dúvidas frequentes"
        ])

    def _get_follow_up_questions(self, intent: str) -> List[str]:
        """Obtém perguntas de follow-up"""
        follow_up_map = {
            'clean_request': [
                "Quando foi a última limpeza?",
                "Há arquivos específicos que não devem ser removidos?",
                "Quer agendar limpezas automáticas?"
            ],
            'performance': [
                "Em que momentos o PC fica mais lento?",
                "Quantos programas você usa simultaneamente?",
                "Já tentou reiniciar recentemente?"
            ],
            'disk_space': [
                "Que tipo de arquivos você mais armazena?",
                "Tem backups externos?",
                "Quer ver análise detalhada do uso?"
            ]
        }
        
        return follow_up_map.get(intent, [
            "Posso esclarecer alguma dúvida?",
            "Há algo específico que precisa?",
            "Quer saber sobre outras funcionalidades?"
        ])

    def _extract_keywords(self, text: str) -> List[str]:
        """Extrai palavras-chave do texto"""
        try:
            words = text.split()
            
            # Remover stop words
            lang = self._detect_language(text)
            stop_words = self.stop_words_pt if lang == 'pt' else self.stop_words_en
            
            keywords = [word for word in words if word not in stop_words and len(word) > 2]
            
            # Contar frequência
            word_freq = Counter(keywords)
            
            # Retornar top keywords
            return [word for word, freq in word_freq.most_common(10)]
            
        except Exception as e:
            nlp_logger.error(f"Erro na extração de keywords: {e}")
            return []

    def _generate_summary(self, text: str) -> str:
        """Gera resumo do texto"""
        try:
            sentences = re.split(r'[.!?]+', text)
            
            if len(sentences) <= 2:
                return text
            
            # Selecionar primeira e última sentença como resumo básico
            summary_sentences = [sentences[0].strip()]
            if len(sentences) > 1:
                summary_sentences.append(sentences[-1].strip())
            
            return '. '.join(filter(None, summary_sentences)) + '.'
            
        except Exception as e:
            nlp_logger.error(f"Erro na geração de resumo: {e}")
            return text[:100] + "..." if len(text) > 100 else text

    def _extract_topics(self, text: str) -> List[str]:
        """Extrai tópicos do texto"""
        try:
            # Buscar tópicos conhecidos na base de conhecimento
            topics = []
            
            knowledge_topics = {
                'limpeza': ['limpar', 'clean', 'temporary', 'temp', 'cache', 'junk'],
                'performance': ['lento', 'slow', 'velocidade', 'speed', 'otimizar', 'optimize'],
                'seguranca': ['virus', 'malware', 'security', 'segurança', 'proteção'],
                'disco': ['espaço', 'space', 'disco', 'disk', 'storage'],
                'memoria': ['memoria', 'memory', 'ram', 'cpu'],
                'inicializacao': ['startup', 'boot', 'inicialização', 'iniciar']
            }
            
            for topic, keywords in knowledge_topics.items():
                if any(keyword in text for keyword in keywords):
                    topics.append(topic)
            
            return topics
            
        except Exception as e:
            nlp_logger.error(f"Erro na extração de tópicos: {e}")
            return []

    def _calculate_text_statistics(self, text: str) -> Dict:
        """Calcula estatísticas do texto"""
        try:
            words = text.split()
            sentences = re.split(r'[.!?]+', text)
            
            return {
                'character_count': len(text),
                'word_count': len(words),
                'sentence_count': len([s for s in sentences if s.strip()]),
                'average_word_length': sum(len(word) for word in words) / len(words) if words else 0,
                'average_sentence_length': len(words) / len(sentences) if sentences else 0,
                'complexity_score': self._calculate_text_complexity(text)
            }
            
        except Exception as e:
            nlp_logger.error(f"Erro no cálculo de estatísticas: {e}")
            return {}

    def _calculate_text_complexity(self, text: str) -> float:
        """Calcula complexidade do texto (0-100)"""
        try:
            words = text.split()
            sentences = re.split(r'[.!?]+', text)
            
            # Fatores de complexidade
            avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
            avg_sentence_length = len(words) / len(sentences) if sentences else 0
            
            # Fórmula simplificada de complexidade
            complexity = (avg_word_length * 10) + (avg_sentence_length * 2)
            
            return min(100, max(0, complexity))
            
        except Exception as e:
            nlp_logger.error(f"Erro no cálculo de complexidade: {e}")
            return 50

    def _calculate_sentiment_intensity(self, text: str) -> float:
        """Calcula intensidade do sentimento (0-1)"""
        try:
            # Palavras de intensificação
            intensifiers = ['muito', 'extremely', 'really', 'super', 'totally', 'completely', 'absolutely']
            words = text.split()
            
            intensity = 0.5  # Base
            
            # Aumentar intensidade se há intensificadores
            for word in words:
                if word in intensifiers:
                    intensity += 0.2
            
            # Pontuação excessiva indica intensidade
            if '!' in text:
                intensity += 0.1 * text.count('!')
            
            return min(1.0, intensity)
            
        except Exception as e:
            nlp_logger.error(f"Erro no cálculo de intensidade: {e}")
            return 0.5

    def _load_knowledge_base(self):
        """Carrega base de conhecimento"""
        try:
            files_to_load = [
                (self.knowledge_base_file, 'knowledge_base'),
                (self.intents_file, 'intents'),
                (self.responses_file, 'responses')
            ]
            
            for file_path, attr_name in files_to_load:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        setattr(self, attr_name, json.load(f))
                    nlp_logger.info(f"Carregado: {attr_name}")
                
        except Exception as e:
            nlp_logger.error(f"Erro ao carregar base de conhecimento: {e}")

    def _load_conversation_history(self):
        """Carrega histórico de conversas"""
        try:
            if os.path.exists(self.conversations_file):
                with open(self.conversations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.conversation_history = data.get('conversations', [])
                    self.interaction_stats = data.get('stats', self.interaction_stats)
                    self.user_profiles = data.get('user_profiles', {})
                
        except Exception as e:
            nlp_logger.error(f"Erro ao carregar histórico: {e}")

    def _save_interaction(self, interaction: Dict):
        """Salva interação no histórico"""
        try:
            self.conversation_history.append(interaction)
            
            # Manter apenas últimas 1000 interações
            if len(self.conversation_history) > 1000:
                self.conversation_history = self.conversation_history[-1000:]
            
            # Salvar arquivo
            self._save_conversation_data()
            
        except Exception as e:
            nlp_logger.error(f"Erro ao salvar interação: {e}")

    def _save_conversation_data(self):
        """Salva dados de conversas"""
        try:
            data = {
                'conversations': self.conversation_history,
                'stats': self.interaction_stats,
                'user_profiles': self.user_profiles,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.conversations_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            nlp_logger.error(f"Erro ao salvar dados de conversas: {e}")

    def _update_stats(self, interaction: Dict):
        """Atualiza estatísticas"""
        try:
            self.interaction_stats['total_interactions'] += 1
            
            if interaction.get('confidence', 0) > self.confidence_threshold:
                self.interaction_stats['successful_responses'] += 1
            else:
                self.interaction_stats['failed_responses'] += 1
            
            # Atualizar tempo médio de resposta
            current_avg = self.interaction_stats['average_response_time']
            new_time = interaction.get('processing_time', 0)
            total = self.interaction_stats['total_interactions']
            
            self.interaction_stats['average_response_time'] = (current_avg * (total - 1) + new_time) / total
            
            # Contar intenções
            intent = interaction.get('intent', 'unknown')
            if intent in self.interaction_stats['most_common_intents']:
                self.interaction_stats['most_common_intents'][intent] += 1
            else:
                self.interaction_stats['most_common_intents'][intent] = 1
            
            # Contar uso de idiomas
            language = interaction.get('detected_language', 'pt')
            if language in self.interaction_stats['language_usage']:
                self.interaction_stats['language_usage'][language] += 1
            else:
                self.interaction_stats['language_usage'][language] = 1
                
        except Exception as e:
            nlp_logger.error(f"Erro ao atualizar estatísticas: {e}")

    def _update_user_profile(self, user_id: str, interaction: Dict):
        """Atualiza perfil do usuário"""
        try:
            if user_id not in self.user_profiles:
                self.user_profiles[user_id] = {
                    'first_interaction': interaction['timestamp'],
                    'total_interactions': 0,
                    'preferred_language': 'pt',
                    'common_intents': {},
                    'sentiment_history': [],
                    'satisfaction_scores': []
                }
            
            profile = self.user_profiles[user_id]
            profile['total_interactions'] += 1
            profile['last_interaction'] = interaction['timestamp']
            
            # Atualizar idioma preferido
            detected_lang = interaction.get('detected_language', 'pt')
            profile['preferred_language'] = detected_lang
            
            # Contar intenções
            intent = interaction.get('intent', 'unknown')
            if intent in profile['common_intents']:
                profile['common_intents'][intent] += 1
            else:
                profile['common_intents'][intent] = 1
            
            # Histórico de sentimentos
            sentiment = interaction.get('sentiment', 'neutral')
            profile['sentiment_history'].append(sentiment)
            
            # Manter apenas últimos 50 sentimentos
            if len(profile['sentiment_history']) > 50:
                profile['sentiment_history'] = profile['sentiment_history'][-50:]
                
        except Exception as e:
            nlp_logger.error(f"Erro ao atualizar perfil do usuário: {e}")

    # Implementar métodos restantes para completar a funcionalidade
    def _get_conversation_context(self, conversation_id: str) -> Dict:
        """Obtém contexto de uma conversa"""
        try:
            context_file = os.path.join(self.data_dir, f"context_{conversation_id}.json")
            if os.path.exists(context_file):
                with open(context_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {'conversation_id': conversation_id, 'history': [], 'topics': []}
        except Exception as e:
            nlp_logger.error(f"Erro ao obter contexto da conversa: {e}")
            return {'conversation_id': conversation_id, 'history': [], 'topics': []}

    def _save_conversation_context(self, conversation_id: str, context: Dict):
        """Salva contexto de uma conversa"""
        try:
            context_file = os.path.join(self.data_dir, f"context_{conversation_id}.json")
            with open(context_file, 'w', encoding='utf-8') as f:
                json.dump(context, f, indent=2, ensure_ascii=False)
        except Exception as e:
            nlp_logger.error(f"Erro ao salvar contexto da conversa: {e}")

    def _analyze_conversation_sentiment(self, history: List[Dict]) -> str:
        """Analisa sentimento geral da conversa"""
        try:
            if not history:
                return 'neutral'
            
            sentiments = [interaction.get('sentiment', 'neutral') for interaction in history]
            sentiment_counts = Counter(sentiments)
            
            # Retornar sentimento mais comum
            most_common = sentiment_counts.most_common(1)[0][0]
            return most_common
            
        except Exception as e:
            nlp_logger.error(f"Erro na análise de sentimento da conversa: {e}")
            return 'neutral'

    def _enrich_response_with_context(self, response: str, intent: str, context: Dict) -> str:
        """Enriquece resposta com contexto adicional"""
        try:
            # Adicionar informações específicas baseadas no contexto
            if intent == 'clean_request' and 'system_data' in context:
                system_data = context['system_data']
                temp_files = system_data.get('temp_files_mb', 0)
                if temp_files > 500:
                    response += f"\n\n💡 *Detectei {temp_files}MB de arquivos temporários. Recomendo limpeza prioritária!*"
            
            elif intent == 'performance' and 'performance_score' in context:
                score = context['performance_score']
                if score < 50:
                    response += f"\n\n⚠️ *Score de performance atual: {score}/100. Otimização urgente recomendada!*"
            
            elif intent == 'disk_space' and 'disk_usage' in context:
                usage = context['disk_usage']
                if usage > 90:
                    response += f"\n\n🚨 *Disco {usage}% cheio! Limpeza imediata necessária.*"
            
            return response
            
        except Exception as e:
            nlp_logger.error(f"Erro ao enriquecer resposta: {e}")
            return response

    def _get_auto_complete_suggestions(self, query: str) -> List[str]:
        """Obtém sugestões de auto-complete"""
        try:
            # Sugestões baseadas em consultas comuns
            common_queries = [
                "como limpar arquivos temporários",
                "como otimizar performance",
                "como liberar espaço em disco",
                "como remover malware",
                "como acelerar inicialização",
                "qual plano escolher",
                "how to clean temporary files",
                "how to optimize performance",
                "how to free disk space"
            ]
            
            # Filtrar sugestões que começam com a query
            suggestions = [q for q in common_queries if q.lower().startswith(query.lower())]
            
            # Se não há sugestões diretas, usar similaridade
            if not suggestions and len(query) > 2:
                suggestions = difflib.get_close_matches(query.lower(), common_queries, n=3, cutoff=0.3)
            
            return suggestions[:5]  # Máximo 5 sugestões
            
        except Exception as e:
            nlp_logger.error(f"Erro nas sugestões de auto-complete: {e}")
            return []

    def _get_related_questions(self, intent: str) -> List[str]:
        """Obtém perguntas relacionadas"""
        related_questions_map = {
            'clean_request': [
                "Com que frequência devo limpar meu PC?",
                "É seguro remover todos os arquivos temporários?",
                "Como programar limpezas automáticas?"
            ],
            'performance': [
                "Por que meu PC está lento?",
                "Quanto de RAM é necessário?",
                "Como verificar uso de CPU?"
            ],
            'disk_space': [
                "Como ver o que ocupa mais espaço?",
                "É seguro usar limpeza de disco do Windows?",
                "Como mover arquivos para nuvem?"
            ],
            'malware': [
                "Como prevenir vírus?",
                "Qual antivírus usar?",
                "Como fazer backup antes da limpeza?"
            ],
            'plans': [
                "Qual a diferença entre os planos?",
                "Posso testar antes de comprar?",
                "Como cancelar a assinatura?"
            ]
        }
        
        return related_questions_map.get(intent, [
            "Como posso otimizar meu PC?",
            "Quais são as melhores práticas?",
            "Preciso de ajuda técnica?"
        ])

    def _get_action_buttons(self, intent: str) -> List[Dict]:
        """Obtém botões de ação para interface"""
        action_buttons_map = {
            'clean_request': [
                {'text': '🧹 Iniciar Limpeza', 'action': 'start_cleanup'},
                {'text': '📊 Ver Relatório', 'action': 'show_report'},
                {'text': '⚙️ Configurar', 'action': 'configure_cleanup'}
            ],
            'performance': [
                {'text': '🚀 Otimizar Agora', 'action': 'optimize_now'},
                {'text': '📈 Análise Completa', 'action': 'full_analysis'},
                {'text': '⏱️ Agendar Otimização', 'action': 'schedule_optimization'}
            ],
            'help': [
                {'text': '📚 Ver Tutorial', 'action': 'show_tutorial'},
                {'text': '💬 Chat com Suporte', 'action': 'contact_support'},
                {'text': '❓ FAQ', 'action': 'show_faq'}
            ],
            'plans': [
                {'text': '🔍 Comparar Planos', 'action': 'compare_plans'},
                {'text': '🆓 Testar Grátis', 'action': 'free_trial'},
                {'text': '💳 Assinar Agora', 'action': 'subscribe'}
            ]
        }
        
        return action_buttons_map.get(intent, [
            {'text': '❓ Preciso de Ajuda', 'action': 'get_help'},
            {'text': '📞 Contato', 'action': 'contact_us'}
        ])

    def _get_quick_responses(self, intent: str) -> List[str]:
        """Obtém respostas rápidas para o usuário"""
        quick_responses_map = {
            'greeting': ["Oi!", "Olá!", "Preciso de ajuda", "Quero limpar meu PC"],
            'clean_request': ["Sim, iniciar", "Não, obrigado", "Mais informações", "Configurar primeiro"],
            'performance': ["Sim, otimizar", "Ver detalhes", "Não agora", "Agendar para depois"],
            'help': ["Entendi", "Preciso de mais ajuda", "Obrigado", "Falar com humano"],
            'plans': ["Ver preços", "Quero testar", "Preciso do Pro", "Qual recomenda?"]
        }
        
        return quick_responses_map.get(intent, ["OK", "Entendi", "Obrigado", "Preciso de mais ajuda"])

    def _extract_feedback_points(self, feedback_text: str) -> List[str]:
        """Extrai pontos principais do feedback"""
        try:
            # Dividir em sentenças
            sentences = re.split(r'[.!?]+', feedback_text)
            
            # Filtrar sentenças relevantes
            relevant_points = []
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 10:  # Ignorar sentenças muito curtas
                    relevant_points.append(sentence)
            
            return relevant_points[:5]  # Máximo 5 pontos
            
        except Exception as e:
            nlp_logger.error(f"Erro na extração de pontos de feedback: {e}")
            return [feedback_text]

    def _categorize_feedback(self, feedback_text: str) -> str:
        """Categoriza tipo de feedback"""
        try:
            text_lower = feedback_text.lower()
            
            # Categorias de feedback
            if any(word in text_lower for word in ['bug', 'erro', 'falha', 'problema', 'error', 'broken']):
                return 'bug_report'
            elif any(word in text_lower for word in ['sugestao', 'suggestion', 'feature', 'melhorar', 'improve']):
                return 'feature_request'
            elif any(word in text_lower for word in ['lento', 'slow', 'performance', 'velocidade']):
                return 'performance_issue'
            elif any(word in text_lower for word in ['dificil', 'confuso', 'difficult', 'confusing', 'usabilidade']):
                return 'usability_issue'
            elif any(word in text_lower for word in ['excelente', 'otimo', 'excellent', 'great', 'love']):
                return 'positive_feedback'
            else:
                return 'general_feedback'
                
        except Exception as e:
            nlp_logger.error(f"Erro na categorização de feedback: {e}")
            return 'general_feedback'

    def _generate_improvement_suggestions(self, analysis: Dict) -> List[str]:
        """Gera sugestões de melhoria baseadas no feedback"""
        try:
            suggestions = []
            
            category = analysis.get('category', 'general_feedback')
            sentiment = analysis.get('sentiment', 'neutral')
            
            if category == 'bug_report':
                suggestions.append("Investigar e corrigir bug reportado")
                suggestions.append("Implementar testes adicionais para prevenir problema")
            
            elif category == 'feature_request':
                suggestions.append("Avaliar viabilidade da funcionalidade solicitada")
                suggestions.append("Adicionar à roadmap de desenvolvimento")
            
            elif category == 'performance_issue':
                suggestions.append("Otimizar performance do sistema")
                suggestions.append("Revisar algoritmos de limpeza")
            
            elif category == 'usability_issue':
                suggestions.append("Melhorar interface do usuário")
                suggestions.append("Adicionar mais orientações e tutoriais")
            
            if sentiment == 'negative':
                suggestions.append("Entrar em contato com usuário para resolução")
                suggestions.append("Oferecer suporte técnico personalizado")
            
            return suggestions
            
        except Exception as e:
            nlp_logger.error(f"Erro na geração de sugestões: {e}")
            return ["Analisar feedback detalhadamente"]

    def _save_user_feedback(self, analysis: Dict):
        """Salva feedback do usuário"""
        try:
            feedback_file = os.path.join(self.data_dir, "user_feedback.json")
            
            # Carregar feedback existente
            if os.path.exists(feedback_file):
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    feedback_data = json.load(f)
            else:
                feedback_data = {'feedback_entries': []}
            
            # Adicionar nova entrada
            feedback_data['feedback_entries'].append(analysis)
            
            # Manter apenas últimos 500 feedbacks
            if len(feedback_data['feedback_entries']) > 500:
                feedback_data['feedback_entries'] = feedback_data['feedback_entries'][-500:]
            
            feedback_data['last_updated'] = datetime.now().isoformat()
            
            # Salvar arquivo
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(feedback_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            nlp_logger.error(f"Erro ao salvar feedback: {e}")

    def _generate_system_recommendations(self, system_data: Dict) -> List[str]:
        """Gera recomendações baseadas nos dados do sistema"""
        try:
            recommendations = []
            
            # Análise de performance
            performance_score = system_data.get('performance_score', 50)
            if performance_score < 30:
                recommendations.append("🚨 **Crítico**: Execute otimização completa imediatamente")
            elif performance_score < 60:
                recommendations.append("⚠️ **Atenção**: Sistema necessita otimização")
            else:
                recommendations.append("✅ **Bom**: Sistema funcionando adequadamente")
            
            # Análise de espaço em disco
            disk_usage = system_data.get('disk_usage_percent', 50)
            if disk_usage > 90:
                recommendations.append("🔴 **Urgente**: Libere espaço em disco imediatamente")
            elif disk_usage > 80:
                recommendations.append("🟡 **Recomendado**: Execute limpeza de arquivos")
            
            # Análise de memória
            memory_usage = system_data.get('memory_usage_percent', 50)
            if memory_usage > 85:
                recommendations.append("💾 **RAM**: Feche programas desnecessários")
            
            # Análise de inicialização
            startup_programs = system_data.get('startup_programs_count', 10)
            if startup_programs > 20:
                recommendations.append("🚀 **Inicialização**: Desabilite programas desnecessários")
            
            return recommendations
            
        except Exception as e:
            nlp_logger.error(f"Erro na geração de recomendações: {e}")
            return ["Execute diagnóstico completo do sistema"]

    def _generate_next_steps(self, system_data: Dict) -> List[str]:
        """Gera próximos passos baseados na análise"""
        try:
            next_steps = []
            
            performance_score = system_data.get('performance_score', 50)
            
            if performance_score < 50:
                next_steps.append("Execute limpeza completa do sistema")
                next_steps.append("Otimize programas de inicialização")
                next_steps.append("Faça verificação de malware")
                next_steps.append("Consider upgrade de hardware se necessário")
            else:
                next_steps.append("Mantenha limpezas regulares (semanal)")
                next_steps.append("Monitor performance periodicamente")
                next_steps.append("Mantenha backups atualizados")
            
            # Sempre incluir manutenção preventiva
            next_steps.append("Agende limpezas automáticas")
            next_steps.append("Configure alertas de performance")
            
            return next_steps
            
        except Exception as e:
            nlp_logger.error(f"Erro na geração de próximos passos: {e}")
            return ["Continue monitorando o sistema"]

    def get_system_health_report(self) -> Dict:
        """Obtém relatório de saúde do sistema NLP"""
        try:
            # Estatísticas atuais
            stats = self.get_conversation_statistics()
            
            # Análise de performance
            health_score = 100
            issues = []
            
            # Verificar taxa de sucesso
            success_rate = stats.get('success_rate', 0)
            if success_rate < 70:
                health_score -= 20
                issues.append("Taxa de sucesso baixa nas respostas")
            
            # Verificar tempo de resposta
            avg_response_time = stats.get('average_response_time', 0)
            if avg_response_time > 2.0:
                health_score -= 15
                issues.append("Tempo de resposta alto")
            
            # Verificar diversidade de intenções
            intent_count = len(stats.get('most_common_intents', {}))
            if intent_count < 5:
                health_score -= 10
                issues.append("Pouca diversidade nas intenções detectadas")
            
            # Verificar satisfação do usuário
            avg_satisfaction = stats.get('average_satisfaction', 0)
            if avg_satisfaction < 3.5:
                health_score -= 25
                issues.append("Satisfação do usuário baixa")
            
            return {
                'health_score': max(0, health_score),
                'status': 'healthy' if health_score > 80 else 'warning' if health_score > 60 else 'critical',
                'issues': issues,
                'recommendations': self._generate_health_recommendations(health_score, issues),
                'statistics': stats,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            nlp_logger.error(f"Erro no relatório de saúde: {e}")
            return {'error': str(e)}

    def _generate_health_recommendations(self, health_score: float, issues: List[str]) -> List[str]:
        """Gera recomendações para melhorar saúde do sistema"""
        recommendations = []
        
        if health_score < 60:
            recommendations.append("Revisar e expandir base de conhecimento")
            recommendations.append("Treinar modelos com mais dados")
            recommendations.append("Otimizar algoritmos de classificação")
        
        if "Taxa de sucesso baixa" in str(issues):
            recommendations.append("Adicionar mais padrões de intenção")
            recommendations.append("Melhorar respostas padrão")
        
        if "Tempo de resposta alto" in str(issues):
            recommendations.append("Otimizar processamento de texto")
            recommendations.append("Implementar cache de respostas")
        
        if "Satisfação do usuário baixa" in str(issues):
            recommendations.append("Coletar mais feedback dos usuários")
            recommendations.append("Personalizar respostas por perfil")
        
        if not recommendations:
            recommendations.append("Sistema funcionando bem - manter monitoramento")
        
        return recommendations

    def cleanup_old_conversations(self, days_old: int = 90) -> int:
        """Remove conversas antigas"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            cutoff_iso = cutoff_date.isoformat()
            
            # Filtrar conversas recentes
            recent_conversations = []
            removed_count = 0
            
            for conversation in self.conversation_history:
                if conversation.get('timestamp', '') > cutoff_iso:
                    recent_conversations.append(conversation)
                else:
                    removed_count += 1
            
            # Atualizar histórico
            self.conversation_history = recent_conversations
            
            # Salvar dados atualizados
            self._save_conversation_data()
            
            # Limpar arquivos de contexto antigos
            context_files_removed = 0
            for file in os.listdir(self.data_dir):
                if file.startswith('context_') and file.endswith('.json'):
                    file_path = os.path.join(self.data_dir, file)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_time < cutoff_date:
                        try:
                            os.remove(file_path)
                            context_files_removed += 1
                        except Exception as e:
                            nlp_logger.error(f"Erro ao remover {file_path}: {e}")
            
            nlp_logger.info(f"Limpeza concluída: {removed_count} conversas e {context_files_removed} contextos removidos")
            return removed_count + context_files_removed
            
        except Exception as e:
            nlp_logger.error(f"Erro na limpeza de conversas: {e}")
            return 0

    def export_knowledge_base(self, export_path: str) -> bool:
        """Exporta base de conhecimento para arquivo"""
        try:
            export_data = {
                'knowledge_base': self.knowledge_base,
                'intents': self.intents,
                'responses': self.responses,
                'conversation_stats': self.interaction_stats,
                'export_timestamp': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            nlp_logger.info(f"Base de conhecimento exportada para: {export_path}")
            return True
            
        except Exception as e:
            nlp_logger.error(f"Erro ao exportar base de conhecimento: {e}")
            return False

    def import_knowledge_base(self, import_path: str) -> bool:
        """Importa base de conhecimento de arquivo"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validar estrutura dos dados
            required_keys = ['knowledge_base', 'intents', 'responses']
            if not all(key in import_data for key in required_keys):
                nlp_logger.error("Arquivo de importação com estrutura inválida")
                return False
            
            # Fazer backup atual
            backup_path = os.path.join(self.data_dir, f"knowledge_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            self.export_knowledge_base(backup_path)
            
            # Importar novos dados
            self.knowledge_base = import_data['knowledge_base']
            self.intents = import_data['intents']
            self.responses = import_data['responses']
            
            # Salvar arquivos atualizados
            self._save_knowledge_files()
            
            nlp_logger.info(f"Base de conhecimento importada de: {import_path}")
            return True
            
        except Exception as e:
            nlp_logger.error(f"Erro ao importar base de conhecimento: {e}")
            return False

    def _save_knowledge_files(self):
        """Salva arquivos de conhecimento"""
        try:
            files_to_save = [
                (self.knowledge_base_file, self.knowledge_base),
                (self.intents_file, self.intents),
                (self.responses_file, self.responses)
            ]
            
            for file_path, data in files_to_save:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            nlp_logger.error(f"Erro ao salvar arquivos de conhecimento: {e}")

    def train_from_conversations(self) -> Dict:
        """Treina sistema baseado no histórico de conversas"""
        try:
            training_results = {
                'new_intents_learned': 0,
                'improved_responses': 0,
                'patterns_discovered': [],
                'training_timestamp': datetime.now().isoformat()
            }
            
            # Analisar conversas para descobrir novos padrões
            intent_patterns = defaultdict(list)
            
            for conversation in self.conversation_history:
                user_input = conversation.get('cleaned_input', '')
                intent = conversation.get('intent', 'default')
                confidence = conversation.get('confidence', 0)
                
                # Coletar padrões de alta confiança
                if confidence > 0.8 and len(user_input) > 3:
                    intent_patterns[intent].append(user_input)
            
            # Adicionar novos padrões aos intents existentes
            for intent, patterns in intent_patterns.items():
                if intent in self.intents:
                    existing_patterns = self.intents[intent].get('patterns', [])
                    new_patterns = []
                    
                    for pattern in patterns:
                        # Extrair palavras-chave do padrão
                        keywords = [word for word in pattern.split() if len(word) > 3]
                        for keyword in keywords:
                            if keyword not in existing_patterns and len(keyword) > 3:
                                new_patterns.append(keyword)
                    
                    if new_patterns:
                        self.intents[intent]['patterns'].extend(new_patterns)
                        training_results['new_intents_learned'] += len(new_patterns)
            
            # Salvar intents atualizados
            self._save_knowledge_files()
            
            nlp_logger.info(f"Treinamento concluído: {training_results['new_intents_learned']} novos padrões aprendidos")
            return training_results
            
        except Exception as e:
            nlp_logger.error(f"Erro no treinamento: {e}")
            return {'error': str(e)}

# Funções utilitárias
def quick_chat(user_message: str, user_id: str = "anonymous") -> Dict:
    """Chat rápido com o assistente"""
    assistant = NLPAssistant()
    return assistant.process_user_input(user_message, user_id)

def analyze_sentiment_quick(text: str) -> Dict:
    """Análise rápida de sentimento"""
    assistant = NLPAssistant()
    return assistant.analyze_text_sentiment(text)

def extract_info_quick(text: str) -> Dict:
    """Extração rápida de informações"""
    assistant = NLPAssistant()
    return assistant.extract_information(text)

def generate_report_quick(system_data: Dict) -> str:
    """Geração rápida de relatório"""
    assistant = NLPAssistant()
    return assistant.generate_system_report(system_data)

def start_conversation(user_id: str = "anonymous") -> Dict:
    """Inicia nova conversa"""
    assistant = NLPAssistant()
    return assistant.chat_conversation("Olá", user_id=user_id)

def get_assistant_stats() -> Dict:
    """Obtém estatísticas do assistente"""
    assistant = NLPAssistant()
    return assistant.get_conversation_statistics()

def train_assistant() -> Dict:
    """Treina assistente com conversas existentes"""
    assistant = NLPAssistant()
    return assistant.train_from_conversations()

# Exemplo de uso e teste
if __name__ == "__main__":
    # Teste básico do sistema
    assistant = NLPAssistant()
    
    # Teste de conversação
    test_messages = [
        "Olá, preciso de ajuda",
        "Meu PC está muito lento",
        "Como posso limpar arquivos temporários?",
        "Qual plano vocês recomendam?",
        "Obrigado pela ajuda!"
    ]
    
    print("🤖 Testando NLP Assistant...")
    print("=" * 50)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n👤 Usuário {i}: {message}")
        
        response = assistant.process_user_input(message, "test_user")
        print(f"🤖 Clara: {response['response']}")
        print(f"   Intent: {response['intent']} (confiança: {response['confidence']:.2f})")
        print(f"   Sentimento: {response['sentiment']}")
        
    print("\n" + "=" * 50)
    print("✅ Teste concluído!")
    
    # Exibir estatísticas
    stats = assistant.get_conversation_statistics()
    print(f"\n📊 Estatísticas:")
    print(f"   Total de interações: {stats['total_interactions']}")
    print(f"   Taxa de sucesso: {stats.get('success_rate', 0):.1f}%")
    print(f"   Tempo médio de resposta: {stats['average_response_time']:.3f}s")