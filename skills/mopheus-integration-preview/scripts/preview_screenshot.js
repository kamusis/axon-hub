#!/usr/bin/env node
/**
 * preview_screenshot.js — Native, deterministic screenshot tool for Mopheus preview.
 *
 * Usage:
 *   node preview_screenshot.js --url <path_or_url> --output <path.png> [options]
 *
 * Options:
 *   --url <url>              Relative path (e.g. /dev-space/tickets/:id) or full URL
 *   --output <path>          Destination PNG file path
 *   --selector <css>         Optional CSS selector to screenshot specific element
 *   --hover <css>            Optional CSS selector to hover before capture (e.g. for HoverCard)
 *   --wait <ms>              Extra delay in ms before capture (default: 1000)
 *   --backend <url>          Backend API URL (default: http://localhost:8230)
 *   --frontend <url>         Frontend base URL (default: http://localhost:3230)
 *   --email <email>          Login email (default: alice@mopheus.dev)
 *   --password <pwd>         Login password (default: Mopheus@123)
 */

const fs = require('fs');
const path = require('path');

// Parse CLI arguments
function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    url: '',
    output: '',
    selector: null,
    hover: null,
    wait: 1000,
    backend: 'http://localhost:8230',
    frontend: 'http://localhost:3230',
    email: 'alice@mopheus.dev',
    password: 'Mopheus@123',
  };

  for (let i = 0; i < args.length; i++) {
    const key = args[i];
    const val = args[i + 1];
    if (key === '--url') { options.url = val; i++; }
    else if (key === '--output') { options.output = val; i++; }
    else if (key === '--selector') { options.selector = val; i++; }
    else if (key === '--hover') { options.hover = val; i++; }
    else if (key === '--wait') { options.wait = parseInt(val, 10); i++; }
    else if (key === '--backend') { options.backend = val; i++; }
    else if (key === '--frontend') { options.frontend = val; i++; }
    else if (key === '--email') { options.email = val; i++; }
    else if (key === '--password') { options.password = val; i++; }
  }

  if (!options.url || !options.output) {
    console.error('Usage: preview_screenshot.js --url <url> --output <output.png> [--selector <css>] [--hover <css>]');
    process.exit(1);
  }
  return options;
}

// Find Playwright chromium binary
function findChromiumExecutable() {
  const candidates = [
    '/usr/bin/google-chrome',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
  ];

  const cacheBase = path.join(process.env.HOME || '', '.cache', 'ms-playwright');
  if (fs.existsSync(cacheBase)) {
    try {
      const dirs = fs.readdirSync(cacheBase).filter((d) => d.startsWith('chromium'));
      for (const d of dirs) {
        const shellPath = path.join(cacheBase, d, 'chrome-headless-shell-linux64', 'chrome-headless-shell');
        if (fs.existsSync(shellPath)) candidates.unshift(shellPath);
      }
    } catch (_) {}
  }

  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }
  return undefined;
}

// Resolve Playwright module
function loadPlaywright() {
  try {
    return require('@playwright/test');
  } catch (_) {
    try {
      return require('playwright');
    } catch (__) {
      // Look into known repo node_modules
      const repoPaths = [
        path.join(__dirname, '../../../..', 'CascadeProjects/mopheus/node_modules/@playwright/test'),
        path.join(process.cwd(), 'node_modules/@playwright/test'),
      ];
      for (const p of repoPaths) {
        if (fs.existsSync(p)) return require(p);
      }
      throw new Error('Playwright not found in system or node_modules.');
    }
  }
}

async function main() {
  const opts = parseArgs();
  const { chromium } = loadPlaywright();
  const executablePath = findChromiumExecutable();

  // 1. Authenticate with backend API
  console.log(`==> Authenticating as ${opts.email}...`);
  const loginRes = await fetch(`${opts.backend}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: opts.email, password: opts.password }),
  });
  if (!loginRes.ok) {
    throw new Error(`Login failed on ${opts.backend}: status ${loginRes.status}`);
  }
  const loginData = await loginRes.json();
  const { user, accessToken } = loginData.data;

  // 2. Launch browser
  const launchOptions = {
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  };
  if (executablePath) {
    launchOptions.executablePath = executablePath;
  }

  const browser = await chromium.launch(launchOptions);
  const context = await browser.newContext({
    viewport: { width: 1280, height: 960 },
  });

  // 3. Inject auth cookie
  await context.addCookies([
    {
      name: 'mopheus_auth',
      value: accessToken,
      domain: 'localhost',
      path: '/',
    },
  ]);

  const page = await context.newPage();

  // 4. Inject localStorage state via initial page visit
  await page.goto(`${opts.frontend}/login`, { waitUntil: 'domcontentloaded' });
  await page.evaluate(
    ({ user, accessToken }) => {
      localStorage.setItem(
        'mopheus-auth',
        JSON.stringify({
          state: { user, token: accessToken, isAuthenticated: true },
          version: 0,
        })
      );
    },
    { user, accessToken }
  );

  // 5. Navigate to target URL
  const targetUrl = opts.url.startsWith('http') ? opts.url : `${opts.frontend}${opts.url}`;
  console.log(`==> Navigating to: ${targetUrl}`);
  await page.goto(targetUrl, { waitUntil: 'networkidle' });

  if (opts.wait > 0) {
    await page.waitForTimeout(opts.wait);
  }

  // 6. Optional hover action
  if (opts.hover) {
    console.log(`==> Hovering over: ${opts.hover}`);
    const hoverEl = page.locator(opts.hover).first();
    await hoverEl.hover();
    await page.waitForTimeout(600); // Wait for HoverCard/Tooltip open animation
  }

  // 7. Capture screenshot
  const outPath = path.resolve(opts.output);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });

  if (opts.selector) {
    console.log(`==> Capturing element selector: ${opts.selector}`);
    const el = await page.$(opts.selector);
    if (el) {
      await el.screenshot({ path: outPath });
    } else {
      console.warn(`Selector "${opts.selector}" not found, capturing full page.`);
      await page.screenshot({ path: outPath });
    }
  } else {
    console.log(`==> Capturing viewport screenshot...`);
    await page.screenshot({ path: outPath });
  }

  await browser.close();
  console.log(`✓ Screenshot captured successfully: ${outPath}`);
}

main().catch((err) => {
  console.error(`ERROR: ${err.message}`);
  process.exit(1);
});
