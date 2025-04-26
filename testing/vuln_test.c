// vuln_test.c
#include <stdio.h>
#include <string.h>

int main() {
    char buffer[10];

    printf("Enter something: ");
    gets(buffer); // 💥 Vulnerable: Buffer Overflow via gets()

    char another_buffer[10];
    strcpy(another_buffer, buffer); // 💥 Vulnerable: Unsafe strcpy()

    printf("You entered: %s\n", buffer);
    return 0;
}
