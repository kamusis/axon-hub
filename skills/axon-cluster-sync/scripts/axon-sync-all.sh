#!/usr/bin/env bash
#
# axon-sync-all.sh - Cross-platform multi-node Axon synchronizer with Smart Convergence
#
# Reads node definitions from ~/.axon/nodes.json (generated from ~/.ssh/config + local/wsl).
# Executes 'axon sync' (or custom axon command) across all enabled nodes and reports results.
# Automatically detects if later nodes pushed new commits and converges earlier nodes.
#

set -o pipefail

# ANSI Color Codes
C_RESET="\033[0m"
C_BOLD="\033[1m"
C_GREEN="\033[32m"
C_RED="\033[31m"
C_YELLOW="\033[33m"
C_CYAN="\033[36m"
C_GRAY="\033[90m"

CONFIG_FILE="${HOME}/.axon/nodes.json"
COMMAND="sync"
DRY_RUN=false
NO_CONVERGE=false
TARGET_NODE=""
ACTION="sync"

log_info() {
    echo -e "${C_CYAN}[INFO]${C_RESET} $1"
}

log_success() {
    echo -e "${C_GREEN}[SUCCESS]${C_RESET} $1"
}

log_warn() {
    echo -e "${C_YELLOW}[WARN]${C_RESET} $1"
}

log_err() {
    echo -e "${C_RED}[ERROR]${C_RESET} $1"
}

show_help() {
    cat << EOF
Axon Multi-Node Synchronizer (Bash with Smart Convergence)

Usage:
  $(basename "$0") [options]

Options:
  -i, --init            Initialize configuration from ~/.ssh/config
  -s, --scan            Probe nodes to detect Axon installation and update nodes.json
  -l, --list            List all configured nodes and their status
  -n, --node <name>     Sync only specific node(s), comma-separated (e.g. -n imac-m1,local)
  -c, --cmd <command>   Axon command to execute (default: sync)
  --no-converge         Disable smart 2nd-pass catch-up convergence
  -d, --dry-run         Simulate execution without running commands
  --config <path>       Path to JSON configuration file (default: ~/.axon/nodes.json)
  -h, --help            Show this help message

Examples:
  $(basename "$0")
  $(basename "$0") -s
  $(basename "$0") -n imac-m1
  $(basename "$0") -c status
  $(basename "$0") -d
EOF
}

# Parse command-line options
while [[ $# -gt 0 ]]; do
    case "$1" in
        -i|--init)
            ACTION="init"
            shift
            ;;
        -s|--scan)
            ACTION="scan"
            shift
            ;;
        -l|--list)
            ACTION="list"
            shift
            ;;
        -n|--node)
            TARGET_NODE="$2"
            shift 2
            ;;
        -c|--cmd)
            COMMAND="$2"
            shift 2
            ;;
        --no-converge)
            NO_CONVERGE=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_err "Unknown argument: $1"
            show_help
            exit 1
            ;;
    esac
done

# Ensure Python 3 or JQ is available for JSON processing
get_json_helper() {
    if command -v python3 >/dev/null 2>&1; then
        echo "python3"
    elif command -v python >/dev/null 2>&1; then
        echo "python"
    elif command -v jq >/dev/null 2>&1; then
        echo "jq"
    else
        log_err "Neither python3 nor jq is installed. Please install python3 or jq to parse JSON."
        exit 1
    fi
}

JSON_HELPER=$(get_json_helper)

# Parse SSH Config Hosts
get_ssh_hosts() {
    local ssh_config="${HOME}/.ssh/config"
    if [[ ! -f "$ssh_config" ]]; then
        return
    fi
    awk '
        tolower($1) == "host" {
            for (i=2; i<=NF; i++) {
                if ($i !~ /[\*\?]/) {
                    print $i
                }
            }
        }
    ' "$ssh_config" | awk '!seen[$0]++'
}

# Detect default WSL distro if on Windows or inside WSL
get_wsl_distro() {
    if command -v wsl.exe >/dev/null 2>&1; then
        local distro
        distro=$(wsl.exe --list --quiet 2>/dev/null | tr -d '\r\0' | head -n 1)
        if [[ -n "$distro" ]]; then
            echo "$distro"
            return
        fi
    fi
    echo "Ubuntu-24.04"
}

