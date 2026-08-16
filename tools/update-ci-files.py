#!/usr/bin/env python3
"""
Update GitHub Actions CI workflow files with frontend dependencies.

This script updates CI workflow YAML files to include all frontends in:
- cache-dependency-path for pnpm caching
- install steps in linter jobs
- PATH entries for node_modules/.bin

Uses only Python stdlib - no external dependencies required.
"""

import argparse
import re
import sys
from pathlib import Path


def get_job_for_updates(ci_filename: str) -> str | None:
    """Determine which job needs install steps and PATH updates."""
    if ci_filename == "backend-ci.yml":
        return "tests-and-linters"
    elif ci_filename == "copilot-setup-steps.yml":
        return "copilot-setup-steps"
    else:
        # All other frontend CI files
        return "run-linters"


def update_cache_dependency_paths(lines: list[str], frontends: list[str]) -> list[str]:
    """Update cache-dependency-path sections in all jobs."""
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        result.append(line)

        # Find cache-dependency-path with pipe
        if re.search(r"cache-dependency-path:\s*\|", line):
            # Skip old cache paths
            i += 1
            indent = None
            while i < len(lines):
                if "pnpm-lock.yaml" in lines[i]:
                    if indent is None:
                        # Capture indentation from first entry
                        indent = re.match(r"^(\s*)", lines[i]).group(1)
                    i += 1
                else:
                    # Hit end of cache paths section
                    break

            # Write new cache paths (sorted)
            if indent:
                result.append(f"{indent}pnpm-lock.yaml\n")
                for frontend in sorted(frontends):
                    result.append(f"{indent}{frontend}/pnpm-lock.yaml\n")
            continue

        i += 1

    return result


def update_install_and_path_in_job(
    lines: list[str], frontends: list[str], job_name: str, ci_filename: str
) -> list[str]:
    """Update install steps and PATH entries in the specified job."""
    result = []
    i = 0
    in_target_job = False
    job_indent_level = None

    while i < len(lines):
        line = lines[i]

        # Track if we're in the target job
        if re.match(rf"^\s*{re.escape(job_name)}:", line):
            in_target_job = True
            # Capture the indentation level of this job
            job_indent_level = len(line) - len(line.lstrip())
        elif in_target_job and job_indent_level is not None:
            # Check if we've hit another job at the same indentation level
            current_indent = len(line) - len(line.lstrip())
            if current_indent == job_indent_level and re.match(r"^\s*[\w-]+:\s*$", line):
                # This is another job at the same level
                in_target_job = False

        # Handle install steps section
        if in_target_job and re.search(r"- name:\s*Install root Node (deps|dependencies)", line):
            # Output root install step
            result.append(line)
            i += 1
            # Copy all properties of root install (if, run, etc.) until next "- name:"
            while i < len(lines) and not re.search(r"^\s*- name:", lines[i]):
                result.append(lines[i])
                i += 1

            # Now skip ALL existing frontend install steps (exclude "root")
            while i < len(lines):
                line_to_check = lines[i]
                if (
                    re.search(r"- name:\s*Install .+ Node (deps|dependencies)", line_to_check)
                    and "root" not in line_to_check.lower()
                ):
                    # This is a frontend install step - skip it entirely
                    i += 1
                    # Skip all properties of this install step
                    while i < len(lines) and not re.search(r"^\s*- name:", lines[i]):
                        i += 1
                else:
                    # Not a frontend install step - stop skipping
                    break

            # Insert all frontend install steps (sorted)
            indent = "            "
            for frontend in sorted(frontends):
                result.append(f"\n{indent}- name: Install {frontend} Node deps\n")

                if ci_filename == "backend-ci.yml":
                    result.append(f"{indent}  if: hashFiles('{frontend}/pnpm-lock.yaml') != ''\n")
                elif ci_filename == "copilot-setup-steps.yml":
                    result.append(
                        f"{indent}  if: ${{{{ hashFiles('{frontend}/pnpm-lock.yaml') != '' }}}}\n"
                    )

                result.append(f"{indent}  working-directory: {frontend}\n")
                result.append(f"{indent}  run: pnpm install --frozen-lockfile\n")

            # i is now positioned at the next step (PATH or something else)
            # Continue processing from there
            continue

        # Handle PATH section
        if in_target_job and re.search(r"- name:\s*Add node bin paths to PATH", line):
            result.append(line)
            i += 1
            # Copy lines until we hit "run: |"
            while i < len(lines) and not re.search(r"^\s*run:\s*\|", lines[i]):
                result.append(lines[i])
                i += 1

            if i < len(lines):
                result.append(lines[i])  # The "run: |" line
                i += 1

                # Skip all existing PATH entries
                indent = None
                while i < len(lines) and "GITHUB_PATH" in lines[i]:
                    if indent is None:
                        indent = re.match(r"^(\s*)", lines[i]).group(1)
                    i += 1

                # Write new PATH entries (sorted)
                if indent:
                    result.append(
                        f'{indent}echo "$GITHUB_WORKSPACE/node_modules/.bin" >> $GITHUB_PATH\n'
                    )
                    for frontend in sorted(frontends):
                        result.append(
                            f'{indent}echo "$GITHUB_WORKSPACE/{frontend}/node_modules/.bin" >> $GITHUB_PATH\n'
                        )

            # i is now positioned after the PATH entries
            continue

        result.append(line)
        i += 1

    return result


def update_ci_file(ci_file_path: Path, frontends: list[str]) -> None:
    """Update a single CI workflow file using text processing."""
    # Read file
    with open(ci_file_path) as f:
        lines = f.readlines()

    ci_filename = ci_file_path.name

    # Update cache-dependency-path in all jobs
    lines = update_cache_dependency_paths(lines, frontends)

    # Determine which job needs install/PATH updates
    job_name = get_job_for_updates(ci_filename)

    if job_name:
        # Update install steps and PATH entries
        lines = update_install_and_path_in_job(lines, frontends, job_name, ci_filename)

    # Write back
    with open(ci_file_path, "w") as f:
        f.writelines(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Update GitHub Actions CI workflow files with frontend dependencies"
    )
    parser.add_argument(
        "--workflows-dir", type=Path, required=True, help="Path to .github/workflows directory"
    )
    parser.add_argument(
        "--frontends",
        type=str,
        required=True,
        help="Comma-separated list of frontend names (e.g., website,auth-frontend,admin-frontend)",
    )

    args = parser.parse_args()

    # Parse frontends list
    frontends = [f.strip() for f in args.frontends.split(",") if f.strip()]

    if not frontends:
        print("Error: No frontends specified", file=sys.stderr)
        sys.exit(1)

    # Find all CI YAML files
    workflows_dir = args.workflows_dir
    if not workflows_dir.exists() or not workflows_dir.is_dir():
        print(f"Error: Workflows directory not found: {workflows_dir}", file=sys.stderr)
        sys.exit(1)

    ci_files = list(workflows_dir.glob("*.yml"))

    if not ci_files:
        print(f"Warning: No YAML files found in {workflows_dir}", file=sys.stderr)
        return

    # Update each CI file
    for ci_file in sorted(ci_files):
        print(f"Updating {ci_file.name}...")
        try:
            update_ci_file(ci_file, frontends)
        except Exception as e:
            print(f"Error updating {ci_file.name}: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"Successfully updated {len(ci_files)} CI workflow files")


if __name__ == "__main__":
    main()
