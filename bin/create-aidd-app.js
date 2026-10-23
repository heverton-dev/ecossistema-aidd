#!/usr/bin/env node
/**
 * @aidd/create — Scaffold de 1 Clique para o Ecossistema AIDD
 * Padrão-Ouro RevNault: TanStack Router + React 19 + Tailwind CSS + FastAPI + SQLite WAL
 */

const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const args = process.argv.slice(2);
const appName = args[0] || 'meu-app-aidd';

console.log('==================================================');
console.log('🚀 [AIDD NPX] Criando aplicação de alta fidelidade: ' + appName);
console.log('==================================================');

const rootDir = path.resolve(__dirname, '..');
const scriptPy = path.join(rootDir, 'scripts', 'create_aidd_app.py');

if (fs.existsSync(scriptPy)) {
  const result = spawnSync('python', [scriptPy, ...args], { stdio: 'inherit', shell: true });
  process.exit(result.status || 0);
} else {
  console.log('Executando instalador autônomo...');
  const result = spawnSync('python', ['-m', 'scripts.create_aidd_app', ...args], { stdio: 'inherit', shell: true });
  process.exit(result.status || 0);
}
