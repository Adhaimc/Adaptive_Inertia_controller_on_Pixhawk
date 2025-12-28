/**
 * @file AttitudeControllerAIC.cpp
 * @brief PX4 Module wrapper for Adaptive Inertia-aware Composite attitude controller
 * 
 * Integrates the AIC controller with PX4's attitude control pipeline
 * Subscribes to: vehicle attitude, reference trajectory, IMU
 * Publishes to: motor commands (actuator outputs)
 */

#include <px4_platform_common/px4_config.h>
#include <px4_platform_common/tasks.h>
#include <px4_platform_common/defines.h>
#include <px4_platform_common/module.h>
#include <px4_platform_common/module_params.h>

#include <drivers/drv_hrt.h>
#include <lib/mathlib/mathlib.h>
#include <matrix/matrix/Matrix.hpp>

#include <uORB/topics/vehicle_attitude.h>
#include <uORB/topics/vehicle_attitude_setpoint.h>
#include <uORB/topics/vehicle_rates_setpoint.h>
#include <uORB/topics/actuator_controls.h>
#include <uORB/topics/parameter_update.h>

#include "attitude_controller_aic.hpp"

using namespace attitude_controller_aic;
using namespace matrix;

class AttitudeControllerAICModule : public ModuleBase<AttitudeControllerAICModule>, public ModuleParams {
public:
    AttitudeControllerAICModule();
    ~AttitudeControllerAICModule();

    static int task_spawn(int argc, char *argv[]);
    static int custom_command(int argc, char *argv[]);
    static int print_usage(const char *reason = nullptr);

    void init();
    void run();

private:
    // Vehicle state subscriptions
    int _vehicle_attitude_sub{-1};
    int _vehicle_attitude_setpoint_sub{-1};
    int _vehicle_rates_setpoint_sub{-1};
    int _parameter_update_sub{-1};

    // Actuator output publication
    orb_advert_t _actuator_controls_pub{nullptr};

    // Controller instance
    AttitudeControllerAIC _controller;

    // State data
    vehicle_attitude_s _vehicle_attitude{};
    vehicle_attitude_setpoint_s _attitude_setpoint{};
    vehicle_rates_setpoint_s _rates_setpoint{};
    actuator_controls_s _actuator_controls{};

    // Timing
    uint64_t _last_run{0};
    float _dt{0.01f};  // 100 Hz control loop

    // Parameters
    DEFINE_PARAMETERS(
        (ParamFloat<px4::params::MC_ROLL_P>) _param_mc_roll_p,
        (ParamFloat<px4::params::MC_PITCH_P>) _param_mc_pitch_p,
        (ParamFloat<px4::params::MC_YAW_P>) _param_mc_yaw_p,
        (ParamFloat<px4::params::MC_ROLLRATE_P>) _param_mc_rollrate_p,
        (ParamFloat<px4::params::MC_PITCHRATE_P>) _param_mc_pitchrate_p,
        (ParamFloat<px4::params::MC_YAWRATE_P>) _param_mc_yawrate_p
    );

    void update_parameters();
    void update_vehicle_state();
    void compute_control();
    void publish_motor_commands(const Vector3f &tau);
};

AttitudeControllerAICModule::AttitudeControllerAICModule() : ModuleBase(), ModuleParams(nullptr) {
    // Initialize default inertia (quadcopter typical values)
    Matrix3f J_init = Matrix3f::Zero();
    J_init(0, 0) = 0.040f;  // Ixx (kg*m^2)
    J_init(1, 1) = 0.040f;  // Iyy
    J_init(2, 2) = 0.025f;  // Izz

    _controller.init(J_init, true, true);  // diagonal inertia, use IWG

    // Set default control gains
    Vector3f K_R(5.0f, 5.0f, 3.0f);
    Vector3f K_Omega(0.3f, 0.3f, 0.2f);
    Vector3f K_robust(0.1f, 0.1f, 0.1f);
    _controller.set_control_gains(K_R, K_Omega, K_robust, 2.0f);

    // Set adaptation parameters
    _controller.set_adaptation_params(1.5f, 1e-4f, 0.01f, 0.001f);

    // Set actuator limits (typically ±0.05 Nm for quadcopters)
    _controller.set_saturation_limit(0.05f);
}

