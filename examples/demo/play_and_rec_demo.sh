#!/bin/bash


# check arguments
if [ -z "$1" ]; then
  echo "Error: Argument is not defined. Please provide a valid demo command file (e.g: $0 demo_commands.sh)."
  exit 1
fi

if [ ! -f "$1" ]; then
  echo "Error: Argument does not point to a valid file. Please provide a valid demo commands file (e.g: $0 demo_commands.sh)."
  exit 1
fi

# killall background process
function cleanup {
    echo "Cleaning up..."
    sleep 1
    kill INT -$$
    sleep 1
    kill -- -$$
}

trap cleanup INT


# Start nested X
Xephyr -screen 1600x1200 :1 &
export DISPLAY=:1

# start the windows manager
sleep 1
mutter  --sm-disable --sync  -&
sleep 0.5

# start the recording process
filename="video_$(date +%Y%m%d_%H%M%S).webm"
echo "$filename"
(sleep 1.5; ffmpeg -f x11grab  -video_size $(xdpyinfo | grep dimensions | awk '{print $2;}') -i :1.0 -c:v libvpx-vp9 -lossless 1 $filename )&

# center the window
(sleep 1
wmctrl -r :ACTIVE: -e 0,150,150,1300,900
)&
terminology -f mono/24 -M --geometry +0-0 -T  tulp -e "sleep 1; bash ./play_demo.sh $1"
cleanup

