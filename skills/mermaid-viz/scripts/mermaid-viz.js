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
  const isTransparent = args.includes('--opaque') ? false : true;

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
    if (['svg', 'jpg', 'png'].includes(type)) {
      const theme = THEMES[themeName] || THEMES['zinc-dark'];
      let svg = await renderMermaid(input, { ...theme, transparent: isTransparent });
      
      if (type === 'jpg' || type === 'png') {
        const sharp = require('sharp');
        
        // Flatten CSS variables as a fallback for sharp's rendering engine
        const bg = theme.bg || '#18181B';
        const fg = theme.fg || '#FAFAFA';
        
        // Simple hex color mixer (approximation of color-mix in srgb)
        const mix = (color1, color2, weight) => {
          const c1 = parseInt(color1.slice(1), 16);
          const c2 = parseInt(color2.slice(1), 16);
          const r1 = (c1 >> 16) & 0xff, g1 = (c1 >> 8) & 0xff, b1 = c1 & 0xff;
          const r2 = (c2 >> 16) & 0xff, g2 = (c2 >> 8) & 0xff, b2 = c2 & 0xff;
          const r = Math.round(r1 * weight + r2 * (1 - weight));
          const g = Math.round(g1 * weight + g2 * (1 - weight));
          const b = Math.round(b1 * weight + b2 * (1 - weight));
          return '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1).toUpperCase();
        };

        const vars = {
          '--_text': fg,
          '--_text-sec': mix(fg, bg, 0.6),
          '--_text-muted': mix(fg, bg, 0.4),
          '--_text-faint': mix(fg, bg, 0.25),
          '--_line': mix(fg, bg, 0.5),
          '--_arrow': mix(fg, bg, 0.85),
          '--_node-fill': mix(fg, bg, 0.03),
          '--_node-stroke': mix(fg, bg, 0.2),
          '--_group-fill': bg,
          '--_group-hdr': mix(fg, bg, 0.05),
          '--_inner-stroke': mix(fg, bg, 0.12),
          '--_key-badge': mix(fg, bg, 0.1),
        };

        for (const [v, val] of Object.entries(vars)) {
          const regex = new RegExp(`var\\(${v}\\)`, 'g');
          svg = svg.replace(regex, val);
        }
        svg = svg.replace(/var\(--bg\)/g, bg).replace(/var\(--fg\)/g, fg);

        let image = sharp(Buffer.from(svg));
        
        if (type === 'jpg') {
          image = image.flatten({ background: bg }).jpeg({ quality: 95 });
        } else {
          // PNG: handle transparency vs opaque
          if (!isTransparent) {
            image = image.flatten({ background: bg });
          }
          image = image.png();
        }
        
        if (outputFile) {
          const absPath = path.isAbsolute(outputFile) ? outputFile : path.join(process.cwd(), outputFile);
          await image.toFile(absPath);
          console.log(`Successfully saved ${type.toUpperCase()} to: ${absPath}`);
        } else {
          const buffer = await image.toBuffer();
          process.stdout.write(buffer);
        }
      } else {
        if (outputFile) {
          const absPath = path.isAbsolute(outputFile) ? outputFile : path.join(process.cwd(), outputFile);
          fs.writeFileSync(absPath, svg);
          console.log(`Successfully saved SVG to: ${absPath}`);
        } else {
          process.stdout.write(svg);
        }
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
