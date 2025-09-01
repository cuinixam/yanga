// sample_cppcheck_input.c
// This file is designed to trigger typical CppCheck warnings/errors for demonstration purposes.
#include <stdio.h>
#include <string.h>

void unused_function() {
    // This function is never called
}

int main() {
    char buffer[10];
    strcpy(buffer, "This string is too long for buffer"); // buffer overflow
    int x;
    printf("x = %d\n", x); // use of uninitialized variable
    int *ptr = NULL;
    *ptr = 42; // dereference of null pointer
    return 0;
}