AttitudeControllerAICModule::~AttitudeControllerAICModule() {
}

void AttitudeControllerAICModule::init() {
    // Subscribe to required topics
    _vehicle_attitude_sub = orb_subscribe(ORB_ID(vehicle_attitude));
    _vehicle_attitude_setpoint_sub = orb_subscribe(ORB_ID(vehicle_attitude_setpoint));
    _vehicle_rates_setpoint_sub = orb_subscribe(ORB_ID(vehicle_rates_setpoint));
    _parameter_update_sub = orb_subscribe(ORB_ID(parameter_update));

    // Advertise actuator controls output
    _actuator_controls.group[0] = ACTUATOR_CONTROLS_GROUP_MC_ATTITUDE;
    _actuator_controls_pub = orb_advertise(ORB_ID(actuator_controls_0), &_actuator_controls);
}

void AttitudeControllerAICModule::update_parameters() {
    // Check for parameter updates
    bool param_updated = false;
    orb_check(_parameter_update_sub, &param_updated);

    if (param_updated) {
        orb_copy(ORB_ID(parameter_update), _parameter_update_sub, nullptr);

        // Update module parameters
        updateParams();

        // Extract PX4 gain parameters and apply to controller
        Vector3f K_R(_param_mc_roll_p.get(), _param_mc_pitch_p.get(), _param_mc_yaw_p.get());
        Vector3f K_Omega(_param_mc_rollrate_p.get(), _param_mc_pitchrate_p.get(),
                         _param_mc_yawrate_p.get());

        Vector3f K_robust(0.1f, 0.1f, 0.1f);  // Default robust gain
        _controller.set_control_gains(K_R, K_Omega, K_robust, 2.0f);

        PX4_INFO("AIC Controller parameters updated");
    }
}

void AttitudeControllerAICModule::update_vehicle_state() {
    // Get latest attitude measurement
    orb_copy(ORB_ID(vehicle_attitude), _vehicle_attitude_sub, &_vehicle_attitude);

    // Get attitude setpoint (desired attitude)
    orb_copy(ORB_ID(vehicle_attitude_setpoint), _vehicle_attitude_setpoint_sub, &_attitude_setpoint);

    // Get rate setpoint (if using rate control mode)
    orb_copy(ORB_ID(vehicle_rates_setpoint), _vehicle_rates_setpoint_sub, &_rates_setpoint);
}

void AttitudeControllerAICModule::compute_control() {
    // Convert PX4 quaternion to rotation matrix
    Quaternionf q(_vehicle_attitude.q[0], _vehicle_attitude.q[1], _vehicle_attitude.q[2],
                  _vehicle_attitude.q[3]);
    Matrix3f R = q.to_dcm();

    // Current angular velocity (from gyro)
    Vector3f omega(_vehicle_attitude.rollspeed, _vehicle_attitude.pitchspeed,
                   _vehicle_attitude.yawspeed);

    // Convert desired quaternion to rotation matrix
    Quaternionf q_d(_attitude_setpoint.q_d[0], _attitude_setpoint.q_d[1],
                    _attitude_setpoint.q_d[2], _attitude_setpoint.q_d[3]);
    Matrix3f R_d = q_d.to_dcm();

    // Desired rates
    Vector3f omega_d(_attitude_setpoint.roll_body, _attitude_setpoint.pitch_body,
                     _attitude_setpoint.yaw_body);

    // Desired angular acceleration (can be zero for nominal tracking)
    Vector3f alpha_d = Vector3f::Zero();

    // Compute control torque
    Vector3f tau = _controller.compute_torque(R, omega, R_d, omega_d, alpha_d, _dt);

    // Publish control torque as motor commands
    publish_motor_commands(tau);
}

