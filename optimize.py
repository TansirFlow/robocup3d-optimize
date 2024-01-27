import math
import os
import subprocess
import time
import cma
import numpy as np
import socket
import configparser

import SimSparkControl

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
    ball_start_pos_temp = config.get("run_param", "ballStartPos").split(',')
    run_param["ballStartPos"] = [float(ball_start_pos_temp[0]), float(ball_start_pos_temp[1])]
    agent_start_pos_temp = config.get("run_param", "agentStartPos").split(',')
    run_param["agentStartPos"] = [float(agent_start_pos_temp[0]), float(agent_start_pos_temp[1])]
    run_param["successKickDistance"] = config.getfloat("run_param", "successKickDistance")
    run_param["minKickFailedTime"] = config.getfloat("run_param", "minKickFailedTime")
    kick_target_pos_temp = config.get("run_param", "kickTargetPos").split(',')
    run_param["kickTargetPos"] = [float(kick_target_pos_temp[0]), float(kick_target_pos_temp[1])]
    run_param["kickTargetDistance"] = config.getfloat("run_param", "kickTargetDistance")

    optimize_server_param["host"] = config.get("optimize_server_param", "host")
    optimize_server_param["port"] = config.getint("optimize_server_param", "port")
    optimize_server_param["username"] = config.get("optimize_server_param", "username")
    optimize_server_param["password"] = config.get("optimize_server_param", "password")

    backup_server_param["host"] = config.get("backup_server_param", "password")
    backup_server_param["port"] = config.getint("backup_server_param", "port")


def save_to_localhost(params, score, avg_dis, avg_t, avg_dev):  # 优秀参数存到本地
    factory = run_param["factory"]
    file_name = factory + "_perfect_params.txt"
    file_object = open(file_name, "a")
    text = "################################################################\n"
    for i in params:
        text = text + str(i) + "\n"
    text = (text + "score:" + str(score) + "avg_dis:" + str(avg_dis) + "avg_t:" + str(avg_t) + "avg_dev:" + str(avg_dev)
            + "\n################################################################\n\n\n")
    file_object.write(text)
    file_object.close()


def save_perfect_params(params, score, avg_dis, avg_t, avg_dev):
    save_to_localhost(params, score, avg_dis, avg_t, avg_dev)
    # send_to_cloud_server(params, score, avg_dis, avg_t, avg_dev)


def train_kick():
    def run_agent():
        factory = run_param["factory"]
        player_id = run_param["playerId"]
        decision_maker = run_param["decisionMaker"]
        jar_file_name = run_param["jarFileName"]
        run_agent_command = "java -jar " + jar_file_name + " --playerid=" + str(
            player_id) + " --factory=" + factory + " --teamname=WeWantKick15m --decisionmaker=" + decision_maker
        subprocess.Popen(run_agent_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def before_kick():
        ball_start_pos = run_param["ballStartPos"]
        agent_start_pos = run_param["agentStartPos"]

        SimSparkControl.play_on()
        time.sleep(0.2)
        SimSparkControl.move_ball(ball_start_pos[0], ball_start_pos[1])
        SimSparkControl.move_player(agent_start_pos[0], agent_start_pos[1])
        SimSparkControl.set_time(0)

    def get_kick_distance():
        ball_start_pos = run_param["ballStartPos"]
        ball_pos = SimSparkControl.get_ball_pos()
        dis = math.sqrt((ball_start_pos[0] - ball_pos[0]) ** 2 + (ball_start_pos[1] - ball_pos[1]) ** 2)
        return dis

    def end_kick():
        SimSparkControl.before_kick_off()

    if not SimSparkControl.is_server_running():
        SimSparkControl.run_rcssserver3d()
        time.sleep(1)

    run_agent()
    before_kick()

    success_kick_distance = run_param["successKickDistance"]
    min_kick_failed_time = run_param["minKickFailedTime"]
    start_time = time.time()
    while 1:
        time.sleep(0.1)
        kick_distance = get_kick_distance()
        game_time_consume = SimSparkControl.get_game_time()
        ball_speed = SimSparkControl.get_ball_speed()
        ball_pos = SimSparkControl.get_ball_pos()
        if not SimSparkControl.is_server_running():  # server意外退出的应对方案
            SimSparkControl.kill_rcssserver3d()
            SimSparkControl.run_rcssserver3d()
            run_agent()
            before_kick()
            start_time = time.time()

        if time.time() - start_time > 6:  # 程序卡死
            SimSparkControl.kill_rcssserver3d()
            SimSparkControl.run_rcssserver3d()
            run_agent()
            before_kick()
            start_time = time.time()

        if game_time_consume > min_kick_failed_time:  # 参数太差，踢不了球
            end_kick()  # 结束此次踢球，但不终止server
            return {"status": False}

        if ball_speed < 0.001 and kick_distance > success_kick_distance:  # 踢球成功
            end_kick()  # 结束此次踢球，但不终止server
            ball_start_pos = run_param["ballStartPos"]
            kick_target_pos = run_param["kickTargetPos"]
            distance = kick_distance
            time_consume = game_time_consume

            vector1 = [ball_pos[0] - ball_start_pos[0], ball_pos[1] - ball_start_pos[1], 0]
            vector2 = [kick_target_pos[0] - ball_start_pos[0], kick_target_pos[1] - ball_start_pos[1], 0]
            # 计算点积
            dot_product = sum(x * y for x, y in zip(vector1, vector2))
            # 计算向量模
            magnitude1 = math.sqrt(sum(x ** 2 for x in vector1))
            magnitude2 = math.sqrt(sum(x ** 2 for x in vector2))
            # 计算余弦相似度和夹角
            cosine_similarity = dot_product / (magnitude1 * magnitude2)
            angle = math.degrees(math.acos(cosine_similarity))
            deviation = angle

            return {"status": True, "distance": distance, "time": time_consume, "deviation": deviation}


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
    score_list = []
    kick_target_distance = run_param["kickTargetDistance"]
    for i in range(len(distance_list)):
        dis_score = 100 * distance_list[i] / kick_target_distance
        time_score = 100 - time_list[i]
        deviation_score = 100 - deviation_list[i]
        single_score = dis_score * 0.6 + time_score * 0.2 + deviation_score * 0.2
        score_list.append(single_score)
    avg_score = sum(score_list) / len(score_list)
    return avg_score


def fitness(params):
    runtimes_per_parameter = run_param["runtimesPerParameter"]
    accept_score = run_param["acceptScore"]
    write_temp_parameter_file(params)

    SimSparkControl.run_rcssserver3d()
    distance_list = []
    time_list = []
    deviation_list = []
    for i in range(runtimes_per_parameter):
        result = train_kick()
        success = result["status"]
        if success:
            dis = result["distance"]
            t = result["time"]
            dev = result["deviation"]
            distance_list.append(dis)
            time_list.append(t)
            deviation_list.append(dev)
    score = estimate_score(distance_list, time_list, deviation_list)
    if score >= accept_score:
        save_perfect_params(params, score, sum(distance_list) / len(distance_list), sum(time_list) / len(time_list),
                            sum(deviation_list) / len(deviation_list))
    print("score", score)
    SimSparkControl.kill_rcssserver3d()
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
