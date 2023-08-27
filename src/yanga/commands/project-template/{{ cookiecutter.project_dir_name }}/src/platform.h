#ifndef PLATFORM_H
#define PLATFORM_H

#ifdef ARDUINO
#include <Arduino.h>
#define PRINTF(...) Serial.print(__VA_ARGS__)
#define PLATFORM "Arduino"
#define SLEEP(ms) delay(ms)
#else
#include <stdlib.h>
#define PRINTF(...) printf(__VA_ARGS__)
#ifdef _WIN32
#include <windows.h>
#define PLATFORM "WIN32"
#define SLEEP(ms) Sleep(ms)
#else
#include <unistd.h>
#define PLATFORM "Unix-like"
#define SLEEP(ms) usleep(ms*1000)
#endif
#endif

#endif
