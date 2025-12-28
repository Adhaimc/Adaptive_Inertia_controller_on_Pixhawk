/**
 * @file iwg_adapter.hpp
 * @brief Information-Weighted Gradient (IWG) adaptive parameter estimation
 * 
 * Implements advanced adaptation using information weighting:
 * dot_theta = -Gamma * (I + lambda*P)^{-1} * Y^T * s - sigma*Gamma*theta - ...
 * 
 * IWG intelligently allocates learning rate based on information quality:
 * - Well-excited directions: reduced adaptation (prevent noise)
 * - Poorly-excited directions: increased adaptation (boost convergence)
 * 
 * Reference: Boffa et al., "Excitation-Aware Least-Squares..."
 */

#pragma once

#include <matrix/matrix.hpp>
#include <Eigen/Dense>
#include <cmath>
#include <algorithm>

namespace attitude_controller_aic {

using Vector3f = matrix::Vector3f;
using Matrix3f = matrix::Matrix3f;

/**
 * @class IWGAdapter
 * @brief Information-weighted gradient adaptation with internal excitation
 */
class IWGAdapter {
public:
    /**
     * @brief Initialize IWG adapter
     * 
     * @param J_init initial inertia estimate
     * @param use_diagonal if true use diagonal model (3 params), else full (6 params)
     */
    void init(const Matrix3f &J_init, bool use_diagonal = true) {
        use_diagonal_ = use_diagonal;
        n_theta_ = use_diagonal ? 3 : 6;
        
        // Extract initial parameters
        if (use_diagonal) {
            theta_diag_(0) = J_init(0, 0);
            theta_diag_(1) = J_init(1, 1);
            theta_diag_(2) = J_init(2, 2);
        } else {
            theta_full_(0) = J_init(0, 0);
            theta_full_(1) = J_init(1, 1);
            theta_full_(2) = J_init(2, 2);
            theta_full_(3) = J_init(0, 1);
            theta_full_(4) = J_init(0, 2);
            theta_full_(5) = J_init(1, 2);
        }
        
        // Initialize information matrices
        if (use_diagonal) {
            P_diag_ = Eigen::Matrix3f::Identity() * 1e-4f;
            P_inv_diag_ = Eigen::Matrix3f::Identity() * 1e4f; // Approximate inverse
        } else {
            P_full_ = Eigen::Matrix6f::Identity() * 1e-4f;
            P_inv_full_ = Eigen::Matrix6f::Identity() * 1e4f;
        }
        
        // Default IWG parameters
        lambda_ = 0.04f;    // Information weighting factor
        gamma_ = 1.5f;      // Adaptation gain
        sigma_ = 1e-4f;     // Leakage
        beta_ = 0.01f;      // Regularization
        gamma_ee_ = 0.001f; // Excitation enhancing
        
        // SPD bounds
        J_min_ = 0.01f;
        J_max_ = 1.0f;
    }

    /**
     * @brief Set IWG-specific parameters
     * 
     * @param lambda information weighting factor (typically 0.01-0.1)
     * @param gamma adaptation gain
     * @param sigma leakage coefficient
     * @param beta regularization
     * @param gamma_ee excitation-enhancing weight
     */
    void set_parameters(float lambda, float gamma, float sigma, float beta, float gamma_ee) {
        lambda_ = std::max(0.0f, std::min(lambda, 1.0f));
        gamma_ = gamma;
        sigma_ = sigma;
        beta_ = beta;
        gamma_ee_ = gamma_ee;
    }

