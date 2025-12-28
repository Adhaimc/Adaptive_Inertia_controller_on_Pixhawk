############################################################################
#
#   Copyright (c) 2024 Adaptive Inertia Estimation Contributors
#   All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 3. Neither the name of the author nor the names of its contributors
#    may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
############################################################################

cmake_minimum_required(VERSION 3.5)
project(attitude_controller_aic C CXX)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find PX4 (when building as part of PX4 firmware)
find_package(PX4 REQUIRED)

# Include directories
include_directories(
    include
    ${PX4_SOURCE_DIR}/src
    ${PX4_SOURCE_DIR}/platforms/common
    ${PX4_SOURCE_DIR}/lib/matrix
    ${PX4_SOURCE_DIR}/src/lib/mathlib
)

# Add Eigen for matrix operations (if not already available)
find_package(Eigen3 QUIET)
if(NOT Eigen3_FOUND)
    # Use system Eigen or bundled version
    include_directories(/usr/include/eigen3)
endif()

# Main source files
set(SOURCES
    AttitudeControllerAIC.cpp
)

# Header-only libraries (included from include/)
set(HEADERS
    include/so3_utils.hpp
    include/regressor.hpp
    include/adaptive_estimator.hpp
    include/iwg_adapter.hpp
    include/attitude_controller_aic.hpp
)

# Create module library
px4_add_module(
    MODULE modules__attitude_controller_aic
    MAIN attitude_controller_aic_main
    STACK_MAIN 2048
    PRIORITY SCHED_PRIORITY_MAX
    SRCS ${SOURCES}
    DEPENDS
        platforms__common
        lib__mathlib
        lib__matrix
)

# Optional: Unit tests (can be added here)
# if(BUILD_TESTING)
#     enable_testing()
#     add_subdirectory(test)
# endif()
