"""An unattended serial capture must not flood the tool's stdout pipe."""
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace


def test_monitor_keeps_bulk_bytes_in_file_only(tmp_path, monkeypatch, capsys):
    source = Path(__file__).resolve().parents[1] / '.codex_artifacts/arduino/monitor_hc05_trace.py'
    script = tmp_path / 'monitor.py'
    script.write_bytes(source.read_bytes())
    lines = [b'HC05_TEST\n'] + [b'R 48\n', b'T 53\n'] * 10000
    class Port:
        def __init__(self, port, baud, timeout):
            assert (port, baud, timeout) == ('COM3', 115200, 0.2)
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def readline(self): return lines.pop(0)
        # No write method: this monitor must never send serial commands.
    clock = SimpleNamespace(strftime=lambda _: 'test',
                            monotonic=lambda: 0 if lines else 1000)
    monkeypatch.setitem(sys.modules, 'serial', SimpleNamespace(Serial=Port))
    monkeypatch.setitem(sys.modules, 'time', clock)
    runpy.run_path(str(script), run_name='__main__')
    captured = capsys.readouterr().out
    assert len(captured) < 1000
    assert '"received_bytes": 10000' in captured
    assert '"transmitted_bytes": 10000' in captured
    log = (tmp_path / 'hc05-trace-test.log').read_text()
    assert log.count('R 48\n') == 10000
    assert log.count('T 53\n') == 10000
