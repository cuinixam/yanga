#include <stdio.h>
#include "autoconf.h"

int main(int argc, char *argv[])
{
#if defined(CONFIG_LANG_DE) && CONFIG_LANG_DE == 1
    printf("Hallo, Welt!\n");
#else
    printf("Hello, world!\n");
#endif
    return 0;
}
