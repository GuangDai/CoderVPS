# syntax=docker/dockerfile:1.7

ARG BASE_IMAGE
ARG NODE_VERSION
ARG UV_VERSION
ARG CODE_SERVER_VERSION
ARG SCCACHE_VERSION
ARG SCCACHE_SHA256
ARG LLVM_VERSION

# Guard against empty UV_VERSION: use "latest" as fallback
FROM ghcr.io/astral-sh/uv:${UV_VERSION:-latest} AS uv_bin

FROM ${BASE_IMAGE}

USER root
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH=/usr/local/go/bin:/usr/local/cargo/bin:/home/coder/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

RUN --mount=type=cache,id=codervps-apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=codervps-apt-lists,target=/var/lib/apt/lists,sharing=locked \
    set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      bash ca-certificates curl git gnupg jq unzip zip tar xz-utils file \
      ripgrep fd-find htop procps tree openssh-client sudo locales \
      build-essential pkg-config make cmake ninja-build autoconf automake libtool \
      gdb ccache xmake python3 python3-venv python3-dev pipx lsb-release; \
    ln -sf /usr/bin/fdfind /usr/local/bin/fd || true; \
    if ! id -u coder >/dev/null 2>&1; then useradd --create-home --shell /bin/bash coder; fi; \
    usermod -aG sudo coder || true; \
    echo "coder ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-coder; \
    chmod 0440 /etc/sudoers.d/90-coder

RUN set -eux; \
    curl -fsSL https://code-server.dev/install.sh | sh -s -- --version "${CODE_SERVER_VERSION}"; \
    code-server --version

RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in amd64) node_arch=x64 ;; arm64) node_arch=arm64 ;; *) exit 1 ;; esac; \
    node_file="node-v${NODE_VERSION}-linux-${node_arch}.tar.xz"; \
    node_url="https://nodejs.org/dist/v${NODE_VERSION}"; \
    curl -fsSLo /tmp/SHASUMS256.txt "${node_url}/SHASUMS256.txt"; \
    node_sha="$(awk -v f="$node_file" '$2 == f {print $1}' /tmp/SHASUMS256.txt)"; \
    curl -fsSLo "/tmp/${node_file}" "${node_url}/${node_file}"; \
    echo "${node_sha}  /tmp/${node_file}" | sha256sum -c -; \
    tar -xJf "/tmp/${node_file}" -C /usr/local --strip-components=1; \
    rm -f "/tmp/${node_file}" /tmp/SHASUMS256.txt; \
    node --version; npm --version; corepack enable || true

RUN --mount=type=bind,from=uv_bin,source=/uv,target=/tmp/uv,ro \
    --mount=type=bind,from=uv_bin,source=/uvx,target=/tmp/uvx,ro \
    set -eux; \
    install -m 0755 /tmp/uv /usr/local/bin/uv; \
    install -m 0755 /tmp/uvx /usr/local/bin/uvx; \
    uv --version

RUN set -eux; \
    export RUSTUP_HOME=/usr/local/rustup; \
    export CARGO_HOME=/usr/local/cargo; \
    curl https://sh.rustup.rs -sSf | sh -s -- -y --profile minimal --default-toolchain stable; \
    chmod -R a+w /usr/local/rustup /usr/local/cargo; \
    rustup --version; rustc --version

# Install sccache only when SHA256 is provided (guard against empty string)
RUN set -eux; \
    if [ -n "${SCCACHE_SHA256}" ] && [ -n "${SCCACHE_VERSION}" ]; then \
      arch="$(dpkg --print-architecture)"; \
      case "$arch" in amd64) sccache_arch=x86_64-unknown-linux-musl ;; arm64) sccache_arch=aarch64-unknown-linux-musl ;; *) exit 1 ;; esac; \
      file="sccache-v${SCCACHE_VERSION}-${sccache_arch}.tar.gz"; \
      url="https://github.com/rust-lang/sccache/releases/download/v${SCCACHE_VERSION}/${file}"; \
      curl -fsSLo "/tmp/${file}" "$url"; \
      echo "${SCCACHE_SHA256}  /tmp/${file}" | sha256sum -c -; \
      mkdir -p /tmp/sccache; \
      tar -xzf "/tmp/${file}" --strip-components=1 -C /tmp/sccache; \
      install -m 0755 /tmp/sccache/sccache /usr/local/bin/sccache; \
      rm -rf "/tmp/${file}" /tmp/sccache; \
      sccache --version; \
    else \
      echo "sccache skipped: SCCACHE_SHA256 or SCCACHE_VERSION not set"; \
    fi

RUN --mount=type=cache,id=codervps-apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=codervps-apt-lists,target=/var/lib/apt/lists,sharing=locked \
    set -eux; \
    . /etc/os-release; codename="${VERSION_CODENAME:-noble}"; \
    curl -fsSL https://apt.llvm.org/llvm-snapshot.gpg.key | gpg --dearmor -o /usr/share/keyrings/llvm-archive-keyring.gpg; \
    echo "deb [signed-by=/usr/share/keyrings/llvm-archive-keyring.gpg] http://apt.llvm.org/${codename}/ llvm-toolchain-${codename}-${LLVM_VERSION} main" > /etc/apt/sources.list.d/llvm.list; \
    apt-get update; \
    apt-get install -y --no-install-recommends clang-${LLVM_VERSION} clangd-${LLVM_VERSION} clang-format-${LLVM_VERSION} lld-${LLVM_VERSION} lldb-${LLVM_VERSION}; \
    update-alternatives --install /usr/bin/clang clang /usr/bin/clang-${LLVM_VERSION} 100; \
    update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-${LLVM_VERSION} 100; \
    update-alternatives --install /usr/bin/clangd clangd /usr/bin/clangd-${LLVM_VERSION} 100; \
    clangd --version

RUN set -eux; \
    xmake --version

RUN set -eux; \
    mkdir -p /workspace /opt/cde/runtime /opt/cde/extensions /opt/cde/vsix /home/coder/.local/bin; \
    chown -R coder:coder /workspace /home/coder

USER coder
WORKDIR /workspace
