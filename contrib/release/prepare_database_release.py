#!/usr/bin/env python3
"""Download the pinned upstream database and package SQL from an exact Git commit."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request
import zipfile

URL = 'https://github.com/slash-design/DestinyCore/releases/download/DB735.02/DB735.02.rar'
SHA256 = 'a887055dbe7cf939d48f23505400b1f615b05e5ef056f70ee322301eaad9374b'
SIZE = 88150908


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]

    def git(*arguments):
        return subprocess.check_output(['git', *arguments], cwd=repo, text=True).strip()

    commit = git('rev-parse', 'HEAD')
    output = args.output.resolve()
    if output == repo or repo in output.parents:
        raise SystemExit('Use an output directory outside the repository.')
    output.mkdir(parents=True, exist_ok=True)
    archive = output / 'DB735.02.rar'
    if not archive.exists() or archive.stat().st_size != SIZE or digest(archive) != SHA256:
        partial = output / 'DB735.02.rar.part'
        try:
            request = urllib.request.Request(URL, headers={'User-Agent': '1KYCore-database-release'})
            print('Downloading pinned DB735.02...', flush=True)
            with urllib.request.urlopen(request, timeout=120) as response, partial.open('wb') as stream:
                while chunk := response.read(1024 * 1024):
                    stream.write(chunk)
            if partial.stat().st_size != SIZE or digest(partial) != SHA256:
                raise SystemExit('Upstream archive size or SHA-256 mismatch; refusing to package it.')
            partial.replace(archive)
        finally:
            partial.unlink(missing_ok=True)

    metadata = {
        'core_commit': commit,
        'upstream_repository': 'https://github.com/slash-design/DestinyCore',
        'upstream_tag': 'DB735.02',
        'upstream_url': URL,
        'upstream_sha256': SHA256,
        'upstream_size': SIZE,
        'database_modified': False,
        'runtime_compatibility_tested': False,
    }
    bundle = output / f'1KYCore-database-support-{commit[:12]}.zip'
    subprocess.run([
        'git', 'archive', '--format=zip', f'--output={bundle}', commit,
        'sql/base/auth_database.sql', 'sql/base/characters_database.sql',
        'sql/base/shop_database.sql', 'sql/updates', 'sql/custom',
        'docs/database-release.md', 'COPYING',
    ], cwd=repo, check=True)
    metadata_text = json.dumps(metadata, indent=2) + '\n'
    with zipfile.ZipFile(bundle, 'a', compression=zipfile.ZIP_DEFLATED) as package:
        package.writestr('database-source.json', metadata_text)
    (output / 'database-source.json').write_text(metadata_text, encoding='utf-8')
    (output / 'SHA256SUMS').write_text(
        ''.join(f'{digest(p)}  {p.name}\n' for p in [archive, bundle, output / 'database-source.json']),
        encoding='utf-8',
    )
    print(f'Verified database and SQL snapshot {commit}; output: {output}')


if __name__ == '__main__':
    main()
