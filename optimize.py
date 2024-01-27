import os
import subprocess
import time
import cma
import numpy as np
import socket
import configparser

factory = "Nao"  # 机器人类型
runtimes = 30  # 每个参数跑几次
playerid = 8  # 上几号球员
decisionmaker = "Training"  # decisionmaker类名
jarName = "magmaagent.jar"  # 导出的jar包名
popsize = 50  # 种群规模
cloud_server_ip = ""  # 远程服务器IP
cloud_server_port = 5678  # 远程服务器端口
perfect_params_score_threshold = 90  # 得分大于多少的参数认为是优秀参数

config_data = {}


def get_optimize_config(configFileName):
    config = configparser.ConfigParser()
    config.read(configFileName)
    config_data["factory"] = config.get("run_param", "factory")
    config_data["playerId"] = config.getint("run_param", "playerId")
    config_data["decisionMaker"] = config.get("run_param", "decisionMaker")
    config_data["jarFileName"] = config.get("run_param", "jarFileName")
    config_data["accept_score"] = config.getfloat("run_param", "accept_score")
    config_data["runtimes"] = config.getint("run_param", "runtimes")



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


def calculate_score(text):
    score = float(text[0])
    print(factory, " kicked", score, "meters")
    return score


def train_kick():
    command1 = "rcssserver3d"
    subprocess.Popen(command1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(1)
    start_command = "java -jar " + jarName + " --playerid=" + str(
        playerid) + " --factory=" + factory + " --teamname=WeWantKick15m --decisionmaker=" + decisionmaker
    subprocess.Popen(start_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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


def write_parms2file(params):
    if os.path.exists("config.txt"):
        os.remove("config.txt")
    time.sleep(0.5)
    file_object = open("config.txt", "w+")
    text = ""
    for i in params:
        text = text + str(i) + "\n"
    file_object.write(text)
    file_object.close()


def fitness(params):
    # x为待优化参数向量，需要传入到控制器中进行测试，返回测试结果用于评估适应度
    # 这里的测试内容可以根据具体情况进行修改和扩展
    write_parms2file(params)
    global runtimes
    fitness_value = 0.0
    for i in range(runtimes):
        fitness_value = fitness_value + (100.0 * train_kick() / 15.0) * 0.6 + (
                    100 * 35.0 / (params[0] + params[1] + params[2])) * 0.4
    fitness_value = fitness_value / runtimes
    global perfect_params_score_threshold
    if fitness_value >= perfect_params_score_threshold:
        save_perfect_params(params, fitness_value)
    print("average score", fitness_value)
    return -fitness_value  # cma-es最小化目标函数，因此将测试结果取负


def get_initial_parameters():
    file_object = open("initial_parameters.txt", "r")
    lines = file_object.readlines()
    params = []
    for line in lines:
        params.append(float(line))
    initial_parameters = np.array(params)
    return initial_parameters


def optimization_controler():
    initial_parameters = get_initial_parameters()
    global factory, runtimes, playerid, decisionmaker, jarName, popsize
    os.system("pkill rcsss -9")
    time.sleep(1)
    best = cma.fmin(fitness, initial_parameters, 0.3, options={"popsize": popsize, "verbose": True, })
    print("最佳参数向量：", best[0])
    print("最佳适应度值：", -best[1])


if __name__ == "__main__":
    optimization_controler()
