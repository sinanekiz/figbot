import pytest
from test_commission_pan import rig
from figbot_lab.commission_batch import BatchProbeBus, run_batch_probe, TEST_SIGNS, EXCURSION, STEP
from figbot_lab._reference_protocol import BusError, BusTimeout


def setup(rig):
    _, review, registers, writes, state, _ = rig
    review['status'] = 'CLEARED_FOR_SIX_JOINT_PROBE'
    bus = BatchProbeBus(None)
    def sleep(seconds):
        state['clock'] += seconds
    def frame():
        return {'pc_read_monotonic': state['clock'], 'pc_age_upper_s': .02}
    def run(**kwargs):
        return run_batch_probe(bus, review, kwargs.pop('fresh_frame', frame),
                               clock=lambda: state['clock'], sleep=sleep, **kwargs)
    return bus, review, registers, writes, state, run


@pytest.mark.parametrize('base_powered', [False, True])
def test_all_six_excursions_return_and_hold_without_changing_settings(rig, base_powered):
    bus, review, registers, writes, state, run = setup(rig)
    state['auto_torque'] = True
    if base_powered:
        registers[1][40] = 1
        registers[1][42:44] = (2100).to_bytes(2, 'little')
    original = {i: bytes(r[:40]) for i, r in registers.items()}
    result = run()
    assert result['status'] == 'SIX_SMALL_MOTOR_PROBES_MEASURED'
    assert result['physical_mapping'] == 'UNVERIFIED' and not result['profile_created']
    for i, row in enumerate(result['joints'], 1):
        assert row['motor'] == i and row['home'] == 2100
        assert row['peak'] == 2100 + TEST_SIGNS[i - 1] * EXCURSION
        assert row['final']['position'] == 2100 and row['final']['torque'] == 1
        goals = [int.from_bytes(data[2:4], 'little') for motor, data in writes
                 if motor == i and data[0] == 41]
        assert goals[0] == goals[-1] == 2100
        assert max(abs(p - 2100) for p in goals) == EXCURSION
        assert max(abs(b - a) for a, b in zip(goals, goals[1:])) == STEP
    assert all(bytes(registers[i][:40]) == original[i] for i in registers)
    motor_order = [i for i, data in writes if data[0] == 41]
    assert motor_order[:6] == list(range(1, 7))
    assert motor_order[6:] == sorted(motor_order[6:])


def test_powered_nonbase_joint_prevents_batch(rig):
    bus, review, registers, writes, state, run = setup(rig)
    registers[4][40] = 1
    with pytest.raises(BusError):
        run()
    assert writes == []


def test_known_powered_state_can_resume_and_all_holds_precede_excursions(rig):
    bus, review, registers, writes, state, run = setup(rig)
    review['torques'] = {str(i): 1 for i in range(1, 7)}
    for r in registers.values():
        r[40] = 1
        r[42:44] = (2100).to_bytes(2, 'little')
    state['auto_torque'] = True
    def event(row):
        if row['kind'] == 'goal_attempt' and row['position'] != 2100:
            assert bus.prepared == set(range(1, 7))
            assert all(r[40] == 1 for r in registers.values())
    result = run(event=event)
    assert result['status'] == 'SIX_SMALL_MOTOR_PROBES_MEASURED'
    assert [i for i, data in writes[:6]] == list(range(1, 7))
    assert all(int.from_bytes(data[2:4], 'little') == 2100 for _, data in writes[:6])


def test_hold_phase_rejects_excursion_before_other_holds(rig):
    bus, review, registers, writes, state, run = setup(rig)
    bus.select(1, 2100)
    with pytest.raises(BusError):
        bus.goal(1, 2092, 57, 1)
    with pytest.raises(BusError):
        bus.begin_probes()
    assert writes == []


def test_probe_accepts_below_preserved_hardware_temperature_limit(rig):
    bus, review, registers, writes, state, run = setup(rig)
    state['auto_torque'] = True
    registers[2][63] = 68
    assert run()['status'] == 'SIX_SMALL_MOTOR_PROBES_MEASURED'


@pytest.mark.parametrize('temperature,limit', [(70, 70), (30, 0), (30, 100)])
def test_factory_limit_and_unknown_limit_prevent_all_writes(rig, temperature, limit):
    bus, review, registers, writes, state, run = setup(rig)
    registers[2][13] = limit
    registers[2][63] = temperature
    with pytest.raises(BusError):
        run()
    assert writes == []


def test_base_probe_clearance_cannot_authorize_batch(rig):
    bus, review, registers, writes, state, run = setup(rig)
    review['status'] = 'CLEARED_FOR_SINGLE_BASE_PROBE'
    with pytest.raises(ValueError):
        run()
    assert writes == []


def test_other_joint_drift_stops_before_next_goal(rig):
    bus, review, registers, writes, state, run = setup(rig)
    state['auto_torque'] = True
    def frame():
        if writes:
            registers[3][56:58] = (2117).to_bytes(2, 'little')
        return {'pc_read_monotonic': state['clock'], 'pc_age_upper_s': .02}
    with pytest.raises(BusError):
        run(fresh_frame=frame)
    assert len(writes) == 1 and all(i == 1 for i, _ in writes)


def test_lost_ack_abandons_all_remaining_joints(rig):
    bus, review, registers, writes, state, run = setup(rig)
    state.update(auto_torque=True, lost_ack=True)
    with pytest.raises(BusTimeout):
        run()
    assert len(writes) == 1
    assert all(registers[i][40] == 0 for i in range(2, 7))


def test_transient_flag_pauses_without_more_goals_until_it_clears(rig):
    bus, review, registers, writes, state, run = setup(rig)
    state['auto_torque'] = True
    pauses = []
    def frame():
        registers[3][66] = int(bool(writes) and state['clock'] < .2)
        return {'pc_read_monotonic': state['clock'], 'pc_age_upper_s': .02}
    def event(row):
        if row['kind'] == 'pause_for_movement_flag':
            pauses.append(len(writes))
    result = run(fresh_frame=frame, event=event)
    assert result['status'] == 'SIX_SMALL_MOTOR_PROBES_MEASURED'
    assert pauses and all(count == 1 for count in pauses)


def test_persistent_flag_aborts_without_any_further_goal(rig):
    bus, review, registers, writes, state, run = setup(rig)
    state['auto_torque'] = True
    def frame():
        registers[3][66] = int(bool(writes))
        return {'pc_read_monotonic': state['clock'], 'pc_age_upper_s': .02}
    with pytest.raises(BusError, match='persisted'):
        run(fresh_frame=frame)
    assert len(writes) == 1


def test_guard_cannot_write_another_joint_or_exceed_probe_budget(rig):
    bus, review, registers, writes, state, run = setup(rig)
    with pytest.raises(BusError):
        bus.select(2, 2100)
    bus.select(1, 2100)
    for call in (lambda: bus.goal(2, 2100, 57, 1),
                 lambda: bus.goal(1, 2091, 57, 1),
                 lambda: bus.goal(1, 2102, 57, 1),
                 lambda: bus.write(1, 31, b'\0\0'),
                 lambda: bus.write(1, 40, b'\0'),
                 lambda: bus.transact(254, 3, b'\x28\x01')):
        with pytest.raises(BusError):
            call()
    assert writes == []
