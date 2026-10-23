#!/usr/bin/env node
/**
 * aidd / @aidd/create — CLI Universal para o Ecossistema AIDD
 * Padrão-Ouro: TanStack Router + React 19 + Tailwind CSS + FastAPI + SQLite WAL
 */

const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const args = process.argv.slice(2);
const rootDir = path.resolve(__dirname, '..');
const scriptPy = path.join(rootDir, 'scripts', 'cli_entrypoint.py');

if (fs.existsSync(scriptPy)) {
  const result = spawnSync('python', [scriptPy, ...args], { stdio: 'inherit', shell: true });
  process.exit(result.status || 0);
} else {
  const result = spawnSync('python', ['-m', 'scripts.cli_entrypoint', ...args], { stdio: 'inherit', shell: true });
  process.exit(result.status || 0);
}
