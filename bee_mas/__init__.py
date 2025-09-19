#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bee-MAS 智能多Agent系统
"""

# 核心架构
from .main import (
    DanceMessage,
    TaskAnnouncement,
    TaskBoard,
    TaskProposal,
    TaskDAG,
    LLMClient,
    BeeAgent,
    SmartBeeAgent,
    SchedulerBee
)

__version__ = "2.0.0"
__author__ = "Bee-MAS Team"

__all__ = [
    # 核心架构
    "DanceMessage",
    "TaskAnnouncement", 
    "TaskBoard",
    "TaskProposal",
    "TaskDAG",
    "LLMClient",
    "BeeAgent",
    "SmartBeeAgent",
    "SchedulerBee"
]
