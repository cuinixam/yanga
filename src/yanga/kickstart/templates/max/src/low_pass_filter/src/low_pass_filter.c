#include "low_pass_filter.h"

/** The parameter for the low pass filter */
#define ALPHA 0.1

double low_pass_filter(double current_value, double new_value) {
    return current_value * (1.0 - ALPHA) + new_value * ALPHA;
}
