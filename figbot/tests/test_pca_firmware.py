import shutil
import subprocess
from pathlib import Path
import pytest

def test_hc05_core_is_exact_shared_protocol_and_separate_serial_owner():
    root=Path(__file__).resolve().parents[1]
    core=(root/'firmware/uno_pca9685/uno_pca9685.ino').read_bytes()
    generated=(root/'firmware/uno_pca9685_hc05/pca_core.h').read_bytes()
    assert generated.split(b'\n',1)[1]==core
    sketch=(root/'firmware/uno_pca9685_hc05/uno_pca9685_hc05.ino').read_text()
    assert '#include <AltSoftSerial.h>' in sketch
    assert 'AltSoftSerial hc05;' in sketch
    assert 'D8 RX' in sketch and 'D9 TX' in sketch
    assert '#define FIGBOT_SERIAL_BAUD 9600' in sketch
    assert '#define Serial hc05' in sketch


def test_firmware_against_fake_wire_and_clock(tmp_path):
    compiler = shutil.which('g++')
    if not compiler:
        pytest.skip('Native g++ needed for firmware behavior test')
    source = Path(__file__).parent / 'pca_firmware_stub'
    exe = tmp_path / 'firmware_test.exe'
    subprocess.run([compiler, '-std=c++11', '-I', str(source), str(source / 'check.cpp'), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
