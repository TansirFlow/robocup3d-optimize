import configparser
import math
import os
import re
import socket
import subprocess
import threading
import time

host = '127.0.0.1'
port = int(os.environ.get('SPARK_SERVERPORT', 3200))
host_username = "desktop"
host_password = "20030713"


def get_config(config_file_name):
    global host, port, host_username, host_password
    config = configparser.ConfigParser()
    config.read(config_file_name)
    host = config.get("optimize_server_param", "host")
    port = config.getint("optimize_server_param", "port")
    host_username = config.get("optimize_server_param", "username")
    host_password = config.get("optimize_server_param", "password")


agent_position_list = [
    [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0],
    [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]
]
ball_pos = [0, 0, 0]
ball_speed = 0
last_speed_update_time = 0
game_time = 0
server_running = False


def run_rcssserver3d():
    kill_rcssserver3d()
    command = "nohup rcssserver3d > /dev/null 2>&1 &"
    subprocess.Popen(command, shell=True)
    time.sleep(0.5)
    global server_running
    server_running = True


def kill_rcssserver3d():
    os.system("pkill rcsss -9")
    os.system("pkill java -9")
    global server_running
    server_running = False


def prepare_msg(msg):
    msg_len = len(msg)
    prefix = msg_len.to_bytes(4, byteorder='big')
    return prefix + msg.encode()


def set_time(t):
    # print(f"尝试连接到{host}:{port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((host, port))
    except ConnectionRefusedError:
        # print(f"无法连接到{host}:{port}")
        return False

    # print(f"设置时间为 {t}")
    msg = f"(time {t})"
    msg = prepare_msg(msg)
    sock.sendall(msg)
    response = sock.recv(1024)
    # print(response[4:])

    sock.close()
    return True


def play_on():
    # print(f"尝试连接到{host}:{port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((host, port))
    except ConnectionRefusedError:
        # print(f"无法连接到{host}:{port}")
        return False

    # print("切换PlayOn模式")
    msg = prepare_msg("(playMode PlayOn)")
    sock.sendall(msg)
    response = sock.recv(1024)
    # print(response[4:])

    sock.close()
    return True


def kick_off():
    # print(f"尝试连接到{host}:{port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((host, port))
    except ConnectionRefusedError:
        # print(f"无法连接到{host}:{port}")
        return False

    # print("切换KickOff_Left模式")
    msg = prepare_msg("(playMode KickOff_Left)")
    sock.sendall(msg)
    response = sock.recv(1024)
    # print(response[4:])

    sock.close()
    return True


def before_kick_off():
    # print(f"尝试连接到{host}:{port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((host, port))
    except ConnectionRefusedError:
        # print(f"无法连接到{host}:{port}")
        return False

    # print("切换BeforeKickOff模式")
    msg = prepare_msg("(playMode BeforeKickOff)")
    sock.sendall(msg)
    response = sock.recv(1024)
    # print(response[4:])

    sock.close()
    return True


def move_player(unum, x, y, side='Left'):
    # TODO:如果球员在场左边，不需要添加side参数,否则写Right，注意首字母大写
    # print(f"尝试连接到{host}:{port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((host, port))
    except ConnectionRefusedError:
        # print(f"无法连接到{host}:{port}")
        return False

    # print(f"移动球员{unum}到({x},{y})")
    msg = f"(agent (unum {unum}) (team {side}) (pos {x} {y} 0.25))"
    msg = prepare_msg(msg)
    sock.sendall(msg)
    response = sock.recv(1024)
    # print(response[4:])

    sock.close()
    return True


def move_ball(x, y):
    # print(f"尝试连接到{host}:{port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((host, port))
    except ConnectionRefusedError:
        # print(f"无法连接到{host}:{port}")
        return False

    # print(f"移动足球到({x},{y})")
    msg = f"(ball (pos {x} {y} 0)(vel 0 0 0))"
    msg = prepare_msg(msg)
    sock.sendall(msg)
    response = sock.recv(1024)
    # print(response[4:])
    global ball_speed
    ball_speed = 0

    sock.close()
    return True


def run_linux_command(command, server=host, username=host_username, password=host_password):
    import paramiko
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=server, username=username, password=password)
    ssh.exec_command(command)
    ssh.close()


def refresh_server_info():
    global server_running, last_speed_update_time, ball_speed
    global ball_pos, game_time, agent_position_list

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((host, port))
        # print(f"成功连接到{host}:{port}")
        while True:
            server_running = True
            msg = prepare_msg("(reqfullstate)")
            sock.sendall(msg)
            response = sock.recv(9999)
            receive_msg = response[4:]
            receive_msg = receive_msg.decode('utf-8')
            pattern = r"\(SLT ([\d\.\s-]+)\)\(nd StaticMesh \(setVisible 1\) \(load models/soccerball.obj\)"
            result = re.search(pattern, receive_msg)
            if result:
                numbers = result.group(1).split()
                numbers = numbers[12:-1]
                x = round(float(numbers[0]), 2)
                y = round(float(numbers[1]), 2)
                z = round(float(numbers[2]), 2)
                if math.sqrt((x - ball_pos[0]) ** 2 + (y - ball_pos[1]) ** 2 + (z - ball_pos[2]) ** 2) > 0.01:
                    # print(f"x={x},y={y},z={z}")
                    delta_time = game_time - last_speed_update_time
                    delta_distance = math.sqrt((x - ball_pos[0]) ** 2 + (y - ball_pos[1]) ** 2 + (z - ball_pos[2]) ** 2)
                    if delta_time > 0.001:
                        ball_speed = delta_distance / delta_time
                    ball_pos = [x, y, z]
                    last_speed_update_time = game_time

            pattern = r"\(time ([^\)]+)\)"
            match = re.search(pattern, receive_msg)
            if match:
                time = round(float(match.group(1)), 2)
                if game_time != time:
                    # print(f"time={time}")
                    game_time = time

            pattern = r"\(nd TRF \(SLT ([\d\.\s-]+)\)\(nd StaticMesh \(setVisible 1\) \(load models/rthigh.obj\) \(sSc 0.07 0.07 0.07\)\(resetMaterials matNum(\d+) matLeft naowhite\)\)\)"
            matches = re.findall(pattern, receive_msg)

            if matches:
                for match in matches:
                    all_numbers = []
                    numbers = match[0].strip().split(' ')
                    all_numbers.extend(numbers)
                    pos = all_numbers[12:-1]
                    x = round(float(pos[0]), 2)
                    y = round(float(pos[1]), 2)
                    z = round(float(pos[2]), 2)
                    unum = int(match[1])
                    agent_position_list[unum - 1] = [x, y, z]
                    # print(f"{unum}号球员坐标({x},{y},{z})")
            response = ''
    except ConnectionRefusedError:
        # print(f"无法连接到{host}:{port}")
        server_running = False
    except ConnectionResetError:
        server_running = False
    except BrokenPipeError:
        kill_rcssserver3d()
        server_running = False
    except UnicodeDecodeError:
        kill_rcssserver3d()
        server_running = False
    sock.close()


def get_ball_speed():
    global ball_speed
    return ball_speed


def get_ball_pos():
    global ball_pos
    return ball_pos


def get_agent_pos(unum):
    if unum < 1 or unum > 11:
        return None
    else:
        return agent_position_list[unum - 1]


def get_game_time():
    global game_time
    return game_time


def is_server_running():
    return server_running


def start_get_server_info():
    def insistence_refresh_server_info():
        while True:
            refresh_server_info()

    t = threading.Thread(target=insistence_refresh_server_info)
    t.start()

