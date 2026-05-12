# syntax=docker/dockerfile:1.7

ARG BASE_IMAGE=codercom/enterprise-base:ubuntu-noble-20260504
ARG UV_VERSION=0.11.13

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv_bin

FROM ${BASE_IMAGE}

USER root
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG INSTALL_RUST=false
ARG INSTALL_CPP=false
ARG INSTALL_GO=false
ARG INSTALL_PYTHON=false
ARG INSTALL_GO_TOOLS=false
ARG INSTALL_DOCKER_CLI=false

ARG NODE_VERSION=latest_lts
ARG GO_VERSION=1.26
ARG LLVM_VERSION=20
ARG SCCACHE_VERSION=0.15.0
ARG CODE_SERVER_VERSION=4.117.0

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH=/usr/local/go/bin:/usr/local/cargo/bin:/home/coder/go/bin:/home/coder/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

RUN --mount=type=cache,id=coder-cde-apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=coder-cde-apt-lists,target=/var/lib/apt/lists,sharing=locked \
    set -eux; \
    rm -f /etc/apt/apt.conf.d/docker-clean; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      bash \
      ca-certificates \
      curl \
      git \
      gnupg \
      jq \
      unzip \
      zip \
      tar \
      xz-utils \
      file \
      ripgrep \
      fd-find \
      htop \
      procps \
      tree \
      openssh-client \
      sudo \
      locales \
      build-essential \
      python3 \
      pkg-config; \
    ln -sf /usr/bin/fdfind /usr/local/bin/fd || true; \
    if ! id -u coder >/dev/null 2>&1; then \
      useradd --create-home --shell /bin/bash coder; \
    fi; \
    usermod -aG sudo coder || true; \
    echo "coder ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-coder; \
    chmod 0440 /etc/sudoers.d/90-coder

RUN set -eux; \
    curl -fsSL https://code-server.dev/install.sh | sh -s -- --version "${CODE_SERVER_VERSION}"; \
    code-server --version

RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    case "${arch}" in \
      amd64) node_arch="x64" ;; \
      arm64) node_arch="arm64" ;; \
      *) echo "Unsupported architecture for Node.js: ${arch}" >&2; exit 1 ;; \
    esac; \
    node_index="$(mktemp)"; \
    curl -fsSL "https://nodejs.org/dist/index.json" -o "$node_index"; \
    if [[ "${NODE_VERSION}" == "latest_lts" ]]; then \
      node_resolved="$(jq -r '[.[] | select(.lts != false)][0].version' "$node_index")"; \
    elif [[ "${NODE_VERSION}" == "latest_current" || "${NODE_VERSION}" == "latest" ]]; then \
      node_resolved="$(jq -r '.[0].version' "$node_index")"; \
    elif [[ "${NODE_VERSION}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then \
      node_resolved="${NODE_VERSION}"; \
    elif [[ "${NODE_VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then \
      node_resolved="v${NODE_VERSION}"; \
    elif [[ "${NODE_VERSION}" =~ ^[0-9]+\.[0-9]+$ ]]; then \
      prefix="v${NODE_VERSION}."; \
      node_resolved="$(jq -r --arg prefix "$prefix" '[.[] | select(.version | startswith($prefix))][0].version // empty' "$node_index")"; \
    elif [[ "${NODE_VERSION}" =~ ^[0-9]+$ ]]; then \
      prefix="v${NODE_VERSION}."; \
      node_resolved="$(jq -r --arg prefix "$prefix" '[.[] | select(.version | startswith($prefix))][0].version // empty' "$node_index")"; \
    else \
      echo "Unsupported NODE_VERSION selector: ${NODE_VERSION}" >&2; \
      exit 1; \
    fi; \
    if [[ -z "${node_resolved}" || "${node_resolved}" == "null" ]]; then \
      echo "Could not resolve NODE_VERSION=${NODE_VERSION}" >&2; \
      exit 1; \
    fi; \
    node_file="node-${node_resolved}-linux-${node_arch}.tar.xz"; \
    node_base_url="https://nodejs.org/dist/${node_resolved}"; \
    curl -fsSLo /tmp/SHASUMS256.txt "${node_base_url}/SHASUMS256.txt"; \
    node_sha="$(awk -v f="${node_file}" '$2 == f {print $1}' /tmp/SHASUMS256.txt)"; \
    if [[ -z "${node_sha}" ]]; then \
      echo "Could not find checksum for ${node_file}" >&2; \
      exit 1; \
    fi; \
    curl -fsSLo "/tmp/${node_file}" "${node_base_url}/${node_file}"; \
    echo "${node_sha}  /tmp/${node_file}" | sha256sum -c -; \
    tar -xJf "/tmp/${node_file}" -C /usr/local --strip-components=1; \
    rm -f "/tmp/${node_file}" /tmp/SHASUMS256.txt "$node_index"; \
    node --version; \
    npm --version; \
    corepack enable || true

RUN --mount=type=cache,id=coder-cde-apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=coder-cde-apt-lists,target=/var/lib/apt/lists,sharing=locked \
    set -eux; \
    if [[ "${INSTALL_RUST}" == "true" ]]; then \
      apt-get update; \
      apt-get install -y --no-install-recommends \
        cmake \
        make \
        libssl-dev \
        zlib1g-dev; \
    else \
      echo "Skipping Rust native build dependencies"; \
    fi

RUN set -eux; \
    if [[ "${INSTALL_RUST}" == "true" ]]; then \
      export RUSTUP_HOME=/usr/local/rustup; \
      export CARGO_HOME=/usr/local/cargo; \
      curl https://sh.rustup.rs -sSf | sh -s -- -y --profile minimal --default-toolchain none; \
      chmod -R a+w /usr/local/rustup /usr/local/cargo; \
      rustup --version; \
    else \
      echo "Skipping rustup"; \
    fi

RUN set -eux; \
    if [[ "${INSTALL_RUST}" == "true" ]]; then \
      arch="$(dpkg --print-architecture)"; \
      case "${arch}" in \
        amd64) sccache_arch="x86_64-unknown-linux-musl" ;; \
        arm64) sccache_arch="aarch64-unknown-linux-musl" ;; \
        *) echo "Unsupported architecture for prebuilt sccache: ${arch}" >&2; exit 1 ;; \
      esac; \
      sccache_file="sccache-v${SCCACHE_VERSION}-${sccache_arch}.tar.gz"; \
      sccache_url="https://github.com/mozilla/sccache/releases/download/v${SCCACHE_VERSION}/${sccache_file}"; \
      curl -fsSLo "/tmp/${sccache_file}" "${sccache_url}"; \
      curl -fsSLo "/tmp/${sccache_file}.sha256" "${sccache_url}.sha256"; \
      expected_sha="$(awk '{print $1}' "/tmp/${sccache_file}.sha256")"; \
      echo "${expected_sha}  /tmp/${sccache_file}" | sha256sum -c -; \
      mkdir -p /tmp/sccache; \
      tar -xzf "/tmp/${sccache_file}" --strip-components=1 -C /tmp/sccache; \
      install -m 0755 /tmp/sccache/sccache /usr/local/bin/sccache; \
      rm -rf "/tmp/${sccache_file}" "/tmp/${sccache_file}.sha256" /tmp/sccache; \
      sccache --version; \
    else \
      echo "Skipping sccache"; \
    fi

