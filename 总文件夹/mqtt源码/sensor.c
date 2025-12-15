//Tempertature.c

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>                                                     
#include <sys/ioctl.h>
/*设备节点名字*/
#define I2C_DEV		"/dev/i2c-1"
/*ioctl 命令*/
#define I2C_SLAVE       0x0703  /* Use this slave address */
#define I2C_TENBIT      0x0704	/* 0 for 7 bit addrs, != 0 for 10 bit */
/* 传感器设备地址*/
#define CHIP_ADDR	0x23


/*****************************
*模块名称：温湿度传感器
*    描述：获取温湿度传感器数据
*    作者：Double_T77
*    时间：2024.3.20
*    版本：UP-Magic-Version 1.5
******************************/

//光照传感器数据

int write_BH1750(int fd, unsigned char addr, size_t count)
{
	int res;
	char  sendbuffer[count+1];
	sendbuffer[0] = addr;
	res=write(fd,sendbuffer,count);
	return 0;
}

static int read_BH1750(int fd, void *buff, int count)
{
	int res;	
	res=read(fd,buff,count);		//读取count个字节数据数据到buff缓存区
	return res;
}

// 获取温湿度信息函数
char *sensor(int *temp, int *humi, float *illum) {
    int fd;
    unsigned char buf[6]; // 定义存放数据的数组
    int length;
    char *senser_info;
    int fd2,res;
	float flux;
	unsigned char buf2[6];

    // 以只读方式打开设备节点
    fd = open("/dev/DHT11", O_RDONLY);
    if (fd == -1) {
        printf("打开设备节点失败！\n");
        return NULL;
    }

    // 循环读取温湿度数据
    // 读取数据
    length = read(fd, buf, 6);
    if (length == -1) {
        printf("读取数据失败！\n");
        close(fd);
        return NULL;
    }

    //获取传感器数据
	fd2 = open("/dev/i2c-1", O_RDWR);			//打开i2c设备节点
	if(fd2 < 0){
		printf("####i2c test device open failed####\n");
		return NULL;
	}
	if(-1 == ioctl(fd2,I2C_TENBIT,0)){		//设置地址位长度为 7bit
		printf("ioctl error on line %d\n",__LINE__);
		return NULL;
	}
	if(-1 == ioctl(fd2,I2C_SLAVE,CHIP_ADDR)){	//设置从设备地址
		printf("ioctl error on line %d\n",__LINE__);
		return NULL;
	}
	res = write_BH1750(fd2, 0x01, 1);		//发送指令0x01：等待测量指令
	if(res == -1){
		printf("write error on line %d\n", __LINE__);
	}
	res = write_BH1750(fd2, 0x10, 1);		//发送指令0x10：连续H分辨率模式
	if(res == -1){
		printf("write error on line %d\n", __LINE__);
	}

    usleep(120*1000);			//延时120ms
    memset(buf2,0,sizeof(buf2));		//清零
    read_BH1750(fd2,buf2,2);			//读取光照强度数据
    flux = (float)(buf2[0] << 8 | buf2[1])/1.2;
    fflush(stdout);		
    // 将值赋给指针变量
    *temp = buf[2];
    *humi = buf[0];
    *illum = flux;

    
    // printf("sensor_info:%s\n",senser_info);

    // 关闭设备节点
    close(fd);
    close(fd2);

    // 返回数据指针
    return 0;
}



/*****************************
*模块名称：led蜂鸣器模块
*    描述：操作led蜂蜜器传感器
*    作者：Double_T77
*    时间：2024.3.20
*    版本：UP-Magic-Version 1.5
******************************/
/*ioctl操作命令*/
#define IOCTL_LED_ON		0	//灯开
#define IOCTL_LED_OFF		1	//灯灭
#define IOCTL_BUZZER_OFF	3	//蜂鸣器关
#define IOCTL_BUZZER_ON		4	//蜂鸣器开

int LED_Open(int on_off)
{
    unsigned int led;	//定义led
    unsigned int puzzer;//定义蜂鸣器
    int fd = -1,menu_num;
    fd = open("/dev/LEDBuzzer", 0);		//打开模块设备文件，0为O_RDONLY
    if (fd < 0) {				//打开失败
        printf("Can't open /dev/LEDBuzzer\n");
        return -1;
    }
    switch(on_off){
        case 0:
            ioctl(fd,IOCTL_LED_OFF);
            break;
        case 1:
            ioctl(fd,IOCTL_LED_ON);
            break;
        case 2:
            ioctl(fd,IOCTL_BUZZER_ON);
            break;
        case 3:
            ioctl(fd,IOCTL_BUZZER_OFF);
            break;
    }
    close(fd);					//关闭文件
	return 0;
}


/*****************************
*模块名称：舵机控制模块
*    描述：操作舵机转速及自动旋转功能
*    作者：Double_T77
*    时间：2024.3.23
*    版本：UP-Magic-Version 1.5
******************************/

/*定义ioctl操作项*/
#define DCM_IOCTRL_SETPWM	(0x10)
#define DCM_IOCTRL_STATUS	(0x20)
#define DCM_IOCTRL_STOP		(0x30)
#define DCM_IOCTRL_START	(0x40)

char *DCM_DEV="/dev/DCMotor";		//定义字符串指针，指向模块设备名
int cmd_group[] = {DCM_IOCTRL_SETPWM, DCM_IOCTRL_START, DCM_IOCTRL_STATUS, DCM_IOCTRL_STOP};

//手动调整舵机角度
int SEmotor(int angle)
{
	int dcm_fd, menu_num, cmd, status;
	long int arg;
	dcm_fd = open(DCM_DEV, O_WRONLY);			//打开模块设备节点	
	if(dcm_fd < 0){		
		printf("Error opening %s device\n", DCM_DEV);
		return 1;
	}
    if (angle < 0 || angle > 360) {
            printf("Invalid angle. Angle should be between 0 and 180.\n");
        }
    arg = (angle*100000/9)+500000;
    cmd = cmd_group[0];
    ioctl(dcm_fd, cmd, arg);
	close(dcm_fd);						//关闭设备文件
	return 0;
}


#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <signal.h>
#include <unistd.h>

//unsigned int flag;

int _KeyModule()
{
	int fd, buf;
	fd = open("/dev/KeyModule",O_RDWR);
	if(fd < 0)
	{
		printf("打开失败\n");
		return -1;
	}
    //printf("waiting \n");
    usleep(1000);
    read(fd,&buf,4);
    switch(buf){
        case 1:
            LED_Open(1);
            break;
        case 2:
            LED_Open(2);
            break;
        case 3:
            LED_Open(3);
            break;
        case 4:
            LED_Open(4);
            break;
    }
    buf = 0;
	close(fd);
	return 0;
}



