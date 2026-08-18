# Python requirements

The `*.in` files are the human-maintained dependency manifests. Keep **direct dependencies only** in these files and pin the version we have intentionally validated.

Do not copy transitive packages from `pip freeze` into an input file merely to pin them. Transitive dependencies are resolved by `pip-tools` and are pinned with hashes in the generated `*.txt` lock files.

After changing any `*.in` file, regenerate the lock files from the repository root:

```bash
tools/update-locked-requirements
```

Commit both the input manifest changes and the generated lock-file changes together. Never hand-edit the generated `*.txt` files.
