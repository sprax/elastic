#!/usr/local/bin/bash

path=${1:-nerd}

ls $path
status=$?
echo  "status from ls $path: $status"
if (( $status != 0 )); then
    echo "Try fooling me again!"
else
    echo "Thanks for playing!"
fi
