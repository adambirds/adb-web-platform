#!/usr/bin/env python3
"""
Update devcontainer.json forwardPorts and portsAttributes.
Handles JSON with comments (JSONC format).
"""

import argparse
import json
import re
import sys
from pathlib import Path


def strip_json_comments(content: str) -> str:
    """Remove // comments from JSONC content."""
    lines = []
    for line in content.split("\n"):
        # Remove line comments but preserve the line structure
        if "//" in line:
            # Keep everything before the comment
            line = line.split("//")[0].rstrip()
        lines.append(line)
    return "\n".join(lines)


def parse_jsonc(content: str) -> dict:
    """Parse JSONC content (JSON with comments)."""
    clean_content = strip_json_comments(content)
    # Remove trailing commas before closing brackets/braces
    clean_content = re.sub(r",(\s*[}\]])", r"\1", clean_content)
    return json.loads(clean_content)


def format_port_entry(port: int, label: str, is_last: bool = False) -> str:
    """Format a single port entry with comment."""
    comma = "" if is_last else ","
    return f"        {port}{comma} // {label}"


def format_ports_attributes(port: int, label: str, notify: bool = True) -> str:
    """Format port attributes entry."""
    auto_forward = "notify" if notify else "silent"
    return f"""        "{port}": {{
            "label": "{label}",
            "onAutoForward": "{auto_forward}"
        }}"""


def update_devcontainer_json(
    devcontainer_path: Path,
    backend_port: int,
    website_port: int,
    auth_frontend_port: int,
    extra_frontends: list[dict],
    postgres_port: int,
    flower_port: int = None,
) -> None:
    """Update devcontainer.json with ports."""

    if not devcontainer_path.exists():
        print(f"Error: {devcontainer_path} not found", file=sys.stderr)
        sys.exit(1)

    content = devcontainer_path.read_text()

    # Build port lists
    ports_config = [
        (backend_port, "Django Backend", True),
        (website_port, "Website", True),
        (auth_frontend_port, "Auth Frontend", True),
    ]

    # Add extra frontends
    for frontend in extra_frontends:
        ports_config.append((frontend["port"], frontend["label"], True))

    # Add Flower if provided
    if flower_port:
        ports_config.append((flower_port, "Flower (Celery Monitor)", True))

    # Add postgres last (silent notification)
    ports_config.append((postgres_port, "PostgreSQL", False))

    # Build forwardPorts array
    forward_ports_lines = ['    "forwardPorts": [']
    for i, (port, label, _) in enumerate(ports_config):
        is_last = i == len(ports_config) - 1
        forward_ports_lines.append(format_port_entry(port, label, is_last))
    forward_ports_lines.append("    ],")

    # Build portsAttributes object
    port_attrs_lines = ['    "portsAttributes": {']
    for i, (port, label, notify) in enumerate(ports_config):
        is_last = i == len(ports_config) - 1
        port_attrs_lines.append(format_ports_attributes(port, label, notify))
        if not is_last:
            port_attrs_lines[-1] += ","
    port_attrs_lines.append("    },")

    # Replace forwardPorts section
    # Match from "forwardPorts": [ to the closing ],
    forward_ports_pattern = r'    "forwardPorts":\s*\[[\s\S]*?\],\s*\n'
    content = re.sub(forward_ports_pattern, "\n".join(forward_ports_lines) + "\n\n", content)

    # Replace portsAttributes section
    # Need to match nested braces properly - find "portsAttributes": { and count braces
    def replace_port_attrs(content):
        start_pattern = r'    "portsAttributes":\s*\{'
        match = re.search(start_pattern, content)
        if not match:
            return content

        start_pos = match.start()
        brace_start = match.end() - 1  # Position of the opening {

        # Count braces to find the matching closing brace
        brace_count = 1
        pos = brace_start + 1
        while pos < len(content) and brace_count > 0:
            if content[pos] == "{":
                brace_count += 1
            elif content[pos] == "}":
                brace_count -= 1
            pos += 1

        # Find the comma after the closing brace
        end_pos = pos
        if end_pos < len(content) and content[end_pos] == ",":
            end_pos += 1

        # Replace the section
        return content[:start_pos] + "\n".join(port_attrs_lines) + "\n" + content[end_pos:]

    content = replace_port_attrs(content)

    devcontainer_path.write_text(content)
    print(f"✓ Updated {devcontainer_path.name} with {len(ports_config)} ports")


def main():
    parser = argparse.ArgumentParser(description="Update devcontainer.json ports configuration")
    parser.add_argument(
        "--devcontainer-path", required=True, type=Path, help="Path to devcontainer.json"
    )
    parser.add_argument("--backend-port", required=True, type=int, help="Backend port")
    parser.add_argument("--website-port", required=True, type=int, help="Website port")
    parser.add_argument("--auth-frontend-port", required=True, type=int, help="Auth frontend port")
    parser.add_argument(
        "--extra-frontends",
        default="",
        help="Comma-separated list of name:port:label (e.g., 'admin-frontend:5174:Admin Frontend,docs:5175:Documentation')",
    )
    parser.add_argument("--postgres-port", required=True, type=int, help="PostgreSQL port")
    parser.add_argument("--flower-port", type=int, help="Flower monitoring port (optional)")

    args = parser.parse_args()

    # Parse extra frontends
    extra_frontends = []
    if args.extra_frontends:
        for frontend_str in args.extra_frontends.split(","):
            if frontend_str.strip():
                name, port, label = frontend_str.strip().split(":")
                extra_frontends.append({"name": name, "port": int(port), "label": label})

    update_devcontainer_json(
        args.devcontainer_path,
        args.backend_port,
        args.website_port,
        args.auth_frontend_port,
        extra_frontends,
        args.postgres_port,
        args.flower_port,
    )


if __name__ == "__main__":
    main()
