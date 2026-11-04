"""Release packaging must include sources without leaking local working files."""
import json
import zipfile

import build


def test_release_files_exclude_local_data(tmp_path, monkeypatch):
    monkeypatch.setattr(build, 'ROOT', tmp_path)
    paths = ['main.py', '.github/workflows/tests.yml', '.gitignore', 'LICENSE',
             'bfl_Challenger_3500.png', 'aircraft_profiles.json', 'airports.json',
             '.DS_Store', '.venv/example.py', '__pycache__/example.py',
             '.build/temp.tex', 'dist/old.py', 'personal-chart.png']
    for name in paths:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('sample')
    actual = {p.relative_to(tmp_path).as_posix() for p in build.release_files()}
    assert actual == {'main.py', '.github/workflows/tests.yml', '.gitignore',
                      'LICENSE', 'bfl_Challenger_3500.png'}


def test_zip_contains_repository_root(tmp_path, monkeypatch):
    monkeypatch.setattr(build, 'ROOT', tmp_path)
    (tmp_path / 'main.py').write_text('print("example")\n')
    build.package()
    with zipfile.ZipFile(tmp_path / 'dist/aircraft-performance-github.zip') as archive:
        assert archive.namelist() == ['aircraft-performance/main.py']
        assert archive.testzip() is None


def test_manifest_hash_changes_when_source_changes(tmp_path, monkeypatch):
    monkeypatch.setattr(build, 'ROOT', tmp_path)
    monkeypatch.setattr(build.importlib.metadata, 'version', lambda name: 'test')
    source = tmp_path / 'main.py'
    source.write_text('original')
    build.write_manifest()
    before = json.loads((tmp_path / 'build_manifest.json').read_text())
    source.write_text('changed')
    build.write_manifest()
    after = json.loads((tmp_path / 'build_manifest.json').read_text())
    assert before['sha256']['main.py'] != after['sha256']['main.py']
    assert 'build_manifest.json' not in after['sha256']
