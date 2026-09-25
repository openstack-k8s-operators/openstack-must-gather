#!/bin/bash

CONCURRENCY=${CONCURRENCY:-5}

# Function to wait for a background slot to be available
# This function is used by run_bg to wait for a slot to be available before
# running a new command in the background.
# This function is can also be used to limit background functions
# to a certain number of concurrent processes.
# Example:
#    CONCURRENCY=2
#    function my_function {
#        echo "my_function: $@"
#        sleep 1
#    }
#    for i in {1..10}; do
#        wait_for_bg_slot
#        my_function $i &
#    done
#    wait_bg
function wait_for_bg_slot {
    while [[ $(jobs -r | wc -l) -ge $CONCURRENCY ]]; do
        wait -n
    done
}

# Function to run commands in background without exceeding $CONCURRENCY
# processes in parallel.
# The recommendation is to use this function at the deepest level that can be
# parallelized and not at the highest.
# For normal commands:
#    run_bg echo hola
# For commands that run multiple commands we can play with strings:
#    run_bg 'sleep 10 && echo hola'
#    run_bg sleep 10 '&& echo hola'
#    run_bg sleep 10 '&&' echo hola
#    run_bg echo hola '>' myfile.txt
#
# For now these methods ignore errors on the calls that are made in the
# background.
function run_bg {
    wait_for_bg_slot

    # Cannot use the alternative suggested by SC2294 which is just "$@"&
    # because that doesn't accomplish what we want, as it executes the first
    # element as the command and the rest as its parameters, so it cannot run
    # multiple commands, use pipes, redirect...
    # shellcheck disable=SC2294
    eval "$@"&
    # Return the new process' PID
    return $!
}


# Waits for all background tasks to complete or just for a list of PIDs
# Disable SC2120 in this to prevent SC2119 when called without the optional PIDs
# shellcheck disable=SC2120
function wait_bg {
    # When we receive a list of PIDs those may be already finished, and we'll
    # get an error complaining those are not children
    wait -f "$@" 2>/dev/null
    return 0
}
