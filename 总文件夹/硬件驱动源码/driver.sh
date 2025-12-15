# 判断温湿度传感器文件是否存在
if [ -f /home/uptech/mqtt_program/modules/Temperature/driver/DHT11_driver.ko ]; then
  insmod /home/uptech/mqtt_program//modules/Temperature/driver/DHT11_driver.ko
  echo '温湿度传感器驱动存在，启动传感器...'
else
  echo "DHT11驱动不存在，开始编译和安装..."
  # 编译驱动
  make -C /home/uptech/mqtt_program/modules/Temperature/driver
  # 安装驱动
  insmod /home/uptech/mqtt_program/modules/Temperature/driver/DHT11_driver.ko
fi


#判断驱动文件是否存在
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

