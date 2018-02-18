/*
 * =====================================================================================
 *
 *       Filename:  hello.c
 *
 *    Description:  test cgi
 *
 *        Version:  1.0
 *        Created:  2018/01/30 20时14分54秒
 *       Revision:  none
 *       Compiler:  gcc
 *
 *         Author:  ssj
 *
 * =====================================================================================
 */

#include <stdio.h>
#include <stdlib.h>

int main(void)
{
    char *query_string;
    char name[1024];

    query_string = getenv("QUERY_STRING");
    if (query_string == NULL) {
        printf("param empty\n");
    } else if (sscanf(query_string, "name=%s", name) != 1) {
        printf("param format error: %s\n", query_string);
    } else {
        printf("Hello: %s\n", name);
    }
    return 0;
}
