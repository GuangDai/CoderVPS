#!/usr/bin/env bash
set -uo pipefail

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/go/bin:/usr/local/cargo/bin:/home/coder/go/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

image_profile="${IMAGE_PROFILE:-full}"
extension_profile="${EXTENSION_PROFILE:-match_image}"

if [[ "$extension_profile" == "match_image" ]]; then
  profile="$image_profile"
else
  profile="$extension_profile"
fi

cache_root="${CDE_CACHE_ROOT:-/opt/cde/cache}"
export CDE_CACHE_ROOT="$cache_root"

ext_dir="/opt/cde/extensions"
vsix_dir="/opt/cde/vsix"

code_server_port="13337"
code_server_url="http://127.0.0.1:${code_server_port}"
pid_file="$HOME/.cache/code-server-${code_server_port}.pid"
code_server_log="$HOME/.cache/code-server.log"

settings="$HOME/.local/share/code-server/User/settings.json"

mkdir -p \
  "$HOME/workspace" \
  "$HOME/.cache" \
  "$HOME/.config/code-server" \
  "$HOME/.local/bin" \
  "$HOME/.local/share/code-server/User" \
  "$cache_root"

setup_shared_link_dir() {
  local target="$1"
  local link="$2"

  mkdir -p "$target" "$(dirname "$link")"

  if [[ -L "$link" ]]; then
    ln -sfn "$target" "$link"
    return 0
  fi

  if [[ ! -e "$link" ]]; then
    ln -sfn "$target" "$link"
    return 0
  fi

  if [[ -d "$link" ]]; then
    if find "$link" -mindepth 1 -maxdepth 1 | read -r _; then
      local backup="${link}.local-backup.$(date +%Y%m%d%H%M%S)"
      echo "[cache] migrating existing directory into shared cache: $link -> $target"
      cp -a "$link"/. "$target"/ 2>/dev/null || true
      mv "$link" "$backup" 2>/dev/null || true
      ln -sfn "$target" "$link"
      echo "[cache] previous local directory kept at: $backup"
      return 0
    fi

    rmdir "$link" 2>/dev/null || true
    ln -sfn "$target" "$link"
    return 0
  fi

  echo "[cache] existing non-directory kept, not replacing: $link"
}

echo "[startup] IMAGE_PROFILE=${image_profile}"
echo "[startup] EXTENSION_PROFILE=${extension_profile}"
echo "[startup] resolved extension profile=${profile}"
echo "[startup] CDE_CACHE_ROOT=${CDE_CACHE_ROOT}"
echo "[startup] NODE_VERSION=${NODE_VERSION:-unknown}"

if command -v node >/dev/null 2>&1; then
  export NPM_CONFIG_CACHE="${NPM_CONFIG_CACHE:-$cache_root/npm}"
  export COREPACK_HOME="${COREPACK_HOME:-$cache_root/corepack}"

  mkdir -p "$NPM_CONFIG_CACHE" "$COREPACK_HOME"

  npm config set cache "$NPM_CONFIG_CACHE" --location=user >/dev/null 2>&1 || true
  corepack enable >/dev/null 2>&1 || true

  echo "[node] $(node --version)"
  echo "[npm] $(npm --version 2>/dev/null || true)"
else
  echo "[node] node not installed; this should not happen in the current template"
fi

if command -v rustup >/dev/null 2>&1; then
  rustup_bin="$(readlink -f "$(command -v rustup)" 2>/dev/null || command -v rustup)"

  case "$rustup_bin" in
  /usr/local/cargo/bin/rustup)
    export CARGO_HOME="/usr/local/cargo"
    ;;
  *)
    export CARGO_HOME="${CARGO_HOME:-$HOME/.cargo}"
    ;;
  esac

  export CARGO_INSTALL_ROOT="${CARGO_INSTALL_ROOT:-$HOME/.local}"
  export RUSTUP_HOME="${RUSTUP_HOME:-$cache_root/rustup}"
  export RUST_DEFAULT_TOOLCHAIN="${RUST_DEFAULT_TOOLCHAIN:-stable}"

  mkdir -p \
    "$CARGO_HOME" \
    "$CARGO_HOME/bin" \
    "$CARGO_INSTALL_ROOT" \
    "$CARGO_INSTALL_ROOT/bin" \
    "$RUSTUP_HOME" \
    "$cache_root/cargo/registry" \
    "$cache_root/cargo/git" \
    "$cache_root/cargo-target"

  setup_shared_link_dir "$cache_root/cargo/registry" "$CARGO_HOME/registry"
  setup_shared_link_dir "$cache_root/cargo/git" "$CARGO_HOME/git"

  if command -v sccache >/dev/null 2>&1; then
    export RUSTC_WRAPPER="${RUSTC_WRAPPER:-sccache}"
    export SCCACHE_DIR="${SCCACHE_DIR:-$cache_root/sccache}"
    export SCCACHE_CACHE_SIZE="${SCCACHE_CACHE_SIZE:-50G}"

    mkdir -p "$SCCACHE_DIR"

    if [[ ! -s "$CARGO_HOME/config.toml" ]]; then
      cat >"$CARGO_HOME/config.toml" <<'TOML'