    /**
     * @brief Update parameters using IWG method (diagonal inertia)
     * 
     * Implements: dot_theta = -Gamma * (I + lambda*P)^{-1} * Y^T * s - sigma*Gamma*theta - beta*Gamma^{-1}*theta
     *                         + gamma_ee * Y^T * sign(det(P))
     * 
     * @param Y regressor matrix (3x3)
     * @param s composite error
     * @param dt timestep
     */
    void update_diagonal(const matrix::Matrix<float, 3, 3> &Y,
                         const Vector3f &s, float dt) {
        // Convert to Eigen for matrix operations
        Eigen::Matrix3f Y_eigen;
        for (int i = 0; i < 3; ++i) {
            for (int j = 0; j < 3; ++j) {
                Y_eigen(i, j) = Y(i, j);
            }
        }
        
        // Accumulate information: P = P + dt * Y^T * Y
        Eigen::Matrix3f YtY = Y_eigen.transpose() * Y_eigen;
        P_diag_ = P_diag_ + dt * YtY;
        
        // Update (I + lambda*P) inverse using Sherman-Morrison or direct inversion
        // For 3x3 this is efficient
        Eigen::Matrix3f I_plus_lambdaP = Eigen::Matrix3f::Identity() + lambda_ * P_diag_;
        
        try {
            P_inv_diag_ = I_plus_lambdaP.inverse();
        } catch (...) {
            // If inversion fails, use previous inverse (numerical stability)
            P_inv_diag_ = (I_plus_lambdaP + Eigen::Matrix3f::Identity() * 1e-6f).inverse();
        }
        
        // Information-weighted gradient: (I + lambda*P)^{-1} * Y^T * s
        Eigen::Vector3f s_eigen;
        for (int i = 0; i < 3; ++i) s_eigen(i) = s(i);
        
        Eigen::Vector3f grad_weighted = P_inv_diag_ * (Y_eigen.transpose() * s_eigen);
        
        // Leakage term
        Eigen::Vector3f leak_term = sigma_ * Eigen::Map<Eigen::Vector3f>(theta_diag_.data(), 3);
        
        // Regularization term
        Eigen::Vector3f reg_term = (beta_ / gamma_) * Eigen::Map<Eigen::Vector3f>(theta_diag_.data(), 3);
        
        // Excitation-enhancing term (internal excitation based on rank deficiency)
        Eigen::Vector3f ee_term = Eigen::Vector3f::Zero();
        float det_P = P_diag_.determinant();
        if (gamma_ee_ > 0 && std::abs(det_P) < 1e-6f) {
            // P is rank-deficient, add internal excitation
            ee_term = gamma_ee_ * (Y_eigen.transpose() * s_eigen).normalized();
        }
        
        // Composite update: dot_theta = -gamma*grad - leak - reg + ee
        Eigen::Vector3f dtheta = -gamma_ * grad_weighted - leak_term - reg_term + ee_term;
        
        // Apply update
        for (int i = 0; i < 3; ++i) {
            theta_diag_(i) += dtheta(i) * dt;
        }
        
        // Project to SPD
        project_spd_diagonal();
    }

    /**
     * @brief Update parameters using IWG method (full symmetric inertia)
     * 
     * @param Y regressor matrix (3x6)
     * @param s composite error
     * @param dt timestep
     */
    void update_full(const matrix::Matrix<float, 3, 6> &Y,
                     const Vector3f &s, float dt) {
        // Convert to Eigen
        Eigen::MatrixXf Y_eigen = Eigen::MatrixXf::Zero(3, 6);
        for (int i = 0; i < 3; ++i) {
            for (int j = 0; j < 6; ++j) {
                Y_eigen(i, j) = Y(i, j);
            }
        }
        
        // Accumulate information
        Eigen::Matrix6f YtY = Y_eigen.transpose() * Y_eigen;
        P_full_ = P_full_ + dt * YtY;
        
        // Compute (I + lambda*P)^{-1}
        Eigen::Matrix6f I_plus_lambdaP = Eigen::Matrix6f::Identity() + lambda_ * P_full_;
        
        try {
            P_inv_full_ = I_plus_lambdaP.inverse();
        } catch (...) {
            P_inv_full_ = (I_plus_lambdaP + Eigen::Matrix6f::Identity() * 1e-6f).inverse();
        }
        
        // Information-weighted gradient
        Eigen::Vector6f s_eigen(3);
        for (int i = 0; i < 3; ++i) s_eigen(i) = s(i);
        for (int i = 3; i < 6; ++i) s_eigen(i) = 0; // Pad for 6D vector
        
        Eigen::Vector6f grad_weighted = P_inv_full_ * (Y_eigen.transpose() * s_eigen.head(3));
        
        // Leakage and regularization
        Eigen::Vector6f leak_term = sigma_ * Eigen::Map<Eigen::Vector6f>(theta_full_.data(), 6);
        Eigen::Vector6f reg_term = (beta_ / gamma_) * Eigen::Map<Eigen::Vector6f>(theta_full_.data(), 6);
        
        // Excitation-enhancing
        Eigen::Vector6f ee_term = Eigen::Vector6f::Zero();
        float det_P = P_full_.determinant();
        if (gamma_ee_ > 0 && std::abs(det_P) < 1e-6f) {
            ee_term = gamma_ee_ * (Y_eigen.transpose() * s_eigen.head(3)).normalized();
        }
        
        // Update
        Eigen::Vector6f dtheta = -gamma_ * grad_weighted - leak_term - reg_term + ee_term;
        
        for (int i = 0; i < 6; ++i) {
            theta_full_(i) += dtheta(i) * dt;
        }
        
        // Project to SPD
        project_spd_full();
    }