# Initialize configuration
init_config() {
    log_info "Initializing configuration from ~/.ssh/config..."
    mkdir -p "$(dirname "$CONFIG_FILE")"

    local default_distro
    default_distro=$(get_wsl_distro)
    local ssh_hosts
    ssh_hosts=$(get_ssh_hosts)

    python3 - << PYEOF
import json, os

hosts_raw = """$ssh_hosts""".strip().split('\n')
hosts = [h.strip() for h in hosts_raw if h.strip() and h.strip() != "wsl-ubuntu"]
distro = """$default_distro""".strip() or "Ubuntu-24.04"

nodes = [
    {
        "name": "local",
        "type": "local",
        "enabled": True,
        "description": "Local workstation environment"
    },
    {
        "name": "wsl",
        "type": "wsl",
        "distro": distro,
        "ssh_host": "wsl-ubuntu",
        "enabled": True,
        "description": f"WSL Linux environment ({distro})"
    }
]

for h in hosts:
    nodes.append({
        "name": h,
        "type": "ssh",
        "host": h,
        "enabled": False,
        "description": "Remote host from SSH config"
    })

config = {
    "version": 1,
    "settings": {
        "ssh_timeout": 10,
        "remote_path": r"\$HOME/.local/bin:\$HOME/go/bin:\$HOME/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:\$PATH",
        "parallel": False
    },
    "nodes": nodes
}

with open("$CONFIG_FILE", "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

PYEOF

    log_success "Configuration initialized at: $CONFIG_FILE"
    log_info "Run with -s / --scan to auto-detect and enable nodes with Axon installed."
}

# List Configured Nodes
list_nodes() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_warn "Configuration file not found at $CONFIG_FILE. Run with -i / --init first."
        exit 1
    fi

    echo -e "\n${C_BOLD}Configured Axon Sync Nodes:${C_RESET}"
    python3 - << PYEOF
import json

with open("$CONFIG_FILE", "r", encoding="utf-8-sig") as f:
    data = json.load(f)

nodes = data.get("nodes", [])
print(f"{'NAME':<22} {'TYPE':<8} {'TARGET':<22} {'ENABLED':<8} {'DESCRIPTION'}")
print("-" * 80)
for n in nodes:
    name = n.get("name", "")
    ntype = n.get("type", "")
    target = n.get("host") or n.get("distro") or "localhost"
    enabled = "Yes" if n.get("enabled", False) else "No"
    desc = n.get("description", "")
    print(f"{name:<22} {ntype:<8} {target:<22} {enabled:<8} {desc}")
print()
PYEOF
}

# Scan and update config
scan_nodes() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        init_config
    fi

    log_info "Scanning all nodes to detect Axon CLI installation..."

    local default_path='$HOME/.local/bin:$HOME/go/bin:$HOME/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH'

    # Read config and update live
    python3 - << PYEOF
import json, subprocess, sys, os, shutil

with open("$CONFIG_FILE", "r", encoding="utf-8-sig") as f:
    config = json.load(f)

settings = config.get("settings", {})
remote_path = settings.get("remote_path", r"$default_path")
timeout = str(settings.get("ssh_timeout", 8))
nodes = config.get("nodes", [])

updated_nodes = []
results = []

C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_GREEN = "\033[32m"
C_RED = "\033[31m"
C_GRAY = "\033[90m"

# Prepare enhanced PATH for subprocess
env = os.environ.copy()
custom_dirs = [
    os.path.expanduser("~/.local/bin"),
    os.path.expanduser("~/go/bin"),
    os.path.expanduser("~/bin"),
    "/usr/local/bin",
    "/opt/homebrew/bin",
    "/usr/bin",
    "/bin"
]
env["PATH"] = ":".join(custom_dirs) + ":" + env.get("PATH", "")

