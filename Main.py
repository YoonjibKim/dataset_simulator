import multiprocessing
import os
import time
from datetime import datetime

from multiprocessing import Process
from AttackConfig import AttackConfig
from Authentication import AuthenticationPhase
from DataSave import DataSave
from DatasetManager import DatasetManager
from Installation import InstallationPhase
from Measurement import Measurement
from Network import V2G_Network


def multi_process_work(param_cs_id, param_conn, param_charging_schedule, param_attack_config, param_return_value_dict,
                       param_return_pid_dict, param_sim_flag):
    param_sim_flag.wait()

    param_return_pid_dict[param_cs_id] = os.getpid()
    authentication_phase = AuthenticationPhase(param_cs_id, param_conn, param_charging_schedule, param_attack_config)
    authentication_phase.running_cs()

    result_list = []
    authentication_phase.running_evs()
    ev_auth_result_list = authentication_phase.get_results()
    result_list.append(ev_auth_result_list)
    authentication_phase.release_cs()
    param_return_value_dict[param_cs_id] = result_list


def parameter_setting():
    # ['no attack', 'correct ID', 'wrong ID', 'wrong ev timestamp', 'wrong cs timestamp']
    scenario_index = 1
    _random_cs_attack_on_off = True
    _guassian_heuristic_on_off = True

    start_date = datetime(year=2019, month=9, day=5)
    end_date = datetime(year=2020, month=9, day=6)
    _attack_ev_random_count_min = 10
    _attack_ev_random_count_max = 10
    _max_profiling_count = 3
    scenario = AttackConfig.attack_scenario_list(scenario_index)
    ret_param_list = [scenario, _attack_ev_random_count_min, _attack_ev_random_count_max, start_date, end_date,
                      _random_cs_attack_on_off, _guassian_heuristic_on_off, _max_profiling_count]
    return ret_param_list


