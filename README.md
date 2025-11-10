# <div align="center">AESIL - CameraExtra</div>

## <div align="center">Outline</div>

- [程式下載 (Downloads)](#downloads)
- [相機控制 (Camera Controll) Extra](#camera)

## <div align="center">Downloads</div>

```bash
git clone https://github.com/FantasyWilly/AESIL-CameraExtra.git
```
---

## <div align="center">Camera</div>

  ### [ XF 系列 ]

  - `官網連結:` [ 先飛科技 ](https://www.allxianfei.com/) - [使用手冊 控制協議 3D圖檔等...]

  - `用途:` 將 `CAMERA 協議指令` 發送至載具端 (載具端須打開 Server)
  
  - `補充:` 載具端 須下載 `AESIL-Camera` 功能包 --- [跳轉連結](https://github.com/FantasyWilly/AESIL-Camera)

    ---

  - ⚠️ 記得修改 發送端 檔案連接的 `Server` IP, Port 且 在同網域底下

    ### 載具端
    ```bash
    # 接收控制指令 - [監聽端]
    ros2 run camera_xf_pkg main_air
    ```

    ----

    ### 發送端
    ```bash
    # 發送控制指令 - [發送端 (Xbox連接控制)]
    python3 ~/<你的路徑>/AESIL-CameraExtra/camera_ground/XF/main_ground_xbox.py
    ```

  ---


  