void AttitudeControllerAICModule::publish_motor_commands(const Vector3f &tau) {
    // Convert torque commands to motor commands for quadcopter
    // This is a simple linear mapping; actual mixing depends on motor configuration
    // 
    // Typical quadcopter motor mixing (X configuration):
    // M1 (front-right)  : +tau_roll + tau_pitch - tau_yaw + thrust
    // M2 (rear-left)    : +tau_roll - tau_pitch - tau_yaw + thrust
    // M3 (front-left)   : -tau_roll + tau_pitch - tau_yaw + thrust
    // M4 (rear-right)   : -tau_roll - tau_pitch - tau_yaw + thrust
    //
    // For attitude-only control (simplification):
    // Normalize tau to [-1, 1] range

    float tau_max = 0.05f;  // Maximum torque (Nm)
    float norm_roll = tau(0) / tau_max;
    float norm_pitch = tau(1) / tau_max;
    float norm_yaw = tau(2) / tau_max;

    // Clamp to [-1, 1]
    norm_roll = math::constrain(norm_roll, -1.0f, 1.0f);
    norm_pitch = math::constrain(norm_pitch, -1.0f, 1.0f);
    norm_yaw = math::constrain(norm_yaw, -1.0f, 1.0f);

    // Simple mixing for quadcopter (would be customized per frame type)
    _actuator_controls.control[0] = norm_roll;
    _actuator_controls.control[1] = norm_pitch;
    _actuator_controls.control[2] = norm_yaw;
    _actuator_controls.control[3] = 0.5f;  // Thrust (should come from altitude controller)

    _actuator_controls.timestamp = hrt_absolute_time();

    orb_publish(ORB_ID(actuator_controls_0), _actuator_controls_pub, &_actuator_controls);
}

void AttitudeControllerAICModule::run() {
    // Wait for first measurement
    bool first_run = true;

    while (!should_exit()) {
        // Wait for new attitude measurement (poll-based)
        int ret = poll(&_vehicle_attitude_sub, 1, 50);  // 50 ms timeout

        if (ret > 0 && !_vehicle_attitude_sub_updated) {
            continue;
        }

        uint64_t now = hrt_absolute_time();

        if (first_run) {
            _last_run = now;
            first_run = false;
            continue;
        }

        // Calculate timestep
        _dt = (now - _last_run) * 1e-6f;  // Convert microseconds to seconds
        _last_run = now;

        // Clamp dt to reasonable bounds
        _dt = math::constrain(_dt, 0.002f, 0.1f);  // 5 Hz to 500 Hz

        // Update parameters
        update_parameters();

        // Get latest vehicle state
        update_vehicle_state();

        // Compute control torque
        compute_control();
    }
}

int AttitudeControllerAICModule::task_spawn(int argc, char *argv[]) {
    AttitudeControllerAICModule *instance = new AttitudeControllerAICModule();

    if (instance) {
        _object.store(instance);
        _task_id = px4_task_spawn_cmd("attitude_controller_aic",
                                      SCHED_DEFAULT,
                                      SCHED_PRIORITY_MAX - 5,
                                      2048,
                                      (px4_main_t)&task_main_wrapper,
                                      (char *const *)argv);

        if (_task_id < 0) {
            PX4_ERR("task spawn failed");
            delete instance;
            _object.store(nullptr);
            _task_id = -1;
            return -errno;
        }

        return PX4_OK;
    }

    PX4_ERR("alloc failed");
    return -ENOMEM;
}

int AttitudeControllerAICModule::custom_command(int argc, char *argv[]) {
    // Custom shell commands can be added here
    return print_usage("unknown command");
}

int AttitudeControllerAICModule::print_usage(const char *reason) {
    if (reason) {
        PX4_WARN("%s\n", reason);
    }

    PRINT_MODULE_DESCRIPTION(
        R"DESCR_STR(
### Description
Adaptive Inertia-aware Composite (AIC) attitude controller for multicopters.

Implements geometric PD control on SO(3) with online adaptive inertia estimation.

### Usage
{
    start [-d <device>] [-a <address>]
    stop
    status
}
)DESCR_STR"
    );

    return 0;
}

extern "C" __EXPORT int attitude_controller_aic_main(int argc, char *argv[]);

int attitude_controller_aic_main(int argc, char *argv[]) {
    return AttitudeControllerAICModule::main(argc, argv);
}
