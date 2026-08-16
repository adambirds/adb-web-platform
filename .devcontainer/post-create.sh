#!/usr/bin/env bash
set -Eeuo pipefail

error_trap() {
	local code=$?
	echo "post-create failed at line $LINENO: ${BASH_COMMAND} (exit $code)"
	exit "$code"
}
trap error_trap ERR

BASHRC="/root/.bashrc"
export SHELL="${SHELL:-/bin/bash}"
export PNPM_HOME="${PNPM_HOME:-/usr/local/share/pnpm}"
export PATH="$PNPM_HOME:$PATH"

echo "Setting up ADB web platform development environment..."
cd /workspace

if [ ! -f .devcontainer/.env ]; then
	echo "Creating devcontainer environment file..."
	cp .devcontainer/.env.example .devcontainer/.env
	echo "Please update .devcontainer/.env with your actual credentials"
fi

echo "Installing Node dependencies from the root workspace..."
pnpm install

echo "Waiting for database to be ready..."
until /opt/venv/bin/python -c "
import sys
import psycopg2
try:
    psycopg2.connect(
        dbname='adbsoftwaresolutions_dev',
        user='adbsoftwaresolutions',
        password='adbsoftwaresolutions_dev_password',
        host='db',
        port=5432,
    )
except psycopg2.OperationalError:
    sys.exit(-1)
sys.exit(0)
"; do
	sleep 1
done
echo "PostgreSQL is available"

echo "Running Django migrations..."
source /opt/venv/bin/activate
python backend/manage.py migrate --noinput

if [ -f .pre-commit-config.yaml ]; then
	if ! command -v pre-commit >/dev/null 2>&1; then
		pip install pre-commit >/dev/null 2>&1 || true
	fi
	echo "Installing pre-commit hooks..."
	pre-commit install || echo "Pre-commit not available"
fi

git config --global --add safe.directory /workspace

MARK_BEGIN="# >>> devcontainer: ensure (venv) prompt begin >>>"
MARK_END="# <<< devcontainer: ensure (venv) prompt end <<<"
if grep -qF "$MARK_BEGIN" "$BASHRC" 2>/dev/null; then
	awk -v s="$MARK_BEGIN" -v e="$MARK_END" '
    $0==s {inblk=1; next}
    $0==e {inblk=0; next}
    !inblk {print}
  ' "$BASHRC" >"${BASHRC}.tmp" && mv "${BASHRC}.tmp" "$BASHRC"
fi

cat >>"$BASHRC" <<'EOF'
# >>> devcontainer: ensure (venv) prompt begin >>>
if [ -n "$PS1" ]; then
  unset VIRTUAL_ENV_DISABLE_PROMPT
  export VIRTUAL_ENV_PROMPT="(venv) "
  if [ -f /opt/venv/bin/activate ]; then
    . /opt/venv/bin/activate
  fi
  if [ -n "$VIRTUAL_ENV" ] && [[ "$PS1" != *"(venv)"* ]] && [[ "$PS1" != *"($(basename "$VIRTUAL_ENV"))"* ]]; then
    PS1="${VIRTUAL_ENV_PROMPT:-($(basename "$VIRTUAL_ENV")) }$PS1"
  fi
fi
# <<< devcontainer: ensure (venv) prompt end <<<
EOF

HIST_DIR="/root/.history"
HIST_FILE="${HIST_DIR}/.bash_history"
HIST_BEGIN="# >>> devcontainer: persistent bash history begin >>>"
HIST_END="# <<< devcontainer: persistent bash history end <<<"
mkdir -p "$HIST_DIR"
touch "$HIST_FILE"
chmod 700 "$HIST_DIR"
chmod 600 "$HIST_FILE"
ln -sf "$HIST_FILE" /root/.bash_history

if grep -qF "$HIST_BEGIN" "$BASHRC" 2>/dev/null; then
	awk -v s="$HIST_BEGIN" -v e="$HIST_END" '
    $0==s {inblk=1; next}
    $0==e {inblk=0; next}
    !inblk {print}
  ' "$BASHRC" >"${BASHRC}.tmp" && mv "${BASHRC}.tmp" "$BASHRC"
fi