[build]
rustc-wrapper = "sccache"

[net]
git-fetch-with-cli = true

[install]
root = "/home/coder/.local"
TOML
    fi

    sccache --start-server >/dev/null 2>&1 || true
  else
    if [[ ! -s "$CARGO_HOME/config.toml" ]]; then
      cat >"$CARGO_HOME/config.toml" <<'TOML'
[net]
git-fetch-with-cli = true

[install]
root = "/home/coder/.local"
TOML
    fi
  fi

  echo "[rust] rustup binary: ${rustup_bin}"
  echo "[rust] CARGO_HOME=${CARGO_HOME}"
  echo "[rust] RUSTUP_HOME=${RUSTUP_HOME}"
  echo "[rust] ensuring default toolchain: ${RUST_DEFAULT_TOOLCHAIN}"

  rustup toolchain install "$RUST_DEFAULT_TOOLCHAIN" \
    --profile minimal \
    >"$HOME/.cache/cde-rustup.log" 2>&1 || {
    echo "[rust] rustup toolchain install did not complete; continuing"
    tail -80 "$HOME/.cache/cde-rustup.log" 2>/dev/null || true
  }

  rustup component add rustfmt --toolchain "$RUST_DEFAULT_TOOLCHAIN" >/dev/null 2>&1 || true
  rustup component add clippy --toolchain "$RUST_DEFAULT_TOOLCHAIN" >/dev/null 2>&1 || true
  rustup component add rust-src --toolchain "$RUST_DEFAULT_TOOLCHAIN" >/dev/null 2>&1 || true
  rustup default "$RUST_DEFAULT_TOOLCHAIN" >/dev/null 2>&1 || true

  cat >"$HOME/.local/bin/cargo-shared" <<'EOS'
#!/usr/bin/env bash
set -uo pipefail

cache_root="${CDE_CACHE_ROOT:-/opt/cde/cache}"

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"

if [[ -n "$repo_root" ]]; then
  repo_key="$(printf '%s' "$repo_root" | sha256sum | awk '{print substr($1,1,16)}')"
else
  repo_key="$(pwd | sha256sum | awk '{print substr($1,1,16)}')"
fi

mkdir -p "$cache_root/cargo-target/$repo_key"

export CARGO_TARGET_DIR="$cache_root/cargo-target/$repo_key"
exec cargo "$@"
EOS

  chmod +x "$HOME/.local/bin/cargo-shared"
else
  echo "[rust] rustup not installed for IMAGE_PROFILE=${image_profile}; skipping Rust setup"
fi

if command -v go >/dev/null 2>&1; then
  export GOCACHE="${GOCACHE:-$cache_root/go/build}"
  export GOMODCACHE="${GOMODCACHE:-$cache_root/go/pkg/mod}"
  export GOTOOLCHAIN="${GOTOOLCHAIN:-local}"

  mkdir -p "$GOCACHE" "$GOMODCACHE"

  cat >"$HOME/.local/bin/cde-install-go-tools" <<'EOS'
#!/usr/bin/env bash
set -uo pipefail

export GOBIN="${GOBIN:-$HOME/go/bin}"
mkdir -p "$GOBIN"

echo "[go] installing gopls and dlv into $GOBIN"
go install golang.org/x/tools/gopls@latest
go install github.com/go-delve/delve/cmd/dlv@latest
EOS

  chmod +x "$HOME/.local/bin/cde-install-go-tools"
else
  echo "[go] Go not installed for IMAGE_PROFILE=${image_profile}; skipping Go cache setup"
fi

