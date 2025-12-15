#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <signal.h>
#include <unistd.h>
#include "MQTTAsync.h"
#include "cJSON/cJSON.h"
#include "all.h"
#include <pthread.h>
#include <math.h>
#if !defined(_WIN32)
#include <unistd.h>
#else
#include <windows.h>
#endif
#include <pthread.h>
#include <stdbool.h>
#if defined(_WRS_KERNEL)
#include <OsWrapper.h>
#endif

#define ADDRESS "139.159.185.58:1883"
#define CLIENTID "ts"

#define TOPIC_Pub "low_pub"
#define TOPIC_Sub "low_sub"

#define Sensor_TOPIC "sensor"
#define BASE_USERNAME "admin"
#define BASE_PASSWORD "admin"
#define PAYLOAD "Hello World!"
#define LED_TOPIC "led"
#define BEEP_TOPIC "beep"
#define SE_Topic "semotor"
#define SE_Auto_TOPIC "se_auto"
#define DC_TOPIC "dcmotor"
#define DC_Auto_TOPIC "dc_auto"
#define QOS 1
#define TIMEOUT 10000L

/*定义ioctl操作项*/
#define DCM_IOCTRL_SETPWM	(0x10)
#define DCM_IOCTRL_STATUS	(0x20)
#define DCM_IOCTRL_STOP		(0x30)
#define DCM_IOCTRL_START	(0x40)

MQTTAsync_connectOptions conn_opts = MQTTAsync_connectOptions_initializer;

int subscribed = 0;
int disc_finished = 0;
_Bool led_control = false;
_Bool se_auto_or_not = false; //判断舵机自动化运行行为
_Bool beep_control = false;
_Bool lower_publish_bool = false;
int se_angle = 0;
int dc_auto_or_not = 0;
int dc_speed = 0;

void onConnect(void *context, MQTTAsync_successData *response);
void onConnectFailure(void *context, MQTTAsync_failureData *response);
void connlost(void *context, char *cause);
int msgarrvd(void *context, char *topicName, int topicLen, MQTTAsync_message *message);
void onDisconnectFailure(void *context, MQTTAsync_failureData *response);
void onDisconnect(void *context, MQTTAsync_successData *response);
void onSubscribe(void *context, MQTTAsync_successData *response);
void onSubscribeFailure(void *context, MQTTAsync_failureData *response);
void onSend(void *context, MQTTAsync_successData *response);
void onSendFailure(void *context, MQTTAsync_failureData *response);

