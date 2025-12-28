/**
 * @file attitude_controller_aic.hpp
 * @brief Composite attitude controller combining geometric PD, adaptive feedforward, and robust damping
 * 
 * Implements the complete control law:
 * tau = -K_R * e_R - K_Omega * e_Omega + Y * theta_hat - K * s + tau_ee
 * 
 * where:
 * - Geometric PD: -K_R * e_R - K_Omega * e_Omega
 * - Adaptive feedforward: Y * theta_hat (learned inertia compensation)
 * - Robust damping: -K * s (attenuates unmodeled effects and noise)
 * - Internal excitation: tau_ee (activates when information is insufficient)
 */

#pragma once

#include <matrix/matrix.hpp>
#include "so3_utils.hpp"
#include "regressor.hpp"
#include "iwg_adapter.hpp"
#include <algorithm>
#include <cmath>

namespace attitude_controller_aic {

using Vector3f = matrix::Vector3f;
using Matrix3f = matrix::Matrix3f;
using Quaternionf = matrix::Quaternionf;

/**
 * @class AttitudeControllerAIC
 * @brief Adaptive Inertia-aware Composite attitude controller on SO(3)
 */
class AttitudeControllerAIC {
public:
    /**
     * @brief Initialize controller
     * 
     * @param J_init initial inertia estimate
     * @param use_diagonal use diagonal inertia model if true, else full symmetric
     * @param use_iwg use information-weighted gradient if true, else standard gradient
     */
    void init(const Matrix3f &J_init, bool use_diagonal = true, bool use_iwg = true) {
        use_diagonal_ = use_diagonal;
        use_iwg_ = use_iwg;
        
        if (use_iwg_) {
            iwg_adapter_.init(J_init, use_diagonal);
        } else {
            // Use basic adaptive estimator instead
            // (implementation would be similar but without IWG)
        }
        
        // Set default control gains (tuning dependent)
        // These values are conservative; tune based on vehicle dynamics
        K_R_ = Vector3f(5.0f, 5.0f, 3.0f);           // Attitude error gain
        K_Omega_ = Vector3f(0.3f, 0.3f, 0.2f);       // Angular velocity error gain
        K_ = Vector3f(0.1f, 0.1f, 0.1f);             // Robust damping gain
        c_ = 2.0f;                                     // Composite error weight
        
        // Actuator saturation (Nm)
        tau_max_ = 0.05f;
        
        // Composite error smoothing (low-pass filter for noise rejection)
        s_filter_alpha_ = 0.1f;  // Filter coefficient (larger = more smoothing)
        s_filtered_ = Vector3f::Zero();
    }

    /**
     * @brief Set control gains
     * 
     * @param K_R attitude error gain (diagonal elements)
     * @param K_Omega angular velocity error gain (diagonal elements)
     * @param K robust damping gain (diagonal elements)
     * @param c composite error weight
     */
    void set_control_gains(const Vector3f &K_R, const Vector3f &K_Omega,
                          const Vector3f &K, float c) {
        K_R_ = K_R;
        K_Omega_ = K_Omega;
        K_ = K;
        c_ = c;
    }

    /**
     * @brief Set adaptation parameters
     * 
     * @param gamma adaptation gain
     * @param sigma leakage coefficient
     * @param beta regularization gain
     * @param gamma_ee excitation-enhancing weight (IWG only)
     */
    void set_adaptation_params(float gamma, float sigma, float beta, float gamma_ee = 0.0f) {
        if (use_iwg_) {
            // For IWG: lambda, gamma, sigma, beta, gamma_ee
            iwg_adapter_.set_parameters(0.04f, gamma, sigma, beta, gamma_ee);
        }
    }

