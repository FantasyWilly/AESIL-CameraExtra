#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File   : main_cmd.py
Author : FantasyWilly   
Email  : bc697522h04@gmail.com  
SPDX-License-Identifier: Apache-2.0 

開發公司:
    • 田屋科技 (XF)

功能總覽:
    • CMD 鍵盤輸入控制
    • 發送相機控制指令
    • 接收相機回傳資料
    • 回傳資料發布至 ROS2

遵循:
    • Google Python Style Guide (含區段標題)
    • PEP 8 (行寬 ≤ 88, snake_case, 2 空行區段分隔)
"""

# ------------------------------------------------------------------------------------ #
# Imports
# ------------------------------------------------------------------------------------ #
# 標準庫
import threading

# 第三方套件
import cv2

# ROS2
import rclpy

# 專案內部模組
import ktg_camera_command as cm
import ktg_camera_loop_command as loop_cm
from ktg_camera_communication import CommunicationController
from ktg_camera_decoder import ReceiveMsg


# ------------------------------------------------------------------------------------ #
# TCP 連線 <IP:Port>
# ------------------------------------------------------------------------------------ #
DEVICE_IP   = "192.168.51.157"
DEVICE_PORT = 9999


# ------------------------------------------------------------------------------------ #
# 影像串流 <CAMERA_URL>
# ------------------------------------------------------------------------------------ #
CAMERA_URL  = 'rtsp://192.168.51.157:8554/live/stream'


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
        5. 讓使用者輸入指令
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

        # 3. 創建 CMD 輸入控制指令界面
        while True:
            cmd = input(
                "請輸入指令 "
                "(reset/ photo / video / down / follow / control / quit):"
            ).strip().lower()

            if cmd == 'reset':
                cm.Command.Netural_command(controller)
            elif cmd == "photo":
                cm.Command.Photo_command(controller)
            elif cmd == "video":
                cm.Command.Video_command(controller)
            elif cmd == "down":
                cm.Command.Down_command(controller)
            elif cmd == "follow":
                cm.Command.FollowHeader_command(controller)
            elif cmd == "control":
                angles = input("請輸入角度 Pitch & Yaw (以空格分隔, Ex: 5 -3.2):").strip()
                try:
                    pitch_str, yaw_str = angles.split()
                    pitch = float(pitch_str)
                    yaw   = float(yaw_str)
                except ValueError:
                    print("輸入格式錯誤, 請輸入兩個數字, 用空格隔開")
                    continue
                cm.Command.GimbalControl_command(controller, pitch, yaw)

            elif cmd == "quit":
                print("已退出操作")
                break
            else:
                print("無效指令,請重新輸入")

    except Exception as e:
        print("[main] 出現錯誤:", e)
    finally:
        controller.disconnect()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
