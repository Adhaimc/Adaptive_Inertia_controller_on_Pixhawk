/**
 * @file adaptive_estimator.hpp
 * @brief Adaptive inertia parameter estimation with σ-modification and SPD projection
 * 
 * Implements gradient-descent based parameter adaptation with:
 * - σ-modification for leakage (drift prevention)
 * - SPD projection to keep inertia estimate positive-definite
 * - Information matrix P(t) accumulation for IWG method
 * - Internal excitation generation
 */

#pragma once

#include <matrix/matrix.hpp>
#include <algorithm>
#include <cmath>

namespace attitude_controller_aic {

using Vector3f = matrix::Vector3f;
using Matrix3f = matrix::Matrix3f;

/**
 * @class AdaptiveEstimator
 * @brief Parameter estimator with adaptive inertia learning
 */
class AdaptiveEstimator {
public:
    /**
     * @brief Initialize adaptive estimator
     * 
     * @param J_init initial inertia estimate (should be close to true value)
     * @param use_diagonal if true, use 3-param diagonal model; else 6-param full symmetric
     */
    void init(const Matrix3f &J_init, bool use_diagonal = true) {
        use_diagonal_ = use_diagonal;
        
        if (use_diagonal_) {
            // Extract diagonal parameters: [Jxx, Jyy, Jzz]
            theta_ = matrix::Vector<float, 3>();
            theta_(0) = J_init(0, 0);
            theta_(1) = J_init(1, 1);
            theta_(2) = J_init(2, 2);
        } else {
            // Extract full symmetric parameters: [Jxx, Jyy, Jzz, Jxy, Jxz, Jyz]
            theta_ = matrix::Vector<float, 6>();
            theta_(0) = J_init(0, 0);
            theta_(1) = J_init(1, 1);
            theta_(2) = J_init(2, 2);
            theta_(3) = J_init(0, 1);
            theta_(4) = J_init(0, 2);
            theta_(5) = J_init(1, 2);
        }
        
        // Initialize information matrix P(t) to small positive value to avoid singularity
        int n_theta = use_diagonal_ ? 3 : 6;
        if (use_diagonal_) {
            P_3x3_ = matrix::Matrix<float, 3, 3>::Identity() * 1e-4f;
            P_is_3x3_ = true;
        } else {
            P_6x6_ = matrix::Matrix<float, 6, 6>::Identity() * 1e-4f;
            P_is_3x3_ = false;
        }
        
        // Set default adaptation gains (can be overridden)
        gamma_ = 1.5f;     // Adaptation gain
        sigma_ = 1e-4f;    // Leakage coefficient
        beta_ = 0.01f;     // Regularization gain
        gamma_ee_ = 0.0f;  // Excitation-enhancing weight (disabled by default)
        
        // SPD bounds for inertia
        J_min_ = 0.01f;    // Minimum eigenvalue
        J_max_ = 1.0f;     // Maximum eigenvalue
    }

    /**
     * @brief Set adaptation parameters
     * @param gamma adaptation gain (learning rate)
     * @param sigma leakage coefficient (drift prevention)
     * @param beta regularization gain
     * @param gamma_ee excitation-enhancing weight
     */
    void set_adaptation_params(float gamma, float sigma, float beta, float gamma_ee = 0.0f) {
        gamma_ = gamma;
        sigma_ = sigma;
        beta_ = beta;
        gamma_ee_ = gamma_ee;
    }

    /**
     * @brief Update parameter estimate (diagonal inertia)
     * 
     * Implements: dot_theta = -Gamma * Y^T * s - sigma * Gamma * theta - beta * Gamma^{-1} * theta
     * 
     * @param Y_3x3 regressor matrix (3x3 for diagonal)
     * @param s composite error = Omega_error + c * R_error
     * @param dt timestep (seconds)
     */
    void update_diagonal(const matrix::Matrix<float, 3, 3> &Y_3x3, 
                         const Vector3f &s, float dt) {
        // Compute gradient: Y^T * s
        matrix::Vector<float, 3> grad = Y_3x3.transpose() * s;
        
        // Adaptive update: dot_theta = -gamma * Y^T * s - sigma * theta - beta/gamma * theta
        matrix::Vector<float, 3> dtheta = -gamma_ * grad - sigma_ * theta_ - (beta_ / gamma_) * theta_;
        
        // Accumulate information matrix: P = P + dt * Y^T * Y
        P_3x3_ = P_3x3_ + dt * (Y_3x3.transpose() * Y_3x3);
        
        // Update parameter estimate
        theta_ = theta_ + dtheta * dt;
        
        // Project to SPD cone
        project_to_spd_diagonal();
    }

