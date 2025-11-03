#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2019 Wuhan PS-Micro Technology Co., Itd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import rospy,sys
from geometry_msgs.msg import PoseStamped,Pose
from moveit_commander import MoveGroupCommander
import moveit_commander
from copy import deepcopy
import numpy,math
from moveit_msgs.msg import RobotTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint

def set_pose(x,y,z,ox,oy,oz,w,reference_frame='world'):
        target_pose = PoseStamped()
        target_pose.header.frame_id = reference_frame
        target_pose.header.stamp = rospy.Time.now()     
        target_pose.pose.position.x = x
        target_pose.pose.position.y = y
        target_pose.pose.position.z = z
        target_pose.pose.orientation.x = ox
        target_pose.pose.orientation.y = oy
        target_pose.pose.orientation.z = oz
        target_pose.pose.orientation.w = w
        return target_pose

def circle_move_yz(move_group, target_pose, radius, direction, start_pose):
    # 初始化路点列表
    waypoints = []
    
    # 获取当前位置作为参考
    current_pose = move_group.get_current_pose().pose
    centerA = target_pose.pose.position.y  # 圆心Y坐标
    centerB = target_pose.pose.position.z  # 圆心Z坐标
    
    # 根据起始位置设置初始角度
    if start_pose == 1:  # 圆心左
        start_angle = math.pi
    elif start_pose == 2:  # 圆心上
        start_angle = 3 * math.pi / 2
    elif start_pose == 3:  # 圆心右
        start_angle = 0
    elif start_pose == 4:  # 圆心下
        start_angle = math.pi / 2
    else:
        start_angle = 0
    
    # 生成圆形轨迹点
    for th in numpy.arange(0, 6.28, 0.02):
        if direction == 0:  # 逆时针
            y = centerA + radius * math.cos(th + start_angle)
            z = centerB + radius * math.sin(th + start_angle)
        else:  # 顺时针
            y = centerA + radius * math.cos(th + start_angle)
            z = centerB - radius * math.sin(th + start_angle)
        
        # 创建新的位姿点
        new_pose = deepcopy(target_pose.pose)
        new_pose.position.y = y
        new_pose.position.z = z
        waypoints.append(deepcopy(new_pose))
   
    fraction = 0.0   # 路径规划覆盖率
    maxtries = 100   # 最大尝试规划次数
    attempts = 0     # 已经尝试规划次数

    # 设置机器臂当前的状态作为运动初始状态
    move_group.set_start_state_to_current_state()
 
    # 尝试规划一条笛卡尔空间下的路径
    plan = None
    while fraction < 1.0 and attempts < maxtries:
        (plan, fraction) = move_group.compute_cartesian_path(
            waypoints,   # waypoint poses，路点列表
            0.01,        # eef_step，终端步进值
            True, )        # avoid_collisions，避障规划       
        
        # 尝试次数累加
        attempts += 1
        
        # 打印运动规划进程
        if attempts % 10 == 0:
            rospy.loginfo("Still trying after " + str(attempts) + " attempts...")
    
    # 如果路径规划成功（覆盖率100%）,则返回规划结果
    if fraction == 1.0:
        rospy.loginfo("Path computed successfully. Moving the arm.")
        return plan
    else:
        rospy.logwarn("Path planning failed with only " + str(fraction) + " success after " + str(maxtries) + " attempts.")
        return None

def plan_plus(plan_l, plan_r):
    # 检查输入是否有效
    if plan_l is None or plan_r is None:
        rospy.logerr("One of the plans is None, cannot merge")
        return None
        
    # 创建一个新的轨迹
    dual_arm_plan = RobotTrajectory()
    
    # 合并关节名称
    dual_arm_plan.joint_trajectory.joint_names = plan_l.joint_trajectory.joint_names + plan_r.joint_trajectory.joint_names
    
    # 确保左臂和右臂轨迹有相同数量的点
    if len(plan_l.joint_trajectory.points) != len(plan_r.joint_trajectory.points):
        rospy.logwarn("Trajectory point counts don't match: left=%d, right=%d", 
                     len(plan_l.joint_trajectory.points), len(plan_r.joint_trajectory.points))
        # 使用较短的长度
        min_length = min(len(plan_l.joint_trajectory.points), len(plan_r.joint_trajectory.points))
    else:
        min_length = len(plan_l.joint_trajectory.points)

    # 合并轨迹点数据
    for i in range(min_length):
        new_point = JointTrajectoryPoint()
        
        # 合并位置数据
        if i < len(plan_l.joint_trajectory.points) and i < len(plan_r.joint_trajectory.points):
            new_point.positions = (plan_l.joint_trajectory.points[i].positions + 
                                 plan_r.joint_trajectory.points[i].positions)
            
            # 合并速度数据（如果有）
            if (len(plan_l.joint_trajectory.points[i].velocities) > 0 and 
                len(plan_r.joint_trajectory.points[i].velocities) > 0):
                new_point.velocities = (plan_l.joint_trajectory.points[i].velocities + 
                                      plan_r.joint_trajectory.points[i].velocities)
            
            # 合并加速度数据（如果有）
            if (len(plan_l.joint_trajectory.points[i].accelerations) > 0 and 
                len(plan_r.joint_trajectory.points[i].accelerations) > 0):
                new_point.accelerations = (plan_l.joint_trajectory.points[i].accelerations + 
                                         plan_r.joint_trajectory.points[i].accelerations)
            
            # 使用左臂的时间（假设两者时间相同）
            new_point.time_from_start = plan_l.joint_trajectory.points[i].time_from_start
            
            dual_arm_plan.joint_trajectory.points.append(new_point)

    return dual_arm_plan