if command -v ccache >/dev/null 2>&1; then
  export CCACHE_DIR="${CCACHE_DIR:-$cache_root/ccache}"
  mkdir -p "$CCACHE_DIR"

  ccache --set-config=max_size=20G >/dev/null 2>&1 || true

  if [[ -x /usr/bin/clang ]]; then
    cat >"$HOME/.local/bin/clang" <<'EOS'
#!/usr/bin/env bash
exec ccache /usr/bin/clang "$@"
EOS
    chmod +x "$HOME/.local/bin/clang"
  fi

  if [[ -x /usr/bin/clang++ ]]; then
    cat >"$HOME/.local/bin/clang++" <<'EOS'
#!/usr/bin/env bash
exec ccache /usr/bin/clang++ "$@"
EOS
    chmod +x "$HOME/.local/bin/clang++"
  fi
else
  echo "[cpp] ccache not installed for IMAGE_PROFILE=${image_profile}; skipping C/C++ compiler wrapper setup"
fi

if command -v uv >/dev/null 2>&1; then
  export PYTHON_VERSION="${PYTHON_VERSION:-system}"
  export UV_CACHE_DIR="${UV_CACHE_DIR:-$cache_root/uv}"
  export PIP_CACHE_DIR="${PIP_CACHE_DIR:-$cache_root/pip}"

  mkdir -p "$UV_CACHE_DIR" "$PIP_CACHE_DIR"

  if [[ "$PYTHON_VERSION" != "system" ]]; then
    echo "[python] ensuring uv-managed Python: ${PYTHON_VERSION}"

    if [[ "$PYTHON_VERSION" == "latest" ]]; then
      uv python install 3 --default \
        >"$HOME/.cache/cde-uv-python.log" 2>&1 || {
        echo "[python] uv latest Python install did not complete; continuing with existing/system Python"
        tail -80 "$HOME/.cache/cde-uv-python.log" 2>/dev/null || true
      }
      py_bin="$(uv python find 3 2>/dev/null || command -v python3 2>/dev/null || true)"
    else
      uv python install "$PYTHON_VERSION" --default \
        >"$HOME/.cache/cde-uv-python.log" 2>&1 || {
        echo "[python] uv python install did not complete; continuing with existing/system Python"
        tail -80 "$HOME/.cache/cde-uv-python.log" 2>/dev/null || true
      }
      py_bin="$(uv python find "$PYTHON_VERSION" 2>/dev/null || command -v python3 2>/dev/null || true)"
    fi

    if [[ -n "${py_bin:-}" && -x "$py_bin" ]]; then
      ln -sfn "$py_bin" "$HOME/.local/bin/python"
      ln -sfn "$py_bin" "$HOME/.local/bin/python3"
      echo "[python] default python -> $py_bin"
    else
      echo "[python] could not resolve uv Python ${PYTHON_VERSION}; leaving system Python"
    fi
  fi

  cat >"$HOME/.local/bin/cde-install-python-tools" <<'EOS'
#!/usr/bin/env bash
set -uo pipefail

echo "[python] installing common Python tools with uv tool install"
uv tool install ruff --force || true
uv tool install debugpy --force || true
uv tool install ipython --force || true
EOS

  chmod +x "$HOME/.local/bin/cde-install-python-tools"
else
  echo "[python] uv not available; skipping uv Python setup"
fi

cat >"$HOME/.local/bin/cde-cache-stats" <<'EOS'
#!/usr/bin/env bash
set -uo pipefail

cache_root="${CDE_CACHE_ROOT:-/opt/cde/cache}"

echo "== cache root =="
echo "$cache_root"
echo

echo "== toolchains =="
node --version 2>/dev/null || true
npm --version 2>/dev/null || true
rustc --version 2>/dev/null || true
cargo --version 2>/dev/null || true
go version 2>/dev/null || true
python --version 2>/dev/null || python3 --version 2>/dev/null || true
clang --version 2>/dev/null | head -1 || true
clangd --version 2>/dev/null | head -1 || true
echo

echo "== sccache =="
if command -v sccache >/dev/null 2>&1; then
  sccache --show-stats || true
else
  echo "sccache not installed"
fi
echo

echo "== ccache =="
if command -v ccache >/dev/null 2>&1; then
  ccache --show-stats || true
else
  echo "ccache not installed"
fi
echo

