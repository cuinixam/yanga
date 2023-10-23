#include "low_pass_filter.h"

double low_pass_filter(double current_value, double new_value) {
    return (current_value + new_value) / 2.0;
}
