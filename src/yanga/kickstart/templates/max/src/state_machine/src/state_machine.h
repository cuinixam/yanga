#ifndef STATE_MACHINE_H
#define STATE_MACHINE_H

typedef enum {STATE_A, STATE_B, STATE_C} State;

/**
 * @brief Determines the next state for the state machine.
 *
 * @param current_state The current state.
 * @return The next state.
 */
State next_state(State current_state);

#endif