    /**
     * @brief Compute attitude control torque
     * 
     * Full control law with adaptive estimation
     * 
     * @param R current attitude (rotation matrix)
     * @param Omega current angular velocity (rad/s)
     * @param R_d desired attitude
     * @param Omega_d desired angular velocity
     * @param dot_Omega_d desired angular acceleration
     * @param dt timestep (for integration)
     * @return 3D control torque command (Nm)
     */
    Vector3f compute_torque(const Matrix3f &R, const Vector3f &Omega,
                           const Matrix3f &R_d, const Vector3f &Omega_d,
                           const Vector3f &dot_Omega_d, float dt) {
        // 1. Compute attitude errors
        Vector3f e_R = SO3Utils::attitude_error(R, R_d);
        Vector3f e_Omega = SO3Utils::angular_velocity_error(Omega, R, R_d, Omega_d);
        
        // 2. Compute composite error: s = e_Omega + c * e_R
        Vector3f s = e_Omega + c_ * e_R;
        
        // Low-pass filter composite error (noise rejection)
        s_filtered_ = s_filter_alpha_ * s + (1.f - s_filter_alpha_) * s_filtered_;
        
        // 3. Compute body-frame commanded angular acceleration
        Vector3f alpha = SO3Utils::commanded_angular_accel(R, R_d, Omega, Omega_d, dot_Omega_d);
        
        // 4. Get regressor matrix Y(Omega, alpha)
        Vector3f tau_adaptive;
        if (use_diagonal_) {
            auto Y = Regressor::regressor_diagonal(Omega, alpha);
            
            // 5. Update adaptive parameters and get estimate
            if (use_iwg_) {
                iwg_adapter_.update_diagonal(Y, s_filtered_, dt);
            }
            
            // Get inertia estimate
            Matrix3f J_hat = iwg_adapter_.get_inertia_estimate();
            
            // Compute adaptive feedforward: Y * J_hat parameters
            matrix::Vector<float, 3> theta_hat;
            theta_hat(0) = J_hat(0, 0);
            theta_hat(1) = J_hat(1, 1);
            theta_hat(2) = J_hat(2, 2);
            tau_adaptive = Y * theta_hat;
        } else {
            auto Y = Regressor::regressor_full(Omega, alpha);
            
            if (use_iwg_) {
                iwg_adapter_.update_full(Y, s_filtered_, dt);
            }
            
            Matrix3f J_hat = iwg_adapter_.get_inertia_estimate();
            
            matrix::Vector<float, 6> theta_hat;
            theta_hat(0) = J_hat(0, 0);
            theta_hat(1) = J_hat(1, 1);
            theta_hat(2) = J_hat(2, 2);
            theta_hat(3) = J_hat(0, 1);
            theta_hat(4) = J_hat(0, 2);
            theta_hat(5) = J_hat(1, 2);
            tau_adaptive = Y * theta_hat;
        }
        
        // 6. Compute geometric PD feedback
        Vector3f tau_pd;
        for (int i = 0; i < 3; ++i) {
            tau_pd(i) = -K_R_(i) * e_R(i) - K_Omega_(i) * e_Omega(i);
        }
        
        // 7. Compute robust damping term
        Vector3f tau_robust;
        for (int i = 0; i < 3; ++i) {
            tau_robust(i) = -K_(i) * s_filtered_(i);
        }
        
        // 8. Compose total torque: tau = tau_pd + tau_adaptive + tau_robust
        Vector3f tau = tau_pd + tau_adaptive + tau_robust;
        
        // 9. Apply actuator saturation
        tau = saturate(tau, tau_max_);
        
        return tau;
    }

    /**
     * @brief Get current inertia matrix estimate
     */
    Matrix3f get_inertia_estimate() const {
        return iwg_adapter_.get_inertia_estimate();
    }

    /**
     * @brief Check persistent excitation status
     * @return true if system has sufficient information for learning
     */
    bool is_persistently_excited() const {
        return iwg_adapter_.is_persistently_excited();
    }

    /**
     * @brief Get information matrix determinant
     */
    float get_information_quality() const {
        return iwg_adapter_.get_information_determinant();
    }

    /**
     * @brief Reset controller state
     */
    void reset(const Matrix3f &J_init) {
        iwg_adapter_.reset(J_init);
        s_filtered_ = Vector3f::Zero();
    }

    /**
     * @brief Set actuator saturation limit
     */
    void set_saturation_limit(float tau_max) {
        tau_max_ = std::max(0.01f, tau_max);  // Ensure positive
    }

    /**
     * @brief Set composite error filter bandwidth
     * @param alpha filter coefficient (0-1, larger = faster response)
     */
    void set_filter_bandwidth(float alpha) {
        s_filter_alpha_ = std::max(0.0f, std::min(alpha, 1.0f));
    }

private:
    /**
     * @brief Apply actuator saturation with smooth clipping
     * 
     * Saturates each component independently to ±tau_max
     * 
     * @param tau unsaturated torque
     * @param tau_max saturation limit (magnitude)
     * @return saturated torque
     */
    Vector3f saturate(const Vector3f &tau, float tau_max) {
        Vector3f tau_sat;
        for (int i = 0; i < 3; ++i) {
            tau_sat(i) = std::max(-tau_max, std::min(tau(i), tau_max));
        }
        return tau_sat;
    }

    // Adaptive estimator (IWG)
    IWGAdapter iwg_adapter_;
    
    // Control gains
    Vector3f K_R_;        // Attitude error gain
    Vector3f K_Omega_;    // Angular velocity gain
    Vector3f K_;          // Robust damping gain
    float c_{2.0f};       // Composite error weight
    
    // Actuator constraints
    float tau_max_{0.05f};
    
    // Filtering for noise rejection
    Vector3f s_filtered_;
    float s_filter_alpha_{0.1f};
    
    // Configuration
    bool use_diagonal_{true};
    bool use_iwg_{true};
};

} // namespace attitude_controller_aic
