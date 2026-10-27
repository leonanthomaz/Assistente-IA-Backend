# app/modules/assistente/services/voice_service.py
import logging
import tempfile
import base64
import os
from io import BytesIO
from typing import Optional, Tuple
import speech_recognition as sr
from gtts import gTTS


class VoiceService:
    """Serviço para operações de voz (STT e TTS)"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.recognizer = sr.Recognizer()
    
    def speech_to_text(self, audio_data: bytes) -> Tuple[bool, str]:
        """
        Converte áudio (WAV) para texto usando Google Speech Recognition
        Retorna (sucesso, texto)
        """
        try:
            # Salva o áudio temporariamente
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name
            
            try:
                # Reconhece o áudio
                with sr.AudioFile(tmp_path) as source:
                    audio = self.recognizer.record(source)
                
                # Usa o Google Speech Recognition (gratuito, precisa de internet)
                text = self.recognizer.recognize_google(audio, language="pt-BR")
                self.logger.info(f"🎤 Áudio convertido: {text}")
                return True, text
                
            except sr.UnknownValueError:
                self.logger.warning("Não foi possível entender o áudio")
                return False, "Não entendi o que você disse"
            except sr.RequestError as e:
                self.logger.error(f"Erro no serviço de reconhecimento: {e}")
                return False, f"Erro no reconhecimento: {e}"
            finally:
                # Limpa o arquivo temporário
                try:
                    os.remove(tmp_path)
                except:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Erro no speech_to_text: {e}")
            return False, f"Erro ao processar áudio: {e}"
    
    def text_to_speech(self, text: str, lang: str = "pt") -> Optional[str]:
        """
        Converte texto para áudio (MP3) e retorna como base64
        """
        try:
            if not text or text.strip() == "":
                return None
            
            # Gera o áudio com gTTS
            tts = gTTS(text=text, lang=lang, slow=False)
            audio_buffer = BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            # Converte para base64
            audio_base64 = base64.b64encode(audio_buffer.getvalue()).decode("utf-8")
            audio_base64 = f"data:audio/mp3;base64,{audio_base64}"
            
            self.logger.info(f"🔊 Áudio gerado com sucesso ({len(text)} caracteres)")
            return audio_base64
            
        except Exception as e:
            self.logger.error(f"Erro no text_to_speech: {e}")
            return None
    
    def text_to_speech_file(self, text: str, filename: str, lang: str = "pt") -> bool:
        """
        Converte texto para áudio e salva em arquivo
        """
        try:
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(filename)
            self.logger.info(f"🔊 Áudio salvo em: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar áudio: {e}")
            return False