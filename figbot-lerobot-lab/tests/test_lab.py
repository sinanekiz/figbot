import json
from pathlib import Path

import numpy as np
import pytest

from figbot_lab.common import JOINTS, load_json, save_json, sha256
from figbot_lab.mapping import JointMapping, validate_state
from figbot_lab.policy import error_metrics
from figbot_lab.records import read_episode, snapshot_episode, video_frame


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')


@pytest.fixture
def mapping_file(tmp_path):
    path = tmp_path / 'mapping.json'
    save_json(path, {"status": "VERIFIED", "evidence": "SYNTHETIC UNIT TEST ONLY",
                    "state_convention": "lerobot_range_m100_100_gripper_0_100",
                    "joint_order": list(JOINTS),
                    "joints": {name: {"raw_counts": [0, 1000, 2000],
                                       "policy_values": [0, 50, 100] if name == 'gripper' else [-100, 0, 100]}
                               for name in JOINTS}})
    return path


@pytest.fixture
def recording(tmp_path):
    import cv2
    source = tmp_path / 'source'
    (source / 'episode').mkdir(parents=True)
    rows, clocks, corrected = [], [], []
    writer = cv2.VideoWriter(str(source / 'episode/camera.avi'), cv2.VideoWriter_fourcc(*'MJPG'), 10, (64, 48))
    assert writer.isOpened()
    for index in range(60):
        positions = [1000 + index + j for j in range(6)]
        rows.append({'frame_index': index, 'elapsed_seconds': index / 10,
                     'motor_readings': [{'id': j + 1, 'ok': True, 'position': positions[j]} for j in range(6)]})
        clocks.append({'frame_index': index, 'estimated_capture_monotonic': 100 + index / 10,
                       'encoder_read_start': 100 + index / 10 - .01, 'encoder_read_end': 100 + index / 10 + .01})
        corrected.append({'time': index / 10, 'corrected': positions})
        frame = np.zeros((48, 64, 3), dtype=np.uint8)
        frame[:, :, 2] = 100 + index
        writer.write(frame)
    writer.release()
    write_jsonl(source / 'episode/samples.jsonl', rows)
    write_jsonl(source / 'timing.jsonl', clocks)
    write_jsonl(source / 'corrected_training/corrected_targets.jsonl', corrected)
    save_json(source / 'status.json', {'state': 'STOPPED'})
    save_json(source / 'episode/session.json', {'status': 'CLOSED', 'task': 'Pick figs and place in container'})
    save_json(source / 'outcome.json', {'outcome': 'SUCCESSFUL_MANUAL_DEMONSTRATION'})
    save_json(source / 'training_annotations.json', {'cycles': [{'start': 0, 'end': 3}, {'start': 3, 'end': 5.9}]})
    save_json(source / 'corrected_training/data_review.json', {
        'excluded_suspect_intervals': [[1.5, 1.8]],
        'source_hashes': {r: sha256(source / r) for r in ('episode/camera.avi', 'episode/samples.jsonl', 'timing.jsonl')}})
    return source


def test_mapping_converts_and_does_not_clip(mapping_file):
    mapping = JointMapping(mapping_file)
    np.testing.assert_allclose(mapping.convert([1000] * 6), [0, 0, 0, 0, 0, 50])
    with pytest.raises(ValueError, match='outside calibrated range'):
        mapping.convert([-1] * 6)


def test_mapping_allows_verified_reverse_direction(mapping_file):
    doc = load_json(mapping_file)
    doc['joints']['shoulder_pan']['policy_values'] = [100, 0, -100]
    save_json(mapping_file, doc)
    assert JointMapping(mapping_file).convert([0] * 6)[0] == 100


@pytest.mark.parametrize('change', ['unverified', 'order', 'nonfinite', 'raw_order', 'policy_order', 'unit', 'raw_range'])
def test_bad_mapping_is_rejected(mapping_file, change):
    doc = load_json(mapping_file)
    if change == 'unverified': doc['status'] = 'UNVERIFIED'
    if change == 'order': doc['joint_order'].reverse()
    if change == 'nonfinite': doc['joints']['elbow_flex']['raw_counts'] = [0, None, 2000]
    if change == 'raw_order': doc['joints']['elbow_flex']['raw_counts'] = [1000, 0, 2000]
    if change == 'policy_order': doc['joints']['elbow_flex']['policy_values'] = [-100, 100, 0]
    if change == 'unit': doc['state_convention'] = 'raw_counts'
    if change == 'raw_range': doc['joints']['elbow_flex']['raw_counts'] = [-1, 1000, 2000]
    save_json(mapping_file, doc)
    with pytest.raises(ValueError): JointMapping(mapping_file)


