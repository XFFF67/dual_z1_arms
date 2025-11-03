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

#左臂正向运动学(fk),右臂逆向运动学(ik)

import rospy, sys
import moveit_commander
from geometry_msgs.msg import PoseStamped, Pose

class MoveItFikDemo:
    def __init__(self):
        # 初始化move_group的API
        moveit_commander.roscpp_initialize(sys.argv)
        
        # 初始化ROS节点
        rospy.init_node('moveit_fik_demo')

        # 初始化左臂和右臂的move group
        self.arm_a = moveit_commander.MoveGroupCommander('manipulator_a')  # 左臂 - 使用FK
        self.arm_b = moveit_commander.MoveGroupCommander('manipulator_b') # 右臂 - 使用IK
        
        # 设置参考坐标系
        reference_frame = 'world'
        self.arm_a.set_pose_reference_frame(reference_frame)
        self.arm_b.set_pose_reference_frame(reference_frame)
                
        # 允许重新规划
        self.arm_a.allow_replanning(True)
        self.arm_b.allow_replanning(True)
        
        # 设置允许误差
        self.arm_a.set_goal_position_tolerance(0.01)
        self.arm_a.set_goal_orientation_tolerance(0.1)
        self.arm_a.set_goal_joint_tolerance(0.01)
        
        self.arm_b.set_goal_position_tolerance(0.01)
        self.arm_b.set_goal_orientation_tolerance(0.1)
        self.arm_b.set_goal_joint_tolerance(0.01)
       
        # 设置最大速度和加速度
        self.arm_a.set_max_acceleration_scaling_factor(0.3)
        self.arm_a.set_max_velocity_scaling_factor(0.3)
        self.arm_b.set_max_acceleration_scaling_factor(0.3)
        self.arm_b.set_max_velocity_scaling_factor(0.3)

        # 执行双机械臂协同运动
        self.run_dual_arm_demo()

    def run_dual_arm_demo(self):
        """执行双机械臂协同运动演示"""
        rospy.loginfo("开始双机械臂协同运动演示")
        
        # 第一步：两个机械臂都回到初始位置
        rospy.loginfo("步骤1: 双机械臂回到初始位置")
        
        # 分别执行，确保每个都成功
        rospy.loginfo("移动左臂到home位置...")
        success_a = self.arm_a.go(wait=True)
        rospy.loginfo("左臂移动结果: %s", "成功" if success_a else "失败")
        
        rospy.loginfo("移动右臂到home位置...")
        success_b = self.arm_b.go(wait=True)
        rospy.loginfo("右臂移动结果: %s", "成功" if success_b else "失败")
        
        rospy.sleep(1)

        # 第二步：左臂使用正向运动学（FK），右臂使用逆向运动学（IK）
        rospy.loginfo("步骤2: 左臂FK控制，右臂IK控制")
        
        # 左臂 - 使用更安全的关节角度
        rospy.loginfo("设置左臂关节角度...")
        left_joint_positions = [0.3, 0.4, -0.3, 0.1, 0.2, 0.0]  # 更安全的角度
        self.arm_a.set_joint_value_target(left_joint_positions)
        
        # 检查左臂目标是否有效
        rospy.loginfo("左臂目标关节角度: %s", left_joint_positions)
        
        # 右臂 - 逆向运动学
        rospy.loginfo("设置右臂目标姿态...")
        target_pose = PoseStamped()
        target_pose.header.frame_id = 'world'
        target_pose.header.stamp = rospy.Time.now()     
        target_pose.pose.position.x = 0.3
        target_pose.pose.position.y = -0.2
        target_pose.pose.position.z = 0.3
        target_pose.pose.orientation.x = 0.0
        target_pose.pose.orientation.y = 0.0
        target_pose.pose.orientation.z = 0.0
        target_pose.pose.orientation.w = 1.0
        
        self.arm_b.set_pose_target(target_pose)
        rospy.loginfo("右臂目标位置: x=%.2f, y=%.2f, z=%.2f", 
                     target_pose.pose.position.x, 
                     target_pose.pose.position.y, 
                     target_pose.pose.position.z)
        
        # 分别执行运动，确保每个都成功
        rospy.loginfo("执行左臂运动...")
        success_a = self.arm_a.go(wait=True)
        rospy.loginfo("左臂运动结果: %s", "成功" if success_a else "失败")
        
        if not success_a:
            rospy.logwarn("左臂运动失败，尝试重新规划...")
            # 尝试更简单的目标
            simple_joints = [0.1, 0.2, -0.1, 0.0, 0.0, 0.0]
            self.arm_a.set_joint_value_target(simple_joints)
            success_a = self.arm_a.go(wait=True)
            rospy.loginfo("左臂重新规划结果: %s", "成功" if success_a else "失败")
        
        rospy.sleep(1)
        
        rospy.loginfo("执行右臂运动...")
        success_b = self.arm_b.go(wait=True)
        rospy.loginfo("右臂运动结果: %s", "成功" if success_b else "失败")
        
        if not success_b:
            rospy.logwarn("右臂运动失败，尝试重新规划...")
            # 尝试更简单的目标位置
            target_pose.pose.position.z = 0.4  # 更高一点可能更容易到达
            self.arm_b.set_pose_target(target_pose)
            success_b = self.arm_b.go(wait=True)
            rospy.loginfo("右臂重新规划结果: %s", "成功" if success_b else "失败")
        
        rospy.sleep(1)

        # 显示当前状态
        rospy.loginfo("=== 当前状态 ===")
        rospy.loginfo("左臂末端姿态: %s", self.arm_a.get_current_pose())
        rospy.loginfo("右臂末端姿态: %s", self.arm_b.get_current_pose())
        rospy.loginfo("左臂关节角度: %s", self.arm_a.get_current_joint_values())
        rospy.loginfo("右臂关节角度: %s", self.arm_b.get_current_joint_values())

        # 回到初始位置
        rospy.loginfo("回到初始位置...")
        self.arm_a.set_named_target('home_a')
        self.arm_b.set_named_target('home_b')
        
        success_a = self.arm_a.go(wait=True)
        success_b = self.arm_b.go(wait=True)
        
        rospy.loginfo("回到home结果 - 左臂: %s, 右臂: %s", 
                     "成功" if success_a else "失败", 
                     "成功" if success_b else "失败")
        
        rospy.sleep(1)

        # 关闭并退出moveit
        moveit_commander.roscpp_shutdown()
        moveit_commander.os._exit(0)

if __name__ == "__main__":
    try:
        MoveItFikDemo()
    except rospy.ROSInterruptException:
        pass