package com.figbot.scanner.so101;

/** UI intent from measured torque; DISARMED alone does not mean torque is off. */
public final class HoldControl {
    public enum Action { HOLD, RELEASE, WAIT, UNKNOWN }
    public static Action action(RobotController controller) {
        if (controller == null) return Action.UNKNOWN;
        var feedback = controller.feedback();
        return action(controller.state(), feedback.size(),
                (int) feedback.values().stream().filter(f -> f.torque() != 0).count());
    }
    public static Action action(RobotController.State state, int feedbackCount, int enabledCount) {
        if (state == RobotController.State.MOVING || state == RobotController.State.STOPPING) return Action.WAIT;
        if (feedbackCount != 6) return Action.UNKNOWN;
        if (enabledCount > 0) return Action.RELEASE;
        return state == RobotController.State.DISARMED ? Action.HOLD : Action.UNKNOWN;
    }
    private HoldControl() {}
}
