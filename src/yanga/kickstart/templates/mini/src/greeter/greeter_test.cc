#include <gtest/gtest.h>

extern "C" {
    #include "greeter.h"
    #include "autoconf.h"
}

#if defined(CONFIG_LANG_DE) && CONFIG_LANG_DE == 1
const char *greeting = "Hallo, Welt!";
#else
const char *greeting = "Hello, world!";
#endif
/**
 * ```{spec} Test greeting
 *    :id: TEST_G-001
 *    :links: SWDD_G-100
 *
 *    Make sure it greets in the proper language.
 * ```
 */
TEST(GreeterTest, Greeting) {
    EXPECT_STREQ(greeting, get_greeting());
}
