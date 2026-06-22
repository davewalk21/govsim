# GovSim

A government simulator game built with Pygame.

# Setup

If you don't have `uv`, it is the best way to manage venvs. It is easy to install:

## Installing uv

[uv](https://github.com/astral-sh/uv) is a fast Python package manager. Choose the install method for your platform:

### macOS / Linux
On macOS, ensure you are in the zsh terminal and that it is set as default.
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows (PowerShell)
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Verify installation
```bash
uv --version
```

> **Note:** After installing via the install script, restart your terminal (or open a new shell session) so your `PATH` picks up the `uv` binary.

> **Note:** More info on wirking with uv in PyCharm (2024+ recommended): 
> https://www.jetbrains.com/help/pycharm/uv.html#uv-workspace-support

## Sync requirements, python version, and venv

```powershell
uv sync
```

## Run

```powershell
uv run main.py
```