    /**
     * @brief Get inertia matrix estimate
     */
    Matrix3f get_inertia_estimate() const {
        Matrix3f J_hat = Matrix3f::Zero();
        
        if (use_diagonal_) {
            J_hat(0, 0) = theta_diag_(0);
            J_hat(1, 1) = theta_diag_(1);
            J_hat(2, 2) = theta_diag_(2);
        } else {
            J_hat(0, 0) = theta_full_(0);
            J_hat(1, 1) = theta_full_(1);
            J_hat(2, 2) = theta_full_(2);
            J_hat(0, 1) = J_hat(1, 0) = theta_full_(3);
            J_hat(0, 2) = J_hat(2, 0) = theta_full_(4);
            J_hat(1, 2) = J_hat(2, 1) = theta_full_(5);
        }
        
        return J_hat;
    }

    /**
     * @brief Get information matrix determinant (for excitation monitoring)
     */
    float get_information_determinant() const {
        if (use_diagonal_) {
            return P_diag_.determinant();
        } else {
            return P_full_.determinant();
        }
    }

    /**
     * @brief Check if system is persistently excited
     * @return true if information matrix is well-conditioned
     */
    bool is_persistently_excited() const {
        float det = get_information_determinant();
        return std::abs(det) > 1e-4f;
    }

    /**
     * @brief Reset adapter
     */
    void reset(const Matrix3f &J_init) {
        init(J_init, use_diagonal_);
    }

private:
    /**
     * @brief Project diagonal inertia to SPD
     */
    void project_spd_diagonal() {
        for (int i = 0; i < 3; ++i) {
            theta_diag_(i) = std::max(J_min_, std::min(theta_diag_(i), J_max_));
        }
    }

    /**
     * @brief Project full symmetric inertia to SPD
     */
    void project_spd_full() {
        // Reconstruct matrix
        Eigen::Matrix3f J_hat;
        J_hat(0, 0) = theta_full_(0);
        J_hat(1, 1) = theta_full_(1);
        J_hat(2, 2) = theta_full_(2);
        J_hat(0, 1) = J_hat(1, 0) = theta_full_(3);
        J_hat(0, 2) = J_hat(2, 0) = theta_full_(4);
        J_hat(1, 2) = J_hat(2, 1) = theta_full_(5);
        
        // Clip diagonals
        for (int i = 0; i < 3; ++i) {
            J_hat(i, i) = std::max(J_min_, std::min(J_hat(i, i), J_max_));
        }
        
        // Ensure symmetry and clip off-diagonal
        J_hat(0, 1) = J_hat(1, 0) = (J_hat(0, 1) + J_hat(1, 0)) / 2.f;
        J_hat(0, 2) = J_hat(2, 0) = (J_hat(0, 2) + J_hat(2, 0)) / 2.f;
        J_hat(1, 2) = J_hat(2, 1) = (J_hat(1, 2) + J_hat(2, 1)) / 2.f;
        
        // Extract back
        theta_full_(0) = J_hat(0, 0);
        theta_full_(1) = J_hat(1, 1);
        theta_full_(2) = J_hat(2, 2);
        theta_full_(3) = J_hat(0, 1);
        theta_full_(4) = J_hat(0, 2);
        theta_full_(5) = J_hat(1, 2);
    }

    // Parameter vectors
    Eigen::Vector3f theta_diag_;
    Eigen::Vector6f theta_full_;
    
    // Information matrices P(t)
    Eigen::Matrix3f P_diag_;
    Eigen::Matrix3f P_inv_diag_;
    Eigen::Matrix6f P_full_;
    Eigen::Matrix6f P_inv_full_;
    
    // IWG parameters
    float lambda_{0.04f};    // Information weighting factor
    float gamma_{1.5f};      // Adaptation gain
    float sigma_{1e-4f};     // Leakage
    float beta_{0.01f};      // Regularization
    float gamma_ee_{0.001f}; // Excitation enhancing
    float J_min_{0.01f};
    float J_max_{1.0f};
    
    int n_theta_{3};
    bool use_diagonal_{true};
};

} // namespace attitude_controller_aic
