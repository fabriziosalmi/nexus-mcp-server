# -*- coding: utf-8 -*-
# tools/text_analysis_tools.py
import logging
import re
from collections import Counter
import math

def register_tools(mcp):
    """Registra i tool di analisi del testo con l'istanza del server MCP."""
    logging.info("📝 Registrazione tool-set: Text Analysis Tools")

    @mcp.tool()
    def analyze_text_sentiment(text: str) -> str:
        """
        Analizza il sentiment di un testo (versione base con dizionario).
        
        Args:
            text: Testo da analizzare
        """
        try:
            # Dizionari semplici per l'analisi del sentiment
            positive_words = {
                'buono', 'ottimo', 'eccellente', 'fantastico', 'perfetto', 'magnifico',
                'bello', 'meraviglioso', 'stupendo', 'felice', 'gioioso', 'contento',
                'soddisfatto', 'piacevole', 'gradevole', 'positivo', 'good', 'great',
                'excellent', 'fantastic', 'perfect', 'wonderful', 'amazing', 'happy',
                'love', 'like', 'best', 'awesome', 'brilliant', 'outstanding'
            }
            
            negative_words = {
                'cattivo', 'pessimo', 'terribile', 'orribile', 'brutto', 'disgustoso',
                'triste', 'arrabbiato', 'deluso', 'frustrato', 'negativo', 'sbagliato',
                'problema', 'errore', 'difetto', 'bad', 'terrible', 'awful', 'horrible',
                'hate', 'dislike', 'worst', 'wrong', 'problem', 'error', 'fail',
                'poor', 'disappointing', 'sad', 'angry', 'frustrated'
            }
            
            # Pulisce e divide il testo
            words = re.findall(r'\b\w+\b', text.lower())
            
            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)
            total_sentiment_words = positive_count + negative_count
            
            if total_sentiment_words == 0:
                sentiment = "Neutrale"
                confidence = 0
            else:
                score = (positive_count - negative_count) / total_sentiment_words
                confidence = total_sentiment_words / len(words) * 100 if words else 0
                
                if score > 0.2:
                    sentiment = "Positivo"
                elif score < -0.2:
                    sentiment = "Negativo"
                else:
                    sentiment = "Neutrale"
            
            return f"""😊 ANALISI SENTIMENT
Testo: {text[:100]}{'...' if len(text) > 100 else ''}
Sentiment: {sentiment}
Parole positive: {positive_count}
Parole negative: {negative_count}
Confidenza: {confidence:.1f}%
Parole totali: {len(words)}"""
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def word_frequency_analysis(text: str, top_n: int = 10) -> str:
        """
        Analizza la frequenza delle parole in un testo.
        
        Args:
            text: Testo da analizzare
            top_n: Numero di parole più frequenti da mostrare
        """
        try:
            # Pulisce il testo e estrae le parole
            words = re.findall(r'\b\w+\b', text.lower())
            
            # Rimuove parole comuni (stop words)
            stop_words = {
                'il', 'la', 'di', 'che', 'e', 'un', 'a', 'è', 'per', 'una', 'in',
                'con', 'i', 'si', 'non', 'le', 'da', 'lo', 'su', 'al', 'del',
                'the', 'and', 'a', 'an', 'as', 'are', 'was', 'were', 'been', 'be',
                'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
                'could', 'can', 'may', 'might', 'must', 'shall', 'to', 'of', 'in',
                'for', 'on', 'with', 'at', 'by', 'from', 'up', 'about', 'into',
                'through', 'during', 'before', 'after', 'above', 'below', 'between'
            }
            
            # Filtra le parole
            filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
            
            # Conta le frequenze
            word_freq = Counter(filtered_words)
            total_words = len(filtered_words)
            unique_words = len(word_freq)
            
            # Top N parole
            top_words = word_freq.most_common(top_n)
            
            result = f"""📊 ANALISI FREQUENZA PAROLE
Parole totali: {total_words}
Parole unique: {unique_words}
Diversità lessicale: {(unique_words/total_words*100):.1f}%

Top {top_n} parole più frequenti:
"""
            
            for i, (word, count) in enumerate(top_words, 1):
                percentage = (count / total_words * 100)
                result += f"{i:2d}. {word:<15} {count:3d} volte ({percentage:.1f}%)\n"
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def readability_score(text: str) -> str:
        """
        Calcola indici di leggibilità del testo.
        
        Args:
            text: Testo da analizzare
        """
        try:
            # Conta frasi, parole e sillabe (approssimativo)
            sentences = len(re.findall(r'[.!?]+', text))
            words = len(re.findall(r'\b\w+\b', text))
            
            # Stima sillabe contando le vocali
            vowels = 'aeiouAEIOU'
            syllables = 0
            for word in re.findall(r'\b\w+\b', text):
                word_syllables = len(re.findall(r'[aeiouAEIOU]', word))
                if word_syllables == 0:
                    word_syllables = 1
                syllables += word_syllables
            
            if sentences == 0 or words == 0:
                return "ERRORE: Testo insufficiente per l'analisi"
            
            # Calcola metriche
            avg_words_per_sentence = words / sentences
            avg_syllables_per_word = syllables / words
            
            # Flesch Reading Ease Score (adattato)
            flesch_score = 206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)
            flesch_score = max(0, min(100, flesch_score))  # Limita tra 0 e 100
            
            # Interpreta il punteggio
            if flesch_score >= 90:
                level = "Molto facile"
            elif flesch_score >= 80:
                level = "Facile"
            elif flesch_score >= 70:
                level = "Abbastanza facile"
            elif flesch_score >= 60:
                level = "Standard"
            elif flesch_score >= 50:
                level = "Abbastanza difficile"
            elif flesch_score >= 30:
                level = "Difficile"
            else:
                level = "Molto difficile"
            
            return f"""📖 ANALISI LEGGIBILITÀ
Frasi: {sentences}
Parole: {words}
Sillabe: {syllables}
Parole per frase: {avg_words_per_sentence:.1f}
Sillabe per parola: {avg_syllables_per_word:.1f}
Punteggio Flesch: {flesch_score:.1f}/100
Livello: {level}

Lunghezza caratteri: {len(text)}
Lunghezza media parola: {len(text.replace(' ', ''))/words:.1f} caratteri"""
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def detect_language_simple(text: str) -> str:
        """
        Rileva la lingua del testo usando pattern semplici.
        
        Args:
            text: Testo da analizzare
        """
        try:
            # Parole comuni per diverse lingue
            language_patterns = {
                'italian': {
                    'words': ['il', 'la', 'di', 'che', 'e', 'un', 'a', 'è', 'per', 'una', 'in', 'con', 'non', 'del', 'della', 'questo', 'sono', 'nel', 'gli', 'alla'],
                    'chars': 'àèéìíîòóù'
                },
                'english': {
                    'words': ['the', 'and', 'a', 'to', 'of', 'in', 'i', 'you', 'it', 'have', 'for', 'not', 'with', 'on', 'do', 'be', 'at', 'by', 'this', 'but'],
                    'chars': ''
                },
                'spanish': {
                    'words': ['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para'],
                    'chars': 'ñáéíóúü'
                },
                'french': {
                    'words': ['le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir', 'que', 'pour', 'dans', 'ce', 'son', 'une', 'sur', 'avec', 'ne', 'se'],
                    'chars': 'àâäéèêëïîôùûüÿç'
                },
                'german': {
                    'words': ['der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich', 'des', 'auf', 'für', 'ist', 'im', 'dem', 'nicht', 'ein', 'eine', 'als'],
                    'chars': 'äöüß'
                }
            }
            
            text_lower = text.lower()
            words = re.findall(r'\b\w+\b', text_lower)
            
            scores = {}
            for lang, patterns in language_patterns.items():
                score = 0
                # Punteggio per parole comuni
                for word in patterns['words']:
                    score += text_lower.count(word) * 2
                
                # Punteggio per caratteri speciali
                for char in patterns['chars']:
                    score += text_lower.count(char)
                
                scores[lang] = score
            
            # Trova la lingua con il punteggio più alto
            if not scores or max(scores.values()) == 0:
                detected_lang = "Sconosciuta"
                confidence = 0
            else:
                detected_lang = max(scores, key=scores.get)
                total_score = sum(scores.values())
                confidence = scores[detected_lang] / total_score * 100 if total_score > 0 else 0
            
            return f"""🌍 RILEVAMENTO LINGUA
Lingua rilevata: {detected_lang.title()}
Confidenza: {confidence:.1f}%
Parole analizzate: {len(words)}

Punteggi per lingua:
""" + '\n'.join([f"{lang.title()}: {score}" for lang, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)])
            
        except Exception as e:
            return f"ERRORE: {str(e)}"