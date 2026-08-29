#!/usr/bin/env python3
"""
Mopheus API and CLI interaction client.
Resolves configuration, active profile, tokens, and workspaces.
Provides robust HTTP and CLI fallback methods for fetching agent tasks and transcripts.
"""

import json
import os
import ssl
import subprocess
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, List, Optional


class MopheusClient:
    """Client for interacting with Mopheus backend API and CLI."""

    def __init__(
        self,
        workspace_slug_or_id: Optional[str] = None,
        profile: str = "",
        server_url: Optional[str] = None,
        token: Optional[str] = None,
    ):
        self.profile = profile or os.environ.get("MOPHEUS_PROFILE", "")
        self.config_dir = self._resolve_config_dir()
        self.config = self._load_config()

        self.server_url = (
            server_url
            or os.environ.get("MOPHEUS_SERVER_URL")
            or os.environ.get("MOPHEUS_BASE_URL")
            or os.environ.get("MOPHEUS_URL")
            or self.config.get("serverUrl")
            or self.config.get("server_url")
            or self.config.get("apiUrl")
            or "http://localhost:8088"
        ).rstrip("/")

        self.token = (
            token
            or os.environ.get("MOPHEUS_TOKEN")
            or os.environ.get("MOPHEUS_API_TOKEN")
            or ""
        )

        self.workspace_slug = (
            workspace_slug_or_id
            or os.environ.get("MOPHEUS_WORKSPACE")
            or os.environ.get("MOPHEUS_WORKSPACE_ID")
            or self.config.get("workspace")
            or self.config.get("workspace_id")
            or self.config.get("workspaceId")
            or "dev"
        )
        self.workspace_id: Optional[str] = None
        self._resolve_workspace()

    def _resolve_config_dir(self) -> Path:
        home = Path.home()
        if self.profile and self.profile != "default":
            return home / ".mopheus" / "profiles" / self.profile
        return home / ".mopheus"

    def _load_config(self) -> Dict[str, Any]:
        cfg_file = self.config_dir / "config.json"
        if cfg_file.exists():
            try:
                with open(cfg_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _resolve_workspace(self) -> None:
        """Resolve workspace slug to UUID if possible."""
        if self.workspace_slug and len(self.workspace_slug) == 36 and self.workspace_slug.count("-") == 4:
            self.workspace_id = self.workspace_slug
            return

        # Try resolving via mop / mopheus CLI workspace list
        for cli_cmd in (["mop"], ["mopheus"]):
            try:
                cmd = cli_cmd + ["workspace", "list", "-o", "json"]
                if self.profile:
                    cmd.extend(["--profile", self.profile])
                res = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
                if res.returncode == 0 and res.stdout:
                    workspaces = json.loads(res.stdout)
                    if isinstance(workspaces, list):
                        target = (self.workspace_slug or "").lower()
                        for ws in workspaces:
                            slug = (ws.get("slug") or "").lower()
                            name = (ws.get("name") or "").lower()
                            wid = ws.get("id") or ""
                            if slug == target or name == target or wid.lower() == target:
                                self.workspace_id = wid
                                self.workspace_slug = ws.get("slug") or self.workspace_slug
                                return
                            if target in ("dev", "dev-space") and (slug in ("dev", "dev-space") or name == "dev"):
                                self.workspace_id = wid
                                self.workspace_slug = ws.get("slug") or self.workspace_slug
                                return
            except Exception:
                pass

        try:
            workspaces = self.get("/workspaces")
            if isinstance(workspaces, list):
                target = (self.workspace_slug or "").lower()
                for ws in workspaces:
                    slug = (ws.get("slug") or "").lower()
                    name = (ws.get("name") or "").lower()
                    wid = ws.get("id") or ""
                    if slug == target or name == target or wid.lower() == target:
                        self.workspace_id = wid
                        self.workspace_slug = ws.get("slug") or self.workspace_slug
                        return
                    if target in ("dev", "dev-space") and (slug in ("dev", "dev-space") or name == "dev"):
                        self.workspace_id = wid
                        self.workspace_slug = ws.get("slug") or self.workspace_slug
                        return
        except Exception:
            pass

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Perform an HTTP request against Mopheus API."""
        clean_path = path.lstrip("/")
        if not clean_path.startswith("api/v1/"):
            clean_path = f"api/v1/{clean_path}"

        url = f"{self.server_url}/{clean_path}"
        if params:
            query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            if query:
                url = f"{url}?{query}"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if self.workspace_id or self.workspace_slug:
            headers["X-Workspace-Id"] = self.workspace_id or self.workspace_slug

        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8") if data else None,
            headers=headers,
            method=method.upper(),
        )

        ctx = ssl._create_unverified_context()
        try:
            with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                raw = resp.read().decode("utf-8")
                if not raw:
                    return None
                parsed = json.loads(raw)
                if isinstance(parsed, dict) and "success" in parsed and "data" in parsed:
                    if not parsed["success"]:
                        raise RuntimeError(f"Mopheus API Error: {parsed.get('error', 'unknown error')}")
                    return parsed["data"]
                return parsed
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            try:
                err_json = json.loads(err_body)
                err_msg = err_json.get("error", err_body)
            except Exception:
                err_msg = err_body
            raise RuntimeError(f"HTTP {e.code} for {url}: {err_msg}") from e

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self.request("GET", path, params=params)

    def fetch_all_agent_tasks(self) -> List[Dict[str, Any]]:
        """Fetch all agent tasks in the workspace snapshot."""
        try:
            tasks = self.get("/agent-tasks/snapshot", params={"status": "all"})
            if isinstance(tasks, list) and len(tasks) > 0:
                return tasks
        except Exception:
            pass

        return self._fetch_tasks_via_cli()

    def _fetch_tasks_via_cli(self) -> List[Dict[str, Any]]:
        """Fallback to mopheus CLI to discover and list agent tasks."""
        try:
            cmd = ["mopheus", "agent", "list", "-o", "json"]
            if self.profile:
                cmd.extend(["--profile", self.profile])
            if self.workspace_id:
                cmd.extend(["--workspace-id", self.workspace_id])

            res = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
            agents = json.loads(res.stdout) if (res.returncode == 0 and res.stdout) else []

            all_tasks = []
            seen_ids = set()
            for agent in agents:
                agent_id = agent.get("id")
                if not agent_id:
                    continue
                page = 1
                while True:
                    task_cmd = ["mopheus", "agent-task", "list", "--agent-id", agent_id, "--page", str(page), "--per-page", "100", "-o", "json"]
                    if self.profile:
                        task_cmd.extend(["--profile", self.profile])
                    if self.workspace_id:
                        task_cmd.extend(["--workspace-id", self.workspace_id])
                    task_res = subprocess.run(task_cmd, capture_output=True, encoding="utf-8", errors="replace")
                    if task_res.returncode == 0 and task_res.stdout:
                        try:
                            tasks = json.loads(task_res.stdout)
                            if isinstance(tasks, list) and len(tasks) > 0:
                                for t in tasks:
                                    tid = t.get("id")
                                    if tid and tid not in seen_ids:
                                        seen_ids.add(tid)
                                        all_tasks.append(t)
                                if len(tasks) < 100:
                                    break
                                page += 1
                            else:
                                break
                        except Exception:
                            break
                    else:
                        break
            return all_tasks
        except Exception as e:
            print(f"[ERROR] CLI fallback failed: {e}")
            return []

    def fetch_task_messages(self, task_id: str) -> List[Dict[str, Any]]:
        """Fetch full transcript messages for an agent task."""
        try:
            msgs = self.get(f"/agent-tasks/{task_id}/messages")
            if isinstance(msgs, list) and len(msgs) > 0:
                return msgs
        except Exception:
            pass

        try:
            cmd = ["mopheus", "agent-task", "messages", task_id, "-o", "json"]
            if self.profile:
                cmd.extend(["--profile", self.profile])
            res = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
            if res.returncode == 0 and res.stdout:
                return json.loads(res.stdout)
        except Exception:
            pass
        return []

    def fetch_task_usage(self, task_id: str) -> List[Dict[str, Any]]:
        """Fetch token usage breakdown for an agent task."""
        try:
            usage = self.get(f"/agent-tasks/{task_id}/usage")
            if isinstance(usage, list) and len(usage) > 0:
                return usage
        except Exception:
            pass

        try:
            cmd = ["mopheus", "agent-task", "usage", task_id, "-o", "json"]
            if self.profile:
                cmd.extend(["--profile", self.profile])
            res = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
            if res.returncode == 0 and res.stdout:
                return json.loads(res.stdout)
        except Exception:
            pass
        return []

    def fetch_agents_map(self) -> Dict[str, Dict[str, Any]]:
        """Fetch all agents and index them by ID."""
        agents_map = {}
        try:
            agents = self.get("/agents")
            if isinstance(agents, list):
                for a in agents:
                    if "id" in a:
                        agents_map[a["id"]] = a
                return agents_map
        except Exception:
            pass

        try:
            cmd = ["mopheus", "agent", "list", "-o", "json"]
            if self.profile:
                cmd.extend(["--profile", self.profile])
            if self.workspace_id:
                cmd.extend(["--workspace-id", self.workspace_id])
            res = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
            if res.returncode == 0 and res.stdout:
                agents = json.loads(res.stdout)
                if isinstance(agents, list):
                    for a in agents:
                        if "id" in a:
                            agents_map[a["id"]] = a
        except Exception:
            pass
        return agents_map

    def fetch_tickets_map(self) -> Dict[str, Dict[str, Any]]:
        """Fetch all tickets in workspace using pagination and index them by ID."""
        tickets_map = {}
        # Try HTTP API with pagination first
        try:
            page = 1
            while True:
                tickets = self.get("/tickets", params={"page": page, "per_page": 100})
                if isinstance(tickets, list) and len(tickets) > 0:
                    for t in tickets:
                        if "id" in t:
                            tickets_map[t["id"]] = t
                    if len(tickets) < 100:
                        break
                    page += 1
                else:
                    break
            if tickets_map:
                return tickets_map
        except Exception:
            pass

        # Fallback to CLI with pagination
        try:
            page = 1
            while True:
                cmd = ["mopheus", "ticket", "list", "--limit", "100", "--page", str(page), "-o", "json"]
                if self.profile:
                    cmd.extend(["--profile", self.profile])
                if self.workspace_id:
                    cmd.extend(["--workspace-id", self.workspace_id])
                res = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
                if res.returncode == 0 and res.stdout:
                    tickets = json.loads(res.stdout)
                    if isinstance(tickets, list) and len(tickets) > 0:
                        for t in tickets:
                            if "id" in t:
                                tickets_map[t["id"]] = t
                        if len(tickets) < 100:
                            break
                        page += 1
                    else:
                        break
                else:
                    break
        except Exception:
            pass
        return tickets_map

    def fetch_runtime_guard_events(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Fetch runtime guard alarm and kill audit events."""
        try:
            events = self.get("/runtime/guard/events", params={"limit": limit})
            if isinstance(events, list):
                return events
        except Exception:
            pass

        try:
            cmd = ["mopheus", "runtime", "guard", "events", "--limit", str(limit), "-o", "json"]
            if self.profile:
                cmd.extend(["--profile", self.profile])
            if self.workspace_id:
                cmd.extend(["--workspace-id", self.workspace_id])
            res = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
            if res.returncode == 0 and res.stdout:
                parsed = json.loads(res.stdout)
                if isinstance(parsed, list):
                    return parsed
        except Exception:
            pass
        return []

    def fetch_task_guard_explain(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Fetch post-mortem forensic diagnostics for a guard-terminated task."""
        try:
            diag = self.get(f"/runtime/guard/tasks/{task_id}/explain")
            if isinstance(diag, dict) and diag.get("reason"):
                return diag
        except Exception:
            pass

        try:
            cmd = ["mopheus", "runtime", "guard", "explain", task_id, "-o", "json"]
            if self.profile:
                cmd.extend(["--profile", self.profile])
            if self.workspace_id:
                cmd.extend(["--workspace-id", self.workspace_id])
            res = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
            if res.returncode == 0 and res.stdout:
                parsed = json.loads(res.stdout)
                if isinstance(parsed, dict) and parsed.get("reason"):
                    return parsed
        except Exception:
            pass
        return None

    def fetch_runtime_guard_stats(self) -> Optional[Dict[str, Any]]:
        """Fetch runtime guard aggregate statistics."""
        try:
            stats = self.get("/runtime/guard/stats")
            if isinstance(stats, dict):
                return stats
        except Exception:
            pass

        try:
            cmd = ["mopheus", "runtime", "guard", "stats", "-o", "json"]
            if self.profile:
                cmd.extend(["--profile", self.profile])
            if self.workspace_id:
                cmd.extend(["--workspace-id", self.workspace_id])
            res = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
            if res.returncode == 0 and res.stdout:
                return json.loads(res.stdout)
        except Exception:
            pass
        return None