class DoubleCircleDemo:
    def __init__(self):
        # 初始化move_group的API
        moveit_commander.roscpp_initialize(sys.argv)

        # 初始化ROS节点
        rospy.init_node('double_circle_demo', anonymous=True)
                        
        # 初始化需要使用move group控制的机械臂中的arm group
        dual_arms = MoveGroupCommander('dual_arms')
        manipulator_a = MoveGroupCommander('manipulator_a')
        manipulator_b = MoveGroupCommander('manipulator_b')
        
        # 设置目标位置所用的参考系
        reference_frame_a = 'link00_a'
        reference_frame_b = 'link00_b'
        manipulator_a.set_pose_reference_frame(reference_frame_a)
        manipulator_b.set_pose_reference_frame(reference_frame_b)

        # 当运动规划失败后，允许重新规划
        manipulator_a.allow_replanning(True)
        manipulator_b.allow_replanning(True)

        # 设置位置(单位：米)和姿态（单位：弧度）的允许误差
        manipulator_a.set_goal_position_tolerance(0.001)
        manipulator_a.set_goal_orientation_tolerance(0.001)
        manipulator_b.set_goal_position_tolerance(0.001)
        manipulator_b.set_goal_orientation_tolerance(0.001)

        # 设置允许的最大速度和加速度
        manipulator_a.set_max_acceleration_scaling_factor(0.3)
        manipulator_a.set_max_velocity_scaling_factor(0.5)
        manipulator_b.set_max_acceleration_scaling_factor(0.3)
        manipulator_b.set_max_velocity_scaling_factor(0.5)
        
        # 获取终端link的名称
        end_effector_link_a = manipulator_a.get_end_effector_link()
        end_effector_link_b = manipulator_b.get_end_effector_link()

        # 控制机械臂先回到初始化位置
        rospy.loginfo("Moving to home position")
        dual_arms.set_named_target('home')
        dual_arms.go()
        rospy.sleep(1)
        
        # 设置目标位姿
        target_pose_a_1 = set_pose(0.112161732251823, -0.3, 0.35, 0, 0, 0, 0, 'link00_a')
        target_pose_b_1 = set_pose(0.112161732251823, 0.3, 0.35, 0, 0, 0, 0, 'link00_b')
        target_pose_a_2 = set_pose(0.112161732251823, -0.4, 0.35, 0, 0, 0, 0, 'link00_a')
        target_pose_b_2 = set_pose(0.112161732251823, 0.4, 0.35, 0, 0, 0, 0, 'link00_b')
        
        # 设置机械臂终端运动的目标位姿
        rospy.loginfo("Moving to start position")
        manipulator_a.set_pose_target(target_pose_a_1)
        manipulator_b.set_pose_target(target_pose_b_1)
        manipulator_a.go()
        manipulator_b.go()
        rospy.sleep(1)

        # 执行圆形轨迹
        rospy.loginfo("Planning first circle trajectories")
        plan_a = circle_move_yz(manipulator_a, target_pose_a_1, 0.1, 0, 3)
        plan_b = circle_move_yz(manipulator_b, target_pose_b_1, 0.1, 1, 1)
        
        if plan_a is not None and plan_b is not None:
            dual_arms_plan = plan_plus(plan_a, plan_b)
            if dual_arms_plan is not None:
                rospy.loginfo("Executing first circle trajectories")
                dual_arms.execute(dual_arms_plan)
                rospy.sleep(1)
        
        # 移动到第二个位置并执行圆形轨迹
        rospy.loginfo("Moving to second position")
        manipulator_a.set_pose_target(target_pose_a_2)
        manipulator_b.set_pose_target(target_pose_b_2)
        manipulator_a.go()
        manipulator_b.go()
        rospy.sleep(1)
        
        rospy.loginfo("Planning second circle trajectories")
        plan_a = circle_move_yz(manipulator_a, target_pose_a_2, 0.02, 1, 1)
        plan_b = circle_move_yz(manipulator_b, target_pose_b_2, 0.02, 0, 3)
        
        if plan_a is not None and plan_b is not None:
            dual_arms_plan = plan_plus(plan_a, plan_b)
            if dual_arms_plan is not None:
                rospy.loginfo("Executing second circle trajectories")
                dual_arms.execute(dual_arms_plan)
                rospy.sleep(1)

        # 控制机械臂回到初始化位置
        rospy.loginfo("Moving back to home position")
        dual_arms.set_named_target('home')
        dual_arms.go()
        rospy.sleep(1)
        
        # 关闭并退出moveit
        moveit_commander.roscpp_shutdown()
        moveit_commander.os._exit(0)

if __name__ == "__main__":
    try:
        DoubleCircleDemo()
    except rospy.ROSInterruptException:
        pass