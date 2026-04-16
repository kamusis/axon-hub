#!/usr/bin/env node
const { renderMermaid } = await import('beautiful-mermaid');
const sharp = require('sharp');
const fs = require('fs');

const input = `flowchart TD
    公司 --> 合同
    合同 --> 合同子项
    合同子项 --> 实施计划
    实施计划 --> 报工
    实施计划 --> 服务请求1
    服务请求1 --> 服务请求2
    员工 -->|执行| 报工
    服务请求1 -->|关联| 报工
    服务请求2 -->|关联| 报工`;

const svg = await renderMermaid(input, {
    bgColor: 'transparent',
    fontFamily: 'Arial, sans-serif'
});
const png = await sharp(Buffer.from(svg)).png().toBuffer();
fs.writeFileSync('/tmp/mes_relation.png', png);
console.log('Written to /tmp/mes_relation.png');
