const fs = require('fs');
const path = require('path');

async function run() {
  const { renderMermaid, THEMES } = await import('beautiful-mermaid');
  const sharp = require('sharp');

  const input = `flowchart TD
    subgraph L2["2. 宿主机 Bare 缓存层"]
        Bare["本地共享 Bare 仓库 (.repos/)"]
    end

    subgraph L3["3. 任务级隔离 Worktree 层"]
        A1["🤖 智能体 A 工作树"]
        A2["🤖 智能体 B 工作树"]
        A3["🤖 智能体 C 工作树"]
    end

    subgraph L1["1. 远程代码托管层"]
        Remote["GitHub / GitLab / Gitea 远程仓库"]
    end

    Bare -->|"秒级派生"| A1
    Bare -->|"秒级派生"| A2
    Bare -->|"秒级派生"| A3
    A1 -->|"提交与推送 PR"| Remote
    A2 -->|"提交与推送 PR"| Remote
    A3 -->|"提交与推送 PR"| Remote
    Remote -->|"增量同步 / 状态同步"| Bare
`;

  const theme = THEMES['zinc-light'] || THEMES['github-light'];
  let svg = await renderMermaid(input, { ...theme, transparent: false });

  const bg = '#FFFFFF';
  const fg = '#18181B';

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

  const outputPath = 'C:/Users/kamus/CascadeProjects/mopheus/docs/blog/assets/mopheus_git_architecture.png';
  await sharp(Buffer.from(svg), { density: 300 })
    .png()
    .toFile(outputPath);

  console.log('SUCCESS: Rendered exact image to ' + outputPath);
}

run().catch(console.error);
