# app/modules/assistente/services/voice_service.py
import logging
import tempfile
import base64
import os
from io import BytesIO
from typing import Optional, Tuple
import speech_recognition as sr
import edge_tts


# Voz padrão — única fonte de verdade
DEFAULT_VOICE = "pt-BR-AntonioNeural"

# Mapeamento de nome amigável → ID técnico
VOICE_MAP = {
    "francisca": "pt-BR-FranciscaNeural",
    "antonio":   "pt-BR-AntonioNeural",
    "thalita":   "pt-BR-ThalitaNeural",
    "julio":     "pt-BR-JulioNeural",
    "leila":     "pt-BR-LeilaNeural",
}


class VoiceService:
    """Serviço para operações de voz (STT e TTS)"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.recognizer = sr.Recognizer()

    # ============ STT ============
    def speech_to_text(self, audio_data: bytes) -> Tuple[bool, str]:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            try:
                with sr.AudioFile(tmp_path) as source:
                    audio = self.recognizer.record(source)

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
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

        except Exception as e:
            self.logger.error(f"Erro no speech_to_text: {e}")
            return False, f"Erro ao processar áudio: {e}"

    # ============ TTS ============
    async def text_to_speech(self, text: str) -> Optional[str]:
        """
        Converte texto em áudio MP3 base64 usando Edge TTS.
        A voz é escolhida aqui dentro (não vem por parâmetro).
        """
        try:
            if not text or not text.strip():
                return None

            voice = self._get_voice()
            self.logger.info(f"🔊 TTS usando voz: '{voice}'")

            audio_bytes = await self._synthesize(text, voice)
            if not audio_bytes:
                return None

            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            return f"data:audio/mp3;base64,{audio_b64}"

        except Exception as e:
            self.logger.error(f"Erro no Edge TTS: {e}")
            return None

    def _get_voice(self) -> str:
        """
        Decide qual voz usar.
        Hoje: constante DEFAULT_VOICE.
        Amanhã: pode ler do banco (preferência do usuário) ou do Master config.
        """
        # TODO: futuramente ler do banco de dados
        return DEFAULT_VOICE

    async def _synthesize(self, text: str, voice: str) -> bytes:
        """Executa a síntese assíncrona do Edge TTS"""
        communicate = edge_tts.Communicate(text, voice)
        audio_buffer = BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])
        return audio_buffer.getvalue()