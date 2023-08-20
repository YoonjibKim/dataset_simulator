import threading
import time

from AttackConfig import AttackConfig
from Network import V2G_Network
from DataSave import DataSave

global_normal_ev_total_count = 0
global_ev_inst_implement_count = 0
global_ev_to_cs_inst_msg = []
global_cs_to_ev_installation_msg = []
global_cs_inst_implement_count = 0
global_cs_gs_connection_dict = {}
global_installed_normal_ev_cs_list = []
global_thread_sync = threading.Lock()


def multi_thread_cs_installation(param_port, param_cs_id):
    global global_normal_ev_total_count
    global global_ev_inst_implement_count
    global global_ev_to_cs_inst_msg
    global global_cs_to_ev_installation_msg
    global global_cs_inst_implement_count
    global global_cs_gs_connection_dict
    global global_thread_sync

    conn, cs_id, is_cs_installed_ok = V2G_Network.installing_cs(param_port, param_cs_id)

    if is_cs_installed_ok:
        while global_ev_inst_implement_count < global_normal_ev_total_count:
            time.sleep(0.1)

        global_thread_sync.acquire()
        for msg in global_ev_to_cs_inst_msg:
            if msg[1] == param_cs_id:
                temp_ev_id = msg[0]
                temp_cs_id = msg[1]
                temp_sleep_sec = msg[2]

                is_auth_ok, hex_ev_id, hex_key, ev_id, _cs_id = V2G_Network.installing_ev(conn, temp_ev_id, temp_cs_id)
                global_cs_to_ev_installation_msg.append([is_auth_ok, hex_ev_id, hex_key, ev_id, _cs_id, temp_sleep_sec])
        global_cs_gs_connection_dict[cs_id] = conn
        print(cs_id + ' has been installed.')
        DataSave.save_cs_installation_result(cs_id)
        global_thread_sync.release()
        global_cs_inst_implement_count += 1
    else:
        global_cs_inst_implement_count -= 1
        print(cs_id + ' has not been installed.')
        conn.close()

    return 0


def multi_thread_ev_installation(param_index, param_ev_cs_session_id_list, param_unique_cs_count, param_sec_delta,
                                 param_scenario):
    global global_ev_inst_implement_count
    global global_cs_inst_implement_count
    global global_cs_to_ev_installation_msg
    global global_installed_normal_ev_cs_list
    global global_ev_to_cs_inst_msg

    ev_id = param_ev_cs_session_id_list[param_index][0]
    cs_id = param_ev_cs_session_id_list[param_index][1]
    sleep_sec = 0.0
    if param_scenario == AttackConfig.attack_scenario_list(0):
        sleep_sec = param_sec_delta

    global_ev_to_cs_inst_msg.append([ev_id, cs_id, sleep_sec])
    global_ev_inst_implement_count += 1

    while global_cs_inst_implement_count < param_unique_cs_count:
        time.sleep(0.1)

    if global_cs_to_ev_installation_msg[param_index][0]:
        _ev_id = global_cs_to_ev_installation_msg[param_index][3]
        _cs_id = global_cs_to_ev_installation_msg[param_index][4]
        hex_ev_id = global_cs_to_ev_installation_msg[param_index][1]
        hex_key = global_cs_to_ev_installation_msg[param_index][2]
        temp_sleep_sec = global_cs_to_ev_installation_msg[param_index][5]

        installation_flag = True
        global_installed_normal_ev_cs_list.append([_ev_id, _cs_id, hex_ev_id, hex_key, installation_flag, 'normal',
                                                   temp_sleep_sec])
        print(str(param_index) + ': ' + _ev_id + ' at ' + _cs_id + ' is installed successfully.')
        save_data = [param_index, _ev_id, _cs_id, hex_ev_id, hex_key, installation_flag]
        DataSave.save_ev_installation_result(save_data)
    else:
        print(str(param_index) + ': ' + ev_id + " can't be connected to " + cs_id + '.')

    return 0


class InstallationPhase:
    __cs_thread_list = []
    __ev_thread_list = []
    __ev_cs_session_id_list = []
    __unique_cs_count = 0

    def __init__(self, unique_cs_id_list, port, unique_normal_ev_id_list, ev_cs_session_id_list):
        global global_normal_ev_total_count
        global_normal_ev_total_count = len(unique_normal_ev_id_list)
        self.__unique_cs_id_list = unique_cs_id_list
        self.__port = port
        self.__ev_cs_session_id_list = ev_cs_session_id_list

    def install_css(self):
        print('-------------------------------------- CS Installation --------------------------------------')
        global global_normal_ev_total_count
        self.__unique_cs_count = len(self.__unique_cs_id_list)
        for i in range(0, self.__unique_cs_count):
            cs_thread = threading.Thread(target=multi_thread_cs_installation, args=(self.__port,
                                                                                    self.__unique_cs_id_list[i]))
            cs_thread.start()
            self.__cs_thread_list.append(cs_thread)

    def install_normal_evs(self, sec_delta_list, scenario):
        print('-------------------------------------- EV Installation --------------------------------------')
        global global_normal_ev_total_count
        ev_count = len(self.__ev_cs_session_id_list)
        for i in range(0, ev_count):
            ev_thread = threading.Thread(target=multi_thread_ev_installation, args=(i, self.__ev_cs_session_id_list,
                                                                                    self.__unique_cs_count,
                                                                                    sec_delta_list[i],
                                                                                    scenario))
            ev_thread.start()
            self.__ev_thread_list.append(ev_thread)

    def release_css(self):
        for cs_thread in self.__cs_thread_list:
            cs_thread.join()
        self.__cs_thread_list.clear()

    def release_evs(self):
        for ev_thread in self.__ev_thread_list:
            ev_thread.join()
        self.__ev_thread_list.clear()

    @classmethod
    def get_cs_connection_dict(cls):
        global global_cs_gs_connection_dict
        return global_cs_gs_connection_dict

    @classmethod
    def get_installed_normal_ev_cs_list(cls):
        global global_installed_normal_ev_cs_list
        return global_installed_normal_ev_cs_list

    @classmethod
    def get_scheduled_charging_of_normal_evs(cls, cs_id, scheduled_charging_list, scenario):
        _temp_list = []
        for schedule in scheduled_charging_list:  # ev_id, cs_id, hex_ev_id, hex_key, type
            if cs_id == schedule[1]:
                _temp_list.append(schedule)

        if scenario == AttackConfig.attack_scenario_list(0):
            _temp_list = sorted(_temp_list, key=lambda temp_list: temp_list[6])
            prev_sec = 0
            for i in range(0, len(_temp_list)):
                sec_delta = _temp_list[i][6] - prev_sec
                prev_sec = _temp_list[i][6]
                _temp_list[i][6] = sec_delta

        return _temp_list
