#include "state_machine.h"

State next_state(State current_state) {
    switch(current_state) {
        case STATE_A: return STATE_B;
        case STATE_B: return STATE_C;
        case STATE_C: return STATE_A;
    }
    return STATE_A;
}
