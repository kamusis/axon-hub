#!/usr/bin/env node

/**
 * scripts/mermaid-viz.js
 * 
 * A CLI bridge for beautiful-mermaid to render diagrams in OpenClaw.
 * Supports ASCII (default) and SVG output.
 * 
 * Usage:
 *   node scripts/mermaid-viz.js --type ascii "graph TD; A-->B"
 *   node scripts/mermaid-viz.js --type svg --theme tokyo-night --output result.svg "graph TD; A-->B"
 */

const fs = require('fs');
const path = require('path');
const { renderMermaid, renderMermaidAscii, THEMES } = require('beautiful-mermaid');

async function main() {
  const args = process.argv.slice(2);
  
  // Parse flags
  const getFlag = (flag) => {
    const idx = args.indexOf(flag);
    return (idx !== -1 && args[idx + 1] && !args[idx + 1].startsWith('--')) ? args[idx + 1] : null;
  };

  const type = getFlag('--type') || 'ascii';
  const themeName = getFlag('--theme') || 'zinc-dark';
  const outputFile = getFlag('--output');
  const useAscii = args.includes('--pure-ascii');

  // Get mermaid code (everything that's not a flag or a flag value)
  let input = '';
  const filteredArgs = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      // Skip flag and its value if it has one
      if (['--type', '--theme', '--output'].includes(args[i])) i++;
      continue;
    }
    filteredArgs.push(args[i]);
  }

  if (filteredArgs.length > 0) {
    input = filteredArgs.join(' ');
  } else if (!process.stdin.isTTY) {
    input = fs.readFileSync(0, 'utf8');
  }

  if (!input || input.trim() === '') {
    console.error('Error: No Mermaid diagram code provided.');
    console.log('Usage: node mermaid-viz.js [--type svg|ascii] [--theme name] [--output file] "diagram code"');
    process.exit(1);
  }

  try {
    if (type === 'svg') {
      const theme = THEMES[themeName] || THEMES['zinc-dark'];
      const svg = await renderMermaid(input, theme);
      
      if (outputFile) {
        const absPath = path.isAbsolute(outputFile) ? outputFile : path.join(process.cwd(), outputFile);
        fs.writeFileSync(absPath, svg);
        console.log(`Successfully saved SVG to: ${absPath}`);
      } else {
        process.stdout.write(svg);
      }
    } else {
      // ASCII / Unicode mode
      const ascii = renderMermaidAscii(input, { useAscii });
      console.log(ascii);
    }
  } catch (err) {
    console.error('Error rendering diagram:', err.message);
    process.exit(1);
  }
}

main();