echo "== cache sizes =="
du -sh \
  "$cache_root/npm" \
  "$cache_root/corepack" \
  "$cache_root/sccache" \
  "$cache_root/ccache" \
  "$cache_root/cargo/registry" \
  "$cache_root/cargo/git" \
  "$cache_root/cargo-target" \
  "$cache_root/go" \
  "$cache_root/uv" \
  "$cache_root/pip" \
  "$cache_root/rustup" \
  2>/dev/null || true
EOS

chmod +x "$HOME/.local/bin/cde-cache-stats"

python_path="/usr/bin/python3"

if [[ -x "$HOME/.local/bin/python3" ]]; then
  python_path="$HOME/.local/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
  python_path="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  python_path="$(command -v python)"
fi

if [[ ! -s "$settings" ]]; then
  cat >"$settings" <<JSON
{
  "editor.formatOnSave": false,
  "terminal.integrated.defaultProfile.linux": "bash",
  "rust-analyzer.check.command": "clippy",
  "clangd.arguments": ["--background-index", "--clang-tidy"],
  "python.defaultInterpreterPath": "${python_path}",
  "go.toolsManagement.autoUpdate": false,
  "terminal.integrated.fontFamily": "Menlo, Monaco, 'Courier New', monospace",
  "terminal.integrated.fontSize": 13,
  "terminal.integrated.lineHeight": 1.1,
  "terminal.integrated.letterSpacing": 0
}
JSON
fi

cat >"$HOME/.config/code-server/config.yaml" <<YAML
bind-addr: 127.0.0.1:${code_server_port}
auth: none
cert: false
YAML

is_code_server_healthy() {
  curl -fsS "${code_server_url}/healthz" >/dev/null 2>&1 ||
    curl -fsS "${code_server_url}/" >/dev/null 2>&1
}

echo "[code-server] checking ${code_server_url}"

if is_code_server_healthy; then
  echo "[code-server] already running"
else
  if [[ -f "$pid_file" ]]; then
    old_pid="$(cat "$pid_file" 2>/dev/null || true)"

    if [[ -n "${old_pid:-}" ]] && kill -0 "$old_pid" 2>/dev/null; then
      if ps -p "$old_pid" -o comm= 2>/dev/null | grep -q '^code-server$'; then
        echo "[code-server] stopping stale pid ${old_pid}"
        kill "$old_pid" 2>/dev/null || true
        sleep 1
      fi
    fi

    rm -f "$pid_file"
  fi

  echo "[code-server] starting on 127.0.0.1:${code_server_port}"

  if command -v setsid >/dev/null 2>&1; then
    setsid code-server \
      --auth none \
      --bind-addr "127.0.0.1:${code_server_port}" \
      "$HOME/workspace" \
      >"$code_server_log" 2>&1 </dev/null &
  else
    nohup code-server \
      --auth none \
      --bind-addr "127.0.0.1:${code_server_port}" \
      "$HOME/workspace" \
      >"$code_server_log" 2>&1 </dev/null &
  fi

  echo "$!" >"$pid_file"
fi

for _ in $(seq 1 15); do
  if is_code_server_healthy; then
    echo "[code-server] ready"
    break
  fi

  sleep 1
done

if ! is_code_server_healthy; then
  echo "[code-server] not healthy yet; continuing without failing workspace startup"
  tail -120 "$code_server_log" 2>/dev/null || true
fi

cat >"$HOME/.cache/cde-install-extensions.sh" <<'EOS'
#!/usr/bin/env bash
set -uo pipefail

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/go/bin:/usr/local/cargo/bin:/home/coder/go/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

image_profile="${IMAGE_PROFILE:-full}"
extension_profile="${EXTENSION_PROFILE:-match_image}"

if [[ "$extension_profile" == "match_image" ]]; then
  profile="$image_profile"
else
  profile="$extension_profile"
fi

ext_dir="/opt/cde/extensions"
vsix_dir="/opt/cde/vsix"

mkdir -p "$HOME/.cache" "$HOME/.local/share/code-server/User"

lists=("core.txt")

case "$profile" in
  core)
    ;;
  rust)
    lists+=("rust.txt")
    ;;
  cpp)
    lists+=("cpp.txt")
    ;;
  go)
    lists+=("go.txt")
    ;;
  python)
    lists+=("python.txt")
    ;;
  full)
    lists+=("rust.txt" "cpp.txt" "go.txt" "python.txt")
    ;;
  *)
    echo "[extensions] unknown profile: ${profile}; using core"
    ;;
