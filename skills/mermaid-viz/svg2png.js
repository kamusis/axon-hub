import sharp from 'sharp';
import { readFileSync, writeFileSync } from 'fs';

const svg = readFileSync('/tmp/mes_relation.svg', 'utf8');
const png = await sharp(Buffer.from(svg)).png().toBuffer();
writeFileSync('/tmp/mes_relation.png', png);
console.log('Done');
