#include "state_machine.h"
#include "low_pass_filter.h"
#include "sensor.h"
#include "platform.h"
#include <stdio.h>

void run(int num_iterations) {
    static State state = STATE_A;
    static double value = 0;

    for(int i = 0; i < num_iterations; i++) {
        // State Machine
        state = next_state(state);
        PRINTF("State: %d\n", state);

        // Low Pass Filter
        value = low_pass_filter(value, read_sensor());
        PRINTF("Filtered value: %f\n", value);

        SLEEP(100); // Wait for 100ms
    }
}

#ifndef ARDUINO
int main(int argc, char *argv[]) {
    int num_iterations = 0;
    if(argc > 1) {
        num_iterations = atoi(argv[1]);
    }

    PRINTF("Running on %s...\n", PLATFORM);
    if (num_iterations > 0) {
        PRINTF("Running for %d iterations...\n", num_iterations);
    } else {
        PRINTF("Skip running...\n");
    }
    run(num_iterations);
    return 0;
}
#endif
