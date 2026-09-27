#!/usr/bin/env node
/**
 * Tesla Fleet Telemetry Streaming Client
 * Uses Node.js native WebSocket to stream live telemetry from Tessie.
 */

const fs = require('fs');
const path = require('path');

function getEnv(name) {
  if (process.env[name]) return process.env[name].trim();
  const zshrc = path.join(process.env.HOME || '', '.zshrc');
  if (fs.existsSync(zshrc)) {
    try {
      const content = fs.readFileSync(zshrc, 'utf8');
      const match = content.match(new RegExp(`^\\s*(?:export\\s+)?${name}=["']?([^"'\\s#]+)`, 'm'));
      if (match) return match[1].trim();
    } catch (_) {}
  }
  return null;
}

const args = process.argv.slice(2);
let vin = null;
let duration = 15;
let outputJson = false;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--vin' && args[i + 1]) {
    vin = args[i + 1];
    i++;
  } else if (args[i] === '--duration' && args[i + 1]) {
    duration = parseInt(args[i + 1], 10);
    i++;
  } else if (args[i] === '--json') {
    outputJson = true;
  }
}

const token = getEnv('TESSIE_ACCESS_TOKEN');
if (!token) {
  console.error('Error: TESSIE_ACCESS_TOKEN not found in environment or ~/.zshrc');
  process.exit(1);
}

if (!vin) {
  vin = getEnv('MY_TESLA_VIN') || process.env.TESLA_VIN || 'LRWYHCFS2NC464870';
}

const url = `wss://streaming.tessie.com/${vin}?access_token=${token}`;
console.log(`[Telemetry] Connecting to wss://streaming.tessie.com/${vin}...`);
console.log(`[Telemetry] Will stream for ${duration} seconds.`);

const ws = new WebSocket(url);

const timer = setTimeout(() => {
  console.log(`\n[Telemetry] Stream duration reached (${duration}s). Closing.`);
  ws.close();
  process.exit(0);
}, duration * 1000);

ws.onopen = () => {
  console.log(`[Telemetry] Connected! Listening for real-time vehicle events...\n`);
};

ws.onmessage = (event) => {
  if (outputJson) {
    console.log(event.data);
    return;
  }

  try {
    const msg = JSON.parse(event.data);
    const time = msg.createdAt ? new Date(msg.createdAt).toLocaleTimeString() : new Date().toLocaleTimeString();

    if (msg.data && Array.isArray(msg.data)) {
      msg.data.forEach((item) => {
        const key = item.key;
        const valObj = item.value || {};
        const val = valObj.doubleValue ?? valObj.stringValue ?? valObj.intValue ?? JSON.stringify(valObj);
        console.log(`[${time}] [DATA] ${key.padEnd(22)} : ${val}`);
      });
    } else if (msg.alerts && Array.isArray(msg.alerts)) {
      msg.alerts.forEach((alert) => {
        console.log(`[${time}] [ALERT] ${alert.name} (Started: ${alert.startedAt || 'N/A'})`);
      });
    } else if (msg.status) {
      console.log(`[${time}] [STATUS] Vehicle connection: ${msg.status}`);
    } else {
      console.log(`[${time}] [RAW] ${event.data}`);
    }
  } catch (err) {
    console.log(`[MSG] ${event.data}`);
  }
};

ws.onerror = (err) => {
  console.error('[Telemetry] WebSocket error:', err.message || err);
};

ws.onclose = (event) => {
  clearTimeout(timer);
  if (event.code !== 1000 && event.code !== 1005) {
    console.log(`[Telemetry] Disconnected (code: ${event.code}, reason: ${event.reason || 'None'})`);
  }
};