//主函数
int main(int argc, char *argv[])
{

    MQTTAsync client;                                                                
    MQTTAsync_disconnectOptions disc_opts = MQTTAsync_disconnectOptions_initializer; 
    pthread_t thread;
    int ret;
    int rc;
    int fd, buf;
    int ch;
    int temp, humi;
    float illum;


    fd = open("/dev/KeyModule",O_RDWR);
    if ((rc = MQTTAsync_create(&client, ADDRESS, CLIENTID, MQTTCLIENT_PERSISTENCE_NONE, NULL)) != MQTTASYNC_SUCCESS)
    {
        printf("Failed to create client, return code %d\n", rc);
        rc = EXIT_FAILURE;
        goto exit;
    };

    if ((rc = MQTTAsync_setCallbacks(client, client, connlost, msgarrvd, NULL)) != MQTTASYNC_SUCCESS)
    {
        printf("Failed to set callbacks, return code %d\n", rc);
        rc = EXIT_FAILURE;
        goto destroy_exit;
    };

    //连接MQTT服务器
    conn_opts.keepAliveInterval = 20;       
    conn_opts.cleansession = 1;             
    conn_opts.onSuccess = onConnect;       
    conn_opts.onFailure = onConnectFailure; 
    conn_opts.context = client;             
    conn_opts.username = BASE_USERNAME;     
    conn_opts.password = BASE_PASSWORD;     

    MQTTAsync_responseOptions send_opts = MQTTAsync_responseOptions_initializer;
    send_opts.onSuccess = onSend;
    send_opts.onFailure = onSendFailure;
    send_opts.context = client;
 
    if ((rc = MQTTAsync_connect(client, &conn_opts)) != MQTTASYNC_SUCCESS)
    {
        printf("Failed to start connect, return code %d\n", rc);
        rc = EXIT_FAILURE;
        goto destroy_exit;
    }

    while (!subscribed && !disc_finished)
#if defined(_WIN32)
        Sleep(100);
#else
        usleep(10000L);
#endif

    if (disc_finished)
        goto exit;
    
    MQTTAsync_message pub_lower_c_msg = MQTTAsync_message_initializer;
    MQTTAsync_message pub_led_msg = MQTTAsync_message_initializer;
    while(1){
    //生成JSON对象
    cJSON *root = cJSON_CreateObject();
    //获取温湿度，光照强度值
    sensor(&temp, &humi, &illum);
    cJSON_AddNumberToObject(root,"temp",temp);
    cJSON_AddNumberToObject(root,"humi",humi);
    cJSON_AddNumberToObject(root,"illum",round(illum));

    // 添加订阅逻辑，会订阅所有设置标题在 MQTTAsync_subscribe(client, LED_TOPIC, QOS, &sub_opts)) 代码中
    MQTTAsync_responseOptions sub_opts = MQTTAsync_responseOptions_initializer;
    sub_opts.onSuccess = onSubscribe;
    sub_opts.onFailure = onSubscribeFailure;
    sub_opts.context = client;

    if ((rc = MQTTAsync_subscribe(client, LED_TOPIC, QOS, &sub_opts)) != MQTTASYNC_SUCCESS) {
        printf("Failed to subscribe to topic %s, return code %d\n", LED_TOPIC, rc);
        // 处理订阅失败 (可选)
    }
    else{
        //打开LED灯
        usleep(100*1000);
        if (led_control){
        LED_Open(1);}
        else{LED_Open(0);}
    }

        if ((rc = MQTTAsync_subscribe(client, BEEP_TOPIC, QOS, &sub_opts)) != MQTTASYNC_SUCCESS) {
        printf("Failed to subscribe to topic %s, return code %d\n", BEEP_TOPIC, rc);
        // 处理订阅失败 (可选)
    }
    else{
        //打开LED灯
        if (beep_control){
        LED_Open(2);}
        else{LED_Open(3);}
    }

    //判断舵机的行为方式
        if ((rc = MQTTAsync_subscribe(client, SE_Auto_TOPIC, QOS, &sub_opts)) != MQTTASYNC_SUCCESS) {
        printf("Failed to subscribe to topic %s, return code %d\n", SE_Auto_TOPIC, rc);
        // 处理订阅失败 (可选)
    }
    usleep(100*1000);

    //接受舵机定位角度
    if (!se_auto_or_not){
        if ((rc = MQTTAsync_subscribe(client, SE_Topic, QOS, &sub_opts)) != MQTTASYNC_SUCCESS) {
            printf("Failed to subscribe to topic %s, return code %d\n", SE_Topic, rc);
            // 处理订阅失败 (可选)
        }
        else{
            //调整舵机
            usleep(100*1000);
            SEmotor(se_angle);
        }
    }
    else{
        int run;
        run = SE_Auto_run();
    }

    //判断电机的行为方式
        if ((rc = MQTTAsync_subscribe(client, DC_Auto_TOPIC, QOS, &sub_opts)) != MQTTASYNC_SUCCESS) {
        printf("Failed to subscribe to topic %s, return code %d\n", SE_Auto_TOPIC, rc);
        // 处理订阅失败 (可选)
    }
    usleep(100*1000);

     if ((rc = MQTTAsync_subscribe(client, DC_TOPIC, QOS, &sub_opts)) != MQTTASYNC_SUCCESS) {
            printf("Failed to subscribe to topic %s, return code %d\n", DC_TOPIC, rc);
            // 处理订阅失败 (可选)
        }

    if (dc_auto_or_not == 1){
        if ((rc = MQTTAsync_subscribe(client, DC_TOPIC, QOS, &sub_opts)) != MQTTASYNC_SUCCESS) {
            printf("Failed to subscribe to topic %s, return code %d\n", DC_TOPIC, rc);
            // 处理订阅失败 (可选)
        }
        // 调整电机
        usleep(100*1000);
        int run2;
        run2 = DCmotor(dc_speed);
    }

    //监听独立按键
    if(fd < 0)
    {
        printf("打开失败\n");
        return -1;
    }
    //printf("waiting \n");
    usleep(1000);
    read(fd,&buf,4);
    if (buf!= 0) {
    lower_publish_bool = true;
    printf("buf%d\n",buf);
    switch(buf){
        case 1:
            if (!led_control){
            LED_Open(1);
            led_control = true;
            }
            else{
            LED_Open(0);
            led_control = false;
            }
            break;
        case 2:
            if (!beep_control){
            LED_Open(2);
            beep_control = true;
            }
            else{
            LED_Open(3);
            beep_control = false;
            }
            break;
        case 3:
            if(!se_auto_or_not)
            {
                se_auto_or_not = true;
            }
            else{
                se_auto_or_not = false;
            }
            break;
        case 4:
            LED_Open(4);
            break;
        case 5:
            LED_Open(1);
            break;
    }
    if ((buf == 1 || buf == 5) && led_control){
        buf = 5;
    }
    else{
        buf = 0;
    }
    }
    else{
        lower_publish_bool = false;
    }
    
    
    if (temp > 80 || humi > 80){
        LED_Open(2);
    }
    else{
        if (beep_control){
        LED_Open(2);
        }
        else{
            LED_Open(3);
        }
    }
    if (illum < 25){
        LED_Open(1);
    }
    else{
        LED_Open(led_control);
    }
    // if (led_control || beep_control){
    //     led_control = true;
    // }
    // else{
    //     led_control = false;
    // }
    cJSON_AddBoolToObject(root,"led_control",led_control);
    cJSON_AddBoolToObject(root,"beep_control",beep_control);
    cJSON_AddBoolToObject(root,"se_auto_or_not",se_auto_or_not);
    cJSON_AddNumberToObject(root,"se_angle",se_angle);
    cJSON_AddBoolToObject(root,"dc_auto_or_not",dc_auto_or_not);
    cJSON_AddNumberToObject(root,"dc_speed",dc_speed);
    cJSON_AddBoolToObject(root,"lower_publish_bool",lower_publish_bool);
    char *json_str = cJSON_Print(root);
        

    // usleep(100*10000);

    pub_lower_c_msg.payload = json_str;
    pub_lower_c_msg.payloadlen = strlen(json_str);
    pub_lower_c_msg.qos = QOS;
    pub_lower_c_msg.retained = 0;

    usleep(100*1000);
    // 发布下位机信息
    if ((rc = MQTTAsync_sendMessage(client, TOPIC_Pub, &pub_lower_c_msg, &send_opts)) != MQTTASYNC_SUCCESS)
    {
        printf("Failed to send message, return code %d\n", rc);
    }

    cJSON_Delete(root);
    };
    close(fd);

    disc_opts.onSuccess = onDisconnect;
    disc_opts.onFailure = onDisconnectFailure;

    if ((rc = MQTTAsync_disconnect(client, &disc_opts)) != MQTTASYNC_SUCCESS)
    {
        printf("Failed to start disconnect, return code %d\n", rc);
        rc = EXIT_FAILURE;
        goto destroy_exit;
    }

    while (!disc_finished)
#if defined(_WIN32)
        Sleep(100);
#else
        usleep(10000L);
#endif

destroy_exit:
    MQTTAsync_destroy(&client);

exit:
    return rc;
}

