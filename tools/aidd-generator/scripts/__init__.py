"""
proj-yt-list - Sistema AIDD de Análise de YouTube
AI-Driven Development Framework v1.0.0
"""

__version__ = "1.0.0"
__author__ = "Engenheiro Agêntico"
__description__ = "Sistema de Análise Inteligente de Listas de Vídeos YouTube via AIDD"

# Importar módulos principais
try:
    from .persistencia import estado_projeto
    from .validacao import gate_g0_qualidade
except ImportError:
    pass  # Em caso de importação parcial
