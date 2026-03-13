#!/usr/bin/env node

/**
 * scripts/mermaid-viz.js
 * 
 * A CLI bridge for beautiful-mermaid to render diagrams in OpenClaw.
 * Supports ASCII (default) and SVG output.
 */

const fs = require('fs');
const path = require('path');

async function main() {
  // Dynamically import ESM module
  const { renderMermaid, renderMermaidAscii, THEMES } = await import('beautiful-mermaid');
  
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

  // Get mermaid code
  let input = '';
  const filteredArgs = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--')) {
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
      const ascii = renderMermaidAscii(input, { useAscii });
      console.log(ascii);
    }
  } catch (err) {
    console.error('Error rendering diagram:', err.message);
    process.exit(1);
  }
}

main();
