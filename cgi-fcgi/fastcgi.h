/*
 * =====================================================================================
 *
 *       Filename:  fastcgi.h
 *
 *    Description:  fastcgi message definition
 *
 *        Version:  1.0
 *        Created:  2018/01/30 20时23分38秒
 *       Revision:  none
 *       Compiler:  gcc
 *
 *         Author:  ssj
 *
 * =====================================================================================
 */


/*
 * 消息类型定义
 */
#define FCGI_BEGIN_REQUEST       1
#define FCGI_ABORT_REQUEST       2
#define FCGI_END_REQUEST         3
#define FCGI_PARAMS              4
#define FCGI_STDIN               5
#define FCGI_STDOUT              6
#define FCGI_STDERR              7
#define FCGI_DATA                8
#define FCGI_GET_VALUES          9
#define FCGI_GET_VALUES_RESULT  10
#define FCGI_UNKNOWN_TYPE       11
#define FCGI_MAXTYPE (FCGI_UNKNOWN_TYPE)


/*
 * 消息头部结构体
 */
typedef struct {
	unsigned char version;
	unsigned char type;
	unsigned char requestIdB1;
	unsigned char requestIdB0;
	unsigned char contentLengthB1;
	unsigned char contentLengthB0;
	unsigned char paddingLength;
	unsigned char reserved;
} FCGI_Header;


/*
 * BEGIN_REQUEST 消息定义
 */
typedef struct {
	unsigned char roleB1;
	unsigned char roleB0;
	unsigned char flags;
	unsigned char reserved[5];
} FCGI_BeginRequestBody;

typedef struct {
	FCGI_Header header;
	FCGI_BeginRequestBody body;
} FCGI_BeginRequestRecord;


/*
 * FCGI_BeginRequestBody 的role字段的定义
 */
#define FCGI_RESPONDER  1
#define FCGI_AUTHORIZER 2
#define FCGI_FILTER     3


/*
 * END_REQUEST 消息定义
 */
typedef struct {
	unsigned char appStatusB3;
	unsigned char appStatusB2;
	unsigned char appStatusB1;
	unsigned char appStatusB0;
	unsigned char protocolStatus;
	unsigned char reserved[3];
} FCGI_EndRequestBody;

typedef struct {
	FCGI_Header header;
	FCGI_EndRequestBody body;
} FCGI_EndRequestRecord;


/*
 * Name-Value Pairs定义，PARAMS消息用的就是这种。
 */
typedef struct {
	unsigned char nameLengthB0;  /* nameLengthB0  >> 7 == 0 */
	unsigned char valueLengthB0; /* valueLengthB0 >> 7 == 0 */
	unsigned char nameData[nameLength];
	unsigned char valueData[valueLength];
} FCGI_NameValuePair11;

typedef struct {
	unsigned char nameLengthB0;  /* nameLengthB0  >> 7 == 0 */
	unsigned char valueLengthB3; /* valueLengthB3 >> 7 == 1 */
	unsigned char valueLengthB2;
	unsigned char valueLengthB1;
	unsigned char valueLengthB0;
	unsigned char nameData[nameLength];
	unsigned char valueData[valueLength
		((B3 & 0x7f) << 24) + (B2 << 16) + (B1 << 8) + B0];
} FCGI_NameValuePair14;

typedef struct {
	unsigned char nameLengthB3;  /* nameLengthB3  >> 7 == 1 */
	unsigned char nameLengthB2;
	unsigned char nameLengthB1;
	unsigned char nameLengthB0;
	unsigned char valueLengthB0; /* valueLengthB0 >> 7 == 0 */
	unsigned char nameData[nameLength
		((B3 & 0x7f) << 24) + (B2 << 16) + (B1 << 8) + B0];
	unsigned char valueData[valueLength];
} FCGI_NameValuePair41;

typedef struct {
	unsigned char nameLengthB3;  /* nameLengthB3  >> 7 == 1 */
	unsigned char nameLengthB2;
	unsigned char nameLengthB1;
	unsigned char nameLengthB0;
	unsigned char valueLengthB3; /* valueLengthB3 >> 7 == 1 */
	unsigned char valueLengthB2;
	unsigned char valueLengthB1;
	unsigned char valueLengthB0;
	unsigned char nameData[nameLength
		((B3 & 0x7f) << 24) + (B2 << 16) + (B1 << 8) + B0];
	unsigned char valueData[valueLength
		((B3 & 0x7f) << 24) + (B2 << 16) + (B1 << 8) + B0];
} FCGI_NameValuePair44;