cat >>"$BASHRC" <<EOF
${HIST_BEGIN}
export HISTFILE="${HIST_FILE}"
export HISTSIZE=50000
export HISTFILESIZE=100000
export HISTCONTROL=ignoredups:erasedups
export HISTTIMEFORMAT='%F %T '
shopt -s histappend
PROMPT_COMMAND="history -a; history -n; \${PROMPT_COMMAND}"
${HIST_END}
EOF

COMP_DIR="/etc/bash_completion.d"
COMP_BEGIN="# >>> devcontainer: bash-completion begin >>>"
COMP_END="# <<< devcontainer: bash-completion end <<<"
mkdir -p "$COMP_DIR"

if grep -qF "$COMP_BEGIN" "$BASHRC" 2>/dev/null; then
	awk -v s="$COMP_BEGIN" -v e="$COMP_END" '
    $0==s {inblk=1; next}
    $0==e {inblk=0; next}
    !inblk {print}
  ' "$BASHRC" >"${BASHRC}.tmp" && mv "${BASHRC}.tmp" "$BASHRC"
fi

cat >>"$BASHRC" <<'EOF'
# >>> devcontainer: bash-completion begin >>>
if [ -n "$PS1" ]; then
  if [ -r /etc/profile.d/bash_completion.sh ]; then
    . /etc/profile.d/bash_completion.sh
  elif [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  fi
fi
bind "set completion-ignore-case on"
bind "set show-all-if-ambiguous on"
bind "set menu-complete-display-prefix on"
# <<< devcontainer: bash-completion end <<<
EOF

if command -v gh >/dev/null 2>&1; then
	gh completion -s bash >"${COMP_DIR}/gh"
fi
if command -v npm >/dev/null 2>&1; then
	npm completion >"${COMP_DIR}/npm"
	cp -f "${COMP_DIR}/npm" "${COMP_DIR}/npx"
fi
if command -v pnpm >/dev/null 2>&1; then
	pnpm completion bash >"${COMP_DIR}/pnpm"
fi
if command -v python >/dev/null 2>&1; then
	python -m pip completion --bash >"${COMP_DIR}/pip" 2>/dev/null || true
fi
if command -v kubectl >/dev/null 2>&1; then
	kubectl completion bash >"${COMP_DIR}/kubectl"
fi
if command -v terraform >/dev/null 2>&1; then
	terraform -install-autocomplete >/dev/null 2>&1 || true
fi

STARSHIP_LINE="# >>> devcontainer: starship init >>>"
if ! grep -qF "$STARSHIP_LINE" "$BASHRC" 2>/dev/null; then
	cat >>"$BASHRC" <<'EOF'
# >>> devcontainer: starship init >>>
if command -v starship >/dev/null 2>&1; then
  eval "$(starship init bash)"
fi
# <<< devcontainer: starship init <<<
EOF
fi

mkdir -p /root/.config
cat >/root/.config/starship.toml <<'EOF'
add_newline = false
format = "$directory$git_branch$git_status$python$cmd_duration$character"

[directory]
truncation_length = 3
truncate_to_repo = true

[git_status]
disabled = true

[cmd_duration]
min_time = 1000

[character]
success_symbol = "\\$ "
error_symbol = "! "
EOF

echo "Development environment setup complete!"
echo ""
echo "Quick start commands:"
echo "  Backend:               python backend/manage.py runserver 0.0.0.0:8000"
echo "  Admin:                 pnpm dev:admin"
echo "  Software Solutions:    pnpm dev:software-solutions"
echo "  Web Designs:           pnpm dev:web-designs"
echo "  ADB Technology:        pnpm dev:technology"
echo "  Auth:                  pnpm dev:auth"
echo "  Flower:                cd /workspace/backend && celery -A adbsoftwaresolutions flower --port=5555 --address=0.0.0.0"
echo ""
echo "Access URLs:"
echo "  Django Admin:          http://localhost:8000/admin/"
echo "  Internal Admin:        http://localhost:3000/"
echo "  Software Solutions:    http://localhost:3001/"
echo "  Web Designs:           http://localhost:3002/"
echo "  ADB Technology:        http://localhost:3003/"
echo "  Auth Frontend:         http://localhost:5173/"
