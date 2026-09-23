#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File   : main_xbox.py
Author : FantasyWilly   
Email  : bc697522h04@gmail.com  
SPDX-License-Identifier: Apache-2.0 

開發公司:
    • 田屋科技 (XF)

功能總覽:
    • Xbox 搖桿控制
    • 發送相機控制指令
    • 接收相機回傳資料
    • 回傳資料發布至 ROS2
"""

# ------------------------------------------------------------------------------------ #
# Imports
# ------------------------------------------------------------------------------------ #
# 標準庫
import time
import pygame
import threading

# 第三方套件
import cv2

# ROS2
import rclpy

# 專案內部模組
import ktg_camera_command as cm
import ktg_camera_loop_command as loop_cm
from ktg_camera_communication import CommunicationController


# ------------------------------------------------------------------------------------ #
# TCP 連線 <IP:Port> 
# ------------------------------------------------------------------------------------ #
DEVICE_IP = "192.168.51.157"
DEVICE_PORT = 9999


# ------------------------------------------------------------------------------------ #
# 影像串流 <CAMERA_URL>
# ------------------------------------------------------------------------------------ #
CAMERA_URL  = 'rtsp://192.168.51.157:8554/live/stream'


# ------------------------------------------------------------------------------------ #
# Gimbal 控制速度
# ------------------------------------------------------------------------------------ #
GIMBAL_SPEED_MIN = 1
GIMBAL_SPEED_MAX = 12
GIMBAL_SPEED_DEFAULT = 5


# ------------------------------------------------------------------------------------ #
# xbox 傳輸控制指令
# ------------------------------------------------------------------------------------ #
def xbox_controller_loop(controller, stop_event: threading.Event):

    # 初始化 xbox 搖桿
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("未找到 Xbox 控制器")
        return

    # 取得第一個連接的控制器並初始化
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print("Xbox 控制器已啟動")

    laser_enabled = False

    # Gimbal 初始速度
    gimbal_speed = GIMBAL_SPEED_DEFAULT

    while True:
        for event in pygame.event.get():

            if event.type == pygame.JOYBUTTONDOWN:

                if joystick.get_button(0):
                    # A：向下
                    cm.Command.Down_command(controller)

                elif joystick.get_button(1):
                    # B：開始追蹤
                    cm.Command.StartTracking_command(
                        controller,
                        4096,
                        4096,
                        20,
                        20
                    )

                elif joystick.get_button(2):
                    # X：取消追蹤
                    cm.Command.StopTracking_command(controller)

                elif joystick.get_button(3):
                    # Y：回中
                    cm.Command.Netural_command(controller)

                # LB：降低 Gimbal 速度
                elif joystick.get_button(4):

                    gimbal_speed -= 1

                    if gimbal_speed < GIMBAL_SPEED_MIN:
                        gimbal_speed = GIMBAL_SPEED_MIN

                    print(f"Gimbal Speed: {gimbal_speed}")

                # RB：增加 Gimbal 速度
                elif joystick.get_button(5):

                    gimbal_speed += 1

                    if gimbal_speed > GIMBAL_SPEED_MAX:
                        gimbal_speed = GIMBAL_SPEED_MAX

                    print(f"Gimbal Speed: {gimbal_speed}")

            # 按鍵 - [選單, 目錄]  
            if event.type == pygame.JOYBUTTONDOWN:
                if joystick.get_button(6):
                    # print("聚焦")
                    cm.Command.PointFocucomand(controller)
                elif joystick.get_button(7):
                    # print("跟隨")
                    cm.Command.FollowHeader_command(controller)
                elif joystick.get_button(11):
                    laser_enabled = not laser_enabled

                    if laser_enabled:
                        cm.Command.Laser_command(controller,1)
                        # print("Laser ON")
                    else:
                        cm.Command.Laser_command(controller,0)
                        # print("Laser OFF")

            # 按鍵 - [上下左右]    
            elif event.type == pygame.JOYHATMOTION:
                hat = joystick.get_hat(0)

                pitch = hat[1] * gimbal_speed * 10
                yaw   = hat[0] * gimbal_speed * 10

                if hat != (0, 0):
                    print(
                        f"發送雲台控制指令 -> "
                        f"Speed Level: {gimbal_speed}, "
                        f"pitch_speed: {pitch / 10} deg/s, "
                        f"yaw_speed: {yaw / 10} deg/s"
                    )

                    cm.Command.GimbalControl_command(
                        controller,
                        yaw_speed=yaw,
                        pitch_speed=pitch
                    )

            # 按鍵 - [右扳機 (RT) - 5], [左扳機 (LT) - 2]
            elif event.type == pygame.JOYAXISMOTION:

                if event.axis == 5:
                    rt_value = joystick.get_axis(5)
                    if rt_value > 0.5:
                        # print("RT 按下: zoom_in")
                        cm.Command.MachineZoom_command(controller, 1)
                    else:
                        # print("RT 釋放: zoom_stop")
                        cm.Command.MachineZoom_command(controller,3)
                
                elif event.axis == 2:
                    lt_value = joystick.get_axis(2)
                    if lt_value > 0.5:
                        # print("LT 按下: zoom_out")
                        cm.Command.MachineZoom_command(controller,2)
                    else:
                        # print("LT 釋放: zoom_stop")
                        cm.Command.MachineZoom_command(controller,3)
        time.sleep(0.1)


# ------------------------------------------------------------------------------------ #
# 主程式
# ------------------------------------------------------------------------------------ #
def main():
    """
    - 說明 [main]
        1. 創建 [GCUController] 並 連線至 GCU控制盒
        2. 初始化 ROS2
        3. 動態獲取 畫面像素大小
        4. 連續發送空命令 -> 接收返回資訊
        5. Xbox 搖桿控制
    """

    # 動態獲取 CAMERA_URL 串流影像大小
    cap = cv2.VideoCapture(CAMERA_URL)
    if not cap.isOpened():
        print(f"[CAMERA_URL] 無法連接到串流: {CAMERA_URL}")
        width = height = 0
    else:
        width   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height  = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        print(f"[CAMERA_URL] 畫面大小: {width}x{height}")

    # 初始化 ROS2 
    rclpy.init()

    # 建立 TCP 連線物件 - [GCUController]
    controller = CommunicationController(DEVICE_IP, DEVICE_PORT, width, height)

    try:
        # 1. TCP 連線
        controller.connect()

        # 2-1. 建立一個 stop_event 讓背景線程知道什麼時候要結束
        stop_event = threading.Event()

        # 2-2. 開啟 [LOOP] 背景線程, 持續發送空命令
        loop_thread = threading.Thread(
            target=loop_cm.loop_in_background,
            args=(controller, stop_event),
            daemon=True
        )
        loop_thread.start()
        print("[LOOP] - 開始不斷發送空命令")

        # 3-1. 開啟 Xbox 遙控控制
        xbox_thread = threading.Thread(
            target=xbox_controller_loop,
            args=(controller, stop_event),
            daemon=True
        )
        xbox_thread.start()

        # 主线程阻塞
        while rclpy.ok() and not stop_event.is_set():
            time.sleep(0.2)

    except Exception as e:
        print("[main] 出現錯誤:", e)
        stop_event.set()
    finally:
        # 通知所有线程退出
        stop_event.set()
        loop_thread.join()
        xbox_thread.join()
        controller.disconnect()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
