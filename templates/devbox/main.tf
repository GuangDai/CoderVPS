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

data "coder_parameter" "node_major" {
  name         = "node_major"
  display_name = "Node.js"
  type         = "string"
  form_type    = "dropdown"
  mutable      = false
  default      = "24"
  order        = 1

  option {
    name  = "Node 24"
    value = "24"
  }

  option {
    name  = "Node 22"
    value = "22"
  }

  option {
    name  = "Node 20"
    value = "20"
  }

  option {
    name  = "Node 18"
    value = "18"
  }

  option {
    name  = "Node 16"
    value = "16"
  }
}

data "coder_parameter" "enable_python" {
  name         = "enable_python"
  display_name = "Enable Python"
  type         = "bool"
  form_type    = "checkbox"
  mutable      = false
  default      = true
  order        = 10
  description  = "Enable Python runtime and tools."
}

data "coder_parameter" "python_version" {
  count        = data.coder_parameter.enable_python.value ? 1 : 0
  name         = "python_version"
  display_name = "Python Runtime"
  type         = "string"
  form_type    = "dropdown"
  mutable      = false
  default      = "cpython@3.13.13"
  order        = 11

  option {
    name  = "CPython 3.15.0b1 preview"
    value = "cpython@3.15.0b1"
  }

  option {
    name  = "CPython 3.15.0b1 free-threaded preview"
    value = "cpython@3.15.0b1+freethreaded"
  }

  option {
    name  = "CPython 3.14.5"
    value = "cpython@3.14.5"
  }

  option {
    name  = "CPython 3.14.5 free-threaded"
    value = "cpython@3.14.5+freethreaded"
  }

  option {
    name  = "CPython 3.13.13"
    value = "cpython@3.13.13"
  }

  option {
    name  = "CPython 3.13.13 free-threaded"
    value = "cpython@3.13.13+freethreaded"
  }

  option {
    name  = "CPython 3.12.13"
    value = "cpython@3.12.13"
  }

  option {
    name  = "GraalPy 3.12.0"
    value = "graalpy@3.12.0"
  }

  option {
    name  = "CPython 3.11.15"
    value = "cpython@3.11.15"
  }

  option {
    name  = "PyPy 3.11.15"
    value = "pypy@3.11.15"
  }

  option {
    name  = "GraalPy 3.11.0"
    value = "graalpy@3.11.0"
  }

  option {
    name  = "CPython 3.10.20"
    value = "cpython@3.10.20"
  }

  option {
    name  = "PyPy 3.10.16"
    value = "pypy@3.10.16"
  }

  option {
    name  = "GraalPy 3.10.0"
    value = "graalpy@3.10.0"
  }

  option {
    name  = "CPython 3.9.25"
    value = "cpython@3.9.25"
  }

  option {
    name  = "PyPy 3.9.19"
    value = "pypy@3.9.19"
  }

  option {
    name  = "CPython 3.8.20"
    value = "cpython@3.8.20"
  }

  option {
    name  = "PyPy 3.8.16"
    value = "pypy@3.8.16"
  }

  option {
    name  = "GraalPy 3.8.5"
    value = "graalpy@3.8.5"
  }
}

data "coder_parameter" "python_tools" {
  count        = data.coder_parameter.enable_python.value ? 1 : 0
  name         = "python_tools"
  display_name = "Python Tools"
  type         = "list(string)"
  form_type    = "multi-select"
  mutable      = false
  default      = jsonencode(["ruff", "debugpy"])
  order        = 12

  option {
    name  = "ruff"
    value = "ruff"
  }

  option {
    name  = "debugpy"
    value = "debugpy"
  }

  option {
    name  = "IPython"
    value = "ipython"
  }

  option {
    name  = "Jupyter"
    value = "jupyter"
  }
}

data "coder_parameter" "enable_go" {
  name         = "enable_go"
  display_name = "Enable Go"
  type         = "bool"
  form_type    = "checkbox"
  mutable      = false
  default      = false
  order        = 20
  description  = "Enable Go runtime and tools."
}

