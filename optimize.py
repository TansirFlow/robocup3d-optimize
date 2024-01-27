import os
import subprocess
import time
import cma
import numpy as np
import socket
import configparser

import SimSparkControl

factory = "Nao"  # 机器人类型
runtimes = 30  # 每个参数跑几次
playerid = 8  # 上几号球员
decisionmaker = "Training"  # decisionmaker类名
jarName = "magmaagent.jar"  # 导出的jar包名
popsize = 50  # 种群规模
cloud_server_ip = ""  # 远程服务器IP
cloud_server_port = 5678  # 远程服务器端口
perfect_params_score_threshold = 90  # 得分大于多少的参数认为是优秀参数

cma_param = {}
run_param = {}
optimize_server_param = {}
backup_server_param = {}


def get_config(config_file_name):
    config = configparser.ConfigParser()
    config.read(config_file_name)

    cma_param["sigma0"] = config.getfloat("cma_param", "sigma0")
    cma_param["initParameterFileName"] = config.get("cma_param", "initParameterFileName")

    run_param["factory"] = config.get("run_param", "factory")
    run_param["playerId"] = config.getint("run_param", "playerId")
    run_param["decisionMaker"] = config.get("run_param", "decisionMaker")
    run_param["jarFileName"] = config.get("run_param", "jarFileName")
    run_param["acceptScore"] = config.getfloat("run_param", "acceptScore")
    run_param["runtimesPerParameter"] = config.getint("run_param", "runtimesPerParameter")
    run_param["tempParameterFileName"] = config.getint("run_param", "tempParameterFileName")

    optimize_server_param["host"] = config.get("optimize_server_param", "host")
    optimize_server_param["port"] = config.getint("optimize_server_param", "port")
    optimize_server_param["username"] = config.get("optimize_server_param", "username")
    optimize_server_param["password"] = config.get("optimize_server_param", "password")

    backup_server_param["host"] = config.get("backup_server_param", "password")
    backup_server_param["port"] = config.getint("backup_server_param", "port")


def save_to_localhost(params, score):  # 优秀参数存到本地
    file_name = factory + "_perfect_params.txt"
    file_object = open(file_name, "a")
    text = "################################################################\n"
    for i in params:
        text = text + str(i) + "\n"
    text = text + "score:" + str(score) + "\n################################################################\n\n\n"
    file_object.write(text)
    file_object.close()


def send_to_cloud_server(params, score):  # 优秀参数发送云端
    global cloud_server_ip, cloud_server_port, factory
    try:
        print("test")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr = (cloud_server_ip, cloud_server_port)
        s.connect(addr)
        text = "DREAMWING3D&&&&&&" + factory + "&&&&&&"
        for i in params:
            text = text + str(i) + "\n"
        text = text + "score:" + str(score)
        s.send(text.encode('utf-8'))
        s.close()
        print("send successful")
    finally:
        print("test2")
        return


def save_perfect_params(params, score):
    save_to_localhost(params, score)
    send_to_cloud_server(params, score)


def train_kick():
    SimSparkControl.run_rcssserver3d()
    time.sleep(1)
    start_agent_command = "java -jar " + jarName + " --playerid=" + str(
        playerid) + " --factory=" + factory + " --teamname=WeWantKick15m --decisionmaker=" + decisionmaker
    subprocess.Popen(start_agent_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    start_time = time.time()
    while 1:
        time.sleep(0.1)
        if time.time() - start_time > 6:
            os.system("pkill rcsss -9")
            return -1
        if os.path.exists("score.txt"):
            time.sleep(0.2)
            os.system("pkill rcsss -9")
            file_object = open("score.txt", "r")
            text = file_object.readlines()
            file_object.close()
            os.remove("score.txt")
            return calculate_score(text)


def write_temp_parameter_file(params):
    temp_parameter_file_name = run_param["tempParameterFileName"]
    if os.path.exists(temp_parameter_file_name):
        os.remove(temp_parameter_file_name)
    time.sleep(0.5)
    file_object = open(temp_parameter_file_name, "w+")
    text = ""
    for i in params:
        text = text + str(i) + "\n"
    file_object.write(text)
    file_object.close()


def estimate_score(distance_list, time_list, deviation_list):
    score = 80
    return score


def fitness(params):
    runtimes_per_parameter = run_param["runtimesPerParameter"]
    accept_score = run_param["acceptScore"]
    write_temp_parameter_file(params)

    SimSparkControl.run_rcssserver3d()
    distance_list = []
    time_list = []
    deviation_list = []
    for i in range(runtimes_per_parameter):
        success, dis, t, dev = train_kick()
        if success:
            distance_list.append(dis)
            time_list.append(t)
            deviation_list.append(dev)
    score = estimate_score(distance_list, time_list, deviation_list)
    if score >= accept_score:
        save_perfect_params(params, score)
    print("score", score)
    return -score


def get_initial_parameters():
    file_object = open(cma_param["initParameterFileName"])
    lines = file_object.readlines()
    params = []
    for line in lines:
        params.append(float(line))
    initial_parameters = np.array(params)
    return initial_parameters


def start_optimization():
    SimSparkControl.kill_rcssserver3d()
    initial_parameters = get_initial_parameters()
    sigma0 = cma_param["sigma0"]
    best_parameter, best_score = cma.fmin2(fitness, initial_parameters, sigma0, options={"verbose": True, })
    print("最佳参数向量：", best_parameter)
    print("最佳适应度值：", -best_score)


if __name__ == "__main__":
    get_config("config.ini")
    start_optimization()
