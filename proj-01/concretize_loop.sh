#!/bin/bash

# Run spack concretize in a loop until no further concretizations occur

while true; do
    echo "Running spack concretize --force..."
    
    # Capture the output of the command
    OUTPUT=$(spack concretize --force 2>&1)
    
    echo "$OUTPUT"
    
    # Check if the output contains any indication that further concretization is needed
    if echo "$OUTPUT" | grep -q "already concretized"; then
        echo "No more concretizations to be made. Exiting."
        break
    fi

    # Optional: Add a sleep to avoid overwhelming the system
    sleep 2
done