data "coder_parameter" "go_version" {
  count        = data.coder_parameter.enable_go.value ? 1 : 0
  name         = "go_version"
  display_name = "Go Version"
  type         = "string"
  form_type    = "dropdown"
  mutable      = false
  default      = "1.26.3"
  order        = 21

  option {
    name  = "Go 1.26.3"
    value = "1.26.3"
  }

  option {
    name  = "Go 1.26.2"
    value = "1.26.2"
  }

  option {
    name  = "Go 1.26.1"
    value = "1.26.1"
  }

  option {
    name  = "Go 1.26.0"
    value = "1.26.0"
  }

  option {
    name  = "Go 1.26rc3"
    value = "1.26rc3"
  }

  option {
    name  = "Go 1.26rc2"
    value = "1.26rc2"
  }

  option {
    name  = "Go 1.26rc1"
    value = "1.26rc1"
  }

  option {
    name  = "Go 1.25.10"
    value = "1.25.10"
  }

  option {
    name  = "Go 1.25.9"
    value = "1.25.9"
  }

  option {
    name  = "Go 1.25.8"
    value = "1.25.8"
  }

  option {
    name  = "Go 1.25.7"
    value = "1.25.7"
  }

  option {
    name  = "Go 1.25.6"
    value = "1.25.6"
  }

  option {
    name  = "Go 1.25.5"
    value = "1.25.5"
  }

  option {
    name  = "Go 1.25.4"
    value = "1.25.4"
  }

  option {
    name  = "Go 1.25.3"
    value = "1.25.3"
  }

  option {
    name  = "Go 1.25.2"
    value = "1.25.2"
  }

  option {
    name  = "Go 1.25.1"
    value = "1.25.1"
  }

  option {
    name  = "Go 1.25.0"
    value = "1.25.0"
  }

  option {
    name  = "Go 1.25rc3"
    value = "1.25rc3"
  }

  option {
    name  = "Go 1.25rc2"
    value = "1.25rc2"
  }

  option {
    name  = "Go 1.25rc1"
    value = "1.25rc1"
  }

  option {
    name  = "Go 1.24.13"
    value = "1.24.13"
  }

  option {
    name  = "Go 1.24.12"
    value = "1.24.12"
  }

  option {
    name  = "Go 1.24.11"
    value = "1.24.11"
  }

  option {
    name  = "Go 1.24.10"
    value = "1.24.10"
  }

  option {
    name  = "Go 1.24.9"
    value = "1.24.9"
  }

  option {
    name  = "Go 1.24.8"
    value = "1.24.8"
  }

  option {
    name  = "Go 1.24.7"
    value = "1.24.7"
  }

  option {
    name  = "Go 1.24.6"
    value = "1.24.6"
  }

  option {
    name  = "Go 1.24.5"
    value = "1.24.5"
  }

  option {
    name  = "Go 1.24.4"
    value = "1.24.4"
  }

  option {
    name  = "Go 1.24.3"
    value = "1.24.3"
  }

  option {
    name  = "Go 1.24.2"
    value = "1.24.2"
  }

  option {
    name  = "Go 1.24.1"
    value = "1.24.1"
  }

  option {
    name  = "Go 1.24.0"
    value = "1.24.0"
  }

  option {
    name  = "Go 1.24rc3"
    value = "1.24rc3"
  }

  option {
    name  = "Go 1.24rc2"
    value = "1.24rc2"
  }

  option {
    name  = "Go 1.24rc1"
    value = "1.24rc1"
  }

  option {
    name  = "Go 1.23.12"
    value = "1.23.12"
  }

  option {
    name  = "Go 1.23.11"
    value = "1.23.11"
  }

  option {
    name  = "Go 1.23.10"
    value = "1.23.10"
  }

  option {
    name  = "Go 1.23.9"
    value = "1.23.9"
  }

  option {
    name  = "Go 1.23.8"
    value = "1.23.8"
  }

  option {
    name  = "Go 1.23.7"
    value = "1.23.7"
  }

  option {
    name  = "Go 1.23.6"
    value = "1.23.6"
  }

  option {
    name  = "Go 1.23.5"
    value = "1.23.5"
  }

  option {
    name  = "Go 1.23.4"
    value = "1.23.4"
  }

  option {
    name  = "Go 1.23.3"
    value = "1.23.3"
  }

  option {
    name  = "Go 1.23.2"
    value = "1.23.2"
  }

  option {
    name  = "Go 1.23.1"
    value = "1.23.1"
  }

  option {
    name  = "Go 1.23.0"
    value = "1.23.0"
  }

  option {
    name  = "Go 1.23rc2"
    value = "1.23rc2"
  }

  option {
    name  = "Go 1.23rc1"
    value = "1.23rc1"
  }

  option {
    name  = "Go 1.22.12"
    value = "1.22.12"
  }

  option {
    name  = "Go 1.22.11"
    value = "1.22.11"
  }

  option {
    name  = "Go 1.22.10"
    value = "1.22.10"
  }

  option {
    name  = "Go 1.22.9"
    value = "1.22.9"
  }

  option {
    name  = "Go 1.22.8"
    value = "1.22.8"
  }

  option {
    name  = "Go 1.22.7"
    value = "1.22.7"
  }

  option {
    name  = "Go 1.22.6"
    value = "1.22.6"
  }

  option {
    name  = "Go 1.22.5"
    value = "1.22.5"
  }

  option {
    name  = "Go 1.22.4"
    value = "1.22.4"
  }

  option {
    name  = "Go 1.22.3"
    value = "1.22.3"
  }

  option {
    name  = "Go 1.22.2"
    value = "1.22.2"
  }

  option {
    name  = "Go 1.22.1"
    value = "1.22.1"
  }

  option {
    name  = "Go 1.22.0"
    value = "1.22.0"
  }

  option {
    name  = "Go 1.22rc2"
    value = "1.22rc2"
  }

  option {
    name  = "Go 1.22rc1"
    value = "1.22rc1"
  }

  option {
    name  = "Go 1.21.13"
    value = "1.21.13"
  }

  option {
    name  = "Go 1.21.12"
    value = "1.21.12"
  }

  option {
    name  = "Go 1.21.11"
    value = "1.21.11"
  }

  option {
    name  = "Go 1.21.10"
    value = "1.21.10"
  }

  option {
    name  = "Go 1.21.9"
    value = "1.21.9"
  }

  option {
    name  = "Go 1.21.8"
    value = "1.21.8"
  }

  option {
    name  = "Go 1.21.7"
    value = "1.21.7"
  }

  option {
    name  = "Go 1.21.6"
    value = "1.21.6"
  }

  option {
    name  = "Go 1.21.5"
    value = "1.21.5"
  }

  option {
    name  = "Go 1.21.4"
    value = "1.21.4"
  }

  option {
    name  = "Go 1.21.3"
    value = "1.21.3"
  }

  option {
    name  = "Go 1.21.2"
    value = "1.21.2"
  }

  option {
    name  = "Go 1.21.1"
    value = "1.21.1"
  }

  option {
    name  = "Go 1.21.0"
    value = "1.21.0"
  }

  option {
    name  = "Go 1.21rc4"
    value = "1.21rc4"
  }

  option {
    name  = "Go 1.21rc3"
    value = "1.21rc3"
  }

  option {
    name  = "Go 1.21rc2"
    value = "1.21rc2"
  }

  option {
    name  = "Go 1.20.14"
    value = "1.20.14"
  }

  option {
    name  = "Go 1.20.13"
    value = "1.20.13"
  }

  option {
    name  = "Go 1.20.12"
    value = "1.20.12"
  }

  option {
    name  = "Go 1.20.11"
    value = "1.20.11"
  }

  option {
    name  = "Go 1.20.10"
    value = "1.20.10"
  }

  option {
    name  = "Go 1.20.9"
    value = "1.20.9"
  }

  option {
    name  = "Go 1.20.8"
    value = "1.20.8"
  }

  option {
    name  = "Go 1.20.7"
    value = "1.20.7"
  }

  option {
    name  = "Go 1.20.6"
    value = "1.20.6"
  }

  option {
    name  = "Go 1.20.5"
    value = "1.20.5"
  }

  option {
    name  = "Go 1.20.4"
    value = "1.20.4"
  }

  option {
    name  = "Go 1.20.3"
    value = "1.20.3"
  }

  option {
    name  = "Go 1.20.2"
    value = "1.20.2"
  }

  option {
    name  = "Go 1.20.1"
    value = "1.20.1"
  }

  option {
    name  = "Go 1.20"
    value = "1.20"
  }

  option {
    name  = "Go 1.20rc3"
    value = "1.20rc3"
  }

  option {
    name  = "Go 1.20rc2"
    value = "1.20rc2"
  }

  option {
    name  = "Go 1.20rc1"
    value = "1.20rc1"
  }

  option {
    name  = "Go 1.19.13"
    value = "1.19.13"
  }

  option {
    name  = "Go 1.19.12"
    value = "1.19.12"
  }

  option {
    name  = "Go 1.19.11"
    value = "1.19.11"
  }

  option {
    name  = "Go 1.19.10"
    value = "1.19.10"
  }

  option {
    name  = "Go 1.19.9"
    value = "1.19.9"
  }

  option {
    name  = "Go 1.19.8"
    value = "1.19.8"
  }

  option {
    name  = "Go 1.19.7"
    value = "1.19.7"
  }

  option {
    name  = "Go 1.19.6"
    value = "1.19.6"
  }

  option {
    name  = "Go 1.19.5"
    value = "1.19.5"
  }

  option {
    name  = "Go 1.19.4"
    value = "1.19.4"
  }

  option {
    name  = "Go 1.19.3"
    value = "1.19.3"
  }

  option {
    name  = "Go 1.19.2"
    value = "1.19.2"
  }

  option {
    name  = "Go 1.19.1"
    value = "1.19.1"
  }

  option {
    name  = "Go 1.19"
    value = "1.19"
  }

  option {
    name  = "Go 1.19rc2"
    value = "1.19rc2"
  }

  option {
    name  = "Go 1.19rc1"
    value = "1.19rc1"
  }

  option {
    name  = "Go 1.19beta1"
    value = "1.19beta1"
  }

  option {
    name  = "Go 1.18.10"
    value = "1.18.10"
  }

  option {
    name  = "Go 1.18.9"
    value = "1.18.9"
  }

  option {
    name  = "Go 1.18.8"
    value = "1.18.8"
  }

  option {
    name  = "Go 1.18.7"
    value = "1.18.7"
  }

  option {
    name  = "Go 1.18.6"
    value = "1.18.6"
  }

  option {
    name  = "Go 1.18.5"
    value = "1.18.5"
  }

  option {
    name  = "Go 1.18.4"
    value = "1.18.4"
  }

  option {
    name  = "Go 1.18.3"
    value = "1.18.3"
  }

  option {
    name  = "Go 1.18.2"
    value = "1.18.2"
  }

  option {
    name  = "Go 1.18.1"
    value = "1.18.1"
  }

  option {
    name  = "Go 1.18"
    value = "1.18"
  }

  option {
    name  = "Go 1.18rc1"
    value = "1.18rc1"
  }

  option {
    name  = "Go 1.18beta2"
    value = "1.18beta2"
  }

  option {
    name  = "Go 1.18beta1"
    value = "1.18beta1"
  }

  option {
    name  = "Go 1.17.13"
    value = "1.17.13"
  }

  option {
    name  = "Go 1.17.12"
    value = "1.17.12"
  }

  option {
    name  = "Go 1.17.11"
    value = "1.17.11"
  }

  option {
    name  = "Go 1.17.10"
    value = "1.17.10"
  }

  option {
    name  = "Go 1.17.9"
    value = "1.17.9"
  }

  option {
    name  = "Go 1.17.8"
    value = "1.17.8"
  }

  option {
    name  = "Go 1.17.7"
    value = "1.17.7"
  }

  option {
    name  = "Go 1.17.6"
    value = "1.17.6"
  }

  option {
    name  = "Go 1.17.5"
    value = "1.17.5"
  }

  option {
    name  = "Go 1.17.4"
    value = "1.17.4"
  }

  option {
    name  = "Go 1.17.3"
    value = "1.17.3"
  }

  option {
    name  = "Go 1.17.2"
    value = "1.17.2"
  }

  option {
    name  = "Go 1.17.1"
    value = "1.17.1"
  }

  option {
    name  = "Go 1.17"
    value = "1.17"
  }

  option {
    name  = "Go 1.17rc2"
    value = "1.17rc2"
  }

  option {
    name  = "Go 1.17rc1"
    value = "1.17rc1"
  }

  option {
    name  = "Go 1.17beta1"
    value = "1.17beta1"
  }

  option {
    name  = "Go 1.16.15"
    value = "1.16.15"
  }

  option {
    name  = "Go 1.16.14"
    value = "1.16.14"
  }

  option {
    name  = "Go 1.16.13"
    value = "1.16.13"
  }

  option {
    name  = "Go 1.16.12"
    value = "1.16.12"
  }

  option {
    name  = "Go 1.16.11"
    value = "1.16.11"
  }

  option {
    name  = "Go 1.16.10"
    value = "1.16.10"
  }

  option {
    name  = "Go 1.16.9"
    value = "1.16.9"
  }

  option {
    name  = "Go 1.16.8"
    value = "1.16.8"
  }

  option {
    name  = "Go 1.16.7"
    value = "1.16.7"
  }

  option {
    name  = "Go 1.16.6"
    value = "1.16.6"
  }

  option {
    name  = "Go 1.16.5"
    value = "1.16.5"
  }

  option {
    name  = "Go 1.16.4"
    value = "1.16.4"
  }

  option {
    name  = "Go 1.16.3"
    value = "1.16.3"
  }

  option {
    name  = "Go 1.16.2"
    value = "1.16.2"
  }

  option {
    name  = "Go 1.16.1"
    value = "1.16.1"
  }

  option {
    name  = "Go 1.16"
    value = "1.16"
  }

  option {
    name  = "Go 1.16rc1"
    value = "1.16rc1"
  }

  option {
    name  = "Go 1.16beta1"
    value = "1.16beta1"
  }

  option {
    name  = "Go 1.15.15"
    value = "1.15.15"
  }

  option {
    name  = "Go 1.15.14"
    value = "1.15.14"
  }

  option {
    name  = "Go 1.15.13"
    value = "1.15.13"
  }

  option {
    name  = "Go 1.15.12"
    value = "1.15.12"
  }

  option {
    name  = "Go 1.15.11"
    value = "1.15.11"
  }

  option {
    name  = "Go 1.15.10"
    value = "1.15.10"
  }

  option {
    name  = "Go 1.15.9"
    value = "1.15.9"
  }

  option {
    name  = "Go 1.15.8"
    value = "1.15.8"
  }

  option {
    name  = "Go 1.15.7"
    value = "1.15.7"
  }

  option {
    name  = "Go 1.15.6"
    value = "1.15.6"
  }

  option {
    name  = "Go 1.15.5"
    value = "1.15.5"
  }

  option {
    name  = "Go 1.15.4"
    value = "1.15.4"
  }

  option {
    name  = "Go 1.15.3"
    value = "1.15.3"
  }

  option {
    name  = "Go 1.15.2"
    value = "1.15.2"
  }

  option {
    name  = "Go 1.15.1"
    value = "1.15.1"
  }

  option {
    name  = "Go 1.15"
    value = "1.15"
  }

  option {
    name  = "Go 1.15rc2"
    value = "1.15rc2"
  }

  option {
    name  = "Go 1.15rc1"
    value = "1.15rc1"
  }

  option {
    name  = "Go 1.15beta1"
    value = "1.15beta1"
  }

  option {
    name  = "Go 1.14.15"
    value = "1.14.15"
  }

  option {
    name  = "Go 1.14.14"
    value = "1.14.14"
  }

  option {
    name  = "Go 1.14.13"
    value = "1.14.13"
  }

  option {
    name  = "Go 1.14.12"
    value = "1.14.12"
  }

  option {
    name  = "Go 1.14.11"
    value = "1.14.11"
  }

  option {
    name  = "Go 1.14.10"
    value = "1.14.10"
  }

  option {
    name  = "Go 1.14.9"
    value = "1.14.9"
  }

  option {
    name  = "Go 1.14.8"
    value = "1.14.8"
  }

  option {
    name  = "Go 1.14.7"
    value = "1.14.7"
  }

  option {
    name  = "Go 1.14.6"
    value = "1.14.6"
  }

  option {
    name  = "Go 1.14.5"
    value = "1.14.5"
  }

  option {
    name  = "Go 1.14.4"
    value = "1.14.4"
  }

  option {
    name  = "Go 1.14.3"
    value = "1.14.3"
  }

  option {
    name  = "Go 1.14.2"
    value = "1.14.2"
  }

  option {
    name  = "Go 1.14.1"
    value = "1.14.1"
  }

  option {
    name  = "Go 1.14"
    value = "1.14"
  }

  option {
    name  = "Go 1.14rc1"
    value = "1.14rc1"
  }

  option {
    name  = "Go 1.14beta1"
    value = "1.14beta1"
  }

  option {
    name  = "Go 1.13.15"
    value = "1.13.15"
  }

  option {
    name  = "Go 1.13.14"
    value = "1.13.14"
  }

  option {
    name  = "Go 1.13.13"
    value = "1.13.13"
  }

  option {
    name  = "Go 1.13.12"
    value = "1.13.12"
  }

  option {
    name  = "Go 1.13.11"
    value = "1.13.11"
  }

  option {
    name  = "Go 1.13.10"
    value = "1.13.10"
  }

  option {
    name  = "Go 1.13.9"
    value = "1.13.9"
  }

  option {
    name  = "Go 1.13.8"
    value = "1.13.8"
  }

  option {
    name  = "Go 1.13.7"
    value = "1.13.7"
  }

  option {
    name  = "Go 1.13.6"
    value = "1.13.6"
  }

  option {
    name  = "Go 1.13.5"
    value = "1.13.5"
  }

  option {
    name  = "Go 1.13.4"
    value = "1.13.4"
  }

  option {
    name  = "Go 1.13.3"
    value = "1.13.3"
  }

  option {
    name  = "Go 1.13.2"
    value = "1.13.2"
  }

  option {
    name  = "Go 1.13.1"
    value = "1.13.1"
  }

  option {
    name  = "Go 1.13"
    value = "1.13"
  }

  option {
    name  = "Go 1.13rc2"
    value = "1.13rc2"
  }

  option {
    name  = "Go 1.13rc1"
    value = "1.13rc1"
  }

  option {
    name  = "Go 1.13beta1"
    value = "1.13beta1"
  }

  option {
    name  = "Go 1.12.17"
    value = "1.12.17"
  }

  option {
    name  = "Go 1.12.16"
    value = "1.12.16"
  }

  option {
    name  = "Go 1.12.15"
    value = "1.12.15"
  }

  option {
    name  = "Go 1.12.14"
    value = "1.12.14"
  }

  option {
    name  = "Go 1.12.13"
    value = "1.12.13"
  }

  option {
    name  = "Go 1.12.12"
    value = "1.12.12"
  }

  option {
    name  = "Go 1.12.11"
    value = "1.12.11"
  }

  option {
    name  = "Go 1.12.10"
    value = "1.12.10"
  }

  option {
    name  = "Go 1.12.9"
    value = "1.12.9"
  }

  option {
    name  = "Go 1.12.8"
    value = "1.12.8"
  }

  option {
    name  = "Go 1.12.7"
    value = "1.12.7"
  }

  option {
    name  = "Go 1.12.6"
    value = "1.12.6"
  }

  option {
    name  = "Go 1.12.5"
    value = "1.12.5"
  }

  option {
    name  = "Go 1.12.4"
    value = "1.12.4"
  }

  option {
    name  = "Go 1.12.3"
    value = "1.12.3"
  }

  option {
    name  = "Go 1.12.2"
    value = "1.12.2"
  }

  option {
    name  = "Go 1.12.1"
    value = "1.12.1"
  }

  option {
    name  = "Go 1.12"
    value = "1.12"
  }

  option {
    name  = "Go 1.12rc1"
    value = "1.12rc1"
  }

  option {
    name  = "Go 1.12beta2"
    value = "1.12beta2"
  }

  option {
    name  = "Go 1.12beta1"
    value = "1.12beta1"
  }

  option {
    name  = "Go 1.11.13"
    value = "1.11.13"
  }

  option {
    name  = "Go 1.11.12"
    value = "1.11.12"
  }

  option {
    name  = "Go 1.11.11"
    value = "1.11.11"
  }

  option {
    name  = "Go 1.11.10"
    value = "1.11.10"
  }

  option {
    name  = "Go 1.11.9"
    value = "1.11.9"
  }

  option {
    name  = "Go 1.11.8"
    value = "1.11.8"
  }

  option {
    name  = "Go 1.11.7"
    value = "1.11.7"
  }

  option {
    name  = "Go 1.11.6"
    value = "1.11.6"
  }

  option {
    name  = "Go 1.11.5"
    value = "1.11.5"
  }

  option {
    name  = "Go 1.11.4"
    value = "1.11.4"
  }

  option {
    name  = "Go 1.11.3"
    value = "1.11.3"
  }

  option {
    name  = "Go 1.11.2"
    value = "1.11.2"
  }

  option {
    name  = "Go 1.11.1"
    value = "1.11.1"
  }

  option {
    name  = "Go 1.11"
    value = "1.11"
  }

  option {
    name  = "Go 1.11rc2"
    value = "1.11rc2"
  }

  option {
    name  = "Go 1.11rc1"
    value = "1.11rc1"
  }

  option {
    name  = "Go 1.11beta3"
    value = "1.11beta3"
  }

  option {
    name  = "Go 1.11beta2"
    value = "1.11beta2"
  }

  option {
    name  = "Go 1.11beta1"
    value = "1.11beta1"
  }

  option {
    name  = "Go 1.10.8"
    value = "1.10.8"
  }

  option {
    name  = "Go 1.10.7"
    value = "1.10.7"
  }

  option {
    name  = "Go 1.10.6"
    value = "1.10.6"
  }

  option {
    name  = "Go 1.10.5"
    value = "1.10.5"
  }

  option {
    name  = "Go 1.10.4"
    value = "1.10.4"
  }

  option {
    name  = "Go 1.10.3"
    value = "1.10.3"
  }

  option {
    name  = "Go 1.10.2"
    value = "1.10.2"
  }

  option {
    name  = "Go 1.10.1"
    value = "1.10.1"
  }

  option {
    name  = "Go 1.10"
    value = "1.10"
  }

  option {
    name  = "Go 1.10rc2"
    value = "1.10rc2"
  }

  option {
    name  = "Go 1.10rc1"
    value = "1.10rc1"
  }

  option {
    name  = "Go 1.10beta2"
    value = "1.10beta2"
  }

  option {
    name  = "Go 1.10beta1"
    value = "1.10beta1"
  }

  option {
    name  = "Go 1.9.7"
    value = "1.9.7"
  }

  option {
    name  = "Go 1.9.6"
    value = "1.9.6"
  }

  option {
    name  = "Go 1.9.5"
    value = "1.9.5"
  }

  option {
    name  = "Go 1.9.4"
    value = "1.9.4"
  }

  option {
    name  = "Go 1.9.3"
    value = "1.9.3"
  }

  option {
    name  = "Go 1.9.2"
    value = "1.9.2"
  }

  option {
    name  = "Go 1.9.2rc2"
    value = "1.9.2rc2"
  }

  option {
    name  = "Go 1.9.1"
    value = "1.9.1"
  }

  option {
    name  = "Go 1.9"
    value = "1.9"
  }

  option {
    name  = "Go 1.9rc2"
    value = "1.9rc2"
  }

  option {
    name  = "Go 1.9rc1"
    value = "1.9rc1"
  }

  option {
    name  = "Go 1.9beta2"
    value = "1.9beta2"
  }

  option {
    name  = "Go 1.9beta1"
    value = "1.9beta1"
  }

  option {
    name  = "Go 1.8.7"
    value = "1.8.7"
  }

  option {
    name  = "Go 1.8.6"
    value = "1.8.6"
  }

  option {
    name  = "Go 1.8.5"
    value = "1.8.5"
  }

  option {
    name  = "Go 1.8.4"
    value = "1.8.4"
  }

  option {
    name  = "Go 1.8.3"
    value = "1.8.3"
  }

  option {
    name  = "Go 1.8.2"
    value = "1.8.2"
  }

  option {
    name  = "Go 1.8.1"
    value = "1.8.1"
  }

  option {
    name  = "Go 1.8"
    value = "1.8"
  }

  option {
    name  = "Go 1.8rc3"
    value = "1.8rc3"
  }

  option {
    name  = "Go 1.8rc2"
    value = "1.8rc2"
  }

  option {
    name  = "Go 1.8rc1"
    value = "1.8rc1"
  }

  option {
    name  = "Go 1.8beta2"
    value = "1.8beta2"
  }

  option {
    name  = "Go 1.8beta1"
    value = "1.8beta1"
  }

  option {
    name  = "Go 1.7.6"
    value = "1.7.6"
  }

  option {
    name  = "Go 1.7.5"
    value = "1.7.5"
  }

  option {
    name  = "Go 1.7.4"
    value = "1.7.4"
  }

  option {
    name  = "Go 1.7.3"
    value = "1.7.3"
  }

  option {
    name  = "Go 1.7.1"
    value = "1.7.1"
  }

  option {
    name  = "Go 1.7"
    value = "1.7"
  }

  option {
    name  = "Go 1.7rc6"
    value = "1.7rc6"
  }

  option {
    name  = "Go 1.7rc5"
    value = "1.7rc5"
  }

  option {
    name  = "Go 1.7rc4"
    value = "1.7rc4"
  }

  option {
    name  = "Go 1.7rc3"
    value = "1.7rc3"
  }

  option {
    name  = "Go 1.7rc2"
    value = "1.7rc2"
  }

  option {
    name  = "Go 1.7rc1"
    value = "1.7rc1"
  }

  option {
    name  = "Go 1.7beta2"
    value = "1.7beta2"
  }

  option {
    name  = "Go 1.7beta1"
    value = "1.7beta1"
  }

  option {
    name  = "Go 1.6.4"
    value = "1.6.4"
  }

  option {
    name  = "Go 1.6.3"
    value = "1.6.3"
  }

  option {
    name  = "Go 1.6.2"
    value = "1.6.2"
  }

  option {
    name  = "Go 1.6.1"
    value = "1.6.1"
  }

  option {
    name  = "Go 1.6"
    value = "1.6"
  }

  option {
    name  = "Go 1.6rc2"
    value = "1.6rc2"
  }

  option {
    name  = "Go 1.6rc1"
    value = "1.6rc1"
  }

  option {
    name  = "Go 1.6beta2"
    value = "1.6beta2"
  }

  option {
    name  = "Go 1.5.4"
    value = "1.5.4"
  }

  option {
    name  = "Go 1.5.3"
    value = "1.5.3"
  }
}

