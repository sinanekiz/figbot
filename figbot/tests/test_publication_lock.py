import subprocess
import sys

import pytest

from scripts.publication_lock import publication_lock


def test_second_process_cannot_publish_until_owner_exits(tmp_path):
    path = tmp_path / 'publication.lock'
    code = (
        'import sys; from scripts.publication_lock import publication_lock\n'
        'with publication_lock(sys.argv[1]):\n'
        ' print("locked", flush=True)\n'
        ' sys.stdin.readline()\n'
    )
    child = subprocess.Popen([sys.executable, '-c', code, str(path)],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True)
    try:
        assert child.stdout.readline().strip() == 'locked'
        with pytest.raises(RuntimeError, match='Another publication'):
            with publication_lock(path):
                pytest.fail('Concurrent archive mutation was allowed')
        child.communicate('\n', timeout=10)
        assert child.returncode == 0
        with publication_lock(path):
            pass
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()


def test_exception_releases_lock_without_removing_lock_file(tmp_path):
    path = tmp_path / 'publication.lock'
    with pytest.raises(ValueError):
        with publication_lock(path):
            raise ValueError('failed publication')
    assert path.exists()
    with publication_lock(path):
        pass
