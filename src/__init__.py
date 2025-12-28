"""
Package initialization for Erle-Brain 2 autonomous flight system.
"""

__version__ = '1.0.0'
__author__ = 'Erle-Brain 2 Development Team'

# Make imports easier
from .autonomous_flight import AutonomousController
from .mission_planner import MissionPlanner
from .safety_manager import SafetyManager
from .telemetry_monitor import TelemetryMonitor

__all__ = [
    'AutonomousController',
    'MissionPlanner',
    'SafetyManager',
    'TelemetryMonitor'
]
