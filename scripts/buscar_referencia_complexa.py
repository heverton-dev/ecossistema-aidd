# -*- coding: utf-8 -*-
from aidd_forge.core.mobbin_client import executar_busca
import json

res = executar_busca(query="trading crypto financial terminal", platform="web", mode="standard", limit=4)
screens = res.get("screens", [])
for i, s in enumerate(screens):
    app = s.get("app_name")
    img = s.get("image_url") or s.get("image", {}).get("url")
    mid = s.get("id")
    print(f"[{i}] App: {app} | ID: {mid} | Img: {img}")