data "coder_parameter" "go_tools" {
  count        = data.coder_parameter.enable_go.value ? 1 : 0
  name         = "go_tools"
  display_name = "Go Tools"
  type         = "list(string)"
  form_type    = "multi-select"
  mutable      = false
  default      = jsonencode(["gopls"])
  order        = 22

  option {
    name  = "gopls"
    value = "gopls"
  }

  option {
    name  = "dlv (Delve debugger)"
    value = "dlv"
  }
}

data "coder_parameter" "enable_rust" {
  name         = "enable_rust"
  display_name = "Enable Rust"
  type         = "bool"
  form_type    = "checkbox"
  mutable      = false
  default      = false
  order        = 30
  description  = "Enable Rust toolchain."
}

data "coder_parameter" "rust_toolchain" {
  count        = data.coder_parameter.enable_rust.value ? 1 : 0
  name         = "rust_toolchain"
  display_name = "Rust Toolchain"
  type         = "string"
  form_type    = "dropdown"
  mutable      = false
  default      = "stable"
  order        = 31

  option {
    name  = "Stable"
    value = "stable"
  }

  option {
    name  = "Beta"
    value = "beta"
  }

  option {
    name  = "Nightly"
    value = "nightly"
  }

  option {
    name  = "Rust 1.95"
    value = "1.95"
  }

  option {
    name  = "Rust 1.94"
    value = "1.94"
  }

  option {
    name  = "Rust 1.93"
    value = "1.93"
  }

  option {
    name  = "Rust 1.92"
    value = "1.92"
  }

  option {
    name  = "Rust 1.91"
    value = "1.91"
  }

  option {
    name  = "Rust 1.90"
    value = "1.90"
  }

  option {
    name  = "Rust 1.89"
    value = "1.89"
  }

  option {
    name  = "Rust 1.88"
    value = "1.88"
  }

  option {
    name  = "Rust 1.87"
    value = "1.87"
  }

  option {
    name  = "Rust 1.86"
    value = "1.86"
  }

  option {
    name  = "Rust 1.85"
    value = "1.85"
  }

  option {
    name  = "Rust 1.84"
    value = "1.84"
  }

  option {
    name  = "Rust 1.83"
    value = "1.83"
  }

  option {
    name  = "Rust 1.82"
    value = "1.82"
  }

  option {
    name  = "Rust 1.81"
    value = "1.81"
  }

  option {
    name  = "Rust 1.80"
    value = "1.80"
  }

  option {
    name  = "Rust 1.79"
    value = "1.79"
  }

  option {
    name  = "Rust 1.78"
    value = "1.78"
  }

  option {
    name  = "Rust 1.77"
    value = "1.77"
  }

  option {
    name  = "Rust 1.76"
    value = "1.76"
  }

  option {
    name  = "Rust 1.75"
    value = "1.75"
  }

  option {
    name  = "Rust 1.74"
    value = "1.74"
  }

  option {
    name  = "Rust 1.73"
    value = "1.73"
  }

  option {
    name  = "Rust 1.72"
    value = "1.72"
  }

  option {
    name  = "Rust 1.71"
    value = "1.71"
  }

  option {
    name  = "Rust 1.70"
    value = "1.70"
  }

  option {
    name  = "Rust 1.69"
    value = "1.69"
  }

  option {
    name  = "Rust 1.68"
    value = "1.68"
  }

  option {
    name  = "Rust 1.67"
    value = "1.67"
  }

  option {
    name  = "Rust 1.66"
    value = "1.66"
  }
}

data "coder_parameter" "enable_cpp" {
  name         = "enable_cpp"
  display_name = "Enable C/C++"
  type         = "bool"
  form_type    = "checkbox"
  mutable      = false
  default      = false
  order        = 40
  description  = "Enable C/C++ LLVM toolchain."
}

data "coder_parameter" "cpp_llvm" {
  count        = data.coder_parameter.enable_cpp.value ? 1 : 0
  name         = "cpp_llvm"
  display_name = "C/C++ LLVM Version"
  type         = "string"
  form_type    = "dropdown"
  mutable      = false
  default      = "22"
  order        = 41

  option {
    name  = "LLVM 23"
    value = "23"
  }

  option {
    name  = "LLVM 22"
    value = "22"
  }

  option {
    name  = "LLVM 21"
    value = "21"
  }
}

data "coder_parameter" "extra_extension_packs" {
  name         = "extra_extension_packs"
  display_name = "Extra Extension Packs"
  type         = "list(string)"
  form_type    = "multi-select"
  mutable      = false
  default      = jsonencode([])
  order        = 50

  option {
    name  = "LeetCode"
    value = "leetcode"
  }
}