void onConnect(void *context, MQTTAsync_successData *response)
{
    MQTTAsync client = (MQTTAsync)context;
    MQTTAsync_responseOptions opts = MQTTAsync_responseOptions_initializer;
    int rc;

    printf("Successful connection\n");

    printf("Subscribing to topic %s\nfor client %s using QoS%d\n\n", TOPIC_Pub, CLIENTID, QOS);
    opts.onSuccess = onSubscribe;
    opts.onFailure = onSubscribeFailure;
    opts.context = client;

    if ((rc = MQTTAsync_subscribe(client, TOPIC_Pub, QOS, &opts)) != MQTTASYNC_SUCCESS)
    {
        printf("Failed to start subscribe, return code %d\n", rc);
        disc_finished = 1;
    }
}

void onConnectFailure(void *context, MQTTAsync_failureData *response)
{
    printf("Connect failed, rc %d\n", response->code);
    disc_finished = 1;
}

void connlost(void *context, char *cause)
{
    MQTTAsync client = (MQTTAsync)context;
    int rc;

    printf("\nConnection lost\n");
    if (cause)
        printf("     cause: %s\n", cause);

    printf("Reconnecting\n");
    conn_opts.keepAliveInterval = 20;
    conn_opts.cleansession = 1;
    conn_opts.onSuccess = onConnect;
    conn_opts.onFailure = onConnectFailure;
    printf("client:");
    if ((rc = MQTTAsync_connect(client, &conn_opts)) != MQTTASYNC_SUCCESS)
    {
        printf("Failed to start connect, return code %d\n", rc);
        disc_finished = 1;
    }
}