esac

hash_vsix_dir() {
  local dir="$1"

  [[ -d "$dir" ]] || return 0
  compgen -G "$dir/*.vsix" >/dev/null || return 0

  sha256sum "$dir"/*.vsix 2>/dev/null || true
}

fingerprint() {
  {
    for f in "${lists[@]}"; do
      [[ -f "${ext_dir}/${f}" ]] && cat "${ext_dir}/${f}"
    done

    hash_vsix_dir "${vsix_dir}"
    hash_vsix_dir "${vsix_dir}/core"

    case "$profile" in
      full)
        hash_vsix_dir "${vsix_dir}/rust"
        hash_vsix_dir "${vsix_dir}/cpp"
        hash_vsix_dir "${vsix_dir}/go"
        hash_vsix_dir "${vsix_dir}/python"
        hash_vsix_dir "${vsix_dir}/full"
        ;;
      rust)
        hash_vsix_dir "${vsix_dir}/rust"
        ;;
      cpp)
        hash_vsix_dir "${vsix_dir}/cpp"
        ;;
      go)
        hash_vsix_dir "${vsix_dir}/go"
        ;;
      python)
        hash_vsix_dir "${vsix_dir}/python"
        ;;
      core)
        ;;
    esac
  } | sha256sum | awk '{print $1}'
}

install_list() {
  local list="$1"

  [[ -f "$list" ]] || return 0

  sed -e 's/#.*//' -e '/^[[:space:]]*$/d' "$list" | while read -r ext; do
    [[ -n "$ext" ]] || continue

    echo "[extensions] install ${ext}"
    code-server --install-extension "$ext" --force || echo "[extensions] failed: ${ext}"
  done
}

install_vsix_dir() {
  local dir="$1"

  [[ -d "$dir" ]] || return 0
  compgen -G "$dir/*.vsix" >/dev/null || return 0

  for vsix in "$dir"/*.vsix; do
    echo "[extensions] install VSIX ${vsix}"
    code-server --install-extension "$vsix" --force || echo "[extensions] failed VSIX: ${vsix}"
  done
}

lockdir="$HOME/.cache/cde-extension-install.lock"

if ! mkdir "$lockdir" 2>/dev/null; then
  echo "[extensions] another installer is running; skip"
  exit 0
fi

trap 'rmdir "$lockdir" 2>/dev/null || true' EXIT

state_file="$HOME/.cache/cde-extension-${profile}.sha256"
fp="$(fingerprint)"
old=""

[[ -f "$state_file" ]] && old="$(cat "$state_file" 2>/dev/null || true)"

if [[ "$fp" == "$old" ]]; then
  echo "[extensions] catalog unchanged; skip"
  exit 0
fi

echo "[extensions] profile=${profile}; installing/updating extension catalog"

for f in "${lists[@]}"; do
  install_list "${ext_dir}/${f}"
done

install_vsix_dir "${vsix_dir}"
install_vsix_dir "${vsix_dir}/core"

case "$profile" in
  full)
    install_vsix_dir "${vsix_dir}/rust"
    install_vsix_dir "${vsix_dir}/cpp"
    install_vsix_dir "${vsix_dir}/go"
    install_vsix_dir "${vsix_dir}/python"
    install_vsix_dir "${vsix_dir}/full"
    ;;
  rust)
    install_vsix_dir "${vsix_dir}/rust"
    ;;
  cpp)
    install_vsix_dir "${vsix_dir}/cpp"
    ;;
  go)
    install_vsix_dir "${vsix_dir}/go"
    ;;
  python)
    install_vsix_dir "${vsix_dir}/python"
    ;;
  core)
    ;;
esac

echo "$fp" > "$state_file"

echo "[extensions] done"
exit 0
EOS

chmod +x "$HOME/.cache/cde-install-extensions.sh"

echo "[extensions] installer started in background"

if command -v setsid >/dev/null 2>&1; then
  setsid bash "$HOME/.cache/cde-install-extensions.sh" \
    >"$HOME/.cache/cde-extension-install.log" 2>&1 </dev/null &
else
  nohup bash "$HOME/.cache/cde-install-extensions.sh" \
    >"$HOME/.cache/cde-extension-install.log" 2>&1 </dev/null &
fi

exit 0