RUN --mount=type=cache,id=coder-cde-apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=coder-cde-apt-lists,target=/var/lib/apt/lists,sharing=locked \
    set -eux; \
    if [[ "${INSTALL_CPP}" == "true" ]]; then \
      apt-get update; \
      apt-get install -y --no-install-recommends \
        cmake \
        ninja-build \
        make \
        autoconf \
        automake \
        libtool \
        gdb \
        ccache \
        lsb-release; \
      if [[ "${LLVM_VERSION}" != "distro" ]]; then \
        . /etc/os-release; \
        codename="${VERSION_CODENAME:-}"; \
        if [[ -z "$codename" ]]; then codename="$(lsb_release -cs)"; fi; \
        rm -f /usr/share/keyrings/llvm-archive-keyring.gpg; \
        curl -fsSL https://apt.llvm.org/llvm-snapshot.gpg.key \
          | gpg --dearmor -o /usr/share/keyrings/llvm-archive-keyring.gpg; \
        echo "deb [signed-by=/usr/share/keyrings/llvm-archive-keyring.gpg] http://apt.llvm.org/${codename}/ llvm-toolchain-${codename}-${LLVM_VERSION} main" \
          > /etc/apt/sources.list.d/llvm.list; \
        apt-get update || true; \
        if apt-get install -y --no-install-recommends \
          clang-${LLVM_VERSION} \
          clangd-${LLVM_VERSION} \
          clang-format-${LLVM_VERSION} \
          lld-${LLVM_VERSION} \
          lldb-${LLVM_VERSION}; then \
          update-alternatives --install /usr/bin/clang clang /usr/bin/clang-${LLVM_VERSION} 100; \
          update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-${LLVM_VERSION} 100; \
          update-alternatives --install /usr/bin/clangd clangd /usr/bin/clangd-${LLVM_VERSION} 100; \
          update-alternatives --install /usr/bin/clang-format clang-format /usr/bin/clang-format-${LLVM_VERSION} 100; \
          update-alternatives --install /usr/bin/lld lld /usr/bin/lld-${LLVM_VERSION} 100 || true; \
        else \
          echo "Versioned LLVM install failed; falling back to distro clang packages"; \
          apt-get install -y --no-install-recommends clang clangd clang-format lld lldb; \
        fi; \
      else \
        apt-get install -y --no-install-recommends clang clangd clang-format lld lldb; \
      fi; \
      clang --version; \
      clangd --version; \
    else \
      echo "Skipping C/C++ toolchain"; \
    fi

RUN --mount=type=cache,id=coder-cde-apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=coder-cde-apt-lists,target=/var/lib/apt/lists,sharing=locked \
    set -eux; \
    if [[ "${INSTALL_CPP}" == "true" ]]; then \
      apt-get update; \
      if ! apt-get install -y --no-install-recommends xmake; then \
        curl -fsSL https://xmake.io/shget.text | bash; \
        if [[ -x /root/.local/bin/xmake ]]; then \
          ln -sf /root/.local/bin/xmake /usr/local/bin/xmake; \
        fi; \
      fi; \
      command -v xmake; \
      xmake --version || true; \
    else \
      echo "Skipping Xmake"; \
    fi