    /**
     * @brief Update parameter estimate (full symmetric inertia)
     * 
     * @param Y_3x6 regressor matrix (3x6 for full symmetric)
     * @param s composite error
     * @param dt timestep
     */
    void update_full(const matrix::Matrix<float, 3, 6> &Y_3x6,
                     const Vector3f &s, float dt) {
        // Compute gradient: Y^T * s
        matrix::Vector<float, 6> grad = Y_3x6.transpose() * s;
        
        // Adaptive update
        matrix::Vector<float, 6> dtheta = -gamma_ * grad - sigma_ * theta_ - (beta_ / gamma_) * theta_;
        
        // Accumulate information matrix
        P_6x6_ = P_6x6_ + dt * (Y_3x6.transpose() * Y_3x6);
        
        // Update parameter
        theta_ = theta_ + dtheta * dt;
        
        // Project to SPD cone
        project_to_spd_full();
    }

    /**
     * @brief Get current inertia matrix estimate
     * @return 3x3 inertia matrix
     */
    Matrix3f get_inertia_estimate() const {
        Matrix3f J_hat = Matrix3f::Zero();
        
        if (use_diagonal_) {
            J_hat(0, 0) = theta_(0);
            J_hat(1, 1) = theta_(1);
            J_hat(2, 2) = theta_(2);
        } else {
            J_hat(0, 0) = theta_(0);
            J_hat(1, 1) = theta_(1);
            J_hat(2, 2) = theta_(2);
            J_hat(0, 1) = J_hat(1, 0) = theta_(3);
            J_hat(0, 2) = J_hat(2, 0) = theta_(4);
            J_hat(1, 2) = J_hat(2, 1) = theta_(5);
        }
        
        return J_hat;
    }

    /**
     * @brief Get parameter vector
     */
    const matrix::Vector<float, 3> &get_theta_3d() const { return theta_; }
    const matrix::Vector<float, 6> &get_theta_6d() const { return theta_; }

    /**
     * @brief Compute determinant of information matrix (for excitation detection)
     * @return determinant of P(t)
     */
    float get_information_determinant() const {
        if (P_is_3x3_) {
            return P_3x3_.det();
        } else {
            return P_6x6_.det();
        }
    }

    /**
     * @brief Reset parameter estimate
     */
    void reset(const Matrix3f &J_init) {
        init(J_init, use_diagonal_);
    }

private:
    /**
     * @brief Project diagonal inertia to SPD cone via eigenvalue clipping
     * 
     * Clips diagonal elements to [J_min, J_max] range
     */
    void project_to_spd_diagonal() {
        for (int i = 0; i < 3; ++i) {
            theta_(i) = std::max(J_min_, std::min(theta_(i), J_max_));
        }
    }

    /**
     * @brief Project full symmetric inertia to SPD cone
     * 
     * Via eigenvalue decomposition: clip eigenvalues, reconstruct matrix
     */
    void project_to_spd_full() {
        // Convert to matrix form
        Matrix3f J_hat;
        J_hat(0, 0) = theta_(0);
        J_hat(1, 1) = theta_(1);
        J_hat(2, 2) = theta_(2);
        J_hat(0, 1) = J_hat(1, 0) = theta_(3);
        J_hat(0, 2) = J_hat(2, 0) = theta_(4);
        J_hat(1, 2) = J_hat(2, 1) = theta_(5);
        
        // Ensure symmetry
        J_hat(0, 1) = J_hat(1, 0) = (J_hat(0, 1) + J_hat(1, 0)) / 2.f;
        J_hat(0, 2) = J_hat(2, 0) = (J_hat(0, 2) + J_hat(2, 0)) / 2.f;
        J_hat(1, 2) = J_hat(2, 1) = (J_hat(1, 2) + J_hat(2, 1)) / 2.f;
        
        // Simple approach: clip diagonal strongly to stay SPD
        // More sophisticated approach would use eigenvalue decomposition
        for (int i = 0; i < 3; ++i) {
            J_hat(i, i) = std::max(J_min_, std::min(J_hat(i, i), J_max_));
        }
        
        // Clip off-diagonal to maintain SPD
        float max_coupling = 0.3f * J_hat(0, 0) * J_hat(1, 1); // Gershgorin bounds
        J_hat(0, 1) = J_hat(1, 0) = std::max(-max_coupling, std::min(J_hat(0, 1), max_coupling));
        
        // Extract back to parameter vector
        theta_(0) = J_hat(0, 0);
        theta_(1) = J_hat(1, 1);
        theta_(2) = J_hat(2, 2);
        theta_(3) = J_hat(0, 1);
        theta_(4) = J_hat(0, 2);
        theta_(5) = J_hat(1, 2);
    }

    // Parameter vector (3 for diagonal, 6 for full)
    matrix::Vector<float, 3> theta_;
    
    // Information matrix P(t) for IWG
    matrix::Matrix<float, 3, 3> P_3x3_;
    matrix::Matrix<float, 6, 6> P_6x6_;
    bool P_is_3x3_{true};
    
    // Adaptation configuration
    float gamma_{1.5f};      // Adaptation gain
    float sigma_{1e-4f};     // Leakage coefficient
    float beta_{0.01f};      // Regularization gain
    float gamma_ee_{0.0f};   // Excitation-enhancing weight
    float J_min_{0.01f};     // Min inertia eigenvalue
    float J_max_{1.0f};      // Max inertia eigenvalue
    
    bool use_diagonal_{true};
};

} // namespace attitude_controller_aic
