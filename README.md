宇数z1双臂仿真平台，以下内容
1. 引言
   （待完善……）

2. 安装依赖
   首先安装libboost-all-dev、libeigen3-dev与liburdfdom-dev

 sudo apt install -y libboost-all-dev libeigen3-dev liburdfdom-dev
 sudo ln -s /usr/include/eigen3/Eigen /usr/local/include/Eigen
 sudo ln -s /usr/include/eigen3/unsupported /usr/local/include/unsupported
接着安装pybind11 

 # Install pybind11

 git clone https://github.com/pybind/pybind11.git
 cd pybind11
 mkdir build && cd build
 cmake .. -DPYBIND11_TEST=OFF
 make -j
 sudo make install
确保系统已安装moveit

 sudo apt install -y ros-noetic-moveit-*
 sudo apt install -y ros-noetic-joint-trajectory-controller ros-noetic-trac-ik-kinematics-plugin
再安装pinocchio

 # Install pinocchio

 git clone --recursive https://github.com/stack-of-tasks/pinocchio
 cd pinocchio && mkdir build && cd build
 cmake .. \
 		-DCMAKE_BUILD_TYPE=Release \
 		-DCMAKE_INSTALL_PREFIX=/usr/local \
 		-DBUILD_PYTHON_INTERFACE=OFF \
 		-DBUILD_TESTING=OFF 

 make
 sudo make install
配置PATH，将下面三行加入~/.bashrc

  export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
  export CMAKE_PREFIX_PATH=/usr/local:$CMAKE_PREFIX_PATH
  export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH

3. 下载SDK并编译
   首先下载所有的SDK，我已将相关仓库整合到个人GitHub仓库中方便下载。

 git clone https://github.com/Lya-M1RA/Unitree-Z1_SDK.git --recursive
其整合了相关的四个仓库：

z1_controller 存储着直接控制机械臂的源码。
z1_sdk 包含了用于控制机械臂的一些接口，用户在创建自己的程序使用z1机械臂时需要包含该文件夹。
unitree_ros 用于机械臂仿真，其中包含了宇树四足产品Go1, A1, Aliengo, Laikago和机械臂产品Z1的仿真文件。
z1_ros（包含unitree_ros）, 提供noetic moveit1支持
Unitree-Z1_SDK/
  ├── z1_controller        # 存储着直接控制机械臂的源码
  ├── z1_moveit_ws         # 存放在z1_ros的工作空间
  │   └── src
  │       └── z1_ros       # 提供ROS Noetic Moveit1支持
  ├── z1_sdk               # 包含了用于控制机械臂的一些接口
  └── z1_ws                # 存放unitree_ros的工作空间  
    └── src
        └── unitree_ros  # 用于机械臂仿真 (Gazebo)
需要注意的是，关于ROS的两个包z1_ros与unitree_ros存在冲突，不能放入同一个ROS工作空间中一起编译。
并且注意z1_ros中也包含z1_controller和z1_sdk，提供的接口可以直接发送UDP结构体进行通信，与上述 z1_sdk 与 z1_controller 不兼容也不是相同的内容。

编译z1_controller

 cd z1_controller
 mkdir build && cd build
 cmake ..
 make
编译z1_sdk

 cd z1_sdk
 mkdir build && cd build
 cmake ..
 make
安装unitree_ros包

 cd z1_ws 
 catkin_make 

 # 使用前执行source

 source devel/setup.bash
注意如果平台为ARM64架构，则需要在./src/unitree_ros/unitree_legged_control/lib中用libunitree_joint_control_tool_arm64.so替换libunitree_joint_control_tool.so，即删去后者并将前者重命名为后者。

配置并安装z1_ros包

 cd z1_moveit_ws

 # 使用rosdep安装所需依赖

 rosdep install --from-paths src --ignore-src -yr --rosdistro noetic

 # 先编译 unitree_legged_msgs

 catkin_make --pkg unitree_legged_msgs
 catkin_make

 # 使用前执行source

 source devel/setup.bash
类似的，注意如果平台为ARM64架构，则需要在./src/z1_ros/unitree_ros/unitree_legged_control/lib中用libunitree_joint_control_tool_arm64.so替换libunitree_joint_control_tool.so，即删去后者并将前者重命名为后者。

4. 在ROS仿真（Gazebo）中使用机械臂
   请注意你使用Ubuntu系统的环境，如果你在Windows上通过WSL2运行Ubuntu，请阅读这一部分。
   Gazebo与Moveit（在RViz显示中）等程序在WSL2中运行的Ubuntu上可能会出现图形错误，具体表现为在Gazebo或RViz窗口中机械臂的模型不显示等。
   这似乎是由于使用GPU时WSL使用的OpenGL版本过旧导致的，将程序转为纯CPU运行可以暂时解决这个问题。参考：Robot meshes not visible in rviz [Windows11, WSL2] 具体方法为在运行Gazebo或Moveit前在Terminal中执行export: LIBGL_ALWAYS_SOFTWARE=1 LIBGL_ALWAYS_INDIRECT=0

首先启动Gazebo中的仿真机械臂。

 roslaunch unitree_gazebo z1.launch

 # 如果不使用末端夹爪，请使用下面的这行

 roslaunch unitree_gazebo z1.launch UnitreeGripperYN:=false
e0b27b44-fe4c-4213-a30a-f731343aa31f 你应当能够看到像上面图片一样的界面。

接着在一个新开的Termial会话中启动机械臂的虚拟控制器。

 cd z1_controller/build
 ./sim_ctrl
最后在一个新开的Termial会话运行SDK中的demo，你应该能看到Gazebo窗口中的机械臂运动。

 cd z1_sdk/build
 ./highcmd_basic
5afdee6d-44ca-410d-944c-0800336c9ff0

（待完善……）

5. 机械臂实机连接
   （待完善……）

6. 在Moveit中使用机械臂
   首先启动moveit

 # 如果使用实机，运行下面这行

 roslaunch z1_bringup real_arm.launch rviz:=true

 # 如果使用Gazebo仿真机械臂，运行下面这行

 roslaunch z1_bringup sim_arm.launch rviz:=true
上面的第一条指令会启动Moveit并打开RViz，如果使用第二条指令，则会额外启动Gazebo来提供仿真环境中的机械臂。

接着启动机械臂控制器程序。

 cd z1_controller/build

 # 如果使用实机，运行下面这行

 ./z1_ctrl

 # 如果使用Gazebo仿真机械臂，运行下面这行

 ./sim_ctrl
这样就可以使用Moveit来规划机械臂路径并控制机械臂了。下图是一个在Moveit中手动指定机械臂末端位置并控制机械臂运动的展示。 f20d1e2e-5753-4835-88bf-d6d8aa96726c

（待完善……）

7. 自定义程序使用SDK接口控制机械臂
   （待完善……）

