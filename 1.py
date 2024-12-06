import psutil
import subprocess
import time
import os
import sys
import PySimpleGUI as sg
import json
import winreg

# 配置文件路径
CONFIG_FILE = "config.json"

# 获取当前连接的Wi-Fi名称
def get_current_wifi():
    wifi_name = None
    for iface, addrs in psutil.net_if_addrs().items():
        if iface.startswith("wlan"):  # 检查是否为无线网卡接口
            for addr in addrs:
                if addr.family == psutil.AF_INET:  # 获取IP地址
                    wifi_name = addr.address
                    break
    return wifi_name

# 禁用系统代理
def disable_proxy():
    print("Disabling system proxy...")
    subprocess.run(["netsh", "winhttp", "reset", "proxy"])

# 检查Wi-Fi连接并关闭代理
def check_wifi_and_disable_proxy(target_wifi):
    while True:
        current_wifi = get_current_wifi()
        if current_wifi == target_wifi:
            disable_proxy()
        time.sleep(10)

# 创建配置文件
def create_config():
    config = {
        "autostart": False,
        "wifi_name": "NJMU_WLAN"
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

# 读取配置文件
def load_config():
    if not os.path.exists(CONFIG_FILE):
        create_config()
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

# 保存配置
def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

# 设置开机自启动
def set_autostart(enable):
    key = winreg.HKEY_CURRENT_USER
    path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    name = "WiFiProxyDisabler"
    exe_path = os.path.abspath(sys.argv[0])

    with winreg.OpenKey(key, path, 0, winreg.KEY_WRITE) as reg_key:
        if enable:
            winreg.SetValueEx(reg_key, name, 0, winreg.REG_SZ, exe_path)
        else:
            try:
                winreg.DeleteValue(reg_key, name)
            except FileNotFoundError:
                pass

# 创建GUI界面
def create_gui():
    config = load_config()

    layout = [
        [sg.Text("Wi-Fi Proxy Disabler", font=("Helvetica", 16))],
        [sg.Text("Wi-Fi Name to Disable Proxy:", size=(30, 1)),
         sg.InputText(config["wifi_name"], size=(25, 1), key="wifi_name")],
        [sg.Checkbox("Run on Startup", default=config["autostart"], key="autostart")],
        [sg.Button("Save Settings"), sg.Button("Exit")]
    ]

    window = sg.Window("Wi-Fi Proxy Disabler", layout)

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED or event == "Exit":
            break
        if event == "Save Settings":
            # 更新配置
            config["wifi_name"] = values["wifi_name"]
            config["autostart"] = values["autostart"]
            save_config(config)

            # 设置开机自启动
            set_autostart(values["autostart"])

            sg.popup("Settings saved!", keep_on_top=True)

    window.close()

# 启动GUI并后台监控Wi-Fi连接
def main():
    config = load_config()
    
    # 启动GUI线程
    import threading
    gui_thread = threading.Thread(target=create_gui, daemon=True)
    gui_thread.start()

    # 开始监控Wi-Fi连接并关闭代理
    check_wifi_and_disable_proxy(config["wifi_name"])

if __name__ == "__main__":
    main()
