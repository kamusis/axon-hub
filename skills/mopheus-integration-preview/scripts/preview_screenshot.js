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
 *   --cdp-log <path>         Destination JSON path for CDP audit log (default: <output>.cdp.json)
 *   --strict-cdp             Fail with exit code 1 if console/page errors detected (default: true)
 *   --no-strict-cdp          Disable strict exit code on console/page errors
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
    click: null,
    clickAfter: null,
    wait: 1000,
    viewport: { width: 1280, height: 960 },
    backend: 'http://localhost:8230',
    frontend: 'http://localhost:3230',
    email: 'alice@mopheus.dev',
    password: 'Mopheus@123',
    cdpLog: null,
    strictCdp: true,
  };

  for (let i = 0; i < args.length; i++) {
    const key = args[i];
    const val = args[i + 1];
    if (key === '--url') { options.url = val; i++; }
    else if (key === '--output') { options.output = val; i++; }
    else if (key === '--selector') { options.selector = val; i++; }
    else if (key === '--hover') { options.hover = val; i++; }
    else if (key === '--click') { options.click = val; i++; }
    else if (key === '--click-after') { options.clickAfter = val; i++; }
    else if (key === '--wait') { options.wait = parseInt(val, 10); i++; }
    else if (key === '--viewport') {
      const [w, h] = val.split('x').map((n) => parseInt(n, 10));
      if (w && h) options.viewport = { width: w, height: h };
      i++;
    }
    else if (key === '--backend') { options.backend = val; i++; }
    else if (key === '--frontend') { options.frontend = val; i++; }
    else if (key === '--email') { options.email = val; i++; }
    else if (key === '--password') { options.password = val; i++; }
    else if (key === '--cdp-log') { options.cdpLog = val; i++; }
    else if (key === '--strict-cdp') { options.strictCdp = true; }
    else if (key === '--no-strict-cdp') { options.strictCdp = false; }
  }

  if (!options.url || !options.output) {
    console.error('Usage: preview_screenshot.js --url <url> --output <output.png> [--selector <css>] [--hover <css>] [--cdp-log <log.json>]');
    process.exit(1);
  }

  if (!options.cdpLog && options.output) {
    options.cdpLog = `${options.output}.cdp.json`;
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
    viewport: opts.viewport,
  });

  // 3. Inject auth cookie
  await context.addCookies([
    {
      name: 'mopheus_auth',
      value: accessToken,
      domain: new URL(opts.frontend).hostname,
      path: '/',
    },
  ]);

  const page = await context.newPage();

  // Initialize CDP audit report
  const cdpReport = {
    targetUrl: opts.url,
    timestamp: new Date().toISOString(),
    consoleErrors: [],
    consoleWarnings: [],
    pageErrors: [],
    failedRequests: [],
    httpErrors: [],
    passed: true,
  };

  // Attach CDP-level listeners to inspect browser runtime behavior
  page.on('console', (msg) => {
    const type = msg.type();
    const text = msg.text();
    const location = msg.location();

    // Ignore known benign noise
    if (text.includes('Download the React DevTools for a better development experience')) return;

    if (type === 'error') {
      const entry = { text, location, timestamp: new Date().toISOString() };
      cdpReport.consoleErrors.push(entry);
      console.error(`[CDP Console Error] ${text} (${location.url || 'inline'}:${location.lineNumber || 0})`);
    } else if (type === 'warning') {
      const entry = { text, location, timestamp: new Date().toISOString() };
      cdpReport.consoleWarnings.push(entry);
      console.warn(`[CDP Console Warning] ${text}`);
    }
  });

  page.on('pageerror', (err) => {
    const entry = {
      message: err.message,
      stack: err.stack,
      timestamp: new Date().toISOString(),
    };
    cdpReport.pageErrors.push(entry);
    console.error(`[CDP Page Runtime Error] ${err.message}\n${err.stack || ''}`);
  });

  page.on('requestfailed', (req) => {
    const failureText = req.failure()?.errorText || 'Unknown failure';
    if (failureText === 'net::ERR_ABORTED') return; // Ignore intentional user navigations/aborts
    const entry = {
      url: req.url(),
      method: req.method(),
      failure: failureText,
      timestamp: new Date().toISOString(),
    };
    cdpReport.failedRequests.push(entry);
    console.error(`[CDP Network Failed] ${entry.method} ${entry.url} -> ${failureText}`);
  });

  page.on('response', (resp) => {
    const status = resp.status();
    const url = resp.url();
    if (status >= 400) {
      if (url.includes('/api/v1/auth/session') && status === 401) return; // benign login check probe
      const entry = {
        url,
        status,
        statusText: resp.statusText(),
        timestamp: new Date().toISOString(),
      };
      cdpReport.httpErrors.push(entry);
      console.warn(`[CDP HTTP Error] ${status} ${resp.statusText()} on ${url}`);
    }
  });

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

  // 6. Optional click action
  if (opts.click) {
    console.log(`==> Clicking: ${opts.click}`);
    const clickEl = page.locator(opts.click).first();
    await clickEl.click();
    await page.waitForTimeout(Math.max(opts.wait, 2500)); // Wait for modal open animation and React Query fetch
  }

  // 6a. Optional second click action (e.g. select a node inside dialog)
  if (opts.clickAfter) {
    console.log(`==> Clicking after: ${opts.clickAfter}`);
    const clickAfterEl = page.locator(opts.clickAfter).first();
    await clickAfterEl.click();
    await page.waitForTimeout(600);
  }

  // 6b. Optional hover action
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

  // 8. Finalize CDP audit report & write evidence file
  const hasErrors =
    cdpReport.consoleErrors.length > 0 ||
    cdpReport.pageErrors.length > 0 ||
    cdpReport.failedRequests.length > 0;
  cdpReport.passed = !hasErrors;

  if (opts.cdpLog) {
    const cdpLogPath = path.resolve(opts.cdpLog);
    fs.mkdirSync(path.dirname(cdpLogPath), { recursive: true });
    fs.writeFileSync(cdpLogPath, JSON.stringify(cdpReport, null, 2), 'utf-8');
    console.log(`✓ CDP audit report written to: ${cdpLogPath}`);
  }

  await browser.close();
  console.log(`✓ Screenshot captured successfully: ${outPath}`);

  // Enforce CDP hard gate if strict mode is active
  if (opts.strictCdp && hasErrors) {
    console.error(
      `\n❌ [CDP Hard Gate Failed] Detected ${cdpReport.consoleErrors.length} console error(s), ${cdpReport.pageErrors.length} page runtime error(s), and ${cdpReport.failedRequests.length} network failure(s).`
    );
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(`ERROR: ${err.message}`);
  process.exit(1);
});