if __name__ == "__main__":
    param_list = parameter_setting()
    attack_sim_sec = 0.0
    start_sim_date = None
    end_sim_date = None
    attack_config = AttackConfig(param_list[0], param_list[1], param_list[2])

    if attack_config.get_scenario() == AttackConfig.attack_scenario_list(0):
        try:
            fd = open('./input/sim_sec_attack.txt', 'r')
        except IOError:
            print('Could not open the input file!')
            exit(-1)
        else:
            read_data = fd.readline()
            read_data_list = read_data.split()
            attack_sim_sec = float(read_data_list[0])
            start_sim_date = datetime(year=int(read_data_list[1]), month=int(read_data_list[2]),
                                      day=int(read_data_list[3]))
            end_sim_date = datetime(year=int(read_data_list[4]), month=int(read_data_list[5]),
                                    day=int(read_data_list[6]))
            fd.close()
    else:
        start_sim_date = param_list[3]
        end_sim_date = param_list[4]

    dataset = DatasetManager(start_sim_date.year, start_sim_date.month, start_sim_date.day,
                             end_sim_date.year, end_sim_date.month, end_sim_date.day)
    random_cs_attack_on_off = param_list[5]
    guassian_heuristic_on_off = param_list[6]
    profiling_count = param_list[7]

    unique_cs_id_list = dataset.get_unique_cs_id_list()
    unique_normal_ev_id_list = dataset.get_unique_normal_ev_id_list()
    ev_cs_session_id_list = dataset.extract_session_cs_id()

    read_pipe, write_pipe = os.pipe()
    if os.fork() == 0:  # child process
        os.close(write_pipe)
        rd = os.fdopen(read_pipe, "r")
        msg_fro_gs = rd.read()
        temp = msg_fro_gs.split()
        port = int(temp[0])
        gs_pid = int(temp[1])

        # installation
        installation_phase = InstallationPhase(unique_cs_id_list, port, unique_normal_ev_id_list, ev_cs_session_id_list)
        installation_phase.install_css()
        sec_delta_list, last_delta = dataset.get_normal_auth_time_delta(attack_sim_sec)
        installation_phase.install_normal_evs(sec_delta_list, attack_config.get_scenario())
        installation_phase.release_css()
        installation_phase.release_evs()
        scheduled_charging_list = installation_phase.get_installed_normal_ev_cs_list()

        manager = multiprocessing.Manager()
        return_result_dict = manager.dict()
        return_pid_dict = manager.dict()
        print('-------------------------------------- Measuring samples --------------------------------------')
        measurement = Measurement(return_pid_dict)

        # authentication
        print('----------------------------------- EV Authentication Result -----------------------------------')

        if guassian_heuristic_on_off:
            guassian_attack_count_dict, mean, std = attack_config.get_normal_distribution(scheduled_charging_list)
            DataSave.save_mean_std(mean, std)
        else:
            guassian_attack_count_dict = 0

        ev_count_dict = {}
        charging_schedule_list = []
        charging_schedule_count_list = []
        for cs_id, conn in installation_phase.get_cs_connection_dict().items():
            charging_schedule = installation_phase.get_scheduled_charging_of_normal_evs(cs_id, scheduled_charging_list,
                                                                                        attack_config.get_scenario())
            charging_schedule, ev_count_dict = attack_config.get_attack_scenario(charging_schedule,
                                                                                 random_cs_attack_on_off,
                                                                                 guassian_heuristic_on_off,
                                                                                 guassian_attack_count_dict)
            charging_schedule_count_list.append([cs_id, len(charging_schedule)])
            charging_schedule_list.append(charging_schedule)

        charging_schedule_count_list.sort(key=lambda a: a[1], reverse=True)
        profiling_target_cs_id_list = []
        for count, target_cs_id in enumerate(charging_schedule_count_list):
            if count == profiling_count:
                break
            else:
                profiling_target_cs_id_list.append(target_cs_id[0])

        print('-------------------------------- CS ID: [Normal EVs, Attack EVs] --------------------------------')
        print(ev_count_dict)
        cs_process_list = []
        sim_flag = multiprocessing.Manager().Event()
        index = 0
        start_sim_time = datetime.now()
        profiling_pid_list = []
        for cs_id, conn in installation_phase.get_cs_connection_dict().items():
            cs_process = Process(target=multi_process_work,
                                 args=(cs_id, conn, charging_schedule_list[index], attack_config, return_result_dict,
                                       return_pid_dict, sim_flag,))
            cs_process.start()

            if cs_id in profiling_target_cs_id_list:
                measurement.start_perf_stat(cs_process.pid, 'cs_stat')
                measurement.start_perf_top(cs_process.pid, 'cs_top', 'instructions')
                measurement.start_perf_top(cs_process.pid, 'cs_top', 'branch')
                measurement.start_perf_top(cs_process.pid, 'cs_top', 'cycles')
                measurement.start_perf_record(cs_process.pid, 'cs_record')
                profiling_pid_list.append(cs_process.pid)

            if index == len(installation_phase.get_cs_connection_dict()) - 1:
                measurement.start_perf_stat(gs_pid, 'gs_stat')
                measurement.start_perf_top(gs_pid, 'gs_top', 'instructions')
                measurement.start_perf_top(gs_pid, 'gs_top', 'branch')
                measurement.start_perf_top(gs_pid, 'gs_top', 'cycles')
                measurement.start_perf_record(gs_pid, 'gs_record')
                profiling_pid_list.append(gs_pid)
                sim_flag.set()
                print('Measuring Start!')

            index += 1
            cs_process_list.append(cs_process)

        for cs_process in cs_process_list:
            cs_process.join()

        Measurement.kill_perf()

        for conn in installation_phase.get_cs_connection_dict().values():
            V2G_Network.end_cs_gs_connection(conn)
        V2G_Network.end_gs_server(port)

        time.sleep(last_delta)
        end_sim_time = datetime.now()
        sim_time_delta = end_sim_time - start_sim_time

        record_list = []
        for key, values in return_result_dict.items():
            print('--------------------------------------- CS ID:', key + ' ---------------------------------------')
            print('Round\tEV ID\tCS ID\tTimestamp\tAuthentication\tInstallation\tType')
            for index, value in enumerate(values):
                print(str(index + 1), value)

        DataSave.save_ev_authentication_result(return_result_dict, return_pid_dict.items())
        DataSave.save_all_data(attack_config.get_scenario(), charging_schedule_list, ev_count_dict,
                               guassian_attack_count_dict, random_cs_attack_on_off, guassian_heuristic_on_off)
        DataSave.save_sim_time(sim_time_delta.total_seconds(), attack_config.get_scenario(), start_sim_date,
                               end_sim_date)

        print('-------------------------------------- Consumed Simulation Time --------------------------------------')
        print(sim_time_delta)
        measurement.convert_perf_record_to_file()
        print('\nEnd EV CS')
        exit(0)
    else:  # parent process
        os.close(read_pipe)
        wd = os.fdopen(write_pipe, "w")
        port = V2G_Network.get_open_port()
        wd.write(str(port) + ' ' + str(os.getpid()))
        wd.close()
        V2G_Network().grid_server(port)
        os.wait()
        print('End Server')

    print('End Program')
