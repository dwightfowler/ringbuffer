#include <stdio.h>

int main(int argc, char** argv)
{
    for (int i = 0; i < argc; i++)
    {
        printf("%d: \x1B[32m%s\x1B[0m\r\n", i, argv[i]);
    }    
}