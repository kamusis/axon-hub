import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const input = readFileSync('/tmp/mmd_input.txt', 'utf8');

const { renderMermaid } = await import(join(__dirname, 'node_modules/beautiful-mermaid'));
const sharp = require('sharp');

const svg = await renderMermaid(input, {
    bgColor: 'transparent',
    fontFamily: 'Inter, system-ui, sans-serif'
});

const png = await sharp(Buffer.from(svg)).png().toBuffer();
require('fs').writeFileSync('/tmp/mes_relation.png', png);
console.log('Done: /tmp/mes_relation.png');
