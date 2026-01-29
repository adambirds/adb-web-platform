#!/usr/bin/env python3
"""
Update .vscode/tasks.json with new frontend tasks.

This script adds new frontend tasks to VS Code tasks.json,
including Start and Test tasks, and updates the dependencies
of the composite tasks "Start Full Stack" and "Test All".

Uses stdlib only - no external dependencies required.
"""

import argparse
import json
import sys
from typing import Dict, List


def capitalize_frontend_name(frontend: str) -> str:
    """Convert frontend name to capitalized label (e.g., 'admin-frontend' -> 'Admin Frontend')."""
    return " ".join(word.capitalize() for word in frontend.split("-"))


def create_start_task(frontend: str, label: str) -> Dict:
    """Create a Start task for a frontend."""
    return {
        "label": f"Start {label}",
        "type": "shell",
        "command": f"start-{frontend}",
        "group": "build",
        "isBackground": True,
        "problemMatcher": []
    }


def create_test_task(frontend: str, label: str) -> Dict:
    """Create a Test task for a frontend."""
    return {
        "label": f"Test {label}",
        "type": "shell",
        "command": f"test-{frontend}",
        "group": "test"
    }


def update_tasks_json(tasks_file: str, frontends: List[str]) -> None:
    """
    Update tasks.json with new frontend tasks.
    
    Args:
        tasks_file: Path to tasks.json file
        frontends: List of all frontend directories (website, auth-frontend, etc.)
    """
    # Read existing tasks.json
    try:
        with open(tasks_file, "r", encoding="utf-8") as f:
            tasks_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {tasks_file} not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse {tasks_file}: {e}", file=sys.stderr)
        sys.exit(1)
    
    if "tasks" not in tasks_data or not isinstance(tasks_data["tasks"], list):
        print(f"Error: {tasks_file} does not have a valid 'tasks' array", file=sys.stderr)
        sys.exit(1)
    
    existing_tasks = tasks_data["tasks"]
    
    # Track existing task labels and commands to detect duplicates
    existing_labels = {}
    for i, task in enumerate(existing_tasks):
        label = task.get("label", "")
        command = task.get("command", "")
        if label:
            existing_labels[label] = i
        # Also track by command for duplicates like "Start Website" vs "Start Website (Next.js)"
        if command:
            # Check if there's another task with same command but different label
            for j, other_task in enumerate(existing_tasks):
                if i != j and other_task.get("command") == command:
                    other_label = other_task.get("label", "")
                    # Keep the simpler label, remove the more complex one
                    if len(label) < len(other_label):
                        existing_labels[other_label] = -1  # Mark for removal
                    elif len(label) > len(other_label):
                        existing_labels[label] = -1  # Mark for removal
    
    # Remove duplicate tasks (marked with -1)
    tasks_to_remove = [label for label, idx in existing_labels.items() if idx == -1]
    if tasks_to_remove:
        existing_tasks[:] = [task for task in existing_tasks if task.get("label", "") not in tasks_to_remove]
        print(f"  Removed {len(tasks_to_remove)} duplicate tasks")
        # Rebuild label index
        existing_labels = {task.get("label", ""): i for i, task in enumerate(existing_tasks) if task.get("label", "")}
    
    # Find "Start Full Stack" and "Test All" tasks
    start_full_stack_task = None
    test_all_task = None
    
    for task in existing_tasks:
        label = task.get("label", "")
        if label == "Start Full Stack":
            start_full_stack_task = task
        elif label == "Test All":
            test_all_task = task
    
    # Build lists of new frontends that need tasks
    new_frontends = []
    for frontend in frontends:
        label = capitalize_frontend_name(frontend)
        start_label = f"Start {label}"
        test_label = f"Test {label}"
        
        # Only add if tasks don't already exist
        if start_label not in existing_labels or test_label not in existing_labels:
            new_frontends.append(frontend)
    
    # Create and add new tasks
    new_tasks = []
    for frontend in new_frontends:
        label = capitalize_frontend_name(frontend)
        
        # Add Start task if it doesn't exist
        start_label = f"Start {label}"
        if start_label not in existing_labels:
            new_tasks.append(create_start_task(frontend, label))
            existing_labels[start_label] = len(existing_tasks) + len(new_tasks) - 1
        
        # Add Test task if it doesn't exist
        test_label = f"Test {label}"
        if test_label not in existing_labels:
            new_tasks.append(create_test_task(frontend, label))
            existing_labels[test_label] = len(existing_tasks) + len(new_tasks) - 1
    
    # Add new tasks to the tasks array
    if new_tasks:
        existing_tasks.extend(new_tasks)
        print(f"  Added {len(new_tasks)} new tasks")
    
    # Update "Start Full Stack" dependencies
    if start_full_stack_task and "dependsOn" in start_full_stack_task:
        current_deps = start_full_stack_task["dependsOn"]
        if not isinstance(current_deps, list):
            current_deps = []
        
        # Add new frontend start tasks
        for frontend in frontends:
            label = capitalize_frontend_name(frontend)
            dep = f"Start {label}"
            if dep not in current_deps:
                current_deps.append(dep)
        
        start_full_stack_task["dependsOn"] = current_deps
        print(f"  Updated 'Start Full Stack' dependencies: {len(current_deps)} tasks")
    
    # Update "Test All" dependencies
    if test_all_task and "dependsOn" in test_all_task:
        current_deps = test_all_task["dependsOn"]
        if not isinstance(current_deps, list):
            current_deps = []
        
        # Add new frontend test tasks
        for frontend in frontends:
            label = capitalize_frontend_name(frontend)
            dep = f"Test {label}"
            if dep not in current_deps:
                current_deps.append(dep)
        
        test_all_task["dependsOn"] = current_deps
        print(f"  Updated 'Test All' dependencies: {len(current_deps)} tasks")
    
    # Write updated tasks.json
    try:
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, indent=4, ensure_ascii=False)
            f.write("\n")  # Add trailing newline
        print(f"  ✓ Successfully updated {tasks_file}")
    except Exception as e:
        print(f"Error: Failed to write {tasks_file}: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Update .vscode/tasks.json with new frontend tasks"
    )
    parser.add_argument(
        "--tasks-file",
        required=True,
        help="Path to tasks.json file"
    )
    parser.add_argument(
        "--frontends",
        required=True,
        help="Comma-separated list of frontend directories (e.g., 'website,auth-frontend,admin-frontend')"
    )
    
    args = parser.parse_args()
    
    # Parse frontends list
    frontends = [f.strip() for f in args.frontends.split(",") if f.strip()]
    
    if not frontends:
        print("Error: No frontends provided", file=sys.stderr)
        sys.exit(1)
    
    print(f"Updating tasks.json with {len(frontends)} frontends...")
    update_tasks_json(args.tasks_file, frontends)


if __name__ == "__main__":
    main()
