# -*- coding: utf-8 -*-
"""Camada de Interfaces da fatia vertical {{ cookiecutter.slug }}."""

# Re-exporta o registrador de rotas para quem importa de interfaces diretamente.
from .routes import registrar_rotas  # noqa: F401

__all__ = ["registrar_rotas"]