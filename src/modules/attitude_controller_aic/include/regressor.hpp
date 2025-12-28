/**
 * @file regressor.hpp
 * @brief Linear-in-parameters rigid-body torque regressor
 * 
 * Implements the regressor matrix Y(Omega, alpha) such that:
 * tau_rb = J*alpha - Omega x (J*Omega) = Y(Omega, alpha) * theta
 * 
 * where theta contains the inertia parameters (diagonal or full symmetric)
 */

#pragma once

#include <matrix/matrix.hpp>
#include "so3_utils.hpp"

namespace attitude_controller_aic {

using Vector3f = matrix::Vector3f;
using Matrix3f = matrix::Matrix3f;

/**
 * @class Regressor
 * @brief Rigid-body torque regressor (linear in inertia parameters)
 */
class Regressor {
public:
    /**
     * @brief Regressor matrix Y for diagonal inertia
     * 
     * For diagonal inertia J = diag(Jxx, Jyy, Jzz), the regressor is 3x3:
     *   Y_d = [ alpha_x,        Omega_y*Omega_z,       -Omega_y*Omega_z       ]
     *         [-Omega_x*Omega_z,  alpha_y,              Omega_x*Omega_z        ]
     *         [ Omega_x*Omega_y, -Omega_x*Omega_y,      alpha_z                ]
     * 
     * tau_rb = Y_d * [Jxx, Jyy, Jzz]^T
     * 
     * @param Omega angular velocity (rad/s)
     * @param alpha angular acceleration (rad/s^2)
     * @return 3x3 regressor matrix
     */
    static matrix::Matrix<float, 3, 3> regressor_diagonal(const Vector3f &Omega, const Vector3f &alpha) {
        float wx = Omega(0), wy = Omega(1), wz = Omega(2);
        float ax = alpha(0), ay = alpha(1), az = alpha(2);
        
        matrix::Matrix<float, 3, 3> Y;
        // Row 1: torque about x-axis
        Y(0, 0) = ax;              Y(0, 1) = wy * wz;        Y(0, 2) = -wy * wz;
        // Row 2: torque about y-axis
        Y(1, 0) = -wx * wz;        Y(1, 1) = ay;             Y(1, 2) = wx * wz;
        // Row 3: torque about z-axis
        Y(2, 0) = wx * wy;         Y(2, 1) = -wx * wy;       Y(2, 2) = az;
        
        return Y;
    }

    /**
     * @brief Regressor matrix Y for full symmetric inertia (6 parameters)
     * 
     * For full symmetric inertia with theta = [Jxx, Jyy, Jzz, Jxy, Jxz, Jyz]^T
     * 
     * tau_rb = J*alpha - Omega x (J*Omega)
     * where both J*alpha and Omega x (J*Omega) are linear in theta
     * 
     * @param Omega angular velocity
     * @param alpha angular acceleration
     * @return 3x6 regressor matrix
     */
    static matrix::Matrix<float, 3, 6> regressor_full(const Vector3f &Omega, const Vector3f &alpha) {
        float wx = Omega(0), wy = Omega(1), wz = Omega(2);
        float ax = alpha(0), ay = alpha(1), az = alpha(2);
        
        matrix::Matrix<float, 3, 6> Y;
        
        // Row 1: tau_x = Jxx*ax + Jxy*ay + Jxz*az + (Jyy*wy - Jyz*wz)*wz + (Jzz*wz - Jzz*wz)*wy - (Jyy*wy + Jyz*wz)*wz
        // tau_x = Jxx*ax + Jxy*(ay - wy*wz) + Jxz*(az + wy*wz) + Jyy*wy*wz - Jyz*(wy^2 - wz^2)
        Y(0, 0) = ax;                    // Jxx coefficient
        Y(0, 1) = wy * wz;               // Jyy coefficient
        Y(0, 2) = -wy * wz;              // Jzz coefficient
        Y(0, 3) = ay + wx * wz;          // Jxy coefficient
        Y(0, 4) = az - wx * wy;          // Jxz coefficient
        Y(0, 5) = -wy * wy + wz * wz;    // Jyz coefficient
        
        // Row 2: tau_y = Jxy*ax + Jyy*ay + Jyz*az + ...
        Y(1, 0) = -wx * wz;              // Jxx coefficient
        Y(1, 1) = ay;                    // Jyy coefficient
        Y(1, 2) = wx * wz;               // Jzz coefficient
        Y(1, 3) = ax - wy * wz;          // Jxy coefficient
        Y(1, 4) = wx * wx - wz * wz;     // Jxz coefficient
        Y(1, 5) = az + wx * wy;          // Jyz coefficient
        
        // Row 3: tau_z = Jxz*ax + Jyz*ay + Jzz*az + ...
        Y(2, 0) = wx * wy;               // Jxx coefficient
        Y(2, 1) = -wx * wy;              // Jyy coefficient
        Y(2, 2) = az;                    // Jzz coefficient
        Y(2, 3) = wy * wy - wx * wx;     // Jxy coefficient
        Y(2, 4) = ax + wy * wz;          // Jxz coefficient
        Y(2, 5) = ay - wx * wz;          // Jyz coefficient
        
        return Y;
    }

    /**
     * @brief Compute rigid-body torque from parameters and regressor
     * 
     * tau_rb = Y(Omega, alpha) * theta
     * 
     * @param Y regressor matrix (3x3 or 3x6)
     * @param theta inertia parameters (3D for diagonal, 6D for full)
     * @return 3D torque vector
     */
    static Vector3f compute_torque_diagonal(const matrix::Matrix<float, 3, 3> &Y, 
                                           const matrix::Matrix<float, 3, 1> &theta) {
        return Y * theta;
    }

    static Vector3f compute_torque_full(const matrix::Matrix<float, 3, 6> &Y,
                                       const matrix::Matrix<float, 6, 1> &theta) {
        return Y * theta;
    }

    /**
     * @brief Test regressor linearity (for validation)
     * 
     * Verify that Y*theta = J*alpha - Omega x (J*Omega) for known J
     * 
     * @param J true inertia matrix
     * @param theta inertia parameters extracted from J
     * @param Omega angular velocity
     * @param alpha angular acceleration
     * @param tolerance acceptable error norm
     * @return true if regressor is accurate within tolerance
     */
    static bool validate_regressor_diagonal(const Matrix3f &J,
                                           const matrix::Matrix<float, 3, 1> &theta,
                                           const Vector3f &Omega,
                                           const Vector3f &alpha,
                                           float tolerance = 1e-5f) {
        // Compute true rigid-body torque: tau = J*alpha - Omega x (J*Omega)
        Vector3f tau_true = J * alpha - SO3Utils::hat(Omega) * (J * Omega);
        
        // Compute via regressor
        auto Y = regressor_diagonal(Omega, alpha);
        Vector3f tau_regressor = Y * theta;
        
        // Compare
        float error = (tau_true - tau_regressor).norm();
        return error < tolerance;
    }

    static bool validate_regressor_full(const Matrix3f &J,
                                       const matrix::Matrix<float, 6, 1> &theta,
                                       const Vector3f &Omega,
                                       const Vector3f &alpha,
                                       float tolerance = 1e-5f) {
        // Compute true rigid-body torque
        Vector3f tau_true = J * alpha - SO3Utils::hat(Omega) * (J * Omega);
        
        // Compute via regressor
        auto Y = regressor_full(Omega, alpha);
        Vector3f tau_regressor = Y * theta;
        
        // Compare
        float error = (tau_true - tau_regressor).norm();
        return error < tolerance;
    }
};

} // namespace attitude_controller_aic
