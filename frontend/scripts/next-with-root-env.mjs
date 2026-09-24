import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import nextEnv from '@next/env';

const { loadEnvConfig } = nextEnv;
const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const frontendDirectory = path.resolve(scriptDirectory, '..');
const repositoryRoot = path.resolve(frontendDirectory, '..');

// Load the repository's single source of configuration before Next starts.
// Next will still expose only NEXT_PUBLIC_* values to browser code.
loadEnvConfig(repositoryRoot);

const nextBin = path.join(frontendDirectory, 'node_modules', 'next', 'dist', 'bin', 'next');
const child = spawn(process.execPath, [nextBin, ...process.argv.slice(2)], {
  cwd: frontendDirectory,
  env: process.env,
  stdio: 'inherit',
});

child.on('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 1);
});