@pytest.mark.parametrize('state', [[1]*5, [float('nan')]*6, [[1]*6], [float('inf')]*6])
def test_state_rejects_invalid(state):
    with pytest.raises(ValueError): validate_state(state)


def test_metrics_compare_hold_baseline():
    result = error_metrics(np.ones((3, 6)), np.ones((3, 6)), np.zeros(6))
    assert result['mae'] == 0 and result['hold_baseline_mae'] == 1
    assert result['beats_hold_baseline']
    with pytest.raises(ValueError): error_metrics(np.ones((2, 6)), np.ones((3, 6)), np.zeros(6))


def test_normalization_requires_actual_state_and_action_statistics():
    from figbot_lab.policy import validate_stats
    with pytest.raises(ValueError, match='observation.state.mean'):
        validate_stats({'so100.buffer.action': {'mean': [0]*6, 'std': [1]*6}})
    valid = {k: {'mean': [0]*6, 'std': [1]*6} for k in ('observation.state','action')}
    assert validate_stats(valid)['action']['std'].shape == (6,)
    valid['action']['std'][0] = 0
    with pytest.raises(ValueError, match='action.std'): validate_stats(valid)


def test_recording_keeps_frame_alignment(recording):
    data = read_episode(recording)
    assert data['indices'][12] == 12
    frame = video_frame(recording / 'episode/camera.avi', 12)
    assert frame[0, 0, 0] > 100 and frame[0, 0, 2] < 10  # decoded RGB, not BGR


@pytest.mark.parametrize('failure', ['clock', 'ids', 'position', 'frame', 'monotonic', 'duration', 'raw_range', 'wrap'])
def test_recording_rejects_bad_alignment(recording, failure):
    from figbot_lab.records import read_rows
    rows = read_rows(recording / 'episode/samples.jsonl')
    timing = read_rows(recording / 'timing.jsonl')
    if failure == 'clock': timing.pop()
    if failure == 'ids': rows[0]['motor_readings'][0]['id'] = 2
    if failure == 'position': rows[0]['motor_readings'][0]['position'] = None
    if failure == 'frame': timing[0]['frame_index'] = 10
    if failure == 'monotonic': rows[1]['elapsed_seconds'] = 0
    if failure == 'duration': timing[0]['encoder_read_end'] = timing[0]['encoder_read_start'] - .1
    if failure == 'raw_range': rows[0]['motor_readings'][0]['position'] = 5000
    if failure == 'wrap': rows[0]['motor_readings'][0]['position'] = 4095
    write_jsonl(recording / 'episode/samples.jsonl', rows)
    write_jsonl(recording / 'timing.jsonl', timing)
    with pytest.raises(ValueError): read_episode(recording)


def test_snapshot_preserves_source_and_detects_changes(recording, tmp_path, monkeypatch):
    import figbot_lab.records as records
    monkeypatch.setattr(records, 'ROOT', tmp_path / 'lab')
    monkeypatch.setattr(records, 'lab_output', lambda p: p)
    before = sha256(recording / 'episode/camera.avi')
    dest, audit = snapshot_episode(recording)
    assert audit['frames'] == 60 and sha256(recording / 'episode/camera.avi') == before
    assert sha256(dest / 'episode/camera.avi') == before
    snapshot_episode(recording)  # idempotent verification
    (dest / 'episode/samples.jsonl').write_text('{}')
    with pytest.raises(ValueError, match='changed'): snapshot_episode(recording)


def test_active_recording_is_rejected(recording):
    save_json(recording / 'status.json', {'state': 'RECORDING'})
    with pytest.raises(ValueError, match='stopped'): snapshot_episode(recording, 'pytest_active')


