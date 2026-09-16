import importlib.util
import os
import tempfile

GATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "G_FRONTEND_LAYERS.py")
_spec = importlib.util.spec_from_file_location("g_frontend_layers", GATE_PATH)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)
audit_frontend_file = gate.audit_frontend_file
scan_frontend_layers = gate.scan_frontend_layers


def test_ui_component_sem_chamada_rede_passa():
    with tempfile.TemporaryDirectory() as tmpdir:
        ui_dir = os.path.join(tmpdir, "components", "ui")
        os.makedirs(ui_dir, exist_ok=True)
        btn_file = os.path.join(ui_dir, "Button.tsx")
        with open(btn_file, "w", encoding="utf-8") as f:
            f.write("""
            import React from 'react';
            export const Button = ({ children, onClick }: any) => {
                return <button onClick={onClick}>{children}</button>;
            };
            """)
        
        violacoes = audit_frontend_file(btn_file)
        assert len(violacoes) == 0


def test_ui_component_com_fetch_direto_falha():
    with tempfile.TemporaryDirectory() as tmpdir:
        ui_dir = os.path.join(tmpdir, "components", "ui")
        os.makedirs(ui_dir, exist_ok=True)
        card_file = os.path.join(ui_dir, "Card.tsx")
        with open(card_file, "w", encoding="utf-8") as f:
            f.write("""
            import React, { useEffect } from 'react';
            export const Card = () => {
                useEffect(() => {
                    fetch('/api/dados');
                }, []);
                return <div>Card</div>;
            };
            """)
        
        violacoes = audit_frontend_file(card_file)
        assert len(violacoes) == 1
        assert "fetch()" in violacoes[0][2]


def test_hook_com_fetch_fora_de_ui_passa():
    with tempfile.TemporaryDirectory() as tmpdir:
        hooks_dir = os.path.join(tmpdir, "hooks")
        os.makedirs(hooks_dir, exist_ok=True)
        hook_file = os.path.join(hooks_dir, "useData.ts")
        with open(hook_file, "w", encoding="utf-8") as f:
            f.write("""
            export const useData = () => {
                return fetch('/api/dados').then(r => r.json());
            };
            """)
        
        violacoes = audit_frontend_file(hook_file)
        assert len(violacoes) == 0