locals {
  images = jsondecode(<<-JSON
[
  {
    "base_image": "codercom/example-base:ubuntu-noble-20260512",
    "code_server_version": "4.118.0",
    "image": "ghcr.io/guangdai/codervps-devbox:noble-20260512-node24",
    "llvm_version": "22",
    "node_major": 24,
    "node_version": "24.15.0",
    "sccache_asset": "sccache-v0.15.0-x86_64-unknown-linux-musl.tar.gz",
    "sccache_sha256": "782d2b5dd7ae0a55ebe368ab258114d0928d019ac2d949ab85d5d02f3926709e",
    "sccache_version": "0.15.0",
    "tag": "noble-20260512-node24",
    "uv_version": "0.11.14"
  },
  {
    "base_image": "codercom/example-base:ubuntu-noble-20260512",
    "code_server_version": "4.118.0",
    "image": "ghcr.io/guangdai/codervps-devbox:noble-20260512-node22",
    "llvm_version": "22",
    "node_major": 22,
    "node_version": "22.22.3",
    "sccache_asset": "sccache-v0.15.0-x86_64-unknown-linux-musl.tar.gz",
    "sccache_sha256": "782d2b5dd7ae0a55ebe368ab258114d0928d019ac2d949ab85d5d02f3926709e",
    "sccache_version": "0.15.0",
    "tag": "noble-20260512-node22",
    "uv_version": "0.11.14"
  },
  {
    "base_image": "codercom/example-base:ubuntu-noble-20260512",
    "code_server_version": "4.118.0",
    "image": "ghcr.io/guangdai/codervps-devbox:noble-20260512-node20",
    "llvm_version": "22",
    "node_major": 20,
    "node_version": "20.20.2",
    "sccache_asset": "sccache-v0.15.0-x86_64-unknown-linux-musl.tar.gz",
    "sccache_sha256": "782d2b5dd7ae0a55ebe368ab258114d0928d019ac2d949ab85d5d02f3926709e",
    "sccache_version": "0.15.0",
    "tag": "noble-20260512-node20",
    "uv_version": "0.11.14"
  },
  {
    "base_image": "codercom/example-base:ubuntu-noble-20260512",
    "code_server_version": "4.118.0",
    "image": "ghcr.io/guangdai/codervps-devbox:noble-20260512-node18",
    "llvm_version": "22",
    "node_major": 18,
    "node_version": "18.20.8",
    "sccache_asset": "sccache-v0.15.0-x86_64-unknown-linux-musl.tar.gz",
    "sccache_sha256": "782d2b5dd7ae0a55ebe368ab258114d0928d019ac2d949ab85d5d02f3926709e",
    "sccache_version": "0.15.0",
    "tag": "noble-20260512-node18",
    "uv_version": "0.11.14"
  },
  {
    "base_image": "codercom/example-base:ubuntu-noble-20260512",
    "code_server_version": "4.118.0",
    "image": "ghcr.io/guangdai/codervps-devbox:noble-20260512-node16",
    "llvm_version": "22",
    "node_major": 16,
    "node_version": "16.20.2",
    "sccache_asset": "sccache-v0.15.0-x86_64-unknown-linux-musl.tar.gz",
    "sccache_sha256": "782d2b5dd7ae0a55ebe368ab258114d0928d019ac2d949ab85d5d02f3926709e",
    "sccache_version": "0.15.0",
    "tag": "noble-20260512-node16",
    "uv_version": "0.11.14"
  }
]
JSON
  )

  catalog = jsondecode(<<-JSON
{
  "arch": "linux/amd64",
  "base": {
    "source": "codercom/example-base",
    "tag": "ubuntu-noble-20260512",
    "ubuntu": "noble"
  },
  "generated_at": "2026-05-16T07:01:18+00:00",
  "node": {
    "majors": {
      "16": {
        "status": "eol",
        "version": "16.20.2"
      },
      "18": {
        "status": "eol",
        "version": "18.20.8"
      },
      "20": {
        "status": "eol",
        "version": "20.20.2"
      },
      "22": {
        "status": "maintenance_lts",
        "version": "22.22.3"
      },
      "24": {
        "status": "active_lts",
        "version": "24.15.0"
      }
    }
  },
  "plugins": {
    "cpp": {
      "defaults": {
        "llvm": "22"
      },
      "versions": [
        {
          "status": "snapshot",
          "version": "23"
        },
        {
          "status": "active",
          "version": "22"
        },
        {
          "status": "supported",
          "version": "21"
        }
      ]
    },
    "go": {
      "defaults": {
        "version": "1.26.3"
      },
      "versions": [
        {
          "sha256": "2b2cfc7148493da5e73981bffbf3353af381d5f93e789c82c79aff64962eb556",
          "status": "active",
          "version": "1.26.3"
        },
        {
          "sha256": "990e6b4bbba816dc3ee129eaeaf4b42f17c2800b88a2166c265ac1a200262282",
          "status": "active",
          "version": "1.26.2"
        },
        {
          "sha256": "031f088e5d955bab8657ede27ad4e3bc5b7c1ba281f05f245bcc304f327c987a",
          "status": "active",
          "version": "1.26.1"
        },
        {
          "sha256": "aac1b08a0fb0c4e0a7c1555beb7b59180b05dfc5a3d62e40e9de90cd42f88235",
          "status": "active",
          "version": "1.26.0"
        },
        {
          "sha256": "5eef7fb80790d3c5339607f7b17b4b8b7b67a4c322fc636cea8820f490cede00",
          "status": "prerelease",
          "version": "1.26rc3"
        },
        {
          "sha256": "16e98a4ecd3ee04354685b6f0d31f67d2109d17dde9a95eaa574f5b182855b7c",
          "status": "prerelease",
          "version": "1.26rc2"
        },
        {
          "sha256": "b395b5d51d45cf2a19e61855edd7bafaa2dfeaafaf8d9649cb3262fd8b81a96a",
          "status": "prerelease",
          "version": "1.26rc1"
        },
        {
          "sha256": "42d4f7a32316aa66591eca7e89867256057a4264451aca10570a715b3637ba70",
          "status": "active",
          "version": "1.25.10"
        },
        {
          "sha256": "00859d7bd6defe8bf84d9db9e57b9a4467b2887c18cd93ae7460e713db774bc1",
          "status": "active",
          "version": "1.25.9"
        },
        {
          "sha256": "ceb5e041bbc3893846bd1614d76cb4681c91dadee579426cf21a63f2d7e03be6",
          "status": "active",
          "version": "1.25.8"
        },
        {
          "sha256": "12e6d6a191091ae27dc31f6efc630e3a3b8ba409baf3573d955b196fdf086005",
          "status": "active",
          "version": "1.25.7"
        },
        {
          "sha256": "f022b6aad78e362bcba9b0b94d09ad58c5a70c6ba3b7582905fababf5fe0181a",
          "status": "active",
          "version": "1.25.6"
        },
        {
          "sha256": "9e9b755d63b36acf30c12a9a3fc379243714c1c6d3dd72861da637f336ebb35b",
          "status": "active",
          "version": "1.25.5"
        },
        {
          "sha256": "9fa5ffeda4170de60f67f3aa0f824e426421ba724c21e133c1e35d6159ca1bec",
          "status": "active",
          "version": "1.25.4"
        },
        {
          "sha256": "0335f314b6e7bfe08c3d0cfaa7c19db961b7b99fb20be62b0a826c992ad14e0f",
          "status": "active",
          "version": "1.25.3"
        },
        {
          "sha256": "d7fa7f8fbd16263aa2501d681b11f972a5fd8e811f7b10cb9b26d031a3d7454b",
          "status": "active",
          "version": "1.25.2"
        },
        {
          "sha256": "7716a0d940a0f6ae8e1f3b3f4f36299dc53e31b16840dbd171254312c41ca12e",
          "status": "active",
          "version": "1.25.1"
        },
        {
          "sha256": "2852af0cb20a13139b3448992e69b868e50ed0f8a1e5940ee1de9e19a123b613",
          "status": "active",
          "version": "1.25.0"
        },
        {
          "sha256": "e6c08a140ae7c28770eeb246934981fe5095ecc92ec232571497c22a7588960e",
          "status": "prerelease",
          "version": "1.25rc3"
        },
        {
          "sha256": "efcd3a151b174ffebde86b9d391ad59084300a4c5e9ea8c1d5dff90bbac38820",
          "status": "prerelease",
          "version": "1.25rc2"
        },
        {
          "sha256": "7588a720e243e4672e0dc1c7942ec7592d480a80440fa2829be8b22c9c44a5b7",
          "status": "prerelease",
          "version": "1.25rc1"
        },
        {
          "sha256": "1fc94b57134d51669c72173ad5d49fd62afb0f1db9bf3f798fd98ee423f8d730",
          "status": "active",
          "version": "1.24.13"
        },
        {
          "sha256": "bddf8e653c82429aea7aec2520774e79925d4bb929fe20e67ecc00dd5af44c50",
          "status": "active",
          "version": "1.24.12"
        },
        {
          "sha256": "bceca00afaac856bc48b4cc33db7cd9eb383c81811379faed3bdbc80edb0af65",
          "status": "active",
          "version": "1.24.11"
        },
        {
          "sha256": "dd52b974e3d9c5a7bbfb222c685806def6be5d6f7efd10f9caa9ca1fa2f47955",
          "status": "active",
          "version": "1.24.10"
        },
        {
          "sha256": "5b7899591c2dd6e9da1809fde4a2fad842c45d3f6b9deb235ba82216e31e34a6",
          "status": "active",
          "version": "1.24.9"
        },
        {
          "sha256": "6842c516ca66c89d648a7f1dbe28e28c47b61b59f8f06633eb2ceb1188e9251d",
          "status": "active",
          "version": "1.24.8"
        },
        {
          "sha256": "da18191ddb7db8a9339816f3e2b54bdded8047cdc2a5d67059478f8d1595c43f",
          "status": "active",
          "version": "1.24.7"
        },
        {
          "sha256": "bbca37cc395c974ffa4893ee35819ad23ebb27426df87af92e93a9ec66ef8712",
          "status": "active",
          "version": "1.24.6"
        },
        {
          "sha256": "10ad9e86233e74c0f6590fe5426895de6bf388964210eac34a6d83f38918ecdc",
          "status": "active",
          "version": "1.24.5"
        },
        {
          "sha256": "77e5da33bb72aeaef1ba4418b6fe511bc4d041873cbf82e5aa6318740df98717",
          "status": "active",
          "version": "1.24.4"
        },
        {
          "sha256": "3333f6ea53afa971e9078895eaa4ac7204a8c6b5c68c10e6bc9a33e8e391bdd8",
          "status": "active",
          "version": "1.24.3"
        },
        {
          "sha256": "68097bd680839cbc9d464a0edce4f7c333975e27a90246890e9f1078c7e702ad",
          "status": "active",
          "version": "1.24.2"
        },
        {
          "sha256": "cb2396bae64183cdccf81a9a6df0aea3bce9511fc21469fb89a0c00470088073",
          "status": "active",
          "version": "1.24.1"
        },
        {
          "sha256": "dea9ca38a0b852a74e81c26134671af7c0fbe65d81b0dc1c5bfe22cf7d4c8858",
          "status": "active",
          "version": "1.24.0"
        },
        {
          "sha256": "9eb3d64e392531781574e65880575c62633436c56f86d88a8dc15bacd546798e",
          "status": "prerelease",
          "version": "1.24rc3"
        },
        {
          "sha256": "3835e217efb30c6ace65fcb98cb8f61da3429bfa9e3f6bb4e5e3297ccfc7d1a4",
          "status": "prerelease",
          "version": "1.24rc2"
        },
        {
          "sha256": "706c3810c0826dd43bb6d5274c5fa4f644488274533a9bb1f9b13a0e302afcc6",
          "status": "prerelease",
          "version": "1.24rc1"
        },
        {
          "sha256": "d3847fef834e9db11bf64e3fb34db9c04db14e068eeb064f49af747010454f90",
          "status": "active",
          "version": "1.23.12"
        },
        {
          "sha256": "80899df77459e0b551d2eb8800ad6eb47023b99cccbf8129e7b5786770b948c5",
          "status": "active",
          "version": "1.23.11"
        },
        {
          "sha256": "535f9f81802499f2a7dbfa70abb8fda3793725fcc29460f719815f6e10b5fd60",
          "status": "active",
          "version": "1.23.10"
        },
        {
          "sha256": "de03e45d7a076c06baaa9618d42b3b6a0561125b87f6041c6397680a71e5bb26",
          "status": "active",
          "version": "1.23.9"
        },
        {
          "sha256": "45b87381172a58d62c977f27c4683c8681ef36580abecd14fd124d24ca306d3f",
          "status": "active",
          "version": "1.23.8"
        },
        {
          "sha256": "4741525e69841f2e22f9992af25df0c1112b07501f61f741c12c6389fcb119f3",
          "status": "active",
          "version": "1.23.7"
        },
        {
          "sha256": "9379441ea310de000f33a4dc767bd966e72ab2826270e038e78b2c53c2e7802d",
          "status": "active",
          "version": "1.23.6"
        },
        {
          "sha256": "cbcad4a6482107c7c7926df1608106c189417163428200ce357695cc7e01d091",
          "status": "active",
          "version": "1.23.5"
        },
        {
          "sha256": "6924efde5de86fe277676e929dc9917d466efa02fb934197bc2eba35d5680971",
          "status": "active",
          "version": "1.23.4"
        },
        {
          "sha256": "a0afb9744c00648bafb1b90b4aba5bdb86f424f02f9275399ce0c20b93a2c3a8",
          "status": "active",
          "version": "1.23.3"
        },
        {
          "sha256": "542d3c1705f1c6a1c5a80d5dc62e2e45171af291e755d591c5e6531ef63b454e",
          "status": "active",
          "version": "1.23.2"
        },
        {
          "sha256": "49bbb517cfa9eee677e1e7897f7cf9cfdbcf49e05f61984a2789136de359f9bd",
          "status": "active",
          "version": "1.23.1"
        },
        {
          "sha256": "905a297f19ead44780548933e0ff1a1b86e8327bb459e92f9c0012569f76f5e3",
          "status": "active",
          "version": "1.23.0"
        },
        {
          "sha256": "fa906bbb6d2077a1a58d91ca267e0fc5cb6d437807fb0725d10f23531e9258d2",
          "status": "prerelease",
          "version": "1.23rc2"
        },
        {
          "sha256": "0d8543abb8f4d566b3c8ef25b38e578ae2cb357bba2db8f0c0481531d8e1c939",
          "status": "prerelease",
          "version": "1.23rc1"
        },
        {
          "sha256": "4fa4f869b0f7fc6bb1eb2660e74657fbf04cdd290b5aef905585c86051b34d43",
          "status": "active",
          "version": "1.22.12"
        },
        {
          "sha256": "0fc88d966d33896384fbde56e9a8d80a305dc17a9f48f1832e061724b1719991",
          "status": "active",
          "version": "1.22.11"
        },
        {
          "sha256": "736ce492a19d756a92719a6121226087ccd91b652ed5caec40ad6dbfb2252092",
          "status": "active",
          "version": "1.22.10"
        },
        {
          "sha256": "84a8f05b7b969d8acfcaf194ce9298ad5d3ddbfc7034930c280006b5c85a574c",
          "status": "active",
          "version": "1.22.9"
        },
        {
          "sha256": "5f467d29fc67c7ae6468cb6ad5b047a274bae8180cac5e0b7ddbfeba3e47e18f",
          "status": "active",
          "version": "1.22.8"
        },
        {
          "sha256": "fc5d49b7a5035f1f1b265c17aa86e9819e6dc9af8260ad61430ee7fbe27881bb",
          "status": "active",
          "version": "1.22.7"
        },
        {
          "sha256": "999805bed7d9039ec3da1a53bfbcafc13e367da52aa823cb60b68ba22d44c616",
          "status": "active",
          "version": "1.22.6"
        },
        {
          "sha256": "904b924d435eaea086515bc63235b192ea441bd8c9b198c507e85009e6e4c7f0",
          "status": "active",
          "version": "1.22.5"
        },
        {
          "sha256": "ba79d4526102575196273416239cca418a651e049c2b099f3159db85e7bade7d",
          "status": "active",
          "version": "1.22.4"
        },
        {
          "sha256": "8920ea521bad8f6b7bc377b4824982e011c19af27df88a815e3586ea895f1b36",
          "status": "active",
          "version": "1.22.3"
        },
        {
          "sha256": "5901c52b7a78002aeff14a21f93e0f064f74ce1360fce51c6ee68cd471216a17",
          "status": "active",
          "version": "1.22.2"
        },
        {
          "sha256": "aab8e15785c997ae20f9c88422ee35d962c4562212bb0f879d052a35c8307c7f",
          "status": "active",
          "version": "1.22.1"
        },
        {
          "sha256": "f6c8a87aa03b92c4b0bf3d558e28ea03006eb29db78917daec5cfb6ec1046265",
          "status": "active",
          "version": "1.22.0"
        },
        {
          "sha256": "f811e7ee8f6dee3d162179229f96a64a467c8c02a5687fac5ceaadcf3948c818",
          "status": "prerelease",
          "version": "1.22rc2"
        },
        {
          "sha256": "fbe9d0585b9322d44008f6baf78b391b22f64294338c6ce2b9eb6040d6373c52",
          "status": "prerelease",
          "version": "1.22rc1"
        },
        {
          "sha256": "502fc16d5910562461e6a6631fb6377de2322aad7304bf2bcd23500ba9dab4a7",
          "status": "active",
          "version": "1.21.13"
        },
        {
          "sha256": "121ab58632787e18ae0caa8ae285b581f9470d0f6b3defde9e1600e211f583c5",
          "status": "active",
          "version": "1.21.12"
        },
        {
          "sha256": "54a87a9325155b98c85bc04dc50298ddd682489eb47f486f2e6cb0707554abf0",
          "status": "active",
          "version": "1.21.11"
        },
        {
          "sha256": "e330e5d977bf4f3bdc157bc46cf41afa5b13d66c914e12fd6b694ccda65fcf92",
          "status": "active",
          "version": "1.21.10"
        },
        {
          "sha256": "f76194c2dc607e0df4ed2e7b825b5847cb37e34fc70d780e2f6c7e805634a7ea",
          "status": "active",
          "version": "1.21.9"
        },
        {
          "sha256": "538b3b143dc7f32b093c8ffe0e050c260b57fc9d57a12c4140a639a8dd2b4e4f",
          "status": "active",
          "version": "1.21.8"
        },
        {
          "sha256": "13b76a9b2a26823e53062fa841b07087d48ae2ef2936445dc34c4ae03293702c",
          "status": "active",
          "version": "1.21.7"
        },
        {
          "sha256": "3f934f40ac360b9c01f616a9aa1796d227d8b0328bf64cb045c7b8c4ee9caea4",
          "status": "active",
          "version": "1.21.6"
        },
        {
          "sha256": "e2bc0b3e4b64111ec117295c088bde5f00eeed1567999ff77bc859d7df70078e",
          "status": "active",
          "version": "1.21.5"
        },
        {
          "sha256": "73cac0215254d0c7d1241fa40837851f3b9a8a742d0b54714cbdfb3feaf8f0af",
          "status": "active",
          "version": "1.21.4"
        },
        {
          "sha256": "1241381b2843fae5a9707eec1f8fb2ef94d827990582c7c7c32f5bdfbfd420c8",
          "status": "active",
          "version": "1.21.3"
        },
        {
          "sha256": "f5414a770e5e11c6e9674d4cd4dd1f4f630e176d1828d3427ea8ca4211eee90d",
          "status": "active",
          "version": "1.21.2"
        },
        {
          "sha256": "b3075ae1ce5dab85f89bc7905d1632de23ca196bd8336afd93fa97434cfa55ae",
          "status": "active",
          "version": "1.21.1"
        },
        {
          "sha256": "d0398903a16ba2232b389fb31032ddf57cac34efda306a0eebac34f0965a0742",
          "status": "active",
          "version": "1.21.0"
        },
        {
          "sha256": "c05c7b5030c4785dd3b4125bdb9eb631a840ea7347f4219b299de308021ac15b",
          "status": "prerelease",
          "version": "1.21rc4"
        },
        {
          "sha256": "b5e3a28d10ba1109cf0549237f2739284a0db2ce6bdc76cd03c4b26304c1a921",
          "status": "prerelease",
          "version": "1.21rc3"
        },
        {
          "sha256": "8fe90332727c606019e80a7368e23f5e65ad59520e45ee4010692f15572e45c6",
          "status": "prerelease",
          "version": "1.21rc2"
        },
        {
          "sha256": "ff445e48af27f93f66bd949ae060d97991c83e11289009d311f25426258f9c44",
          "status": "active",
          "version": "1.20.14"
        },
        {
          "sha256": "9a9d3dcae2b6a638b1f2e9bd4db08ffb39c10e55d9696914002742d90f0047b5",
          "status": "active",
          "version": "1.20.13"
        },
        {
          "sha256": "9c5d48c54dd8b0a3b2ef91b0f92a1190aa01f11d26e98033efa64c46a30bba7b",
          "status": "active",
          "version": "1.20.12"
        },
        {
          "sha256": "ef79a11aa095a08772d2a69e4f152f897c4e96ee297b0dc20264b7dec2961abe",
          "status": "active",
          "version": "1.20.11"
        },
        {
          "sha256": "80d34f1fd74e382d86c2d6102e0e60d4318461a7c2f457ec1efc4042752d4248",
          "status": "active",
          "version": "1.20.10"
        },
        {
          "sha256": "8921369701afa749b07232d2c34d514510c32dbfd79c65adb379451b5f0d7216",
          "status": "active",
          "version": "1.20.9"
        },
        {
          "sha256": "cc97c28d9c252fbf28f91950d830201aa403836cbed702a05932e63f7f0c7bc4",
          "status": "active",
          "version": "1.20.8"
        },
        {
          "sha256": "f0a87f1bcae91c4b69f8dc2bc6d7e6bfcd7524fceec130af525058c0c17b1b44",
          "status": "active",
          "version": "1.20.7"
        },
        {
          "sha256": "b945ae2bb5db01a0fb4786afde64e6fbab50b67f6fa0eb6cfa4924f16a7ff1eb",
          "status": "active",
          "version": "1.20.6"
        },
        {
          "sha256": "d7ec48cde0d3d2be2c69203bc3e0a44de8660b9c09a6e85c4732a3f7dc442612",
          "status": "active",
          "version": "1.20.5"
        },
        {
          "sha256": "698ef3243972a51ddb4028e4a1ac63dc6d60821bf18e59a807e051fee0a385bd",
          "status": "active",
          "version": "1.20.4"
        },
        {
          "sha256": "979694c2c25c735755bf26f4f45e19e64e4811d661dd07b8c010f7a8e18adfca",
          "status": "active",
          "version": "1.20.3"
        },
        {
          "sha256": "4eaea32f59cde4dc635fbc42161031d13e1c780b87097f4b4234cfce671f1768",
          "status": "active",
          "version": "1.20.2"
        },
        {
          "sha256": "000a5b1fca4f75895f78befeb2eecf10bfff3c428597f3f1e69133b63b911b02",
          "status": "active",
          "version": "1.20.1"
        },
        {
          "sha256": "5a9ebcc65c1cce56e0d2dc616aff4c4cedcfbda8cc6f0288cc08cda3b18dcbf1",
          "status": "active",
          "version": "1.20"
        },
        {
          "sha256": "a53434fa355bcae0cd02796690715b08ebe1c3f33d384d83cf155842fd6856ba",
          "status": "prerelease",
          "version": "1.20rc3"
        },
        {
          "sha256": "9ba01a3be1a682b89f5bfc62f9fba0e7d6990a5b7018f6c7aaa56ad65ed96a0e",
          "status": "prerelease",
          "version": "1.20rc2"
        },
        {
          "sha256": "4757fb32d7514145e43d4f37713f98d8cc0ecbbb5b1737accfc84be50e1e2e32",
          "status": "prerelease",
          "version": "1.20rc1"
        },
        {
          "sha256": "4643d4c29c55f53fa0349367d7f1bb5ca554ea6ef528c146825b0f8464e2e668",
          "status": "active",
          "version": "1.19.13"
        },
        {
          "sha256": "48e4fcfb6abfdaa01aaf1429e43bdd49cea5e4687bd5f5b96df1e193fcfd3e7e",
          "status": "active",
          "version": "1.19.12"
        },
        {
          "sha256": "ee18f98a03386e2bf48ff75737ea17c953b1572f9b1114352f104ac5eef04bb4",
          "status": "active",
          "version": "1.19.11"
        },
        {
          "sha256": "8b045a483d3895c6edba2e90a9189262876190dbbd21756870cdd63821810677",
          "status": "active",
          "version": "1.19.10"
        },
        {
          "sha256": "e858173b489ec1ddbe2374894f52f53e748feed09dde61be5b4b4ba2d73ef34b",
          "status": "active",
          "version": "1.19.9"
        },
        {
          "sha256": "e1a0bf0ab18c8218805a1003fd702a41e2e807710b770e787e5979d1cf947aba",
          "status": "active",
          "version": "1.19.8"
        },
        {
          "sha256": "7a75720c9b066ae1750f6bcc7052aba70fa3813f4223199ee2a2315fd3eb533d",
          "status": "active",
          "version": "1.19.7"
        },
        {
          "sha256": "e3410c676ced327aec928303fef11385702a5562fd19d9a1750d5a2979763c3d",
          "status": "active",
          "version": "1.19.6"
        },
        {
          "sha256": "36519702ae2fd573c9869461990ae550c8c0d955cd28d2827a6b159fda81ff95",
          "status": "active",
          "version": "1.19.5"
        },
        {
          "sha256": "c9c08f783325c4cf840a94333159cc937f05f75d36a8b307951d5bd959cf2ab8",
          "status": "active",
          "version": "1.19.4"
        },
        {
          "sha256": "74b9640724fd4e6bb0ed2a1bc44ae813a03f1e72a4c76253e2d5c015494430ba",
          "status": "active",
          "version": "1.19.3"
        },
        {
          "sha256": "5e8c5a74fe6470dd7e055a461acda8bb4050ead8c2df70f227e3ff7d8eb7eeb6",
          "status": "active",
          "version": "1.19.2"
        },
        {
          "sha256": "acc512fbab4f716a8f97a8b3fbaa9ddd39606a28be6c2515ef7c6c6311acffde",
          "status": "active",
          "version": "1.19.1"
        },
        {
          "sha256": "464b6b66591f6cf055bc5df90a9750bf5fbc9d038722bb84a9d56a2bea974be6",
          "status": "active",
          "version": "1.19"
        },
        {
          "sha256": "9130c6f8e87ce9bb4813533a68c3f17c82c7307caf8795d3c9427652b77f81aa",
          "status": "prerelease",
          "version": "1.19rc2"
        },
        {
          "sha256": "6dce5b8784149dc983ad809f6a185356ebdd143aaf3df90a942d29ccd2267303",
          "status": "prerelease",
          "version": "1.19rc1"
        },
        {
          "sha256": "7d4df5bb5f94acf23edeb5a87f962696e6c6a2ea0b58280433deea79f9a231d3",
          "status": "prerelease",
          "version": "1.19beta1"
        },
        {
          "sha256": "5e05400e4c79ef5394424c0eff5b9141cb782da25f64f79d54c98af0a37f8d49",
          "status": "active",
          "version": "1.18.10"
        },
        {
          "sha256": "015692d2a48e3496f1da3328cf33337c727c595011883f6fc74f9b5a9c86ffa8",
          "status": "active",
          "version": "1.18.9"
        },
        {
          "sha256": "4d854c7bad52d53470cf32f1b287a5c0c441dc6b98306dea27358e099698142a",
          "status": "active",
          "version": "1.18.8"
        },
        {
          "sha256": "6c967efc22152ce3124fc35cdf50fc686870120c5fd2107234d05d450a6105d8",
          "status": "active",
          "version": "1.18.7"
        },
        {
          "sha256": "bb05f179a773fed60c6a454a24141aaa7e71edfd0f2d465ad610a3b8f1dc7fe8",
          "status": "active",
          "version": "1.18.6"
        },
        {
          "sha256": "9e5de37f9c49942c601b191ac5fba404b868bfc21d446d6960acc12283d6e5f2",
          "status": "active",
          "version": "1.18.5"
        },
        {
          "sha256": "c9b099b68d93f5c5c8a8844a89f8db07eaa58270e3a1e01804f17f4cf8df02f5",
          "status": "active",
          "version": "1.18.4"
        },
        {
          "sha256": "956f8507b302ab0bb747613695cdae10af99bbd39a90cae522b7c0302cc27245",
          "status": "active",
          "version": "1.18.3"
        },
        {
          "sha256": "e54bec97a1a5d230fc2f9ad0880fcbabb5888f30ed9666eca4a91c5a32e86cbc",
          "status": "active",
          "version": "1.18.2"
        },
        {
          "sha256": "b3b815f47ababac13810fc6021eb73d65478e0b2db4b09d348eefad9581a2334",
          "status": "active",
          "version": "1.18.1"
        },
        {
          "sha256": "e85278e98f57cdb150fe8409e6e5df5343ecb13cebf03a5d5ff12bd55a80264f",
          "status": "active",
          "version": "1.18"
        },
        {
          "sha256": "9ea4e6adee711e06fa95546e1a9629b63de3aaae85fac9dc752fb533f3e5be23",
          "status": "prerelease",
          "version": "1.18rc1"
        },
        {
          "sha256": "b5dacafa59737cfb0d657902b70c2ad1b6bb4ed15e85ea2806f72ce3d4824688",
          "status": "prerelease",
          "version": "1.18beta2"
        },
        {
          "sha256": "128f72c5c22640085e4187cd1b540c587cf8fb280f941519bd2d1ae9fdab4f37",
          "status": "prerelease",
          "version": "1.18beta1"
        },
        {
          "sha256": "4cdd2bc664724dc7db94ad51b503512c5ae7220951cac568120f64f8e94399fc",
          "status": "active",
          "version": "1.17.13"
        },
        {
          "sha256": "6e5203fbdcade4aa4331e441fd2e1db8444681a6a6c72886a37ddd11caa415d4",
          "status": "active",
          "version": "1.17.12"
        },
        {
          "sha256": "d69a4fe2694f795d8e525c72b497ededc209cb7185f4c3b62d7a98dd6227b3fe",
          "status": "active",
          "version": "1.17.11"
        },
        {
          "sha256": "87fc728c9c731e2f74e4a999ef53cf07302d7ed3504b0839027bd9c10edaa3fd",
          "status": "active",
          "version": "1.17.10"
        },
        {
          "sha256": "9dacf782028fdfc79120576c872dee488b81257b1c48e9032d122cfdb379cca6",
          "status": "active",
          "version": "1.17.9"
        },
        {
          "sha256": "980e65a863377e69fd9b67df9d8395fd8e93858e7a24c9f55803421e453f4f99",
          "status": "active",
          "version": "1.17.8"
        },
        {
          "sha256": "02b111284bedbfa35a7e5b74a06082d18632eff824fd144312f6063943d49259",
          "status": "active",
          "version": "1.17.7"
        },
        {
          "sha256": "231654bbf2dab3d86c1619ce799e77b03d96f9b50770297c8f4dff8836fc8ca2",
          "status": "active",
          "version": "1.17.6"
        },
        {
          "sha256": "bd78114b0d441b029c8fe0341f4910370925a4d270a6a590668840675b0c653e",
          "status": "active",
          "version": "1.17.5"
        },
        {
          "sha256": "adab2483f644e2f8a10ae93122f0018cef525ca48d0b8764dae87cb5f4fd4206",
          "status": "active",
          "version": "1.17.4"
        },
        {
          "sha256": "550f9845451c0c94be679faf116291e7807a8d78b43149f9506c1b15eb89008c",
          "status": "active",
          "version": "1.17.3"
        },
        {
          "sha256": "f242a9db6a0ad1846de7b6d94d507915d14062660616a61ef7c808a76e4f1676",
          "status": "active",
          "version": "1.17.2"
        },
        {
          "sha256": "dab7d9c34361dc21ec237d584590d72500652e7c909bf082758fb63064fca0ef",
          "status": "active",
          "version": "1.17.1"
        },
        {
          "sha256": "6bf89fc4f5ad763871cf7eac80a2d594492de7a818303283f1366a7f6a30372d",
          "status": "active",
          "version": "1.17"
        },
        {
          "sha256": "328235edc7c7d2a51d6c6cb4d7ff97e97357654ef9e1098b9a4603a9d278ad04",
          "status": "prerelease",
          "version": "1.17rc2"
        },
        {
          "sha256": "bfbd3881a01ca3826777b1c40f241acacd45b14730d373259cd673d74e15e534",
          "status": "prerelease",
          "version": "1.17rc1"
        },
        {
          "sha256": "a479681705b65971f9db079bfce53c4393bfa241d952eb09de88fb40677d3c4c",
          "status": "prerelease",
          "version": "1.17beta1"
        },
        {
          "sha256": "77c782a633186d78c384f972fb113a43c24be0234c42fef22c2d8c4c4c8e7475",
          "status": "active",
          "version": "1.16.15"
        },
        {
          "sha256": "f4f5f02eb6809ac5bf19b5ad517b23504fd5fc036f6487651968ad36aa7a20e0",
          "status": "active",
          "version": "1.16.14"
        },
        {
          "sha256": "275fc03c90c13b0bbff13125a43f1f7a9f9c00a0d5a9f2d5b16dbc2fa2c6e12a",
          "status": "active",
          "version": "1.16.13"
        },
        {
          "sha256": "7d657e86493ac1d5892f340a7d88b862b12edb5ac6e73c099e8e0668a6c916b7",
          "status": "active",
          "version": "1.16.12"
        },
        {
          "sha256": "aa22d0e2be68c0a7027a64e76cbb2869332fbc42ce14e3d10b69007b51030775",
          "status": "active",
          "version": "1.16.11"
        },
        {
          "sha256": "414cd18ce1d193769b9e97d2401ad718755ab47816e13b2a1cde203d263b55cf",
          "status": "active",
          "version": "1.16.10"
        },
        {
          "sha256": "d2c095c95f63c2a3ef961000e0ecb9d81d5c68b6ece176e2a8a2db82dc02931c",
          "status": "active",
          "version": "1.16.9"
        },
        {
          "sha256": "f32501aeb8b7b723bc7215f6c373abb6981bbc7e1c7b44e9f07317e1a300dce2",
          "status": "active",
          "version": "1.16.8"
        },
        {
          "sha256": "7fe7a73f55ba3e2285da36f8b085e5c0159e9564ef5f63ee0ed6b818ade8ef04",
          "status": "active",
          "version": "1.16.7"
        },
        {
          "sha256": "be333ef18b3016e9d7cb7b1ff1fdb0cac800ca0be4cf2290fe613b3d069dfe0d",
          "status": "active",
          "version": "1.16.6"
        },
        {
          "sha256": "b12c23023b68de22f74c0524f10b753e7b08b1504cb7e417eccebdd3fae49061",
          "status": "active",
          "version": "1.16.5"
        },
        {
          "sha256": "7154e88f5a8047aad4b80ebace58a059e36e7e2e4eb3b383127a28c711b4ff59",
          "status": "active",
          "version": "1.16.4"
        },
        {
          "sha256": "951a3c7c6ce4e56ad883f97d9db74d3d6d80d5fec77455c6ada6c1f7ac4776d2",
          "status": "active",
          "version": "1.16.3"
        },
        {
          "sha256": "542e936b19542e62679766194364f45141fde55169db2d8d01046555ca9eb4b8",
          "status": "active",
          "version": "1.16.2"
        },
        {
          "sha256": "3edc22f8332231c3ba8be246f184b736b8d28f06ce24f08168d8ecf052549769",
          "status": "active",
          "version": "1.16.1"
        },
        {
          "sha256": "013a489ebb3e24ef3d915abe5b94c3286c070dfe0818d5bca8108f1d6e8440d2",
          "status": "active",
          "version": "1.16"
        },
        {
          "sha256": "6a62610f56a04bae8702cd2bd73bfea34645c1b89ded3f0b81a841393b6f1f14",
          "status": "prerelease",
          "version": "1.16rc1"
        },
        {
          "sha256": "3931a0d493d411d6c697df6f15d5292fdd8031fde7014fded399effdad4c12d8",
          "status": "prerelease",
          "version": "1.16beta1"
        },
        {
          "sha256": "0885cf046a9f099e260d98d9ec5d19ea9328f34c8dc4956e1d3cd87daaddb345",
          "status": "active",
          "version": "1.15.15"
        },
        {
          "sha256": "6f5410c113b803f437d7a1ee6f8f124100e536cc7361920f7e640fedf7add72d",
          "status": "active",
          "version": "1.15.14"
        },
        {
          "sha256": "3d3beec5fc66659018e09f40abb7274b10794229ba7c1e8bdb7d8ca77b656a13",
          "status": "active",
          "version": "1.15.13"
        },
        {
          "sha256": "bbdb935699e0b24d90e2451346da76121b2412d30930eabcd80907c230d098b7",
          "status": "active",
          "version": "1.15.12"
        },
        {
          "sha256": "8825b72d74b14e82b54ba3697813772eb94add3abf70f021b6bdebe193ed01ec",
          "status": "active",
          "version": "1.15.11"
        },
        {
          "sha256": "4aa1267517df32f2bf1cc3d55dfc27d0c6b2c2b0989449c96dd19273ccca051d",
          "status": "active",
          "version": "1.15.10"
        },
        {
          "sha256": "a55f3e75bc1098045851d40ea74f9d77efc7958e9af85131a96ca387d38b1834",
          "status": "active",
          "version": "1.15.9"
        },
        {
          "sha256": "d3379c32a90fdf9382166f8f48034c459a8cc433730bc9476d39d9082c94583b",
          "status": "active",
          "version": "1.15.8"
        },
        {
          "sha256": "0d142143794721bb63ce6c8a6180c4062bcf8ef4715e7d6d6609f3a8282629b3",
          "status": "active",
          "version": "1.15.7"
        },
        {
          "sha256": "3918e6cc85e7eaaa6f859f1bdbaac772e7a825b0eb423c63d3ae68b21f84b844",
          "status": "active",
          "version": "1.15.6"
        },
        {
          "sha256": "9a58494e8da722c3aef248c9227b0e9c528c7318309827780f16220998180a0d",
          "status": "active",
          "version": "1.15.5"
        },
        {
          "sha256": "eb61005f0b932c93b424a3a4eaa67d72196c79129d9a3ea8578047683e2c80d5",
          "status": "active",
          "version": "1.15.4"
        },
        {
          "sha256": "010a88df924a81ec21b293b5da8f9b11c176d27c0ee3962dc1738d2352d3c02d",
          "status": "active",
          "version": "1.15.3"
        },
        {
          "sha256": "b49fda1ca29a1946d6bb2a5a6982cf07ccd2aba849289508ee0f9918f6bb4552",
          "status": "active",
          "version": "1.15.2"
        },
        {
          "sha256": "70ac0dbf60a8ee9236f337ed0daa7a4c3b98f6186d4497826f68e97c0c0413f6",
          "status": "active",
          "version": "1.15.1"
        },
        {
          "sha256": "2d75848ac606061efe52a8068d0e647b35ce487a15bb52272c427df485193602",
          "status": "active",
          "version": "1.15"
        },
        {
          "sha256": "f41a08f630f018bc5d9fd100bd9899516e4965356c78165157eb0eda9a17ac09",
          "status": "prerelease",
          "version": "1.15rc2"
        },
        {
          "sha256": "ac092ebb92f88366786063e68a9531d5eccac51371f9becb128f064721731b2e",
          "status": "prerelease",
          "version": "1.15rc1"
        },
        {
          "sha256": "11814b7475680a09720f3de32c66bca135289c8d528b2e1132b0ce56b3d9d6d7",
          "status": "prerelease",
          "version": "1.15beta1"
        },
        {
          "sha256": "c64a57b374a81f7cf1408d2c410a28c6f142414f1ffa9d1062de1d653b0ae0d6",
          "status": "active",
          "version": "1.14.15"
        },
        {
          "sha256": "6f1354c9040d65d1622b451f43c324c1e5197aa9242d00c5a117d0e2625f3e0d",
          "status": "active",
          "version": "1.14.14"
        },
        {
          "sha256": "bfea0c8d7b70c1ad99b0266b321608db57df75820e8f4333efa448a43da01992",
          "status": "active",
          "version": "1.14.13"
        },
        {
          "sha256": "fb26f951c88c0685d7df393611189c58e6eabd3c17bdaef37df11355ab8db9d3",
          "status": "active",
          "version": "1.14.12"
        },
        {
          "sha256": "ef150041e1af0890ecdd98ebdd6c759096884052a584c09ce50b2b5bb9bab2cd",
          "status": "active",
          "version": "1.14.11"
        },
        {
          "sha256": "66eb6858f375731ba07b0b33f5c813b141a81253e7e74071eec3ae85e9b37098",
          "status": "active",
          "version": "1.14.10"
        },
        {
          "sha256": "f0d26ff572c72c9823ae752d3c81819a81a60c753201f51f89637482531c110a",
          "status": "active",
          "version": "1.14.9"
        },
        {
          "sha256": "5504e077a29d0bd6649ca7b66e317f1a4b264e960f74115d6f0f405c49a8e738",
          "status": "active",
          "version": "1.14.8"
        },
        {
          "sha256": "4a7fa60f323ee1416a4b1425aefc37ea359e9d64df19c326a58953a97ad41ea5",
          "status": "active",
          "version": "1.14.7"
        },
        {
          "sha256": "5c566ddc2e0bcfc25c26a5dc44a440fcc0177f7350c1f01952b34d5989a0d287",
          "status": "active",
          "version": "1.14.6"
        },
        {
          "sha256": "82a1b84f16858db03231eb201f90cce2a991078dda543879b87e738e2586854b",
          "status": "active",
          "version": "1.14.5"
        },
        {
          "sha256": "aed845e4185a0b2a3c3d5e1d0a35491702c55889192bb9c30e67a3de6849c067",
          "status": "active",
          "version": "1.14.4"
        },
        {
          "sha256": "1c39eac4ae95781b066c144c58e45d6859652247f7515f0d2cba7be7d57d2226",
          "status": "active",
          "version": "1.14.3"
        },
        {
          "sha256": "6272d6e940ecb71ea5636ddb5fab3933e087c1356173c61f4a803895e947ebb3",
          "status": "active",
          "version": "1.14.2"
        },
        {
          "sha256": "2f49eb17ce8b48c680cdb166ffd7389702c0dec6effa090c324804a5cac8a7f8",
          "status": "active",
          "version": "1.14.1"
        },
        {
          "sha256": "08df79b46b0adf498ea9f320a0f23d6ec59e9003660b4c9c1ce8e5e2c6f823ca",
          "status": "active",
          "version": "1.14"
        },
        {
          "sha256": "69398d41e5f6b87cdf3969aae665be4dfd3cc2ef36a61ab47a261f96130ed788",
          "status": "prerelease",
          "version": "1.14rc1"
        },
        {
          "sha256": "ebe68aa4219b673dbd060b8a6d9a339b6b6b0383772aa4349c8183f0a8f339e4",
          "status": "prerelease",
          "version": "1.14beta1"
        },
        {
          "sha256": "01cc3ddf6273900eba3e2bf311238828b7168b822bb57a9ccab4d7aa2acd6028",
          "status": "active",
          "version": "1.13.15"
        },
        {
          "sha256": "32617db984b18308f2b00279c763bff060d2739229cb8037217a49c9e691b46a",
          "status": "active",
          "version": "1.13.14"
        },
        {
          "sha256": "0b8573c2335bebef53e819ab8d323456dc2b94838bebdbd8cc6623bb8a6d77b7",
          "status": "active",
          "version": "1.13.13"
        },
        {
          "sha256": "9cacc6653563771b458c13056265aa0c21b8a23ca9408278484e4efde4160618",
          "status": "active",
          "version": "1.13.12"
        },
        {
          "sha256": "a4d71ca9e02923fa96669a4b5faf78ee8331b18e7209b09dd87fe763b4838ada",
          "status": "active",
          "version": "1.13.11"
        },
        {
          "sha256": "8a4cbc9f2b95d114c38f6cbe94a45372d48c604b707db2057c787398dfbf8e7f",
          "status": "active",
          "version": "1.13.10"
        },
        {
          "sha256": "f4ad8180dd0aaf7d7cda7e2b0a2bf27e84131320896d376549a7d849ecf237d7",
          "status": "active",
          "version": "1.13.9"
        },
        {
          "sha256": "0567734d558aef19112f2b2873caa0c600f1b4a5827930eb5a7f35235219e9d8",
          "status": "active",
          "version": "1.13.8"
        },
        {
          "sha256": "b3dd4bd781a0271b33168e627f7f43886b4c5d1c794a4015abf34e99c6526ca3",
          "status": "active",
          "version": "1.13.7"
        },
        {
          "sha256": "a1bc06deb070155c4f67c579f896a45eeda5a8fa54f35ba233304074c4abbbbd",
          "status": "active",
          "version": "1.13.6"
        },
        {
          "sha256": "512103d7ad296467814a6e3f635631bd35574cab3369a97a323c9a585ccaa569",
          "status": "active",
          "version": "1.13.5"
        },
        {
          "sha256": "692d17071736f74be04a72a06dab9cac1cd759377bd85316e52b2227604c004c",
          "status": "active",
          "version": "1.13.4"
        },
        {
          "sha256": "0804bf02020dceaa8a7d7275ee79f7a142f1996bfd0c39216ccb405f93f994c0",
          "status": "active",
          "version": "1.13.3"
        },
        {
          "sha256": "293b41a6ccd735eebcfb4094b6931bfd187595555cecf3e4386e9e119220c0b7",
          "status": "active",
          "version": "1.13.2"
        },
        {
          "sha256": "94f874037b82ea5353f4061e543681a0e79657f787437974214629af8407d124",
          "status": "active",
          "version": "1.13.1"
        },
        {
          "sha256": "68a2297eb099d1a76097905a2ce334e3155004ec08cdea85f24527be3c48e856",
          "status": "active",
          "version": "1.13"
        },
        {
          "sha256": "3cd4490021a5f1f25a7440edca03910e40a38e587b578cf52ab7143a81db1861",
          "status": "prerelease",
          "version": "1.13rc2"
        },
        {
          "sha256": "0b45d086aefcfb9d0ebe7fc9ffbe470e45f9c104a6a97ea275512152cdbfead1",
          "status": "prerelease",
          "version": "1.13rc1"
        },
        {
          "sha256": "dbd131c92f381a5bc5ca1f0cfd942cb8be7d537007b6f412b5be41ff38a7d0d9",
          "status": "prerelease",
          "version": "1.13beta1"
        },
        {
          "sha256": "a53dd476129d496047487bfd53d021dd17e0c96895865a0e7d0469ce3db8c8d2",
          "status": "active",
          "version": "1.12.17"
        },
        {
          "sha256": "bf3a85d75658144c06ce986ba05e07ef08af4320089b74b1d41de3b0f340ea7e",
          "status": "active",
          "version": "1.12.16"
        },
        {
          "sha256": "61068419f3d3fcd3cc415c352c4a93d6ae0e723ac18a22ac572b4904d78b5a4c",
          "status": "active",
          "version": "1.12.15"
        },
        {
          "sha256": "925a1a9d8b31c2425d7313fe73d3342288968a66e26cd8bf1b6b5656f4603fcb",
          "status": "active",
          "version": "1.12.14"
        },
        {
          "sha256": "da036454cb3353f9f507f0ceed4048feac611065e4e1818b434365eb32ac9bdc",
          "status": "active",
          "version": "1.12.13"
        },
        {
          "sha256": "4cf11ac6a8fa42d26ab85e27a5d916ee171900a87745d9f7d4a29a21587d78fc",
          "status": "active",
          "version": "1.12.12"
        },
        {
          "sha256": "2c5960292da8b747d83f171a28a04116b2977e809169c344268c893e4cf0a857",
          "status": "active",
          "version": "1.12.11"
        },
        {
          "sha256": "aaa84147433aed24e70b31da369bb6ca2859464a45de47c2a5023d8573412f6b",
          "status": "active",
          "version": "1.12.10"
        },
        {
          "sha256": "ac2a6efcc1f5ec8bdc0db0a988bb1d301d64b6d61b7e8d9e42f662fbb75a2b9b",
          "status": "active",
          "version": "1.12.9"
        },
        {
          "sha256": "bd26cd4962a362ed3c11835bca32c2e131c2ae050304f2c4df9fa6ded8db85d2",
          "status": "active",
          "version": "1.12.8"
        },
        {
          "sha256": "66d83bfb5a9ede000e33c6579a91a29e6b101829ad41fffb5c5bb6c900e109d9",
          "status": "active",
          "version": "1.12.7"
        },
        {
          "sha256": "dbcf71a3c1ea53b8d54ef1b48c85a39a6c9a935d01fc8291ff2b92028e59913c",
          "status": "active",
          "version": "1.12.6"
        },
        {
          "sha256": "aea86e3c73495f205929cfebba0d63f1382c8ac59be081b6351681415f4063cf",
          "status": "active",
          "version": "1.12.5"
        },
        {
          "sha256": "d7d1f1f88ddfe55840712dc1747f37a790cbcaa448f6c9cf51bbe10aa65442f5",
          "status": "active",
          "version": "1.12.4"
        },
        {
          "sha256": "3924819eed16e55114f02d25d03e77c916ec40b7fd15c8acb5838b63135b03df",
          "status": "active",
          "version": "1.12.3"
        },
        {
          "sha256": "f28c1fde8f293cc5c83ae8de76373cf76ae9306909564f54e0edcf140ce8fe3f",
          "status": "active",
          "version": "1.12.2"
        },
        {
          "sha256": "2a3fdabf665496a0db5f41ec6af7a9b15a49fbe71a85a50ca38b1f13a103aeec",
          "status": "active",
          "version": "1.12.1"
        },
        {
          "sha256": "750a07fef8579ae4839458701f4df690e0b20b8bcce33b437e4df89c451b6f13",
          "status": "active",
          "version": "1.12"
        },
        {
          "sha256": "e5a03e1f2e065b17b2fbbd3429f18a6f51fe2848e0120586652b9f14ada72c9a",
          "status": "prerelease",
          "version": "1.12rc1"
        },
        {
          "sha256": "9e4884b46a72e0558187a8af6e8733e039432df1b755f14b361f18b63fa5a63e",
          "status": "prerelease",
          "version": "1.12beta2"
        },
        {
          "sha256": "65bfd4a99925f1f85d712f4c1109977aa24ee4c6e198162bf8e819fdde19e875",
          "status": "prerelease",
          "version": "1.12beta1"
        },
        {
          "sha256": "50fe8e13592f8cf22304b9c4adfc11849a2c3d281b1d7e09c924ae24874c6daa",
          "status": "active",
          "version": "1.11.13"
        },
        {
          "sha256": "14ec881815eb9e6618f95df5eb385d961283efc196d97912595ba6484a56180d",
          "status": "active",
          "version": "1.11.12"
        },
        {
          "sha256": "2fd47b824d6e32154b0f6c8742d066d816667715763e06cebb710304b195c775",
          "status": "active",
          "version": "1.11.11"
        },
        {
          "sha256": "aefaa228b68641e266d1f23f1d95dba33f17552ba132878b65bb798ffa37e6d0",
          "status": "active",
          "version": "1.11.10"
        },
        {
          "sha256": "e88aa3e39104e3ba6a95a4e05629348b4a1ec82791fb3c941a493ca349730608",
          "status": "active",
          "version": "1.11.9"
        },
        {
          "sha256": "e32ab1c934b747999d04e8a550b97f4647f8b1b43e152de5650d4476bfd1d2e1",
          "status": "active",
          "version": "1.11.8"
        },
        {
          "sha256": "db687814288b3b541c1754dfd4ecc2b8fd0d5e7995624945e3054a350ca573d8",
          "status": "active",
          "version": "1.11.7"
        },
        {
          "sha256": "4e1864282d8d20010d6385a12a1e35641783a380a7c57907bfb46a5499c5eb49",
          "status": "active",
          "version": "1.11.6"
        },
        {
          "sha256": "ff54aafedff961eb94792487e827515da683d61a5f9482f668008832631e5d25",
          "status": "active",
          "version": "1.11.5"
        },
        {
          "sha256": "fb26c30e6a04ad937bbc657a1b5bba92f80096af1e8ee6da6430c045a8db3a5b",
          "status": "active",
          "version": "1.11.4"
        },
        {
          "sha256": "d20a4869ffb13cee0f7ee777bf18c7b9b67ef0375f93fac1298519e0c227a07f",
          "status": "active",
          "version": "1.11.3"
        },
        {
          "sha256": "1dfe664fa3d8ad714bbd15a36627992effd150ddabd7523931f077b3926d736d",
          "status": "active",
          "version": "1.11.2"
        },
        {
          "sha256": "2871270d8ff0c8c69f161aaae42f9f28739855ff5c5204752a8d92a1c9f63993",
          "status": "active",
          "version": "1.11.1"
        },
        {
          "sha256": "b3fcf280ff86558e0559e185b601c9eade0fd24c900b4c63cd14d1d38613e499",
          "status": "active",
          "version": "1.11"
        },
        {
          "sha256": "7d3fc1dec64b056cbd22ffd80bb9733725c1296aabfd58cc92bab8a5c6560e03",
          "status": "prerelease",
          "version": "1.11rc2"
        },
        {
          "sha256": "1a071f069982427b245aea736d3174e065a12e8481c34051c672d62a5ca59ca9",
          "status": "prerelease",
          "version": "1.11rc1"
        },
        {
          "sha256": "674c1091f4712c1cfdcd77ecddafe6aef81cbda740af64a6e3f893ddf3dfb11c",
          "status": "prerelease",
          "version": "1.11beta3"
        },
        {
          "sha256": "ccb60f1ae6efe4fcef115db8143eb7f9ba134c63486f47b2c5176706ede35af5",
          "status": "prerelease",
          "version": "1.11beta2"
        },
        {
          "sha256": "df7fe096ffab5d331d35c6d038d2ec0426b45ce17f55a93037e371d3af9d4e6d",
          "status": "prerelease",
          "version": "1.11beta1"
        },
        {
          "sha256": "d8626fb6f9a3ab397d88c483b576be41fa81eefcec2fd18562c87626dbb3c39e",
          "status": "active",
          "version": "1.10.8"
        },
        {
          "sha256": "1aabe10919048822f3bb1865f7a22f8b78387a12c03cd573101594bc8fb33579",
          "status": "active",
          "version": "1.10.7"
        },
        {
          "sha256": "acbdedf28b55b38d2db6f06209a25a869a36d31bdcf09fd2ec3d40e1279e0592",
          "status": "active",
          "version": "1.10.6"
        },
        {
          "sha256": "a035d9beda8341b645d3f45a1b620cf2d8fb0c5eb409be36b389c0fd384ecc3a",
          "status": "active",
          "version": "1.10.5"
        },
        {
          "sha256": "fa04efdb17a275a0c6e137f969a1c4eb878939e91e1da16060ce42f02c2ec5ec",
          "status": "active",
          "version": "1.10.4"
        },
        {
          "sha256": "fa1b0e45d3b647c252f51f5e1204aba049cde4af177ef9f2181f43004f901035",
          "status": "active",
          "version": "1.10.3"
        },
        {
          "sha256": "4b677d698c65370afa33757b6954ade60347aaca310ea92a63ed717d7cb0c2ff",
          "status": "active",
          "version": "1.10.2"
        },
        {
          "sha256": "72d820dec546752e5a8303b33b009079c15c2390ce76d67cf514991646c6127b",
          "status": "active",
          "version": "1.10.1"
        },
        {
          "sha256": "b5a64335f1490277b585832d1f6c7f8c6c11206cba5cd3f771dcb87b98ad1a33",
          "status": "active",
          "version": "1.10"
        },
        {
          "sha256": "6a6a4c0654bc603bcfee4d6ac34a479c260ac61b3edcc8d6773384eb0bda512e",
          "status": "prerelease",
          "version": "1.10rc2"
        },
        {
          "sha256": "c10d3cc7760bf3799037bd39027bbffdc568aea21d6fe60fe833373289c7b7c6",
          "status": "prerelease",
          "version": "1.10rc1"
        },
        {
          "sha256": "ab3abb7d731dd5ac7a06d5d5e64ef19946f57d4ce34555d262a87b8899901a93",
          "status": "prerelease",
          "version": "1.10beta2"
        },
        {
          "sha256": "ec7a10b5bf147a8e06cf64e27384ff3c6d065c74ebd8fdd31f572714f74a1055",
          "status": "prerelease",
          "version": "1.10beta1"
        },
        {
          "sha256": "88573008f4f6233b81f81d8ccf92234b4f67238df0f0ab173d75a302a1f3d6ee",
          "status": "active",
          "version": "1.9.7"
        },
        {
          "sha256": "d1eb07f99ac06906225ac2b296503f06cc257b472e7d7817b8f822fe3766ebfe",
          "status": "active",
          "version": "1.9.6"
        },
        {
          "sha256": "d21bdabf4272c2248c41b45cec606844bdc5c7c04240899bde36c01a28c51ee7",
          "status": "active",
          "version": "1.9.5"
        },
        {
          "sha256": "15b0937615809f87321a457bb1265f946f9f6e736c563d6c5e0bd2c22e44f779",
          "status": "active",
          "version": "1.9.4"
        },
        {
          "sha256": "a4da5f4c07dfda8194c4621611aeb7ceaab98af0b38bfb29e1be2ebb04c3556c",
          "status": "active",
          "version": "1.9.3"
        },
        {
          "sha256": "de874549d9a8d8d8062be05808509c09a88a248e77ec14eb77453530829ac02b",
          "status": "active",
          "version": "1.9.2"
        },
        {
          "sha256": "bf28294bc9ac1fe2102a139c49b52d3947953a7aaa2cd52e6bb9772d25611faa",
          "status": "prerelease",
          "version": "1.9.2rc2"
        },
        {
          "sha256": "07d81c6b6b4c2dcf1b5ef7c27aaebd3691cdb40548500941f92b221147c5d9c7",
          "status": "active",
          "version": "1.9.1"
        },
        {
          "sha256": "d70eadefce8e160638a9a6db97f7192d8463069ab33138893ad3bf31b0650a79",
          "status": "active",
          "version": "1.9"
        },
        {
          "sha256": "0d17d440f02505d8fbf6becb777175c242486c1d71046705876dcd20e0574002",
          "status": "prerelease",
          "version": "1.9rc2"
        },
        {
          "sha256": "a8ea2ac09878b7a5ac04fe52f144cdc64ab637230638af6975c0f1facbba3ec2",
          "status": "prerelease",
          "version": "1.9rc1"
        },
        {
          "sha256": "023f778f063d2234e7c95f572a92298b307807693f7e045a88c90ecd7a08f29d",
          "status": "prerelease",
          "version": "1.9beta2"
        },
        {
          "sha256": "85719a2c704ad1352052e185c760d7c65b9d8a18b491287a7e5f6775ccc27d3b",
          "status": "prerelease",
          "version": "1.9beta1"
        },
        {
          "sha256": "de32e8db3dc030e1448a6ca52d87a1e04ad31c6b212007616cfcc87beb0e4d60",
          "status": "active",
          "version": "1.8.7"
        },
        {
          "sha256": "f558c91c2f6aac7222e0bd83e6dd595b8fac85aaa96e55d15229542eb4aaa1ff",
          "status": "active",
          "version": "1.8.6"
        },
        {
          "sha256": "4f8aeea2033a2d731f2f75c4d0a4995b357b22af56ed69b3015f4291fca4d42d",
          "status": "active",
          "version": "1.8.5"
        },
        {
          "sha256": "0ef737a0aff9742af0f63ac13c97ce36f0bbc8b67385169e41e395f34170944f",
          "status": "active",
          "version": "1.8.4"
        },
        {
          "sha256": "1862f4c3d3907e59b04a757cfda0ea7aa9ef39274af99a784f5be843c80c6772",
          "status": "active",
          "version": "1.8.3"
        },
        {
          "sha256": "5477d6c9a4f96fa120847fafa88319d7b56b5d5068e41c3587eebe248b939be7",
          "status": "active",
          "version": "1.8.2"
        },
        {
          "sha256": "a579ab19d5237e263254f1eac5352efcf1d70b9dacadb6d6bb12b0911ede8994",
          "status": "active",
          "version": "1.8.1"
        },
        {
          "sha256": "53ab94104ee3923e228a2cb2116e5e462ad3ebaeea06ff04463479d7f12d27ca",
          "status": "active",
          "version": "1.8"
        },
        {
          "sha256": "0ff3faba02ac83920a65b453785771e75f128fbf9ba4ad1d5e72c044103f9c7a",
          "status": "prerelease",
          "version": "1.8rc3"
        },
        {
          "sha256": "d62c2d44d0c6b434e3cda12505f3c9fb880757e3396af1e9ba861f7b547cc864",
          "status": "prerelease",
          "version": "1.8rc2"
        },
        {
          "sha256": "bb8fe0d81161e4a8b0a8b2145ee5f8a60370baf5d48c07a83f6f09e1ad253bec",
          "status": "prerelease",
          "version": "1.8rc1"
        },
        {
          "sha256": "4cb9bfb0e82d665871b84070929d6eeb4d51af6bedbc8fdd3df5766e937ef84c",
          "status": "prerelease",
          "version": "1.8beta2"
        },
        {
          "sha256": "768d8d73ccea69c9a0941f9ef2333b1ff8c82120abfcdedd4e91af039c674a8d",
          "status": "prerelease",
          "version": "1.8beta1"
        },
        {
          "sha256": "ad5808bf42b014c22dd7646458f631385003049ded0bb6af2efc7f1f79fa29ea",
          "status": "active",
          "version": "1.7.6"
        },
        {
          "sha256": "2e4dd6c44f0693bef4e7b46cc701513d74c3cc44f2419bf519d7868b12931ac3",
          "status": "active",
          "version": "1.7.5"
        },
        {
          "sha256": "47fda42e46b4c3ec93fa5d4d4cc6a748aa3f9411a2a2b7e08e3a6d80d753ec8b",
          "status": "active",
          "version": "1.7.4"
        },
        {
          "sha256": "508028aac0654e993564b6e2014bf2d4a9751e3b286661b0b0040046cf18028e",
          "status": "active",
          "version": "1.7.3"
        },
        {
          "sha256": "43ad621c9b014cde8db17393dc108378d37bc853aa351a6c74bf6432c1bbd182",
          "status": "active",
          "version": "1.7.1"
        },
        {
          "sha256": "702ad90f705365227e902b42d91dd1a40e48ca7f67a2f4b2fd052aaa4295cd95",
          "status": "active",
          "version": "1.7"
        },
        {
          "sha256": "45e3dfba542927ea58146a5d47a983feb36401ccafeea28a9e0a79534738b154",
          "status": "prerelease",
          "version": "1.7rc6"
        },
        {
          "sha256": "2ddf9f553aefe91d96dd3f13be55159869a221fd0111cd211dccf2cab3ee5e4a",
          "status": "prerelease",
          "version": "1.7rc5"
        },
        {
          "sha256": "b75fa3bd2159754c404e3c83ba333d1ea80cb74de382b409afa6996abf0cc48a",
          "status": "prerelease",
          "version": "1.7rc4"
        },
        {
          "sha256": "53393c132223415c30ef877cb5c900d989f8a953e864e1119aeaedbca1918144",
          "status": "prerelease",
          "version": "1.7rc3"
        },
        {
          "sha256": "145e486499d349757cbb7ae8dfeeea5d7a76f146f6c8880173fe3d0aacc5dd42",
          "status": "prerelease",
          "version": "1.7rc2"
        },
        {
          "sha256": "afe956b6d323c68fbd851f4e962f26f16dde61d7caa1de1a8408c7de0b6034aa",
          "status": "prerelease",
          "version": "1.7rc1"
        },
        {
          "sha256": "688f895b51def9e065fb2610ff91afcb2b0d9637233b74130c8ca331d35d5ca5",
          "status": "prerelease",
          "version": "1.7beta2"
        },
        {
          "sha256": "a55e718935e2be1d5b920ed262fd06885d2d7fc4eab7722aa02c205d80532e3b",
          "status": "prerelease",
          "version": "1.7beta1"
        },
        {
          "sha256": "b58bf5cede40b21812dfa031258db18fc39746cc0972bc26dae0393acc377aaf",
          "status": "active",
          "version": "1.6.4"
        },
        {
          "sha256": "cdde5e08530c0579255d6153b08fdb3b8e47caabbe717bc7bcd7561275a87aeb",
          "status": "active",
          "version": "1.6.3"
        },
        {
          "sha256": "e40c36ae71756198478624ed1bb4ce17597b3c19d243f3f0899bb5740d56212a",
          "status": "active",
          "version": "1.6.2"
        },
        {
          "sha256": "6d894da8b4ad3f7f6c295db0d73ccc3646bce630e1c43e662a0120681d47e988",
          "status": "active",
          "version": "1.6.1"
        },
        {
          "sha256": "5470eac05d273c74ff8bac7bef5bad0b5abbd1c4052efbdbc8db45332e836b0b",
          "status": "active",
          "version": "1.6"
        },
        {
          "sha256": "9c19fa0fe32ee9bff79123d47147a5fd15fec451806bf5644a01173a86a8a4b9",
          "status": "prerelease",
          "version": "1.6rc2"
        },
        {
          "sha256": "6a8aeab9548faf933a66dafeb809bd8623c5bba1ca9626c2f28ef619b5723218",
          "status": "prerelease",
          "version": "1.6rc1"
        },
        {
          "sha256": "7ddf9797c7baaac2c16eed1a8d42f9a446223301c7dc8771ea805f211828e6a5",
          "status": "prerelease",
          "version": "1.6beta2"
        },
        {
          "sha256": "a3358721210787dc1e06f5ea1460ae0564f22a0fbd91be9dcd947fb1d19b9560",
          "status": "active",
          "version": "1.5.4"
        },
        {
          "sha256": "43afe0c5017e502630b1aea4d44b8a7f059bf60d7f29dfd58db454d4e4e0ae53",
          "status": "active",
          "version": "1.5.3"
        }
      ]
    },
    "python": {
      "defaults": {
        "version": "cpython@3.13.13"
      },
      "versions": [
        {
          "implementation": "cpython",
          "label": "CPython 3.15.0b1 preview",
          "minor": "3.15",
          "request": "cpython@3.15.0b1",
          "status": "preview",
          "uv_key": "cpython-3.15.0b1-linux-x86_64-gnu",
          "variant": "default",
          "version": "3.15.0b1"
        },
        {
          "implementation": "cpython",
          "label": "CPython 3.15.0b1 free-threaded preview",
          "minor": "3.15",
          "request": "cpython@3.15.0b1+freethreaded",
          "status": "preview",
          "uv_key": "cpython-3.15.0b1+freethreaded-linux-x86_64-gnu",
          "variant": "freethreaded",
          "version": "3.15.0b1"
        },
        {
          "implementation": "cpython",
          "label": "CPython 3.14.5",
          "minor": "3.14",
          "request": "cpython@3.14.5",
          "status": "supported",
          "uv_key": "cpython-3.14.5-linux-x86_64-gnu",
          "variant": "default",
          "version": "3.14.5"
        },
        {
          "implementation": "cpython",
          "label": "CPython 3.14.5 free-threaded",
          "minor": "3.14",
          "request": "cpython@3.14.5+freethreaded",
          "status": "supported",
          "uv_key": "cpython-3.14.5+freethreaded-linux-x86_64-gnu",
          "variant": "freethreaded",
          "version": "3.14.5"
        },
        {
          "implementation": "cpython",
          "label": "CPython 3.13.13",
          "minor": "3.13",
          "request": "cpython@3.13.13",
          "status": "active",
          "uv_key": "cpython-3.13.13-linux-x86_64-gnu",
          "variant": "default",
          "version": "3.13.13"
        },
        {
          "implementation": "cpython",
          "label": "CPython 3.13.13 free-threaded",
          "minor": "3.13",
          "request": "cpython@3.13.13+freethreaded",
          "status": "active",
          "uv_key": "cpython-3.13.13+freethreaded-linux-x86_64-gnu",
          "variant": "freethreaded",
          "version": "3.13.13"
        },
        {
          "implementation": "cpython",
          "label": "CPython 3.12.13",
          "minor": "3.12",
          "request": "cpython@3.12.13",
          "status": "supported",
          "uv_key": "cpython-3.12.13-linux-x86_64-gnu",
          "variant": "default",
          "version": "3.12.13"
        },
        {
          "implementation": "graalpy",
          "label": "GraalPy 3.12.0",
          "minor": "3.12",
          "request": "graalpy@3.12.0",
          "status": "supported",
          "uv_key": "graalpy-3.12.0-linux-x86_64-gnu",
          "variant": "default",
          "version": "3.12.0"
        },
        {
          "implementation": "cpython",
          "label": "CPython 3.11.15",
          "minor": "3.11",
          "request": "cpython@3.11.15",
          "status": "supported",
          "uv_key": "cpython-3.11.15-linux-x86_64-gnu",
          "variant": "default",
          "version": "3.11.15"
        },
        {
          "implementation": "pypy",
          "label": "PyPy 3.11.15",
          "minor": "3.11",
          "request": "pypy@3.11.15",
          "status": "supported",
          "uv_key": "pypy-3.11.15-linux-x86_64-gnu",
          "variant": "default",
          "version": "3.11.15"
        },
        {
          "implementation": "graalpy",
          "label": "GraalPy 3.11.0",
          "minor": "3.11",
          "request": "graalpy@3.11.0",
          "status": "supported",
          "uv_key": "graalpy-3.11.0-linux-x86_64-gnu",
          "variant": "default",
          "version": "3.11.0"
        },
        {
          "implementation": "cpython",
          "label": "CPython 3.10.20",
          "minor": "3.10",
          "request": "cpython@3.10.20",
          "status": "legacy",
          "uv_key": "cpython-3.10.20-linux-x86_64-gnu",
          "variant": "default",
          "version": "3.10.20"
        },
        {
          "implementation": "pypy",
          "label": "PyPy 3.10.16",
          "minor": "3.10",
          "request": "pypy@3.10.16",
          "status": "supported",
          "uv_key": "pypy-3.10.16-linux-x86_64-gnu",
          "variant": "default",
          "version": "3.10.16"
        },
        {
          "implementation": "graalpy",
          "label": "GraalPy 3.10.0",
          "minor": "3.10",
          "request": "graalpy@3.10.0",
          "status": "supported",
          "uv_key": "graalpy-3.10.0-linux-x86_64-gnu",
          "variant": "default",
          "version": "3.10.0"
        },
        {
          "implementation": "cpython",
          "label": "CPython 3.9.25",
          "minor": "3.9",
          "request": "cpython@3.9.25",
          "status": "legacy",
          "uv_key": "cpython-3.9.25-linux-x86_64-gnu",
          "variant": "default",
          "version": "3.9.25"
        },
        {
          "implementation": "pypy",
          "label": "PyPy 3.9.19",
          "minor": "3.9",
          "request": "pypy@3.9.19",
          "status": "supported",
          "uv_key": "pypy-3.9.19-linux-x86_64-gnu",
          "variant": "default",
          "version": "3.9.19"
        },
        {
          "implementation": "cpython",
          "label": "CPython 3.8.20",
          "minor": "3.8",
          "request": "cpython@3.8.20",
          "status": "legacy",
          "uv_key": "cpython-3.8.20-linux-x86_64-gnu",
          "variant": "default",
          "version": "3.8.20"
        },
        {
          "implementation": "pypy",
          "label": "PyPy 3.8.16",
          "minor": "3.8",
          "request": "pypy@3.8.16",
          "status": "supported",
          "uv_key": "pypy-3.8.16-linux-x86_64-gnu",
          "variant": "default",
          "version": "3.8.16"
        },
        {
          "implementation": "graalpy",
          "label": "GraalPy 3.8.5",
          "minor": "3.8",
          "request": "graalpy@3.8.5",
          "status": "supported",
          "uv_key": "graalpy-3.8.5-linux-x86_64-gnu",
          "variant": "default",
          "version": "3.8.5"
        }
      ]
    },
    "rust": {
      "defaults": {
        "toolchain": "stable"
      },
      "versions": [
        {
          "status": "active",
          "version": "stable"
        },
        {
          "status": "prerelease",
          "version": "beta"
        },
        {
          "status": "prerelease",
          "version": "nightly"
        },
        {
          "status": "active",
          "version": "1.95"
        },
        {
          "status": "supported",
          "version": "1.94"
        },
        {
          "status": "supported",
          "version": "1.93"
        },
        {
          "status": "supported",
          "version": "1.92"
        },
        {
          "status": "supported",
          "version": "1.91"
        },
        {
          "status": "supported",
          "version": "1.90"
        },
        {
          "status": "supported",
          "version": "1.89"
        },
        {
          "status": "supported",
          "version": "1.88"
        },
        {
          "status": "supported",
          "version": "1.87"
        },
        {
          "status": "supported",
          "version": "1.86"
        },
        {
          "status": "supported",
          "version": "1.85"
        },
        {
          "status": "supported",
          "version": "1.84"
        },
        {
          "status": "supported",
          "version": "1.83"
        },
        {
          "status": "supported",
          "version": "1.82"
        },
        {
          "status": "supported",
          "version": "1.81"
        },
        {
          "status": "supported",
          "version": "1.80"
        },
        {
          "status": "supported",
          "version": "1.79"
        },
        {
          "status": "supported",
          "version": "1.78"
        },
        {
          "status": "supported",
          "version": "1.77"
        },
        {
          "status": "supported",
          "version": "1.76"
        },
        {
          "status": "supported",
          "version": "1.75"
        },
        {
          "status": "supported",
          "version": "1.74"
        },
        {
          "status": "supported",
          "version": "1.73"
        },
        {
          "status": "supported",
          "version": "1.72"
        },
        {
          "status": "supported",
          "version": "1.71"
        },
        {
          "status": "supported",
          "version": "1.70"
        },
        {
          "status": "supported",
          "version": "1.69"
        },
        {
          "status": "supported",
          "version": "1.68"
        },
        {
          "status": "supported",
          "version": "1.67"
        },
        {
          "status": "supported",
          "version": "1.66"
        }
      ]
    }
  },
  "schema_version": 1,
  "tools": {
    "code_server": {
      "version": "4.118.0"
    },
    "llvm_prebundle": {
      "version": "22"
    },
    "sccache": {
      "asset": "sccache-v0.15.0-x86_64-unknown-linux-musl.tar.gz",
      "sha256": "782d2b5dd7ae0a55ebe368ab258114d0928d019ac2d949ab85d5d02f3926709e",
      "target": "x86_64-unknown-linux-musl",
      "version": "0.15.0"
    },
    "uv": {
      "version": "0.11.14"
    }
  }
}
JSON
  )

  selected_image = one([
    for image in local.images :
    image.image
    if tostring(image.node_major) == data.coder_parameter.node_major.value
  ])

  enable_python= data.coder_parameter.enable_python.value
  enable_rust  = data.coder_parameter.enable_rust.value
  enable_go    = data.coder_parameter.enable_go.value
  enable_cpp   = data.coder_parameter.enable_cpp.value

  selected_languages = compact([
    local.enable_python ? "python" : "",
    local.enable_go ? "go" : "",
    local.enable_rust ? "rust" : "",
    local.enable_cpp ? "cpp" : "",
  ])

  cdev_selection = {
    node_major            = data.coder_parameter.node_major.value
    languages             = local.selected_languages
    extra_extension_packs = jsondecode(data.coder_parameter.extra_extension_packs.value)
    python = local.enable_python ? {
      version = data.coder_parameter.python_version[0].value
      tools   = jsondecode(data.coder_parameter.python_tools[0].value)
    } : null
    go = local.enable_go ? {
      version = data.coder_parameter.go_version[0].value
      tools   = jsondecode(data.coder_parameter.go_tools[0].value)
    } : null
    rust = local.enable_rust ? {
      toolchain = data.coder_parameter.rust_toolchain[0].value
    } : null
    cpp = local.enable_cpp ? {
      llvm = data.coder_parameter.cpp_llvm[0].value
    } : null
  }
}

