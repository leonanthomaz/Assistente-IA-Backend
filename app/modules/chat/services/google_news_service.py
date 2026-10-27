# app/modules/chat/services/google_news_service.py
import logging
import requests
from typing import Dict, List
from datetime import datetime
import feedparser
import re
from urllib.parse import urlparse

class GoogleNewsService:
    """Serviço para buscar notícias via Google News (apenas Brasil)"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://news.google.com/rss"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
                
    def buscar_noticias_recentes(self, limite: int = 10) -> List[Dict]:
        """Busca notícias recentes (sem filtro específico)"""
        try:
            url = f"{self.base_url}/headlines/section/world?hl=pt-BR&gl=BR&ceid=BR:pt-419"
            
            self.logger.info(f"🔍 Buscando notícias recentes")
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                self.logger.warning(f"⚠️ Erro ao acessar Google News: {response.status_code}")
                return []
            
            feed = feedparser.parse(response.content)
            
            noticias = []
            for entry in feed.entries[:limite]:
                noticias.append(self._parse_entry(entry))
            
            self.logger.info(f"✅ Encontradas {len(noticias)} notícias recentes")
            return noticias
            
        except Exception as e:
            self.logger.error(f"❌ Erro: {e}")
            return []
    
    def _parse_entry(self, entry) -> Dict:
        """Parseia uma entrada do feed do Google News"""
        link_original = self._extrair_url_original(entry.get('link', ''))
        
        data = entry.get('published', '')
        try:
            data_dt = datetime.strptime(data, '%a, %d %b %Y %H:%M:%S %Z')
            data_formatada = data_dt.strftime('%d/%m/%Y %H:%M')
        except:
            data_formatada = data
        
        resumo_limpo = self._limpar_resumo(entry.get('summary', ''))
        
        return {
            "titulo": entry.get('title', 'Sem título'),
            "link_original": link_original,
            "link_google": entry.get('link', ''),
            "data": data_formatada,
            "fonte": entry.get('source', {}).get('title', 'Google News'),
            "resumo": resumo_limpo,
            "provider": "google_news"
        }
    
    def _extrair_url_original(self, link_google: str) -> str:
        """Extrai a URL original do link do Google News"""
        try:
            try:
                response = requests.head(link_google, allow_redirects=True, timeout=5)
                return response.url
            except:
                pass
            
            parsed = urlparse(link_google)
            if 'news.google.com' in parsed.netloc:
                if parsed.fragment:
                    return parsed.fragment
                
                try:
                    response = requests.get(link_google, timeout=5)
                    match = re.search(r'<a href="([^"]+)"', response.text)
                    if match:
                        return match.group(1)
                except:
                    pass
            
            return link_google
            
        except Exception as e:
            self.logger.debug(f"Erro ao extrair URL original: {e}")
            return link_google
    
    def _limpar_resumo(self, resumo: str) -> str:
        """Limpa o resumo removendo tags HTML e links"""
        try:
            resumo_limpo = re.sub(r'<[^>]+>', '', resumo)
            resumo_limpo = re.sub(r'\s+', ' ', resumo_limpo)
            resumo_limpo = resumo_limpo.replace('&nbsp;', ' ')
            resumo_limpo = resumo_limpo.replace('&amp;', '&')
            resumo_limpo = resumo_limpo.strip()
            
            if len(resumo_limpo) > 500:
                resumo_limpo = resumo_limpo[:500] + '...'
            
            return resumo_limpo
            
        except Exception as e:
            return resumo