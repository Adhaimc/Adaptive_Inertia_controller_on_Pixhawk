/**
 * @file so3_utils.hpp
 * @brief SO(3) mathematical utilities for geometric attitude control
 * 
 * Implements vee/hat maps, attitude error computation, and kinematics on SO(3)
 * Reference: Lee et al. "Geometric Tracking Control of a Quadrotor UAV on SE(3)"
 */

#pragma once

#include <matrix/matrix.hpp>
#include <cmath>

namespace attitude_controller_aic {

using Vector3f = matrix::Vector3f;
using Matrix3f = matrix::Matrix3f;
using Quaternionf = matrix::Quaternionf;

/**
 * @class SO3Utils
 * @brief Static utilities for SO(3) geometry and attitude control
 */
class SO3Utils {
public:
    /**
     * @brief Hat map: converts vector to skew-symmetric matrix
     * @param v 3D vector [v_x, v_y, v_z]
     * @return 3x3 skew-symmetric matrix
     */
    static Matrix3f hat(const Vector3f &v) {
        Matrix3f v_hat;
        v_hat(0, 0) = 0.f;      v_hat(0, 1) = -v(2);   v_hat(0, 2) = v(1);
        v_hat(1, 0) = v(2);     v_hat(1, 1) = 0.f;     v_hat(1, 2) = -v(0);
        v_hat(2, 0) = -v(1);    v_hat(2, 1) = v(0);    v_hat(2, 2) = 0.f;
        return v_hat;
    }

    /**
     * @brief Vee map: extracts vector from skew-symmetric matrix
     * @param v_hat 3x3 skew-symmetric matrix
     * @return 3D vector
     */
    static Vector3f vee(const Matrix3f &v_hat) {
        return Vector3f(v_hat(2, 1), v_hat(0, 2), v_hat(1, 0));
    }

    /**
     * @brief Compute attitude error on SO(3)
     * 
     * Error measure: e_R = 0.5 * vee(R_d^T * R - R^T * R_d)
     * This is the standard SO(3) tracking error used in geometric control
     * 
     * @param R current attitude (rotation matrix)
     * @param R_d desired attitude (rotation matrix)
     * @return 3D attitude error vector
     */
    static Vector3f attitude_error(const Matrix3f &R, const Matrix3f &R_d) {
        // Compute R_d^T * R
        Matrix3f R_error = R_d.transpose() * R;
        // e_R = 0.5 * vee(R_d^T * R - R^T * R_d) = 0.5 * vee(R_error - R_error^T)
        return 0.5f * vee(R_error - R_error.transpose());
    }

    /**
     * @brief Compute angular velocity error
     * 
     * e_Omega = Omega - R^T * R_d * Omega_d
     * 
     * @param Omega current angular velocity (body frame)
     * @param R current attitude
     * @param R_d desired attitude
     * @param Omega_d desired angular velocity
     * @return 3D angular velocity error
     */
    static Vector3f angular_velocity_error(const Vector3f &Omega, const Matrix3f &R,
                                          const Matrix3f &R_d, const Vector3f &Omega_d) {
        // E = R^T * R_d
        Matrix3f E = R.transpose() * R_d;
        return Omega - E * Omega_d;
    }

    /**
     * @brief Compute body-frame commanded angular acceleration
     * 
     * alpha = E * dot_Omega_d - hat(Omega) * E * Omega_d
     * where E = R^T * R_d
     * 
     * @param R current attitude
     * @param R_d desired attitude
     * @param Omega current angular velocity
     * @param Omega_d desired angular velocity
     * @param dot_Omega_d desired angular acceleration
     * @return 3D commanded angular acceleration in body frame
     */
    static Vector3f commanded_angular_accel(const Matrix3f &R, const Matrix3f &R_d,
                                            const Vector3f &Omega, const Vector3f &Omega_d,
                                            const Vector3f &dot_Omega_d) {
        Matrix3f E = R.transpose() * R_d;
        return E * dot_Omega_d - hat(Omega) * E * Omega_d;
    }

    /**
     * @brief Compute trace-based attitude error measure (for Lyapunov function)
     * 
     * Psi = (1 - tr(R^T * R_d)) / 2
     * Used in attitude Lyapunov function for stability analysis
     * 
     * @param R current attitude
     * @param R_d desired attitude
     * @return Scalar error measure
     */
    static float trace_attitude_error(const Matrix3f &R, const Matrix3f &R_d) {
        // Psi = (1 - tr(R^T * R_d)) / 2 = (3 - tr(R^T * R_d)) / 2
        float trace = (R.transpose() * R_d).trace();
        return (3.f - trace) / 2.f;
    }

    /**
     * @brief Time derivative of trace error (for Lyapunov analysis)
     * 
     * dot_Psi = e_R^T * e_Omega
     * 
     * @param e_R attitude error
     * @param e_Omega angular velocity error
     * @return Scalar rate of error
     */
    static float trace_attitude_error_rate(const Vector3f &e_R, const Vector3f &e_Omega) {
        return e_R.dot(e_Omega);
    }

    /**
     * @brief Convert quaternion to rotation matrix
     * @param q quaternion
     * @return 3x3 rotation matrix
     */
    static Matrix3f quat_to_dcm(const Quaternionf &q) {
        return q.to_dcm();
    }

    /**
     * @brief Verify rotation matrix properties (for numerical validation)
     * @param R rotation matrix candidate
     * @param tol tolerance for orthogonality check
     * @return true if R^T*R ≈ I and det(R) ≈ 1
     */
    static bool is_valid_rotation(const Matrix3f &R, float tol = 1e-4f) {
        Matrix3f RTR = R.transpose() * R;
        Matrix3f I = Matrix3f::Identity();
        
        // Check orthogonality: ||R^T*R - I|| < tol
        float ortho_error = (RTR - I).norm();
        
        // Check determinant (use trace and norm as heuristic)
        float det = R.det();
        
        return (ortho_error < tol) && (std::abs(det - 1.f) < tol);
    }
};

} // namespace attitude_controller_aic
