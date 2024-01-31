#include "sensor.h"
#ifdef ARDUINO
#include <Arduino.h>
#else
#include <stdlib.h>
#endif

double read_sensor() {
    #ifdef ARDUINO
    return random(100) / 100.0;
    #else
    return rand() / (double) RAND_MAX;
    #endif
}
