cmake_minimum_required(VERSION 3.8)
project(kinova_gen3_description)

find_package(ament_cmake REQUIRED)

install(DIRECTORY urdf meshes rviz launch
  DESTINATION share/${PROJECT_NAME})

install(PROGRAMS scripts/fake_joint_states.py
  DESTINATION lib/${PROJECT_NAME})

ament_package()
