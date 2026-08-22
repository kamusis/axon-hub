---
name: axon-cluster-sync
description: >
  Synchronize Axon skills, configurations, and hub across all machines (Windows local, WSL, and remote SSH servers) using the multi-node sync tool with smart convergence. Automatically resolves sequence drift and ensures 100% commit SHA convergence. Triggers on: "sync all nodes", "sync all servers", "sync across machines", "同步所有服务器", "同步所有机器", "多节点同步", "集群同步", "axon sync all", "axon-sync-all", "更新所有服务器的skills", "同步所有机器的skills".
---

# axon-cluster-sync Skill

Synchronize skills, workflows, and configurations managed by Axon CLI across the entire machine cluster (Windows Local, WSL Ubuntu, and Remote SSH servers).

## Key Features

1. **Smart Convergence (智能收敛)**:
   - **Phase 1**: Sequentially executes `axon sync` on all active nodes, capturing the resulting Git `Commit SHA` in real-time.
   - **Drift Analysis**: Compares all nodes against the latest `Target SHA`. If zero drift is detected, skips Phase 2 (0 overhead).
   - **Phase 2 (Catch-up)**: If any earlier node missed a subsequent node's push, automatically triggers a fast catch-up sync on only the lagging nodes, achieving 100% cluster consistency.
2. **Zero SSH Key Exposure**: Only reads host aliases from `~/.ssh/config`; authentication is handled entirely by the host OpenSSH client.
3. **Environment-Aware**: Automatically fixes non-interactive SSH PATH (`~/.local/bin`, `~/go/bin`, `/opt/homebrew/bin`, `/usr/local/bin`).

---

## Quick Reference Commands

### On Windows (PowerShell)

```powershell
# 1. Standard Cluster Sync (with Smart Convergence)
pwsh -File ~/.axon/axon-sync-all.ps1

# 2. Sync Specific Node(s)
pwsh -File ~/.axon/axon-sync-all.ps1 -Node "local,wsl,imac-m1"

# 3. Probe and Scan All Nodes from ~/.ssh/config
pwsh -File ~/.axon/axon-sync-all.ps1 -Scan

# 4. List Configured Nodes
pwsh -File ~/.axon/axon-sync-all.ps1 -List

# 5. Run Custom Axon Command Across Cluster (e.g. status, version, doctor)
pwsh -File ~/.axon/axon-sync-all.ps1 -Command "status"

# 6. Dry Run
pwsh -File ~/.axon/axon-sync-all.ps1 -DryRun
```

### On Linux / WSL / macOS (Bash)

```bash
# 1. Standard Cluster Sync (with Smart Convergence)
~/.axon/axon-sync-all.sh

# 2. Sync Specific Node(s)
~/.axon/axon-sync-all.sh -n "local,wsl,imac-m1"

# 3. Probe and Scan Nodes
~/.axon/axon-sync-all.sh -s

# 4. List Configured Nodes
~/.axon/axon-sync-all.sh -l

# 5. Run Custom Axon Command
~/.axon/axon-sync-all.sh -c status

# 6. Dry Run
~/.axon/axon-sync-all.sh -d
```

---

## Node Configuration (`~/.axon/nodes.json`)

Nodes are stored in `~/.axon/nodes.json`:

```json
{
  "version": 1,
  "settings": {
    "ssh_timeout": 10,
    "remote_path": "$HOME/.local/bin:$HOME/go/bin:$HOME/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH",
    "parallel": false
  },
  "nodes": [
    {
      "name": "local",
      "type": "local",
      "enabled": true,
      "description": "Local workstation environment"
    },
    {
      "name": "wsl",
      "type": "wsl",
      "distro": "Ubuntu-24.04",
      "ssh_host": "wsl-ubuntu",
      "enabled": true,
      "description": "WSL Linux environment (Ubuntu-24.04)"
    },
    {
      "name": "imac-m1",
      "type": "ssh",
      "host": "imac-m1",
      "enabled": true,
      "description": "Remote host from SSH config"
    }
  ]
}
```

To temporarily disable a node without deleting it, set `"enabled": false`.

---

## Agent Operational Guidelines

1. **Platform Selection**:
   - On Windows environments, default to running `pwsh -File ~/.axon/axon-sync-all.ps1`.
   - On Linux, WSL, or macOS environments, run `~/.axon/axon-sync-all.sh`.
2. **Missing Configuration**:
   - If `~/.axon/nodes.json` does not exist, running the script will automatically initialize it from `~/.ssh/config`. Run `-Scan` / `-s` to probe which nodes have `axon` installed.
3. **Interpreting Results**:
   - Check the summary table for `Status` and `Commit`.
   - A healthy cluster run displays `✔ Cluster 100% Converged at commit [<sha>] across all N active node(s).`
   - If a node fails due to SSH timeout or network, diagnose using the error details reported in the summary table.
