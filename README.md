# Notebook Publish Check

[![Tests](https://github.com/R-Koda/notebook-publish-check/actions/workflows/tests.yml/badge.svg)](https://github.com/R-Koda/notebook-publish-check/actions/workflows/tests.yml)
**Keep useful figures. Review risky output. Publish a separate copy.**

A dependency-free, non-executing publication review tool for Jupyter notebooks. Generate a local HTML preview, inspect cell-level findings, choose which outputs or metadata to remove, and download a separate notebook.

Notebook公開前に、セルごとの点検結果を確認し、残す図と削除する出力を選べます。元ファイルは変更しません。

## Try the demo

Download and open [`examples/demo.html`](examples/demo.html). The sample uses synthetic logs and clearly fake credentials. Keep the figure in cell 2, remove outputs in cell 3, and inspect the warning in cell 4: deleting outputs does **not** remove a credential-like value from source code.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
nbpublish examples/publication-demo.ipynb --output reports/review.html --json reports/findings.json
```

Without installation: `PYTHONPATH=src python3 -m notebook_publish_check` followed by the same arguments.

Python 3.10+. No runtime dependencies. Not yet published to PyPI.

Exit codes: **0** no selected findings; **1** findings for review (report successfully created); **2** invalid input or I/O error. No findings does not mean a notebook is safe to publish.

## Workflow

1. Generate the local report; code is never executed.
2. Inspect source, text output, raster images, and findings. HTML/SVG/JavaScript outputs are shown as text, never executed.
3. Select output or metadata removal per cell. Selecting outputs clears the entire cell output and its execution count. It does not edit individual values.
4. Download `reviewed-copy.ipynb`; the original is unchanged. Manually edit flagged source code when necessary.
5. Re-run the checker on the downloaded copy, then review remaining content before publishing.

## Checks and coverage

- Credential-like assignments (`api_key`, `access_token`, `password`, `secret`) and selected token prefixes; heuristic, with false positives and false negatives.
- Selected Unix/macOS/Windows home-directory absolute paths.
- Large serialized cell outputs (100,000 UTF-8 bytes by default; change with `--max-output-kb`).
- Rich outputs and embedded attachments marked for manual review.
- Notebook/cell metadata and textual attachments inspected for the same selected patterns.

**The HTML report embeds the original notebook**, including values omitted from the findings summary. Keep reports private. JSON findings omit matched values but may include metadata key names. Images are not OCR-scanned; binary attachments, arbitrary personal information, encoded/obfuscated secrets and Git history are not comprehensively checked. Source and attachments are preserved in exported copies. Metadata removal may remove tags, kernel info or presentation settings.

This is not a replacement for [Gitleaks](https://github.com/gitleaks/gitleaks), [nbstripout](https://github.com/kynan/nbstripout) or [nbdime](https://github.com/jupyter/nbdime). The focus is a publication review workflow with selective output retention.

## Python API and development

`scan(notebook)` returns cell-indexed findings (indices are zero-based). `sanitize(notebook, remove_outputs=[2], remove_metadata=[2, 'notebook'])` returns a deep copy, leaving the input intact.

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Experimental 0.1, nbformat 4 only, 20 MB input limit. Basic structure checks are not a full nbformat schema validator. Output files must be new and cannot overwrite inputs. No telemetry or external services. MIT licensed.