resource "docker_volume" "home" {
  name = "coder-${data.coder_workspace.me.id}-home"

  lifecycle {
    ignore_changes = all
  }

  labels {
    label = "coder.workspace_id"
    value = data.coder_workspace.me.id
  }

  labels {
    label = "coder.owner"
    value = data.coder_workspace_owner.me.name
  }

  labels {
    label = "coder.owner_id"
    value = data.coder_workspace_owner.me.id
  }

  labels {
    label = "coder.workspace_name_at_creation"
    value = data.coder_workspace.me.name
  }
}

resource "coder_agent" "main" {
  arch = data.coder_provisioner.me.arch
  os   = "linux"

  display_apps {
    vscode                 = true
    web_terminal           = true
    ssh_helper             = true
    port_forwarding_helper = true
  }

  env = {
    GIT_AUTHOR_NAME     = coalesce(data.coder_workspace_owner.me.full_name, data.coder_workspace_owner.me.name)
    GIT_AUTHOR_EMAIL    = data.coder_workspace_owner.me.email
    GIT_COMMITTER_NAME  = coalesce(data.coder_workspace_owner.me.full_name, data.coder_workspace_owner.me.name)
    GIT_COMMITTER_EMAIL = data.coder_workspace_owner.me.email
  }

  startup_script_behavior = "blocking"

  startup_script = <<-EOT
    #!/usr/bin/env bash
    set -Eeuo pipefail

    log() {
      printf '[codervps-startup] %s\n' "$*"
    }

    exec > >(tee -a /tmp/codervps-startup-debug.log) 2>&1
    set -x

    export HOME="/home/coder"
    export CDEV_RUNTIME_ROOT="/home/coder/.cdev"
    export RUNTIME_LIB_DIR="/opt/cde/runtime/lib"
    export CDEV_SELECTION_JSON='${jsonencode(local.cdev_selection)}'

    mkdir -p "/home/coder/workspace" "$HOME/.config/code-server" "$CDEV_RUNTIME_ROOT"
    mkdir -p "$HOME/.local/share/code-server/extensions"

    printf '%s\n' \
      'bind-addr: 127.0.0.1:13337' \
      'auth: none' \
      'cert: false' \
      > "$HOME/.config/code-server/config.yaml"

    code_server_health="http://127.0.0.1:13337/healthz"
    code_server_pid="/tmp/code-server.pid"
    code_server_log="/tmp/code-server.log"
    code_server_extensions_dir="$HOME/.local/share/code-server/extensions"

    selected_languages() {
      node -e 'const raw = process.env.CDEV_SELECTION_JSON || "{}"; const j = JSON.parse(raw); for (const x of (j.languages || [])) console.log(x);'
    }

    selected_extension_packs() {
      node -e 'const raw = process.env.CDEV_SELECTION_JSON || "{}"; const j = JSON.parse(raw); for (const x of (j.extra_extension_packs || [])) console.log(x);'
    }

    selected_extension_manifests() {
      # Always install the base editor extensions.
      printf '%s\n' "/opt/cde/extensions/core.txt"

      # Install only selected language manifests: python/go/rust/cpp.
      while IFS= read -r language; do
        [ -n "$language" ] || continue
        printf '%s\n' "/opt/cde/extensions/$language.txt"
      done < <(selected_languages)

      # Install only explicitly selected extension packs, e.g. leetcode.
      while IFS= read -r pack; do
        [ -n "$pack" ] || continue
        printf '%s\n' "/opt/cde/extensions/packs/$pack.txt"
      done < <(selected_extension_packs)
    }

    find_local_vsix_for_extension_id() {
      extension_id="$1"

      find /opt/cde/vsix -type f \
        \( -iname "$extension_id-*.vsix" -o -iname "$extension_id.vsix" \) \
        2>/dev/null | sort -V | tail -n 1
    }

    install_one_code_server_extension() {
      extension_spec="$1"
      extension_spec="$(printf '%s' "$extension_spec" | sed 's/#.*$//' | xargs)"

      [ -n "$extension_spec" ] || return 0

      # Allow manifest lines to point directly to a VSIX path.
      if [ -f "$extension_spec" ]; then
        log "Installing VSIX path: $extension_spec"
        code-server \
          --extensions-dir "$code_server_extensions_dir" \
          --install-extension "$extension_spec" \
          --force || {
            log "Failed to install VSIX path: $extension_spec"
          }
        return 0
      fi

      # Allow relative VSIX filename under /opt/cde/vsix.
      if [ -f "/opt/cde/vsix/$extension_spec" ]; then
        log "Installing VSIX file: /opt/cde/vsix/$extension_spec"
        code-server \
          --extensions-dir "$code_server_extensions_dir" \
          --install-extension "/opt/cde/vsix/$extension_spec" \
          --force || {
            log "Failed to install VSIX file: /opt/cde/vsix/$extension_spec"
          }
        return 0
      fi

      # Otherwise treat it as a Marketplace/OpenVSX extension ID.
      extension_id="$extension_spec"

      if code-server \
        --extensions-dir "$code_server_extensions_dir" \
        --list-extensions 2>/dev/null | grep -Fxq "$extension_id"; then
        log "Extension already installed: $extension_id"
        return 0
      fi

      local_vsix="$(find_local_vsix_for_extension_id "$extension_id" || true)"

      if [ -n "$local_vsix" ] && [ -f "$local_vsix" ]; then
        log "Installing extension ID from local VSIX: $extension_id -> $local_vsix"
        code-server \
          --extensions-dir "$code_server_extensions_dir" \
          --install-extension "$local_vsix" \
          --force || {
            log "Failed to install local VSIX for extension ID: $extension_id"
          }
      else
        log "Installing extension ID from registry: $extension_id"
        code-server \
          --extensions-dir "$code_server_extensions_dir" \
          --install-extension "$extension_id" \
          --force || {
            log "Failed to install extension ID: $extension_id"
          }
      fi
    }

    install_code_server_extensions() {
      log "Installing selected code-server extensions"

      mkdir -p "$code_server_extensions_dir"

      log "CDEV_SELECTION_JSON=$CDEV_SELECTION_JSON"

      while IFS= read -r manifest_file; do
        [ -n "$manifest_file" ] || continue

        if [ ! -f "$manifest_file" ]; then
          log "Extension manifest not found, skipping: $manifest_file"
          continue
        fi

        log "Reading extension manifest: $manifest_file"

        while IFS= read -r extension_spec || [ -n "$extension_spec" ]; do
          install_one_code_server_extension "$extension_spec"
        done < "$manifest_file"
      done < <(selected_extension_manifests | awk '!seen[$0]++')

      log "Installed extensions:"
      code-server \
        --extensions-dir "$code_server_extensions_dir" \
        --list-extensions || true
    }

    if ! command -v code-server >/dev/null 2>&1; then
      echo "code-server not found in PATH" >&2
      exit 1
    fi

    log "code-server version"
    code-server --version || true

    install_code_server_extensions

    if curl -fsS "$code_server_health" >/dev/null 2>&1; then
      log "code-server already healthy"
    else
      log "Starting code-server"

      rm -f "$code_server_log"
      touch "$code_server_log"

      if command -v setsid >/dev/null 2>&1; then
        setsid code-server \
          --auth none \
          --disable-telemetry \
          --disable-update-check \
          --bind-addr 127.0.0.1:13337 \
          --extensions-dir "$code_server_extensions_dir" \
          "/home/coder/workspace" \
          > "$code_server_log" 2>&1 < /dev/null &
      else
        nohup code-server \
          --auth none \
          --disable-telemetry \
          --disable-update-check \
          --bind-addr 127.0.0.1:13337 \
          --extensions-dir "$code_server_extensions_dir" \
          "/home/coder/workspace" \
          > "$code_server_log" 2>&1 < /dev/null &
      fi

      echo "$!" > "$code_server_pid"
      log "code-server pid=$(cat "$code_server_pid" 2>/dev/null || true)"

      for _ in $(seq 1 120); do
        if curl -fsS "$code_server_health" >/dev/null 2>&1; then
          log "code-server is healthy"
          break
        fi

        if [ -s "$code_server_pid" ]; then
          if ! kill -0 "$(cat "$code_server_pid")" 2>/dev/null; then
            log "code-server process exited"
            tail -n 120 "$code_server_log" >&2 || true
            break
          fi
        fi

        sleep 0.5
      done

      if ! curl -fsS "$code_server_health" >/dev/null 2>&1; then
        log "code-server did not become healthy"
        ps aux >&2 || true
        ss -lntp >&2 || true
        tail -n 200 "$code_server_log" >&2 || true
        exit 1
      fi
    fi

    if [ -f /opt/cde/runtime/startup.sh ]; then
      log "Running CoderVPS runtime startup"

      set +e
      bash /opt/cde/runtime/startup.sh
      runtime_rc="$?"
      set -e

      if [ "$runtime_rc" -ne 0 ]; then
        log "CoderVPS runtime startup failed with rc=$runtime_rc"

        if curl -fsS "$code_server_health" >/dev/null 2>&1; then
          log "code-server is still healthy, ignoring runtime startup failure"
          exit 0
        fi

        log "runtime failed and code-server is not healthy"
        tail -n 200 "$code_server_log" >&2 || true
        exit "$runtime_rc"
      fi
    fi

    if curl -fsS "$code_server_health" >/dev/null 2>&1; then
      log "startup completed successfully"
      exit 0
    fi

    log "startup finished but code-server is not healthy"
    tail -n 200 "$code_server_log" >&2 || true
    exit 1
  EOT

  metadata {
    display_name = "CPU Usage"
    key          = "0_cpu_usage"
    script       = "coder stat cpu"
    interval     = 10
    timeout      = 1
  }

  metadata {
    display_name = "RAM Usage"
    key          = "1_ram_usage"
    script       = "coder stat mem"
    interval     = 10
    timeout      = 1
  }

  metadata {
    display_name = "Home Disk"
    key          = "2_home_disk"
    script       = "coder stat disk --path /home/coder"
    interval     = 60
    timeout      = 1
  }
}

