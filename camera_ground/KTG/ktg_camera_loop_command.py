#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
File   : camera_loop_command.py
author : FantasyWilly
email  : bc697522h04@gmail.com

相機型號 : KTG-TT30
檔案大綱 :
    A. 持續發送 回傳命令
'''

# Python
import time
import threading

# ROS2
import rclpy

# 引用 Python 檔 (mine)
from ktg_camera_communication import CommunicationController

def loop_in_background(controller: CommunicationController, stop_event: threading.Event):
    while not stop_event.is_set():
        if not rclpy.ok():
            print("[LOOP] rclpy 已關閉，背景迴圈退出")
            break

        try:
            controller.loop_send_command(b'\x4B\x4B\x01\x97')

        except Exception as e:
            if stop_event.is_set() or not rclpy.ok():
                print("[LOOP] 偵測到關閉狀態，背景執行緒結束")
                break

            print("[LOOP ERROR] 無法送出資料", e)
            time.sleep(0.2)

        time.sleep(0.05)

    print("[LOOP] 背景執行緒已結束")
