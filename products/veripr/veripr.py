#!/usr/bin/env python3
"""Backwards-compatible single-file shim delegating to the `veripr` package."""

from veripr.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