def test_training_split_has_no_cycle_leakage(recording, mapping_file):
    from figbot_lab.training import select_training_rows
    rows = select_training_rows(recording, JointMapping(mapping_file))
    train = [r for r in rows if r['split'] == 'train']
    validation = [r for r in rows if r['split'] == 'validation']
    assert train and validation
    assert {r['cycle'] for r in train}.isdisjoint({r['cycle'] for r in validation})
    assert all(not 1.2 <= r['source_time_s'] <= 2.0 for r in train)
    assert all(r['state'].shape == r['action'].shape == (6,) for r in rows)


def test_model_missing_stats_rejected(tmp_path):
    from figbot_lab.assets import validate_model_files
    (tmp_path / 'config.json').write_text('{}')
    (tmp_path / 'model.safetensors').write_bytes(b'fixture')
    save_json(tmp_path / 'policy_preprocessor.json', {'steps': [{'state_file': 'missing.safetensors'}]})
    save_json(tmp_path / 'policy_postprocessor.json', {'steps': []})
    with pytest.raises(ValueError, match='statistics'): validate_model_files(tmp_path)


def test_camera_reports_open_failure(monkeypatch):
    import cv2
    from figbot_lab.camera import capture
    class ClosedCamera:
        def isOpened(self): return False
        def release(self): pass
    monkeypatch.setattr(cv2, 'VideoCapture', lambda *a: ClosedCamera())
    with pytest.raises(ValueError, match='could not be opened'): capture()


def test_camera_capture_writes_local_timing(tmp_path, monkeypatch):
    import cv2
    import figbot_lab.camera as camera
    class SyntheticCamera:
        def isOpened(self): return True
        def set(self, *a): return True
        def read(self): return True, np.zeros((48, 64, 3), dtype=np.uint8)
        def release(self): pass
    monkeypatch.setattr(cv2, 'VideoCapture', lambda *a: SyntheticCamera())
    monkeypatch.setattr(camera, 'new_run', lambda _: tmp_path)
    capture_path = camera.capture(seconds=.05)
    report = load_json(capture_path / 'capture.json')
    assert report['frames'] > 0 and report['has_robot_state'] is False


def test_outputs_cannot_target_original_project(tmp_path):
    from figbot_lab.common import lab_output
    with pytest.raises(ValueError, match='inside'): lab_output(tmp_path)


def test_actual_lerobot_export_round_trip(recording, mapping_file, tmp_path, monkeypatch):
    from figbot_lab.common import configure_environment
    configure_environment()
    import figbot_lab.training as training
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
    monkeypatch.setattr(training, 'ROOT', tmp_path / 'lab')
    monkeypatch.setattr(training, 'lab_output', lambda p: p)
    output = training.export_training(recording, mapping_file, 'synthetic_test')
    manifest = load_json(output / 'export_manifest.json')
    dataset = LeRobotDataset('local/synthetic_test_train', root=output / 'train', video_backend='pyav')
    assert len(dataset) == manifest['splits']['train']['frames']
    sample = dataset[0]
    assert sample['observation.state'].shape == sample['action'].shape == (6,)
    assert sample['observation.images.camera1'].shape == (3, 48, 64)
    assert manifest['splits']['validation']['cycles'] == [1]
    assert sample['task'] == manifest['task'] == 'Pick figs and place in container'


def test_overlapping_cycles_cannot_leak_into_holdout(recording, mapping_file):
    from figbot_lab.training import select_training_rows
    save_json(recording / 'training_annotations.json', {'cycles': [
        {'start': 0, 'end': 4}, {'start': 3, 'end': 5.9}]})
    with pytest.raises(ValueError, match='nonoverlapping'):
        select_training_rows(recording, JointMapping(mapping_file))


@pytest.mark.parametrize('failure', ['missing_hashes', 'reversed_interval'])
def test_training_requires_complete_provenance_and_valid_exclusions(recording, mapping_file, failure):
    from figbot_lab.training import select_training_rows
    path = recording / 'corrected_training/data_review.json'
    review = load_json(path)
    if failure == 'missing_hashes': review['source_hashes'] = {}
    if failure == 'reversed_interval': review['excluded_suspect_intervals'] = [[2, 1]]
    save_json(path, review)
    with pytest.raises(ValueError):
        select_training_rows(recording, JointMapping(mapping_file))


