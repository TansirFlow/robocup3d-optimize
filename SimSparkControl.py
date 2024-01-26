import os
import socket
import subprocess

host = '192.168.128.130'
port = int(os.environ.get('SPARK_SERVERPORT', 3200))
host_username = "desktop"
host_password = "20030713"


def run_rcssserver3d():
    command = "nohup rcssserver3d > /dev/null 2>&1 &"
    subprocess.Popen(command, shell=True)


def kill_rcssserver3d():
    os.system("pkill rcsss -9")


def prepare_msg(msg):
    msg_len = len(msg)
    prefix = msg_len.to_bytes(4, byteorder='big')
    return prefix + msg.encode()


def set_time(t):
    print(f"尝试连接到{host}:{port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((host, port))
    except ConnectionRefusedError:
        print(f"无法连接到{host}:{port}")
        return False

    print(f"设置时间为 {t}")
    msg = f"(time {t})"
    msg = prepare_msg(msg)
    sock.sendall(msg)
    response = sock.recv(1024)
    print(response[4:])

    sock.close()
    return True


def play_on():
    print(f"尝试连接到{host}:{port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((host, port))
    except ConnectionRefusedError:
        print(f"无法连接到{host}:{port}")
        return False

    print("切换PlayOn模式")
    msg = prepare_msg("(playMode PlayOn)")
    sock.sendall(msg)
    response = sock.recv(1024)
    print(response[4:])

    sock.close()
    return True


def kick_off():
    print(f"尝试连接到{host}:{port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((host, port))
    except ConnectionRefusedError:
        print(f"无法连接到{host}:{port}")
        return False

    print("切换KickOff_Left模式")
    msg = prepare_msg("(playMode KickOff_Left)")
    sock.sendall(msg)
    response = sock.recv(1024)
    print(response[4:])

    sock.close()
    return True


def before_kick_off():
    print(f"尝试连接到{host}:{port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((host, port))
    except ConnectionRefusedError:
        print(f"无法连接到{host}:{port}")
        return False

    print("切换BeforeKickOff模式")
    msg = prepare_msg("(playMode BeforeKickOff)")
    sock.sendall(msg)
    response = sock.recv(1024)
    print(response[4:])

    sock.close()
    return True


def move_player(unum, x, y, side='Left'):
    # TODO:如果球员在场左边，不需要添加side参数,否则写Right，注意首字母大写
    print(f"尝试连接到{host}:{port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((host, port))
    except ConnectionRefusedError:
        print(f"无法连接到{host}:{port}")
        return False

    print(f"移动球员{unum}到({x},{y})")
    msg = f"(agent (unum {unum}) (team {side}) (pos {x} {y} 0.3))"
    msg = prepare_msg(msg)
    sock.sendall(msg)
    response = sock.recv(1024)
    print(response[4:])

    sock.close()
    return True


def move_ball(x, y):
    print(f"尝试连接到{host}:{port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((host, port))
    except ConnectionRefusedError:
        print(f"无法连接到{host}:{port}")
        return False

    print(f"移动足球到({x},{y})")
    msg = f"(ball (pos {x} {y} 0)(vel 0 0 0))"
    msg = prepare_msg(msg)
    sock.sendall(msg)
    response = sock.recv(1024)
    print(response[4:])

    sock.close()
    return True


def run_linux_command(command, server=host, username=host_username, password=host_password):
    import paramiko
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=server, username=username, password=password)
    ssh.exec_command(command)
    ssh.close()
