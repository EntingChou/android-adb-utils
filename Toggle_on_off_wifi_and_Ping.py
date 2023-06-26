import time
import os
import sys
import time, os, sys, subprocess
from datetime import date
from datetime import datetime

cmd_toggleOff_wifi = 'adb shell "svc wifi disable"'
cmd_toggleOn_wifi = 'adb shell "svc wifi enable"'
cmd_toogle_wifi = 'adb shell "svc wifi disable"&&adb shell "svc wifi enable"'
cmd_reboot = 'adb reboot'

sn = ''

def get_device_sn():
    global dev_sn
    print("%s - Detecting device serial number..." % datetime.now())
    out_bytes = subprocess.check_output(['adb', 'devices']).decode('utf-8').split('\n')
    if (len(out_bytes)) > 4:
        for device in out_bytes:
            model = subprocess.check_output(['adb', '-s', device,
                                             'shell', 'getprop ro.product.model']).decode('utf-8').rstrip("\n")
            print(datetime.now(), '-', device, model)
        n = input('Please select DUT first.\n')
        dev_sn = out_bytes[int(n)].replace('	device', '')
        model = subprocess.check_output(['adb', '-s', dev_sn,
                                         'shell', 'getprop ro.product.model']).decode('utf-8').rstrip("\n")
        print(datetime.now(), '- Connected', dev_sn, model)
        return dev_sn

    elif out_bytes[int(1)] == '':
        print("%s - Please connecting at least one device or open adb port first." % datetime.now())
    else:
        dev_sn = out_bytes[int(1)].replace('	device', '')
        model = subprocess.check_output(['adb', '-s', dev_sn, 'shell',
                                         'getprop ro.product.model']).decode('utf-8').rstrip("\n")
        print(datetime.now(), '- Connected', dev_sn, model)

def adb(command, dwelltime=180):
    cmd = "adb -s " + dev_sn + " %s" % command
    process = subprocess.Popen(cmd.split(),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    time.sleep(.3)
    out, err = process.communicate(timeout=dwelltime)
    adb_output = out.decode('utf-8').strip()
    adb_error = err.decode('utf-8').strip()
    if "not found" in adb_error:
        raise Exception("adb disconnected!! Please check your device")
    return adb_output

def adb_shell(command, dwelltime=180):
    cmd = "adb -s " + dev_sn + " shell %s" % command
    process = subprocess.Popen(cmd.split(),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    time.sleep(.3)
    out, err = process.communicate(timeout=dwelltime)
    shell_output = out.decode('utf-8').strip()
    shell_error = err.decode('utf-8').strip()
    if "not found" in shell_error:
        raise Exception("adb disconnected!! Please check your device")
    return shell_output

def adb_reboot(boot_stuck=False):
    print("%s - Reboot device" % datetime.now())
    adb("reboot")
    if not boot_stuck:
        print("%s - Wait for device to boot up..." % datetime.now())
        reboot_check()

def reboot_check():
    timeout_start = time.time()
    timeout = 180
    stuck_flag = 1
    while time.time() < timeout_start + timeout:
        adb("wait-for-device")
        complete = adb_shell("getprop sys.boot_completed")
        if complete == "1":
            adb_shell("input keyevent 82")
            print("%s - Boot up successfully" % datetime.now())
            return
        elif time.time() > (timeout_start + (timeout / 2)) and stuck_flag == 1:
            print("%s - Boot up stuck. Reboot again..." % datetime.now())
            adb_reboot(boot_stuck=True)
            stuck_flag = 0
    raise Exception(
        "Device booting process timed out in %d seconds!!" % timeout)

def check_screen_state():
    adb("root")
    print("%s - Check screen state" % datetime.now())
    screen_out = adb_shell("dumpsys display")
    for screen_line in screen_out.split("\n"):
        if "mScreenState" in screen_line:
            screen_state = screen_line.split("=")[1]
            if screen_state != "ON":
                print("%s - Turn screen on" % datetime.now())
                adb_shell("input keyevent KEYCODE_POWER")
            adb_shell("input keyevent 82")
    print("%s - Screen is ON" % datetime.now())

def check_iswifi():
    for s in range(60):
        ssid = adb_shell('dumpsys netstats | grep -E "iface=wlan.*networkId"')
        if ssid == '':
            time.sleep(1)
        elif s == 59:
            raise Exception("Wifi not connected.")
        else:
            print("%s - SSID found." % datetime.now())
            break


if __name__ == "__main__":
    get_device_sn()
    print("%s - Please input cycles." % datetime.now())
    cycle = int(input())
    for i in range(cycle):
        i += 1
        print("=============== cycle " + str(i) + " ===============")
        print("%s - Check device state." % datetime.now())
        check_screen_state()
        adb_reboot()
        reboot_check()
        os.system('adb shell am start -a android.settings.WIFI_SETTINGS')
        print("%s - Open device WIFI_SETTINGS page." % datetime.now())
        time.sleep(5)
        os.system(cmd_toggleOn_wifi)
        print("%s - Turn WiFi on." % datetime.now())
        check_iswifi()
        time.sleep(60)
        response = os.system("adb shell ping -c 3 www.google.com")
        print("%s - Check connected to AP." % datetime.now())
        time.sleep(10)
        os.system(cmd_toggleOff_wifi)
        print("%s - Turn WiFi off." % datetime.now())
        time.sleep(10)

        if response != 0:
            raise Exception("Test failed.")
        else:
            print("=============== cycle " + str(i) + " Pass ===============")
            print("%s - Passed." % datetime.now())

