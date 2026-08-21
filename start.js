#!/usr/bin/env node

const { spawn } = require('child_process');

const args = process.argv.slice(2);
const pythonCmd = process.env.PYTHON || 'python3';

let scriptToRun;
let scriptArgs;

if (args.length === 0) {
  scriptToRun = 'api/app.py';
  scriptArgs = [];
} else {
  scriptToRun = 'rss_scanner.py';
  scriptArgs = args;
}

function runProcess(cmd) {
  let settled = false;
  const child = spawn(cmd, [scriptToRun, ...scriptArgs], {
    stdio: 'inherit',
    env: process.env
  });

  child.on('error', (err) => {
    if (settled) return;
    settled = true;
    if (err.code === 'ENOENT' && cmd === 'python3') {
      runProcess('python');
    } else {
      console.error(`Error executing ${cmd}: ${err.message}`);
      process.exit(1);
    }
  });

  child.on('exit', (code, signal) => {
    if (settled) return;
    settled = true;
    if (signal) {
      process.kill(process.pid, signal);
    } else {
      process.exit(code !== null ? code : 0);
    }
  });
}

runProcess(pythonCmd);
