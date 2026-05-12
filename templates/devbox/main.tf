terraform {
  required_providers {
    coder = {
      source  = "coder/coder"
      version = ">= 2.5.3"
    }
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

provider "coder" {}
provider "docker" {}

data "coder_workspace" "me" {}
data "coder_workspace_owner" "me" {}
data "coder_provisioner" "me" {}

locals {
  base_image_options = [
    {
      name  = "Coder Enterprise Base Ubuntu 24.04 Noble pinned"
      value = "coder_noble_pinned"
    },
    {
      name  = "Coder Enterprise Base Ubuntu rolling"
      value = "coder_ubuntu_rolling"
    },
    {
      name  = "Ubuntu 26.04 LTS Resolute official"
      value = "ubuntu_2604"
    },
    {
      name  = "Ubuntu 24.04 LTS Noble official"
      value = "ubuntu_2404"
    },
    {
      name  = "Ubuntu 22.04 LTS Jammy official"
      value = "ubuntu_2204"
    },
    {
      name  = "Ubuntu 20.04 LTS Focal official / ESM"
      value = "ubuntu_2004"
    }
  ]

  node_version_options = [
    {
      name  = "Latest LTS"
      value = "latest_lts"
    },
    {
      name  = "Latest Current"
      value = "latest_current"
    },
    {
      name  = "Node 24 LTS channel"
      value = "24"
    },
    {
      name  = "Node 22 LTS channel"
      value = "22"
    },
    {
      name  = "Node 20 LTS channel"
      value = "20"
    },
    {
      name  = "Node 18 LTS channel"
      value = "18"
    },
    {
      name  = "Node 16 LTS channel"
      value = "16"
    },
    {
      name  = "Node 14 LTS channel"
      value = "14"
    },
    {
      name  = "Node 12 LTS channel"
      value = "12"
    },
    {
      name  = "Node 10 LTS channel"
      value = "10"
    },
    {
      name  = "Custom Node version"
      value = "custom"
    }
  ]

  llvm_version_options = [
    {
      name  = "LLVM / clangd 20"
      value = "20"
    },
    {
      name  = "LLVM / clangd 21"
      value = "21"
    },
    {
      name  = "Ubuntu distro clang/clangd"
      value = "distro"
    }
  ]

  go_version_options = [
    {
      name  = "Latest stable Go"
      value = "latest"
    },
    {
      name  = "Go 1.26 latest patch"
      value = "1.26"
    },
    {
      name  = "Go 1.25 latest patch"
      value = "1.25"
    },
    {
      name  = "Go 1.24 latest patch"
      value = "1.24"
    },
    {
      name  = "Go 1.23 latest patch"
      value = "1.23"
    },
    {
      name  = "Go 1.22 latest patch"
      value = "1.22"
    },
    {
      name  = "Go 1.21 latest patch"
      value = "1.21"
    },
    {
      name  = "Go 1.20 latest patch"
      value = "1.20"
    },
    {
      name  = "Go 1.19 latest patch"
      value = "1.19"
    },
    {
      name  = "Go 1.18 latest patch"
      value = "1.18"
    },
    {
      name  = "Go 1.17 latest patch"
      value = "1.17"
    },
    {
      name  = "Custom Go version"
      value = "custom"
    }
  ]

  rust_toolchain_options = [
    {
      name  = "Rust stable channel"
      value = "stable"
    },
    {
      name  = "Rust beta channel"
      value = "beta"
    },
    {
      name  = "Rust nightly channel"
      value = "nightly"
    },
    {
      name  = "Rust 1.95 latest patch"
      value = "1.95"
    },
    {
      name  = "Rust 1.94 latest patch"
      value = "1.94"
    },
    {
      name  = "Rust 1.93 latest patch"
      value = "1.93"
    },
    {
      name  = "Rust 1.92 latest patch"
      value = "1.92"
    },
    {
      name  = "Rust 1.91 latest patch"
      value = "1.91"
    },
    {
      name  = "Rust 1.90 latest patch"
      value = "1.90"
    },
    {
      name  = "Rust 1.89 latest patch"
      value = "1.89"
    },
    {
      name  = "Rust 1.88 latest patch"
      value = "1.88"
    },
    {
      name  = "Rust 1.87 latest patch"
      value = "1.87"
    },
    {
      name  = "Rust 1.86 latest patch"
      value = "1.86"
    },
    {
      name  = "Rust 1.85 latest patch"
      value = "1.85"
    },
    {
      name  = "Rust 1.84 latest patch"
      value = "1.84"
    },
    {
      name  = "Rust 1.83 latest patch"
      value = "1.83"
    },
    {
      name  = "Rust 1.82 latest patch"
      value = "1.82"
    },
    {
      name  = "Rust 1.81 latest patch"
      value = "1.81"
    },
    {
      name  = "Rust 1.80 latest patch"
      value = "1.80"
    },
    {
      name  = "Rust 1.79 latest patch"
      value = "1.79"
    },
    {
      name  = "Rust 1.78 latest patch"
      value = "1.78"
    },
    {
      name  = "Rust 1.77 latest patch"
      value = "1.77"
    },
    {
      name  = "Rust 1.76 latest patch"
      value = "1.76"
    },
    {
      name  = "Rust 1.75 latest patch"
      value = "1.75"
    },
    {
      name  = "Custom Rust toolchain"
      value = "custom"
    }
  ]

  python_version_options = [
    {
      name  = "Latest Python supported by uv"
      value = "latest"
    },
    {
      name  = "Python 3.14 latest patch"
      value = "3.14"
    },
    {
      name  = "Python 3.13 latest patch"
      value = "3.13"
    },
    {
      name  = "Python 3.12 latest patch"
      value = "3.12"
    },
    {
      name  = "Python 3.11 latest patch"
      value = "3.11"
    },
    {
      name  = "Python 3.10 latest patch"
      value = "3.10"
    },
    {
      name  = "Python 3.9 latest patch"
      value = "3.9"
    },
    {
      name  = "Python 3.8 latest patch"
      value = "3.8"
    },
    {
      name  = "Python 3.7 latest patch"
      value = "3.7"
    },
    {
      name  = "Use system Python only"
      value = "system"
    },
    {
      name  = "Custom Python version"
      value = "custom"
    }
  ]
}

data "coder_parameter" "base_image" {
  name         = "base_image"
  display_name = "Base image"
  description  = "Base image used for the workspace image. Coder base is recommended; official Ubuntu bases are available for compatibility testing."
  default      = "coder_noble_pinned"
  mutable      = false
  order        = 1
  type         = "string"
  form_type    = "radio"

  dynamic "option" {
    for_each = local.base_image_options
    content {
      name  = option.value.name
      value = option.value.value
    }
  }
}

data "coder_parameter" "image_profile" {
  name         = "image_profile"
  display_name = "Image profile"
  description  = "Controls which language toolchains are baked into the Docker image. Node.js/npm are always installed because code-server extensions and many tools depend on them."
  default      = "full"
  mutable      = false
  order        = 2
  type         = "string"
  form_type    = "radio"

  option {
    name  = "Full: Rust + C/C++ + Go + Python"
    value = "full"
  }

  option {
    name  = "Rust only"
    value = "rust"
  }

  option {
    name  = "C/C++ only"
    value = "cpp"
  }

  option {
    name  = "Go only"
    value = "go"
  }

  option {
    name  = "Python only"
    value = "python"
  }

  option {
    name  = "Core only + Node.js"
    value = "core"
  }
}

data "coder_parameter" "node_version" {
  name         = "node_version"
  display_name = "Node.js version"
  description  = "Node.js/npm are always installed. Major-channel options resolve to the latest patch at image build time."
  default      = "latest_lts"
  mutable      = false
  order        = 3
  type         = "string"
  form_type    = "dropdown"

  dynamic "option" {
    for_each = local.node_version_options
    content {
      name  = option.value.name
      value = option.value.value
    }
  }
}

data "coder_parameter" "node_custom_version" {
  count = data.coder_parameter.node_version.value == "custom" ? 1 : 0

  name         = "node_custom_version"
  display_name = "Custom Node.js version"
  description  = "Use a full version like 22.11.0 or v22.11.0."
  default      = "24"
  mutable      = false
  order        = 4
  type         = "string"
  form_type    = "input"
}

data "coder_parameter" "extension_profile" {
  name         = "extension_profile"
  display_name = "VS Code extension profile"
  description  = "Controls which shared extension lists are installed at startup."
  default      = "match_image"
  mutable      = true
  order        = 5
  type         = "string"
  form_type    = "radio"

  option {
    name  = "Same as image profile"
    value = "match_image"
  }

  option {
    name  = "Full: Rust + C/C++ + Go + Python"
    value = "full"
  }

  option {
    name  = "Rust"
    value = "rust"
  }

  option {
    name  = "C/C++"
    value = "cpp"
  }

  option {
    name  = "Go"
    value = "go"
  }

  option {
    name  = "Python"
    value = "python"
  }

  option {
    name  = "Core only"
    value = "core"
  }
}

data "coder_parameter" "llvm_version" {
  count = contains(["cpp", "full"], data.coder_parameter.image_profile.value) ? 1 : 0

  name         = "llvm_version"
  display_name = "LLVM / clangd version"
  description  = "Only shown for C/C++ or Full image profiles. Versioned LLVM uses apt.llvm.org; distro uses Ubuntu packages."
  default      = "20"
  mutable      = false
  order        = 10
  type         = "string"
  form_type    = "radio"

  dynamic "option" {
    for_each = local.llvm_version_options
    content {
      name  = option.value.name
      value = option.value.value
    }
  }
}

data "coder_parameter" "go_version" {
  count = contains(["go", "full"], data.coder_parameter.image_profile.value) ? 1 : 0

  name         = "go_version"
  display_name = "Go version"
  description  = "Only shown for Go or Full. Major-channel options resolve to latest patch from go.dev metadata."
  default      = "1.26"
  mutable      = false
  order        = 20
  type         = "string"
  form_type    = "dropdown"

  dynamic "option" {
    for_each = local.go_version_options
    content {
      name  = option.value.name
      value = option.value.value
    }
  }
}

data "coder_parameter" "go_custom_version" {
  count = contains(["go", "full"], data.coder_parameter.image_profile.value) && try(data.coder_parameter.go_version[0].value, "") == "custom" ? 1 : 0

  name         = "go_custom_version"
  display_name = "Custom Go version"
  description  = "Use a full version like 1.22.12."
  default      = "1.26.3"
  mutable      = false
  order        = 21
  type         = "string"
  form_type    = "input"
}

data "coder_parameter" "install_go_tools" {
  count = contains(["go", "full"], data.coder_parameter.image_profile.value) ? 1 : 0

  name         = "install_go_tools"
  display_name = "Preinstall Go tools"
  description  = "If enabled, builds gopls and dlv during image build. Disabled by default to avoid compiling during image build."
  default      = "false"
  mutable      = false
  order        = 22
  type         = "string"
  form_type    = "radio"

  option {
    name  = "No: skip gopls/dlv build"
    value = "false"
  }

  option {
    name  = "Yes: compile/install gopls and dlv"
    value = "true"
  }
}

data "coder_parameter" "rust_toolchain" {
  count = contains(["rust", "full"], data.coder_parameter.image_profile.value) ? 1 : 0

  name         = "rust_toolchain"
  display_name = "Default Rust toolchain"
  description  = "Only shown for Rust or Full. Channel/minor options are resolved by rustup at startup. Projects should still pin with rust-toolchain.toml."
  default      = "stable"
  mutable      = true
  order        = 30
  type         = "string"
  form_type    = "dropdown"

  dynamic "option" {
    for_each = local.rust_toolchain_options
    content {
      name  = option.value.name
      value = option.value.value
    }
  }
}

data "coder_parameter" "rust_custom_toolchain" {
  count = contains(["rust", "full"], data.coder_parameter.image_profile.value) && try(data.coder_parameter.rust_toolchain[0].value, "") == "custom" ? 1 : 0

  name         = "rust_custom_toolchain"
  display_name = "Custom Rust toolchain"
  description  = "Use stable, beta, nightly, 1.90, 1.90.0, or a dated nightly like nightly-2026-05-01."
  default      = "stable"
  mutable      = true
  order        = 31
  type         = "string"
  form_type    = "input"
}

data "coder_parameter" "sccache_cache_size" {
  count = contains(["rust", "full"], data.coder_parameter.image_profile.value) ? 1 : 0

  name         = "sccache_cache_size"
  display_name = "sccache cache size"
  description  = "Only shown for Rust or Full. Maximum size for the shared sccache directory."
  default      = "50G"
  mutable      = true
  order        = 32
  type         = "string"
  form_type    = "radio"

  option {
    name  = "20G"
    value = "20G"
  }

  option {
    name  = "50G"
    value = "50G"
  }

  option {
    name  = "100G"
    value = "100G"
  }
}

data "coder_parameter" "python_version" {
  count = contains(["python", "full"], data.coder_parameter.image_profile.value) ? 1 : 0

  name         = "python_version"
  display_name = "Default Python version"
  description  = "Only shown for Python or Full. Minor-channel options resolve to latest patch with uv."
  default      = "3.13"
  mutable      = true
  order        = 40
  type         = "string"
  form_type    = "dropdown"

  dynamic "option" {
    for_each = local.python_version_options
    content {
      name  = option.value.name
      value = option.value.value
    }
  }
}

data "coder_parameter" "python_custom_version" {
  count = contains(["python", "full"], data.coder_parameter.image_profile.value) && try(data.coder_parameter.python_version[0].value, "") == "custom" ? 1 : 0

  name         = "python_custom_version"
  display_name = "Custom Python version"
  description  = "Use 3.12.8, 3.13.5, 3.14, etc. uv must support the requested build."
  default      = "3.13"
  mutable      = true
  order        = 41
  type         = "string"
  form_type    = "input"
}

data "coder_parameter" "memory_gb" {
  name         = "memory_gb"
  display_name = "Memory"
  description  = "Container memory limit. Your VPS has 8G, so 4G is a good default."
  default      = "4"
  mutable      = true
  order        = 90
  type         = "string"
  form_type    = "radio"

  option {
    name  = "2 GB"
    value = "2"
  }

  option {
    name  = "4 GB"
    value = "4"
  }

  option {
    name  = "6 GB"
    value = "6"
  }

  option {
    name  = "8 GB"
    value = "8"
  }
}

data "coder_parameter" "docker_socket" {
  name         = "docker_socket"
  display_name = "Mount host Docker socket"
  description  = "Powerful but risky. If enabled, Docker CLI is also baked into the image."
  default      = "false"
  mutable      = false
  order        = 100
  type         = "string"
  form_type    = "radio"

  option {
    name  = "No"
    value = "false"
  }

  option {
    name  = "Yes"
    value = "true"
  }
}

locals {
  username_raw   = data.coder_workspace_owner.me.name
  username       = lower(replace(local.username_raw, "/[^a-z0-9_.-]/", "-"))
  workspace_name = lower(replace(data.coder_workspace.me.name, "/[^a-z0-9_.-]/", "-"))

  container_name  = "coder-${local.username}-${local.workspace_name}"
  host_docker_gid = "988"
  mem_bytes       = tonumber(data.coder_parameter.memory_gb.value) * 1024 * 1024 * 1024
  cache_root      = "/opt/cde/cache"

  base_images = {
    coder_noble_pinned   = "codercom/enterprise-base:ubuntu-noble-20260504"
    coder_ubuntu_rolling = "codercom/enterprise-base:ubuntu"
    ubuntu_2604          = "ubuntu:26.04"
    ubuntu_2404          = "ubuntu:24.04"
    ubuntu_2204          = "ubuntu:22.04"
    ubuntu_2004          = "ubuntu:20.04"
  }

  base_image = local.base_images[data.coder_parameter.base_image.value]

  install_rust   = contains(["rust", "full"], data.coder_parameter.image_profile.value)
  install_cpp    = contains(["cpp", "full"], data.coder_parameter.image_profile.value)
  install_go     = contains(["go", "full"], data.coder_parameter.image_profile.value)
  install_python = contains(["python", "full"], data.coder_parameter.image_profile.value)

  selected_node_version       = data.coder_parameter.node_version.value == "custom" ? try(data.coder_parameter.node_custom_version[0].value, "24") : data.coder_parameter.node_version.value
  selected_llvm_version       = try(data.coder_parameter.llvm_version[0].value, "20")
  selected_go_version_raw     = try(data.coder_parameter.go_version[0].value, "1.26")
  selected_go_version         = local.selected_go_version_raw == "custom" ? try(data.coder_parameter.go_custom_version[0].value, "1.26.3") : local.selected_go_version_raw
  selected_install_go_tools   = try(data.coder_parameter.install_go_tools[0].value, "false")
  selected_rust_toolchain_raw = try(data.coder_parameter.rust_toolchain[0].value, "stable")
  selected_rust_toolchain     = local.selected_rust_toolchain_raw == "custom" ? try(data.coder_parameter.rust_custom_toolchain[0].value, "stable") : local.selected_rust_toolchain_raw
  selected_sccache_size       = try(data.coder_parameter.sccache_cache_size[0].value, "50G")
  selected_python_version_raw = try(data.coder_parameter.python_version[0].value, "system")
  selected_python_version     = local.selected_python_version_raw == "custom" ? try(data.coder_parameter.python_custom_version[0].value, "3.13") : local.selected_python_version_raw

  node_key = lower(replace(local.selected_node_version, "/[^0-9A-Za-z_.-]/", "-"))
  llvm_key = local.install_cpp ? lower(replace(local.selected_llvm_version, "/[^0-9A-Za-z_.-]/", "-")) : "none"
  go_key   = local.install_go ? lower(replace(local.selected_go_version, "/[^0-9A-Za-z_.-]/", "-")) : "none"
  py_key   = local.install_python ? lower(replace(local.selected_python_version, "/[^0-9A-Za-z_.-]/", "-")) : "none"
  rs_key   = local.install_rust ? lower(replace(local.selected_rust_toolchain, "/[^0-9A-Za-z_.-]/", "-")) : "none"

  image_name = "coder-devbox:${data.coder_parameter.image_profile.value}-${data.coder_parameter.base_image.value}-node${local.node_key}-llvm${local.llvm_key}-go${local.go_key}-py${local.py_key}-rs${local.rs_key}"

  devbox_build_args = {
    BASE_IMAGE          = local.base_image
    UV_VERSION          = "0.11.13"
    NODE_VERSION        = local.selected_node_version
    INSTALL_RUST        = tostring(local.install_rust)
    INSTALL_CPP         = tostring(local.install_cpp)
    INSTALL_GO          = tostring(local.install_go)
    INSTALL_PYTHON      = tostring(local.install_python)
    INSTALL_GO_TOOLS    = local.selected_install_go_tools
    INSTALL_DOCKER_CLI  = data.coder_parameter.docker_socket.value
    LLVM_VERSION        = local.selected_llvm_version
    GO_VERSION          = local.selected_go_version
    CODE_SERVER_VERSION = "4.117.0"
    SCCACHE_VERSION     = "0.15.0"
  }

  base_env = [
    "CODER_AGENT_TOKEN=${coder_agent.main.token}",
    "IMAGE_PROFILE=${data.coder_parameter.image_profile.value}",
    "EXTENSION_PROFILE=${data.coder_parameter.extension_profile.value}",
    "CDE_CACHE_ROOT=${local.cache_root}",
    "NODE_VERSION=${local.selected_node_version}",
    "NPM_CONFIG_CACHE=${local.cache_root}/npm",
    "COREPACK_HOME=${local.cache_root}/corepack",
    "PATH=/home/coder/.local/bin:/home/coder/.cargo/bin:/usr/local/go/bin:/usr/local/cargo/bin:/home/coder/go/bin:/usr/local/bin:/usr/bin:/bin"
  ]

  rust_env = local.install_rust ? [
    "RUST_DEFAULT_TOOLCHAIN=${local.selected_rust_toolchain}",
    "RUSTUP_HOME=${local.cache_root}/rustup",
    "CARGO_HOME=/usr/local/cargo",
    "CARGO_INSTALL_ROOT=/home/coder/.local",
    "RUSTC_WRAPPER=sccache",
    "SCCACHE_DIR=${local.cache_root}/sccache",
    "SCCACHE_CACHE_SIZE=${local.selected_sccache_size}"
  ] : []

  cpp_env = local.install_cpp ? [
    "CCACHE_DIR=${local.cache_root}/ccache"
  ] : []

  go_env = local.install_go ? [
    "GOCACHE=${local.cache_root}/go/build",
    "GOMODCACHE=${local.cache_root}/go/pkg/mod",
    "GOTOOLCHAIN=local"
  ] : []

  python_env = local.install_python ? [
    "PYTHON_VERSION=${local.selected_python_version}",
    "UV_CACHE_DIR=${local.cache_root}/uv",
    "PIP_CACHE_DIR=${local.cache_root}/pip"
  ] : []

  workspace_env = concat(local.base_env, local.rust_env, local.cpp_env, local.go_env, local.python_env)
}

resource "docker_image" "devbox" {
  count        = data.coder_workspace.me.start_count
  name         = local.image_name
  keep_locally = true

  build {
    context    = path.module
    dockerfile = "Dockerfile"
    build_args = local.devbox_build_args
  }

  triggers = {
    dockerfile_sha1 = filesha1("${path.module}/Dockerfile")
    build_args_sha1 = sha1(jsonencode(local.devbox_build_args))
  }
}

resource "coder_agent" "main" {
  arch = data.coder_provisioner.me.arch
  os   = "linux"
  dir  = "/home/coder/workspace"

  env = {
    GIT_AUTHOR_NAME     = coalesce(data.coder_workspace_owner.me.full_name, data.coder_workspace_owner.me.name)
    GIT_AUTHOR_EMAIL    = data.coder_workspace_owner.me.email
    GIT_COMMITTER_NAME  = coalesce(data.coder_workspace_owner.me.full_name, data.coder_workspace_owner.me.name)
    GIT_COMMITTER_EMAIL = data.coder_workspace_owner.me.email
  }

  startup_script = file("${path.module}/startup.sh")

  metadata {
    display_name = "CPU"
    key          = "0_cpu"
    script       = "coder stat cpu"
    interval     = 10
    timeout      = 1
  }

  metadata {
    display_name = "Memory"
    key          = "1_mem"
    script       = "coder stat mem"
    interval     = 10
    timeout      = 1
  }

  metadata {
    display_name = "Disk"
    key          = "2_disk"
    script       = "coder stat disk --path $HOME"
    interval     = 60
    timeout      = 1
  }

  metadata {
    display_name = "Toolchains"
    key          = "3_toolchains"
    script       = "printf 'node: '; node --version 2>/dev/null || echo 'not installed'; printf 'npm: '; npm --version 2>/dev/null || echo 'not installed'; printf 'rust: '; rustc --version 2>/dev/null || echo 'not installed'; printf 'go: '; go version 2>/dev/null || echo 'not installed'; printf 'python: '; python --version 2>/dev/null || python3 --version 2>/dev/null || echo 'not installed'; printf 'clangd: '; clangd --version 2>/dev/null | head -1 || echo 'not installed'"
    interval     = 300
    timeout      = 5
  }

  metadata {
    display_name = "sccache"
    key          = "4_sccache"
    script       = "sccache --show-stats 2>/dev/null | awk '/Compile requests|Cache hits|Cache misses|Cache location|Cache size/ {print}' || echo 'not installed'"
    interval     = 60
    timeout      = 3
  }
}

resource "coder_app" "code_server" {
  agent_id     = coder_agent.main.id
  slug         = "code-server"
  display_name = "VS Code Web"
  icon         = "/icon/code.svg"
  url          = "http://127.0.0.1:13337/?folder=/home/coder/workspace"
  share        = "owner"
  subdomain    = false

  healthcheck {
    url       = "http://127.0.0.1:13337/healthz"
    interval  = 5
    threshold = 20
  }
}

resource "docker_volume" "home" {
  name = "coder-${data.coder_workspace.me.id}-home"

  lifecycle {
    ignore_changes = all
  }

  labels {
    label = "coder.owner"
    value = data.coder_workspace_owner.me.name
  }

  labels {
    label = "coder.workspace_id"
    value = data.coder_workspace.me.id
  }
}

resource "docker_volume" "shared_cache" {
  name = "coder-${local.username}-shared-cache"

  lifecycle {
    ignore_changes = all
  }

  labels {
    label = "coder.owner"
    value = data.coder_workspace_owner.me.name
  }

  labels {
    label = "coder.cache"
    value = "shared"
  }
}

resource "docker_container" "workspace" {
  count    = data.coder_workspace.me.start_count
  image    = docker_image.devbox[0].image_id
  name     = local.container_name
  hostname = data.coder_workspace.me.name
  restart  = "unless-stopped"
  memory   = local.mem_bytes

  entrypoint = [
    "sh",
    "-c",
    replace(coder_agent.main.init_script, "/localhost|127\\.0\\.0\\.1/", "host.docker.internal")
  ]

  env = local.workspace_env

  host {
    host = "host.docker.internal"
    ip   = "host-gateway"
  }

  volumes {
    container_path = "/home/coder"
    volume_name    = docker_volume.home.name
    read_only      = false
  }

  volumes {
    container_path = local.cache_root
    volume_name    = docker_volume.shared_cache.name
    read_only      = false
  }

  volumes {
    host_path      = "/opt/coder-cde/extensions"
    container_path = "/opt/cde/extensions"
    read_only      = true
  }

  volumes {
    host_path      = "/opt/coder-cde/vsix"
    container_path = "/opt/cde/vsix"
    read_only      = true
  }

  dynamic "volumes" {
    for_each = data.coder_parameter.docker_socket.value == "true" ? [1] : []

    content {
      host_path      = "/var/run/docker.sock"
      container_path = "/var/run/docker.sock"
      read_only      = false
    }
  }

  group_add = data.coder_parameter.docker_socket.value == "true" ? [local.host_docker_gid] : []

  capabilities {
    add = ["SYS_PTRACE"]
  }

  security_opts = ["seccomp=unconfined"]

  labels {
    label = "coder.owner"
    value = data.coder_workspace_owner.me.name
  }

  labels {
    label = "coder.workspace_id"
    value = data.coder_workspace.me.id
  }

  labels {
    label = "coder.workspace_name"
    value = data.coder_workspace.me.name
  }

  labels {
    label = "coder.image"
    value = local.image_name
  }

  labels {
    label = "coder.image_profile"
    value = data.coder_parameter.image_profile.value
  }

  labels {
    label = "coder.base_image"
    value = data.coder_parameter.base_image.value
  }
}
