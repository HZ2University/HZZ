#!/bin/bash
#运行的主脚本

# 判断温湿度传感器文件是否存在
if [ -f /home/uptech/mqtt_program/modules/Temperature/driver/DHT11_driver.ko ]; then
  insmod /home/uptech/mqtt_program/modules/Temperature/driver/DHT11_driver.ko
  echo '温湿度传感器驱动存在，启动传感器...'
else
  echo "DHT11驱动不存在，开始编译和安装..."
  # 编译驱动
  make -C /home/uptech/mqtt_program/modules/Temperature/driver
  # 安装驱动
  insmod /home/uptech/mqtt_program/modules/Temperature/driver/DHT11_driver.ko
fi


#判断LED驱动文件是否存在
if [ -f /home/uptech/mqtt_program/modules/LEDBuzzer/driver/LEDBuzzer_driver.ko ]; then
    echo "LED灯驱动文件存在"
    insmod /home/uptech/mqtt_program/modules/LEDBuzzer/driver/LEDBuzzer_driver.ko
else 
  echo "LED灯驱动文件不存在，重进编译加载"
  #编译驱动，启动Makefile文件
  make -C /home/uptech/mqtt_program/modules/LEDBuzzer/driver/
  #安装驱动  
  insmod /home/uptech/mqtt_program/modules/LEDBuzzer/driver/LEDBuzzer_driver.ko
fi

# 判断舵机驱动文件是否存在
if [ -f /home/uptech/mqtt_program/modules/Steering_engine/driver/DCMotor_driver.ko ];then
  echo "舵机驱动存在。"
  insmod /home/uptech/mqtt_program/modules/Steering_engine/driver/DCMotor_driver.ko
else
  echo "舵机驱动文件不存在，重新编译加载"
  make -C /home/uptech/mqtt_program/modules/Steering_engine/driver
  insmod /home/uptech/mqtt_program/modules/Steering_engine/driver/DCMotor_driver.ko
fi

#判断光照驱动文件是否存在
if [ -f /home/uptech/mqtt_program/modules/BH1750/driver/BH1750_driver.ko ]; then
    echo "光照传感器驱动文件存在"
    insmod /home/uptech/mqtt_program/modules/BH1750/driver/BH1750_driver.ko
else 
  echo "光照传感器文件不存在，重进编译加载"
  #编译驱动，启动Makefile文件
  make -C /home/uptech/mqtt_program/modules/BH1750/driver/
  #安装驱动  
  insmod /home/uptech/mqtt_program/modules/BH1750/driver/BH1750_driver.ko
fi

#判断独立按键驱动文件是否存在
if [ -f /home/uptech/mqtt_program/modules/KeyModule/driver/KeyModule_driver.ko ]; then
    echo "独立按键驱动文件存在"
    insmod /home/uptech/mqtt_program/modules/KeyModule/driver/KeyModule_driver.ko
else 
  echo "独立按键文件不存在，重进编译加载"
  #编译驱动，启动Makefile文件
  make -C /home/uptech/mqtt_program/modules/KeyModule/driver/
  #安装驱动  
  insmod /home/uptech/mqtt_program/modules/KeyModule/driver/KeyModule_driver.ko
fi


#判断启动文件是否编译
if [ -f /home/uptech/mqtt_program/mqtt_run ]; then
   rm /home/uptech/mqtt_program/mqtt_run
else
   echo "编译传感器文件"
   
fi
#编译
gcc -o mqtt_run mqtt_transmit.c sensor.c -lpaho-mqtt3a -lcjson -lm
# 测试
/home/uptech/mqtt_program/mqtt_run