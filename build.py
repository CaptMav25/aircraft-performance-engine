"""Regenerate project outputs and optionally package a clean GitHub release.

Run: python build.py --zip
Requires requirements-build.txt, Playwright Chromium and a LaTeX installation.
"""

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
OUTPUTS = [
    'bfl_Challenger_3500.png',
    'sensitivity_Cessna_172S.png',
    'sensitivity_Cirrus_SR22T.png',
    'sensitivity_Challenger_3500.png',
    'report/examples_challenger_3500.tex',
    'report/examples_cirrus_sr22t.tex',
    'report/figures/bfl_example_Challenger_3500.png',
    'report/performance_model.pdf',
    'flowcharts/calculation_flow.png',
    'flowcharts/program_flow.png',
    'flowcharts/flowcharts.pdf',
]
EXCLUDED_DIRS = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache',
                 '.build', 'dist', '.idea', '.vscode'}
EXCLUDED_FILES = {'.DS_Store', 'aircraft_profiles.json', 'airports.json'}
SOURCE_SUFFIXES = {'.py', '.md', '.txt', '.html', '.tex', '.yml', '.ttf'}


def run(command, cwd=ROOT):
    subprocess.run(command, cwd=cwd, check=True)


def release_files():
    """Include project sources and named outputs, never local user data."""
    for path in sorted(ROOT.rglob('*')):
        relative = path.relative_to(ROOT)
        if not path.is_file() or path.is_symlink():
            continue
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        if path.name in EXCLUDED_FILES:
            continue
        if (path.suffix in SOURCE_SUFFIXES or relative.as_posix() in OUTPUTS
                or path.name in {'LICENSE', '.gitignore', 'build_manifest.json'}):
            yield path


def preflight():
    """Check optional build tools before changing generated outputs."""
    for package in ('numpy', 'scipy', 'matplotlib', 'pytest', 'Pillow', 'playwright'):
        importlib.metadata.version(package)
    if shutil.which('latexmk') is None:
        raise RuntimeError('Install TeX Live or MacTeX and put latexmk on PATH.')
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        if not Path(pw.chromium.executable_path).is_file():
            raise RuntimeError('Run: python -m playwright install chromium')


def generate():
    import matplotlib
    matplotlib.use('Agg')
    from aircraft import C172, SR22T, CL3500
    from bfl import balanced_field, plot_bfl
    from sensitivity import run_sweeps, plot_sensitivity

    print('Generating performance charts...', flush=True)
    plot_bfl(balanced_field(CL3500), str(ROOT / OUTPUTS[0]))
    for acft in (C172, SR22T, CL3500):
        filename = ROOT / f"sensitivity_{acft.name.replace(' ', '_')}.png"
        plot_sensitivity(acft, run_sweeps(acft), str(filename))

    (ROOT / 'report/figures').mkdir(parents=True, exist_ok=True)
    run([sys.executable, 'report/make_examples.py'])
    run([sys.executable, 'flowcharts/make_flowcharts.py'])

    print('Compiling the LaTeX report...', flush=True)
    output_dir = ROOT / '.build/latex'
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = ROOT / '.build/latex-build.log'
    with log_path.open('w', encoding='utf-8') as log:
        status = subprocess.run(
            ['latexmk', '-pdf', '-interaction=nonstopmode', '-halt-on-error',
             f'-outdir={output_dir}', 'performance_model.tex'],
            cwd=ROOT / 'report', stdout=log, stderr=subprocess.STDOUT,
        )
    if status.returncode:
        raise RuntimeError(f'LaTeX failed; see {log_path}')
    shutil.copyfile(output_dir / 'performance_model.pdf', ROOT / 'report/performance_model.pdf')

    for relative in OUTPUTS:
        path = ROOT / relative
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f'Missing or empty output: {relative}')


def write_manifest():
    files = {}
    for path in release_files():
        if path.name != 'build_manifest.json':
            files[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {
        'command': 'python build.py --zip',
        'python': platform.python_version(),
        'packages': {name: importlib.metadata.version(name) for name in
                     ('numpy', 'scipy', 'matplotlib', 'pytest', 'Pillow', 'playwright')},
        'generated_outputs': OUTPUTS,
        'sha256': files,
    }
    (ROOT / 'build_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')


def package():
    output_dir = ROOT / 'dist'
    output_dir.mkdir(exist_ok=True)
    archive = output_dir / 'aircraft-performance-github.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in release_files():
            bundle.write(path, Path('aircraft-performance') / path.relative_to(ROOT))
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            raise RuntimeError('ZIP verification failed')
    print(f'Created: {archive}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip', action='store_true', help='Package sources and rebuilt outputs')
    args = parser.parse_args()
    os.environ.setdefault('MPLBACKEND', 'Agg')
    os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.build/matplotlib'))
    preflight()
    run([sys.executable, '-m', 'pytest', '-q'])
    generate()
    write_manifest()
    if args.zip:
        package()
    print('All project outputs rebuilt successfully.', flush=True)


if __name__ == '__main__':
    main()