def test_recorded_task_cannot_silently_be_replaced(recording):
    from figbot_lab.records import recorded_task
    assert recorded_task(recording) == 'Pick figs and place in container'
    save_json(recording / 'episode/session.json', {'status': 'CLOSED'})
    with pytest.raises(ValueError, match='original task'):
        recorded_task(recording)


def test_live_camera_task_uses_current_scene(tmp_path, monkeypatch):
    from PIL import Image
    import figbot_lab.camera as camera
    import figbot_lab.common as common
    import figbot_lab.policy as policy
    monkeypatch.setattr(common, 'ROOT', tmp_path)
    monkeypatch.setattr(camera, 'new_run', lambda _: tmp_path)
    save_json(tmp_path / 'configs/current_scene.json', {'task': 'Put the fig on the white paper'})
    image = tmp_path / 'image.jpg'
    Image.new('RGB', (64, 48)).save(image)
    class Runner:
        def __init__(self, *args): pass
        def training_mean_state(self): return np.zeros(6)
        def predict(self, images, state, task): return {'task': task}
    monkeypatch.setattr(policy, 'PolicyRunner', Runner)
    camera.camera_smoke(image)
    result = load_json(tmp_path / 'prediction.json')
    assert result['task'] == 'Put the fig on the white paper'
    assert result['suitable_for_robot_control'] is False
    camera.camera_smoke(image, task='Explicit diagnostic command')
    assert load_json(tmp_path / 'prediction.json')['task'] == 'Explicit diagnostic command'


def test_checkpoint_rejects_external_processor_files(tmp_path):
    from figbot_lab.assets import validate_model_files
    model = tmp_path / 'model'
    model.mkdir()
    (model / 'config.json').write_text('{}')
    (model / 'model.safetensors').write_bytes(b'fixture')
    (tmp_path / 'outside.safetensors').write_bytes(b'fixture')
    for name, registry in [('policy_preprocessor.json', 'normalizer_processor'),
                           ('policy_postprocessor.json', 'unnormalizer_processor')]:
        save_json(model / name, {'steps': [{'registry_name': registry, 'state_file': '../outside.safetensors'}]})
    with pytest.raises(ValueError, match='escapes'):
        validate_model_files(model)


def test_asset_hashes_are_checked_before_loading(tmp_path, monkeypatch):
    import figbot_lab.assets as assets
    monkeypatch.setattr(assets, 'ROOT', tmp_path)
    model = tmp_path / 'model'
    model.mkdir()
    weights = model / 'model.safetensors'
    weights.write_bytes(b'original')
    save_json(tmp_path / 'assets.lock.json', {'model:fixture': {
        'revision': 'a'*40, 'files_sha256': {'model.safetensors': sha256(weights)}}})
    assert assets.verify_asset('fixture', model) == 'a'*40
    weights.write_bytes(b'changed')
    with pytest.raises(ValueError, match='integrity mismatch'):
        assets.verify_asset('fixture', model)


def test_training_config_parses_with_installed_lerobot(tmp_path, monkeypatch):
    import figbot_lab.training as training
    from lerobot.policies.smolvla.configuration_smolvla import SmolVLAConfig
    from lerobot.configs.train import TrainPipelineConfig
    import draccus
    monkeypatch.setattr(training, 'ROOT', tmp_path)
    monkeypatch.setattr(training, 'lab_output', lambda p: Path(p))
    checkpoint = tmp_path / 'models/base'
    checkpoint.mkdir(parents=True)
    SmolVLAConfig().save_pretrained(checkpoint)
    dataset = tmp_path / 'data/test'
    save_json(dataset / 'export_manifest.json', {'mapping': {'status': 'VERIFIED'},
              'splits': {'train': {'repo_id': 'local/test_train'}}})
    command = training.training_command(dataset, 'base')
    assert command.startswith('& "')
    with (dataset / 'train_config.json').open() as stream:
        config = draccus.load(TrainPipelineConfig, stream)
    assert config.policy.pretrained_path == checkpoint
    assert config.policy.push_to_hub is False and config.wandb.enable is False
    assert config.dataset.root == str(dataset / 'train')
    assert config.policy.chunk_size == 16