int msgarrvd(void *context, char *topicName, int topicLen, MQTTAsync_message *message)
{
printf("Message arrived\n");
    printf("  topic: %s\n", topicName);
    printf("  message: %.*s\n", message->payloadlen, (char*)message->payload);
    if ((strcmp(topicName, "low_pub") == 0)){
    cJSON *root = cJSON_Parse((char*)message->payload);
    // if (root != NULL) {
    // cJSON *name = cJSON_GetObjectItem(root, "name");
    // cJSON *age = cJSON_GetObjectItem(root, "age");
    // if (name != NULL && cJSON_IsString(name) && age != NULL && cJSON_IsNumber(age)) {
    //     printf("  Name: %s, Age: %d\n", name->valuestring, age->valueint);
    // }
    cJSON_Delete(root);
    }
    else{
        char str[5];
        strncpy(str, (char*)message->payload, sizeof(message) - 1);
        if (strcmp(topicName, "led") == 0){
        if (strcmp(str, "true") == 0) {
        led_control = true;
         }
        else if (strcmp(str, "false") == 0) {
            led_control = false;
        }
    }
    if (strcmp(topicName, "beep") == 0){
        if (strcmp(str, "true") == 0) {
        beep_control = true;
         }
        else if (strcmp(str, "false") == 0) {
            beep_control = false;
        }
    }
    if (strcmp(topicName, "se_auto") == 0){
        if (strcmp(str, "true") == 0) {
        se_auto_or_not = true;
         }
        else if (strcmp(str, "false") == 0) {
            se_auto_or_not = false;
        }
    }
    if (strcmp(topicName,"semotor") == 0){
        se_angle = atoi(str);
    }
    // if (strcmp(topicName, "dc_auto") == 0){
    //     dc_auto_or_not = atoi(str);
    // }
    // if (strcmp(topicName,"dcmotor") == 0){
    //     dc_speed = atoi(str);
    //     DCmotor(0);
    //     DCmotor(dc_speed);
    // }
    }
    MQTTAsync_freeMessage(&message);
    MQTTAsync_free(topicName);
    return 1;
}


void onDisconnectFailure(void *context, MQTTAsync_failureData *response)
{
    printf("Disconnect failed, rc %d\n", response->code);
    disc_finished = 1;
}

void onDisconnect(void *context, MQTTAsync_successData *response)
{
    printf("Successful disconnection\n");
    disc_finished = 1;
}

void onSubscribe(void *context, MQTTAsync_successData *response)
{
    subscribed = 1;
}
void onSubscribeFailure(void *context, MQTTAsync_failureData *response)
{
    printf("Subscribe failed, rc %d\n", response->code);
    disc_finished = 1;
}
void onSend(void *context, MQTTAsync_successData *response)
{}
void onSendFailure(void *context, MQTTAsync_failureData *response)
{
    printf("Failed to send message, rc %d\n", response->code);
}




//舵机自动运行
int SE_Auto_run() {
    int increasing,dcm_fd;
    char *DCM_DEV="/dev/DCMotor";		//定义字符串指针，指向模块设备名
    int cmd_group[] = {DCM_IOCTRL_SETPWM, DCM_IOCTRL_START, DCM_IOCTRL_STATUS, DCM_IOCTRL_STOP};
    dcm_fd = open(DCM_DEV, O_WRONLY);
    
    // 循环程序
    // 设置舵机初始角度
    dcm_fd = open(DCM_DEV, O_WRONLY);
    if(dcm_fd < 0){
        printf("Error opening %s device\n", DCM_DEV);
        return 1;
    }
  // 设置舵机初始角度
    printf("se_auto_or_not:%d\n",se_auto_or_not);
    // 计算舵机脉冲宽度
    int arg = (se_angle*100000/9)+500000;

    // 设置舵机脉冲宽度
    int cmd = cmd_group[0];
    ioctl(dcm_fd, cmd, arg);

    // 延时 10 毫秒
    usleep(1000*1000);

    if (se_angle==180){
        se_angle = 0;
    }
    else{
        se_angle =180;
    }
    // 更新舵机角度
    // if (increasing) {
    // se_angle+=180;
    // if (se_angle >= 180) {
    //     increasing = 0;
    // }
    // } 
    // else {
    // se_angle-=180;
    // if (se_angle <= 0) {
    //     increasing = 1;
    // }
    // }
    printf("se_angle:%d\n",se_angle);

    close(dcm_fd);
    return 0;
  
}


int DCmotor(int speed)
{
    char *DCM_DEV2="/dev/DCMotor2";		//定义字符串指针，指向模块设备名
    int cmd_group2[] = {DCM_IOCTRL_SETPWM, DCM_IOCTRL_START, DCM_IOCTRL_STATUS, DCM_IOCTRL_STOP};

	int dcm_fd, menu_num, cmd,cmd2, status;
	dcm_fd = open(DCM_DEV2, O_WRONLY);			//打开模块设备节点	

	if(dcm_fd < 0){		
		printf("Error opening %s device\n", DCM_DEV2);
		return 1;
	}

    if(speed == 0){
        cmd = cmd_group2[3];
        ioctl(dcm_fd, cmd, 65535);
        close(dcm_fd);						//关闭设备文件
        return 0;
    }
    // while(dc_auto_or_not == 1)
	// {
	// 	/*使用ioctl操作控制电机*/
		// cmd = cmd_group2[1];
    //     printf("speed:%d\n",speed);
	// 	ioctl(dcm_fd, cmd, speed);
	// }
    cmd = cmd_group2[1];
    ioctl(dcm_fd, cmd, speed);
	close(dcm_fd);						//关闭设备文件
	return 0;
}


