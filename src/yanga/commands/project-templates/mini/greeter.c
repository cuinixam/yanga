#include "greeter.h"
#include "autoconf.h"

// Function to return the greeting string based on the configuration.
const char* get_greeting() {
    #if defined(CONFIG_LANG_DE) && CONFIG_LANG_DE == 1
        return "Hallo, Welt!";
    #else
        return "Hello, world!";
    #endif
}
