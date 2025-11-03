该工作空间的上级文件夹为z1_moveit_ws.可以参考宇树的官方文档
## 1.安装依赖
首先安装libboost-all-dev、libeigen3-dev与liburdfdom-dev

 sudo apt install -y libboost-all-dev libeigen3-dev liburdfdom-dev
 sudo ln -s /usr/include/eigen3/Eigen /usr/local/include/Eigen
 sudo ln -s /usr/include/eigen3/unsupported /usr/local/include/unsupported
接着安装pybind11 

 ### Install pybind11
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

 ### Install pinocchio
 git clone --recursive https://github.com/stack-of-tasks/pinocchio
 cd pinocchio && mkdir build && cd build
 cmake .. \
 		-DCMAKE_BUILD_TYPE=Release \
 		-DCMAKE_INSTALL_PREFIX=/usr/local \
 		-DBUILD_PYTHON_INTERFACE=OFF \
 		-DBUILD_TESTING=OFF 

 make
 sudo make install
 ## 2.配置z1_ros包
 ### 配置并安装z1_ros包 
 git clone -b master https://github.com/XFFF67/dual_z1_arms/
 ### 使用rosdep安装所需依赖
 rosdep install --from-paths src --ignore-src -yr --rosdistro noetic
 ### 先编译 unitree_legged_msgs
 catkin_make --pkg unitree_legged_msgs
 catkin_make
 ### 使用前执行source
 source devel/setup.bash
  ## 3.单臂启动
  ## 4.双臂启动