RUN set -eux; \
    if [[ "${INSTALL_GO}" == "true" ]]; then \
      arch="$(dpkg --print-architecture)"; \
      case "${arch}" in \
        amd64) go_arch="amd64" ;; \
        arm64) go_arch="arm64" ;; \
        *) echo "Unsupported architecture for Go: ${arch}" >&2; exit 1 ;; \
      esac; \
      go_index="$(mktemp)"; \
      curl -fsSL "https://go.dev/dl/?mode=json&include=all" -o "$go_index"; \
      if [[ "${GO_VERSION}" == "latest" ]]; then \
        go_resolved="$(jq -r '.[0].version | sub("^go"; "")' "$go_index")"; \
      elif [[ "${GO_VERSION}" =~ ^[0-9]+\.[0-9]+$ ]]; then \
        prefix="go${GO_VERSION}."; \
        go_resolved="$(jq -r --arg prefix "$prefix" '[.[].version | select(startswith($prefix))][0] // empty | sub("^go"; "")' "$go_index")"; \
      elif [[ "${GO_VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then \
        go_resolved="${GO_VERSION}"; \
      else \
        echo "Unsupported GO_VERSION selector: ${GO_VERSION}" >&2; \
        exit 1; \
      fi; \
      if [[ -z "${go_resolved}" ]]; then \
        echo "Could not resolve GO_VERSION=${GO_VERSION}" >&2; \
        exit 1; \
      fi; \
      go_file="go${go_resolved}.linux-${go_arch}.tar.gz"; \
      go_sha="$(jq -r --arg filename "${go_file}" '[.[].files[]? | select(.filename == $filename)][0].sha256 // empty' "$go_index")"; \
      if [[ -z "${go_sha}" ]]; then \
        echo "Could not find ${go_file} in official go.dev/dl metadata" >&2; \
        exit 1; \
      fi; \
      curl -fsSLo /tmp/go.tgz "https://go.dev/dl/${go_file}"; \
      echo "${go_sha}  /tmp/go.tgz" | sha256sum -c -; \
      rm -rf /usr/local/go; \
      tar -C /usr/local -xzf /tmp/go.tgz; \
      rm /tmp/go.tgz "$go_index"; \
      /usr/local/go/bin/go version; \
    else \
      echo "Skipping Go toolchain"; \
    fi

RUN --mount=type=cache,id=coder-cde-go-mod,target=/root/go/pkg/mod,sharing=locked \
    --mount=type=cache,id=coder-cde-go-build,target=/root/.cache/go-build,sharing=locked \
    set -eux; \
    if [[ "${INSTALL_GO}" == "true" && "${INSTALL_GO_TOOLS}" == "true" ]]; then \
      GOBIN=/usr/local/bin /usr/local/go/bin/go install golang.org/x/tools/gopls@latest || echo "gopls install failed; continuing"; \
      GOBIN=/usr/local/bin /usr/local/go/bin/go install github.com/go-delve/delve/cmd/dlv@latest || echo "dlv install failed; continuing"; \
      gopls version || true; \
      dlv version || true; \
    else \
      echo "Skipping Go tools compile/install"; \
    fi

RUN --mount=type=bind,from=uv_bin,source=/uv,target=/tmp/uv,ro \
    --mount=type=bind,from=uv_bin,source=/uvx,target=/tmp/uvx,ro \
    set -eux; \
    if [[ "${INSTALL_PYTHON}" == "true" ]]; then \
      install -m 0755 /tmp/uv /usr/local/bin/uv; \
      install -m 0755 /tmp/uvx /usr/local/bin/uvx; \
      uv --version; \
    else \
      echo "Skipping uv install"; \
    fi

RUN --mount=type=cache,id=coder-cde-apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=coder-cde-apt-lists,target=/var/lib/apt/lists,sharing=locked \
    set -eux; \
    if [[ "${INSTALL_PYTHON}" == "true" ]]; then \
      apt-get update; \
      apt-get install -y --no-install-recommends \
        python3-pip \
        python3-venv \
        python3-dev \
        pipx \
        libssl-dev \
        zlib1g-dev; \
      python3 --version; \
    else \
      echo "Skipping Python system dependencies"; \
    fi

RUN --mount=type=cache,id=coder-cde-apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=coder-cde-apt-lists,target=/var/lib/apt/lists,sharing=locked \
    set -eux; \
    if [[ "${INSTALL_DOCKER_CLI}" == "true" ]]; then \
      apt-get update; \
      apt-get install -y --no-install-recommends docker.io docker-compose-v2 || \
        apt-get install -y --no-install-recommends docker.io || true; \
      if command -v docker >/dev/null 2>&1; then docker --version; fi; \
    else \
      echo "Skipping Docker CLI"; \
    fi

RUN set -eux; \
    mkdir -p \
      /home/coder/workspace \
      /home/coder/go \
      /home/coder/.local/bin \
      /opt/cde/cache \
      /opt/cde/extensions \
      /opt/cde/vsix; \
    chown -R coder:coder /home/coder /opt/cde/cache

USER coder
WORKDIR /home/coder/workspace

ENV PATH=/home/coder/.local/bin:/home/coder/.cargo/bin:/usr/local/go/bin:/usr/local/cargo/bin:/home/coder/go/bin:/usr/local/bin:/usr/bin:/bin
