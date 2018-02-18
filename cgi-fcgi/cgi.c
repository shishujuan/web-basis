/*
 * =====================================================================================
 *
 *       Filename:  cgi.c
 *
 *    Description:  cgi server
 *
 *        Version:  1.0
 *        Created:  2018/01/30 20时02分54秒
 *       Revision:  none
 *       Compiler:  gcc
 *
 *         Author:  ssj
 *
 * =====================================================================================
 */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <string.h>
#include <signal.h>

#define SERV_PORT 6006
#define BUFSIZE 1024
typedef char* pchar;

char *str_join(char *str1, char *str2);
void handle_one_connection(int client_fd);
void make_response(int client_fd, char *result);

int main(void)
{
    struct sockaddr_in server_addr;
    int listen_fd;

    if((listen_fd = socket(AF_INET,SOCK_STREAM,0)) == -1){
        perror("create socket failed");
        exit(1);
    }

    bzero(&server_addr, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    server_addr.sin_port = htons(SERV_PORT);

	int opt = 1;
	setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    if(bind(listen_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) == -1) {
        perror("bind error");
        exit(1);
    }

    if(listen(listen_fd, 128) == -1) {
        perror("listen error");
        exit(1);
    }

    while(1) {
		struct sockaddr_in client_addr;
		int client_fd;
        socklen_t client_len;
        client_len = sizeof(client_addr);
        if ((client_fd = accept(listen_fd, (struct sockaddr *)&client_addr, &client_len)) == -1) {
            perror("accept error\n");
            continue;
        }

        int pid = fork();
		if (pid < 0) {
			perror("fork error");
			exit(1);
		}

        if (pid > 0) {
            close(client_fd);
        } else {
            close(listen_fd);
			handle_one_connection(client_fd);
			exit(0);
        }
    }

    close(listen_fd);
    return 0;
}

void handle_one_connection(int client_fd) {
    char input[BUFSIZE];
    FILE *cin;
    cin = fdopen(client_fd, "r");
    fgets(input, BUFSIZE, cin);
    printf("request:%s\n", input);
    pchar method, filename, query_string;

    method = strtok(input, " ");
    char *p = strtok(NULL, " ");
    filename = strtok(p, "?");
    if (strcmp(filename, "/favicon.ico") == 0) {
		make_response(client_fd, "favicon.ico");
        return;
    }

    query_string = strtok(NULL, "?");
    if (!query_string) {
		make_response(client_fd, "no query string");
        return;
    }

    putenv(str_join("QUERY_STRING=", query_string));

	int pp[2];
	pipe(pp);

	if (fork() == 0) {
		close(1);
		dup(pp[1]);
		close(pp[0]);
		close(pp[1]);
		char *file = str_join(".", filename);
		execl(file, "", NULL);
	} else {
		close(0);
		dup(pp[0]);
		close(pp[0]);
		close(pp[1]);
	    char result[BUFSIZE];
        size_t count = read(0, result, sizeof(result)-1);
	    result[count] = '\0';
		make_response(client_fd, result);
	}
}

char *str_join(char *str1, char *str2)
{
    char *result = malloc(strlen(str1) + strlen(str2) + 1);
    if (result == NULL) exit (1);

    strcpy(result, str1);
    strcat(result, str2);
    return result;
}

void make_response(int client_fd, char *result) {
    char *response_header = "HTTP/1.1 200 OK\r\nContent-Type:text/html\r\nContent-Length: %d\r\nServer: CGI\r\n\r\n%s";
    char output[BUFSIZE];
    sprintf(output, response_header, strlen(result), result);
    write(client_fd, output, sizeof(output));
    close(client_fd);
}

