FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl wget git python3 python3-pip \
    openjdk-21-jdk screen tmux htop \
    fuse inotify-tools rsync sudo unzip \
    && curl https://rclone.org/install.sh | bash \
    && wget -q https://github.com/tsl0922/ttyd/releases/download/1.7.3/ttyd.x86_64 -O /usr/bin/ttyd \
    && chmod +x /usr/bin/ttyd \
    && pip3 install --no-cache-dir flask requests psutil \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create user
RUN useradd -m -s /bin/bash termux && \
    echo "termux ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER termux
WORKDIR /home/termux

# Set safe default environment variables
ENV NODE_COUNT=1
ENV TOTAL_RAM=8
ENV SERVICE_TYPE=main
ENV AUTO_COMBINE=true
ENV NODE_ID=main

# Create directories
RUN mkdir -p \
    ~/cloud-storage \
    ~/storage/shared \
    ~/scripts \
    ~/cluster \
    ~/minecraft/servers \
    ~/.config/rclone

# Copy scripts
COPY --chown=termux:termux scripts/ /home/termux/scripts/
COPY --chown=termux:termux start.sh /home/termux/start.sh
COPY --chown=termux:termux requirements.txt /home/termux/

RUN chmod +x ~/scripts/*.sh ~/start.sh

# Create symbolic links
RUN ln -sf ~/cloud-storage ~/storage/shared/cloud

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:10000/ || exit 1

EXPOSE 10000 25565 25566 25567 5001 5002

CMD ["./start.sh"]