for n in nodes:
    name = n.get("name", "")
    ntype = n.get("type", "")
    host = n.get("host", "")
    distro = n.get("distro", "")
    desc = n.get("description", "")

    sys.stdout.write(f"  Probing {C_BOLD}{name}{C_RESET} ({ntype})... ")
    sys.stdout.flush()

    found = False
    ver = ""
    err = ""

    if ntype == "local":
        try:
            res = subprocess.run(["axon", "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5, env=env)
            if res.returncode == 0 and res.stdout.strip():
                found = True
                ver = res.stdout.strip().split('\n')[0]
            else:
                err = res.stderr.strip() or "axon not found in PATH"
        except Exception as e:
            err = str(e)
    elif ntype == "wsl":
        if shutil.which("wsl.exe"):
            try:
                wsl_cmd = f'export PATH="{remote_path}"; which axon >/dev/null 2>&1 && axon version'
                res = subprocess.run(["wsl.exe", "-d", distro or "Ubuntu-24.04", "--", "bash", "-c", wsl_cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=8)
                if res.returncode == 0 and res.stdout.strip():
                    found = True
                    ver = res.stdout.strip().split('\n')[0]
                else:
                    err = "axon not found in WSL"
            except Exception as e:
                err = str(e)
        else:
            try:
                res = subprocess.run(["axon", "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5, env=env)
                if res.returncode == 0 and res.stdout.strip():
                    found = True
                    ver = res.stdout.strip().split('\n')[0]
                else:
                    err = "axon not found"
            except Exception as e:
                err = str(e)
    elif ntype == "ssh":
        try:
            ssh_cmd = f'export PATH="{remote_path}"; which axon >/dev/null 2>&1 && axon version'
            res = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", f"ConnectTimeout={timeout}", host or name, ssh_cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=12, env=env)
            if res.returncode == 0 and res.stdout.strip():
                found = True
                ver = res.stdout.strip().split('\n')[0]
            else:
                err = (res.stderr or res.stdout).strip().replace('\n', ' ') or "Host unreachable / axon not found"
        except Exception as e:
            err = str(e)

    n["enabled"] = found
    updated_nodes.append(n)

    if found:
        print(f"{C_GREEN}FOUND{C_RESET} ({ver})")
        results.append((name, ntype, "FOUND", ver, "Yes"))
    else:
        print(f"{C_GRAY}NOT FOUND / UNREACHABLE{C_RESET}")
        results.append((name, ntype, "NOT FOUND", "-", "No"))

config["nodes"] = updated_nodes

with open("$CONFIG_FILE", "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"\n{C_GREEN}[SUCCESS]{C_RESET} Configuration updated and saved to: $CONFIG_FILE\n")
print(f"{'NODE':<22} {'TYPE':<8} {'STATUS':<12} {'VERSION':<25} {'ENABLED'}")
print("-" * 80)
for r in results:
    print(f"{r[0]:<22} {r[1]:<8} {r[2]:<12} {r[3]:<25} {r[4]}")
print()
PYEOF
}

# Execute Sync across nodes with Smart Convergence
sync_nodes() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        init_config
    fi

    echo -e "\n${C_BOLD}====================================================${C_RESET}"
    echo -e "${C_BOLD}     Axon Multi-Node Synchronizer (Smart Convergence)${C_RESET}"
    echo -e "${C_BOLD}====================================================${C_RESET}"
    log_info "Command:    axon $COMMAND"
    log_info "Config:     $CONFIG_FILE"
    if [[ "$NO_CONVERGE" == "true" ]]; then
        log_info "Convergence: Disabled"
    else
        log_info "Convergence: Smart Auto-Detection (2-Pass if drift detected)"
    fi
    echo ""

    python3 - << PYEOF
import json, subprocess, sys, os, shutil, time, re

with open("$CONFIG_FILE", "r", encoding="utf-8-sig") as f:
    config = json.load(f)

settings = config.get("settings", {})
remote_path = settings.get("remote_path", r"\$HOME/.local/bin:\$HOME/go/bin:\$HOME/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:\$PATH")
timeout = str(settings.get("ssh_timeout", 10))
nodes = config.get("nodes", [])

filter_str = """$TARGET_NODE""".strip()
filter_nodes = [x.strip() for x in filter_str.split(',') if x.strip()] if filter_str else []

if filter_nodes:
    target_nodes = [n for n in nodes if n.get("name") in filter_nodes]
    if not target_nodes:
        print(f"\033[31m[ERROR]\033[0m No matching nodes found for: {filter_str}")
        sys.exit(1)
else:
    target_nodes = nodes

dry_run = True if """$DRY_RUN""".lower() == "true" else False
no_converge = True if """$NO_CONVERGE""".lower() == "true" else False
command = """$COMMAND"""

C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_GREEN = "\033[32m"
C_RED = "\033[31m"
C_YELLOW = "\033[33m"
C_CYAN = "\033[36m"
C_GRAY = "\033[90m"

# Prepare enhanced PATH for subprocess
env = os.environ.copy()
custom_dirs = [
    os.path.expanduser("~/.local/bin"),
    os.path.expanduser("~/go/bin"),
    os.path.expanduser("~/bin"),
    "/usr/local/bin",
    "/opt/homebrew/bin",
    "/usr/bin",
    "/bin"
]
env["PATH"] = ":".join(custom_dirs) + ":" + env.get("PATH", "")

def run_node_cmd(node):
    ntype = node.get("type", "")
    host = node.get("host", node.get("name", ""))
    distro = node.get("distro", "Ubuntu-24.04")

    status = "OK"
    details = ""
    output_lines = []
    commit_sha = ""
    exit_code = 0

    try:
        if ntype == "local":
            proc = subprocess.run(["axon", command], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
            output_lines = [line for line in proc.stdout.strip().split('\n') if line.strip()] if proc.stdout else []
            exit_code = proc.returncode
            
            # Query commit SHA
            local_repo = os.path.expanduser("~/.axon/repo")
            sha_proc = subprocess.run(["git", "-C", local_repo, "rev-parse", "--short", "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if sha_proc.returncode == 0 and sha_proc.stdout.strip():
                sha_cand = sha_proc.stdout.strip()
                if re.match(r'^[0-9a-fA-F]{7,40}$', sha_cand):
                    commit_sha = sha_cand

        elif ntype == "wsl":
            if shutil.which("wsl.exe"):
                wsl_cmd = f'export PATH="{remote_path}"; axon {command}; _ec=\$?; echo "___AXON_DELIM___"; echo "EXIT:\$_ec"; git -C ~/.axon/repo rev-parse --short HEAD 2>/dev/null'
                proc = subprocess.run(["wsl.exe", "-d", distro, "--", "bash", "-c", wsl_cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
            else:
                local_cmd = f'export PATH="{remote_path}"; axon {command}; _ec=\$?; echo "___AXON_DELIM___"; echo "EXIT:\$_ec"; git -C ~/.axon/repo rev-parse --short HEAD 2>/dev/null'
                proc = subprocess.run(["bash", "-c", local_cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)

            raw_lines = [line for line in proc.stdout.strip().split('\n') if line.strip()] if proc.stdout else []
            if "___AXON_DELIM___" in raw_lines:
                idx = raw_lines.index("___AXON_DELIM___")
                output_lines = raw_lines[:idx]
                for m in raw_lines[idx+1:]:
                    if m.startswith("EXIT:"):
                        try:
                            exit_code = int(m.split(":", 1)[1])
                        except:
                            pass
                    elif re.match(r'^[0-9a-fA-F]{7,40}$', m.strip()):
                        commit_sha = m.strip()
            else:
                output_lines = raw_lines
                exit_code = proc.returncode

        elif ntype == "ssh":
            ssh_cmd = f'export PATH="{remote_path}"; axon {command}; _ec=\$?; echo "___AXON_DELIM___"; echo "EXIT:\$_ec"; git -C ~/.axon/repo rev-parse --short HEAD 2>/dev/null'
            proc = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", f"ConnectTimeout={timeout}", host, ssh_cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)

            raw_lines = [line for line in proc.stdout.strip().split('\n') if line.strip()] if proc.stdout else []
            if "___AXON_DELIM___" in raw_lines:
                idx = raw_lines.index("___AXON_DELIM___")
                output_lines = raw_lines[:idx]
                for m in raw_lines[idx+1:]:
                    if m.startswith("EXIT:"):
                        try:
                            exit_code = int(m.split(":", 1)[1])
                        except:
                            pass
                    elif re.match(r'^[0-9a-fA-F]{7,40}$', m.strip()):
                        commit_sha = m.strip()
            else:
                output_lines = raw_lines
                exit_code = proc.returncode
        else:
            status = "ERROR"
            details = f"Unknown node type: {ntype}"
            exit_code = 1

        if exit_code != 0:
            combined_err = " ".join(output_lines)
            if "timed out" in combined_err.lower() or "connection timed out" in combined_err.lower():
                status = "TIMEOUT"
                details = f"Connection timed out ({timeout}s)"
            elif "permission denied" in combined_err.lower() or "bad permissions" in combined_err.lower():
                status = "AUTH_ERR"
                details = "SSH authentication failed"
            elif "command not found" in combined_err.lower():
                status = "FAILED"
                details = "axon command not found"
            else:
                status = "FAILED"
                details = output_lines[-1] if output_lines else f"Exit code {exit_code}"
        else:
            status = "SUCCESS"
            details = "Synced successfully"

    except Exception as e:
        status = "ERROR"
        details = str(e)

    return status, details, output_lines, commit_sha

node_results = {}
start_total = time.time()
total_count = len(target_nodes)

print(f"{C_BOLD}[Phase 1: Initial Sync & State Discovery]{C_RESET}")
print(f"{C_GRAY}----------------------------------------------------{C_RESET}")

for idx, node in enumerate(target_nodes, 1):
    name = node.get("name", "")
    ntype = node.get("type", "")
    is_enabled = node.get("enabled", False)

    if not is_enabled and not filter_nodes:
        print(f"{C_BOLD}[{idx}/{total_count}] Node: {C_CYAN}{name}{C_RESET} ({ntype}) {C_YELLOW}[SKIPPED]{C_RESET}")
        print(f"    {C_GRAY}Disabled in nodes.json{C_RESET}\n")
        node_results[name] = {
            "index": idx,
            "node": name,
            "type": ntype,
            "status": "SKIPPED",
            "commit_sha": "-",
            "passes": 0,
            "duration": 0.0,
            "details": "Disabled in configuration",
            "node_obj": node
        }
        continue

    print(f"{C_BOLD}[{idx}/{total_count}] Node: {C_CYAN}{name}{C_RESET} ({ntype})")

    if dry_run:
        print(f"  {C_GRAY}(Dry Run) Would execute: axon {command}{C_RESET}\n")
        node_results[name] = {
            "index": idx,
            "node": name,
            "type": ntype,
            "status": "DRY-RUN",
            "commit_sha": "simulated",
            "passes": 1,
            "duration": 0.0,
            "details": "Simulated",
            "node_obj": node
        }
        continue

    t0 = time.time()
    status, details, output_lines, commit_sha = run_node_cmd(node)
    duration = round(time.time() - t0, 2)

    for l in output_lines:
        print(f"    {C_GRAY}│{C_RESET} {l}")

    sha_txt = f" [SHA: {C_CYAN}{commit_sha}{C_RESET}]" if commit_sha else ""

    if status == "SUCCESS":
        print(f"    {C_GREEN}✔ Success{C_RESET} in {duration}s{sha_txt}\n")
    else:
        print(f"    {C_RED}✖ {status}{C_RESET} in {duration}s: {details}\n")

    node_results[name] = {
        "index": idx,
        "node": name,
        "type": ntype,
        "status": status,
        "commit_sha": commit_sha or "-",
        "passes": 1,
        "duration": duration,
        "details": details,
        "node_obj": node
    }

# Phase 2: Convergence
if not dry_run and not no_converge and command == "sync":
    successful_nodes = [r for r in node_results.values() if r["status"] == "SUCCESS" and r["commit_sha"] != "-"]
    if len(successful_nodes) > 1:
        target_sha = successful_nodes[-1]["commit_sha"]
        lagging_nodes = [r for r in successful_nodes if r["commit_sha"] != target_sha]

        if lagging_nodes:
            print(f"{C_BOLD}[Phase 2: Catch-up Convergence]{C_RESET}")
            print(f"{C_YELLOW}[!] Detected commit drift across cluster.{C_RESET}")
            print(f"    Latest Target SHA: {C_CYAN}{target_sha}{C_RESET} (from {successful_nodes[-1]['node']})")
            print(f"    Lagging nodes to converge: {C_YELLOW}{', '.join(r['node'] for r in lagging_nodes)}{C_RESET}")
            print(f"{C_GRAY}----------------------------------------------------{C_RESET}")

            for p2_idx, lag_item in enumerate(lagging_nodes, 1):
                node = lag_item["node_obj"]
                name = node.get("name", "")
                ntype = node.get("type", "")

                print(f"{C_BOLD}[{p2_idx}/{len(lagging_nodes)}] Converging Node: {C_CYAN}{name}{C_RESET} ({ntype}) [{lag_item['commit_sha']} -> {target_sha}]")

                t0 = time.time()
                status, details, output_lines, new_sha = run_node_cmd(node)
                p2_dur = round(time.time() - t0, 2)

                for l in output_lines:
                    print(f"    {C_GRAY}│{C_RESET} {l}")

                if status == "SUCCESS":
                    lag_item["commit_sha"] = new_sha or target_sha
                    lag_item["passes"] = 2
                    lag_item["duration"] = round(lag_item["duration"] + p2_dur, 2)
                    lag_item["details"] = f"Converged to {target_sha}"
                    print(f"    {C_GREEN}✔ Converged{C_RESET} in {p2_dur}s [SHA: {C_CYAN}{lag_item['commit_sha']}{C_RESET}]\n")
                else:
                    lag_item["status"] = status
                    lag_item["details"] = f"Pass 2 failed: {details}"
                    lag_item["duration"] = round(lag_item["duration"] + p2_dur, 2)
                    print(f"    {C_RED}✖ Convergence Failed{C_RESET}: {details}\n")
        else:
            print(f"{C_GREEN}[Phase 2: Skipped]{C_RESET} All active nodes already converged at commit {C_CYAN}{target_sha}{C_RESET}.\n")

total_time = round(time.time() - start_total, 2)

# Summary
print(f"{C_BOLD}===================================================={C_RESET}")
print(f"{C_BOLD}               Execution Summary                    {C_RESET}")
print(f"{C_BOLD}===================================================={C_RESET}")

all_results = sorted(node_results.values(), key=lambda x: x["index"])
success_cnt = sum(1 for r in all_results if r["status"] == "SUCCESS")
failed_cnt = sum(1 for r in all_results if r["status"] in ["FAILED", "TIMEOUT", "AUTH_ERR", "ERROR"])
skipped_cnt = sum(1 for r in all_results if r["status"] == "SKIPPED")

active_shas = list(set(r["commit_sha"] for r in all_results if r["status"] == "SUCCESS" and r["commit_sha"] != "-"))
is_fully_converged = len(active_shas) <= 1

print(f"{'NODE':<20} {'TYPE':<8} {'STATUS':<10} {'COMMIT':<10} {'PASSES':<8} {'DURATION':<10} {'DETAILS'}")
print("-" * 86)
for r in all_results:
    passes_str = str(r["passes"]) if r["passes"] > 0 else "-"
    print(f"{r['node']:<20} {r['type']:<8} {r['status']:<10} {r['commit_sha']:<10} {passes_str:<8} {r['duration']}s{'':<5} {r['details']}")

print()
if is_fully_converged and active_shas:
    print(f"{C_GREEN}✔ Cluster 100% Converged at commit [{active_shas[0]}] across all {success_cnt} active node(s).{C_RESET}")
elif len(active_shas) > 1:
    print(f"{C_YELLOW}⚠ Cluster Divergence detected: multiple SHAs ({', '.join(active_shas)}){C_RESET}")

print(f"Total: {len(all_results)} | {C_GREEN}Success: {success_cnt}{C_RESET} | {C_RED}Failed: {failed_cnt}{C_RESET} | {C_YELLOW}Skipped: {skipped_cnt}{C_RESET} | Total Time: {total_time}s\n")

if failed_cnt > 0:
    sys.exit(1)
else:
    sys.exit(0)
PYEOF
}

# Main Execution Flow
case "$ACTION" in
    "init")
        init_config
        ;;
    "scan")
        scan_nodes
        ;;
    "list")
        list_nodes
        ;;
    "sync")
        sync_nodes
        ;;
esac
