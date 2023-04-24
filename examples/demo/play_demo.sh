#!/bin/bash
# made by @tulp v0.5.0
# Introduction comment 
# This script automates a terminal interaction, simulating manual typing.
# It executes a list of commands in order and waits for the result.

PS1='\033[01;32mfede@liebre\033[00m:\033[01;34m~ \033[00m$'


source ./demo_commands.sh

reset; clear
# Loop through the commands and execute them
for command in "${commands[@]}"
do
    echo -ne "\n$PS1 "
    sleep 0.1
    # Print the command being executed
    #echo "Executing command: $command"
 
    echo "$command" | randtype -m 3 -t 18,5000
    #   # Simulate manual typing
    #   for (( i=0; i<${#command}; i++ )); do
    #       echo -n "${command:$i:1}"
    #       sleep 0.1
    #   done
    #   echo ""
    
    sleep 0.3
    # Execute the command and wait for the result
    eval $command
done
