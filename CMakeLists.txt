cmake_minimum_required(VERSION 3.8)
project(chars_dashboard)

find_package(ament_cmake REQUIRED)

# Install web files
install(DIRECTORY web/
  DESTINATION share/${PROJECT_NAME}/web
)

# Install launch files
install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

ament_package()
