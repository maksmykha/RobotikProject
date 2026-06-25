# Basis-Image
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    ROS_DISTRO=jazzy \
    PYTHONUNBUFFERED=1 \
    LANG=en_US.UTF-8

# Grundtools + Locale
RUN apt-get update && apt-get install -y \
    locales \
    curl \
    wget \
    git \
    ca-certificates \
    gnupg \
    lsb-release \
    && locale-gen en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# ROS2 Repository Setup
RUN mkdir -p /usr/share/keyrings && \
    curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    | gpg --dearmor -o /usr/share/keyrings/ros-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
http://packages.ros.org/ros2/ubuntu noble main" \
    > /etc/apt/sources.list.d/ros2.list

RUN apt-get update

# ROS2 Jazzy Desktop
RUN apt-get install -y \
    ros-jazzy-desktop \
    ros-dev-tools \
    python3-rosdep \
    python3-colcon-common-extensions \
    python3-vcstool \
    && rm -rf /var/lib/apt/lists/*

# Dev Tools
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# rosdep init
RUN rosdep init || true && \
    rosdep update

WORKDIR /home/robotics

# Repository klonen
RUN git clone https://github.com/maksmykha/RobotikProject.git . && \
    git submodule update --init --recursive

# Python Dependencies - MIT --break-system-packages (in Docker OK!)
RUN pip install --break-system-packages --upgrade pip setuptools wheel && \
    pip install --break-system-packages typeguard lark requests && \
    pip install --break-system-packages numpy==1.26.4 && \
    pip install --break-system-packages torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install --break-system-packages ultralytics && \
    pip install --break-system-packages lap || pip install --break-system-packages lapx

# ROS Dependencies
RUN bash -c "source /opt/ros/jazzy/setup.bash && \
    rosdep install --from-paths src --ignore-src -r -y" || true

# Workspace bauen
RUN bash -c "source /opt/ros/jazzy/setup.bash && \
    colcon build --symlink-install --parallel-workers 1"

# EntryPoint Script
RUN echo '#!/bin/bash\n\
source /opt/ros/jazzy/setup.bash\n\
source /home/robotics/install/setup.bash\n\
exec "$@"' > /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]

