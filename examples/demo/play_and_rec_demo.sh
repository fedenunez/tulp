
#!/bin/bash

function cleanup {
    echo "Cleaning up..."
    sleep 1
    kill INT -$$
    sleep 1
    kill -- -$$
}

trap cleanup INT

Xephyr -screen 1200x600 :1 &
export DISPLAY=:1
sleep 1
blackbox &
sleep 1
feh --bg-scale ~/Desktop/Desktop_23_04_2023/AI.jpeg

filename="video_$(date +%Y%m%d_%H%M%S).mp4"
echo "$filename"
(sleep 0.5; ffmpeg -f x11grab -video_size $(xdpyinfo | grep dimensions | awk '{print $2;}') -i :1.0  $filename )&

terminology -f mono/24 -2 -M -e bash ./play_demo.sh

cleanup