resource "coder_app" "code_server" {
  count = data.coder_workspace.me.start_count

  agent_id     = coder_agent.main.id
  slug         = "code-server"
  display_name = "VS Code Web"
  icon         = "/icon/code.svg"

  url       = "http://127.0.0.1:13337/?folder=/home/coder/workspace"
  share     = "owner"
  subdomain = false
  open_in   = "tab"
  order     = 1

  healthcheck {
    url       = "http://127.0.0.1:13337/healthz"
    interval  = 3
    threshold = 20
  }
}

resource "docker_container" "workspace" {
  count = data.coder_workspace.me.start_count

  image    = local.selected_image
  name     = "coder-${data.coder_workspace.me.id}"
  hostname = lower(data.coder_workspace.me.name)

  entrypoint = ["sh", "-c", replace(coder_agent.main.init_script, "/localhost|127\\.0\\.0\\.1/", "host.docker.internal")]
  env        = ["CODER_AGENT_TOKEN=${coder_agent.main.token}"]

  host {
    host = "host.docker.internal"
    ip   = "host-gateway"
  }

  volumes {
    volume_name    = docker_volume.home.name
    container_path = "/home/coder"
    read_only      = false
  }

  volumes {
    host_path      = "/opt/coder-cde/templates/devbox/runtime"
    container_path = "/opt/cde/runtime"
    read_only      = true
  }

  volumes {
    host_path      = "/opt/coder-cde/templates/devbox/extensions"
    container_path = "/opt/cde/extensions"
    read_only      = true
  }

  volumes {
    host_path      = "/opt/coder-cde/vsix"
    container_path = "/opt/cde/vsix"
    read_only      = true
  }

  labels {
    label = "coder.workspace_id"
    value = data.coder_workspace.me.id
  }

  labels {
    label = "coder.owner"
    value = data.coder_workspace_owner.me.name
  }

  labels {
    label = "coder.owner_id"
    value = data.coder_workspace_owner.me.id
  }

  labels {
    label = "coder.workspace_name"
    value = data.coder_workspace.me.name
  }
}
