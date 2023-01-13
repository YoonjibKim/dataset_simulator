
import threading
import time
from datetime import datetime

from Network import V2G_Network
from Security import Authentication

global_ev_to_cs_auth_msg = []
global_cs_to_ev_auth_msg = None
global_cs_running_flag = True
global_ev_auth_result_list = []


def cs_ready_for_ev_authentication(param_conn, param_attack_config):
    global global_ev_to_cs_auth_msg
    global global_cs_to_ev_auth_msg
    global global_cs_running_flag

    while global_cs_running_flag:
        if len(global_ev_to_cs_auth_msg) > 0:
            ev_to_cs_access_date_time = datetime.now()
            msg = global_ev_to_cs_auth_msg.pop()
            _ev_id = msg[0]
            _cs_id = msg[1]
            bin_encryption = msg[2]
            bin_verification = msg[3]
            bin_ev_id = msg[4]
            bin_ts = msg[5]
            installation_flag = msg[6]
            _type = msg[7]

            is_ev_fresh = Authentication.cs_check_fresh(bin_ts)
            ev_auth_flag = False
            if is_ev_fresh:
                wrong_cs_ts_flag = param_attack_config.get_wrong_cs_ts()
                if wrong_cs_ts_flag and installation_flag is False:
                    bin_ts = '00000000000000000000000000000000000000000000000000000000000000000000000000000000'
                ev_auth_flag = \
                    V2G_Network.authenticating_ev(param_conn, bin_encryption, bin_verification, bin_ev_id, bin_ts,
                                                  _cs_id)
                send_data = _ev_id + '|' + _cs_id + '|fresh|' + str(ev_auth_flag) + '|' + \
                            str(installation_flag) + '|' + _type + '|' + str(ev_to_cs_access_date_time)
            else:
                send_data = _ev_id + '|' + _cs_id + '|old|' + str(ev_auth_flag) + '|' + \
                            str(installation_flag) + '|' + _type + '|' + str(ev_to_cs_access_date_time)

            global_cs_to_ev_auth_msg = send_data


global_ev_thread_sync = threading.Lock()


def multi_thread_ev_authentication(param_ev_id, param_cs_id, param_hex_ev_id, param_hex_hey, param_installation_flag,
                                   param_attack_config, param_type):
    global global_ev_thread_sync
    global global_ev_to_cs_auth_msg
    global global_cs_to_ev_auth_msg
    global global_ev_auth_result_list

    global_ev_thread_sync.acquire()
    bin_encryption, bin_verification, bin_ev_id, bin_ts = Authentication.get_evidts(param_hex_ev_id, param_hex_hey)
    wrong_ev_ts_flag = param_attack_config.get_wrong_ev_ts()
    if wrong_ev_ts_flag and param_installation_flag is False:
        bin_ts = '00000000000000000000000000000000000000000000000000000000000000000000000000000000'
    global_ev_to_cs_auth_msg.append([param_ev_id, param_cs_id, bin_encryption, bin_verification, bin_ev_id, bin_ts,
                                     param_installation_flag, param_type])

    while True:
        if global_cs_to_ev_auth_msg is not None:
            break

    global_ev_auth_result_list.append(global_cs_to_ev_auth_msg)
    global_cs_to_ev_auth_msg = None
    global_ev_thread_sync.release()
    return 0


class AuthenticationPhase:
    __cs_thread = None
    __output_count = 0

    def __init__(self, cs_id, conn, charging_schedule, attack_config):
        self.__cs_id = cs_id
        self.__conn = conn
        self.__charging_schedule = charging_schedule
        self.__attack_config = attack_config

    def running_cs(self):
        self.__cs_thread = threading.Thread(target=cs_ready_for_ev_authentication,
                                            args=(self.__conn, self.__attack_config,))
        self.__cs_thread.start()

    def running_evs(self):
        ev_thread_list = []
        for schedule in self.__charging_schedule:
            ev_id = schedule[0]
            cs_id = schedule[1]
            hex_ev_id = schedule[2]
            hex_key = schedule[3]
            installation_flag = schedule[4]
            _type = schedule[5]
            sleep_sec = schedule[6]
            if self.__attack_config.get_scenario() == self.__attack_config.attack_scenario_list(0):
                time.sleep(sleep_sec)

            ev_thread = threading.Thread(target=multi_thread_ev_authentication, args=(ev_id, cs_id, hex_ev_id, hex_key,
                                                                                      installation_flag,
                                                                                      self.__attack_config,
                                                                                      _type))
            ev_thread.start()
            ev_thread_list.append(ev_thread)

        for ev_thread in ev_thread_list:
            ev_thread.join()

    @classmethod
    def get_results(cls):
        global global_ev_auth_result_list
        temp_list = []
        for i in global_ev_auth_result_list:
            temp_list.append(i)
        global_ev_auth_result_list.clear()
        return temp_list

    def release_cs(self):
        global global_cs_running_flag
        global_cs_running_flag = False
        self.__cs_thread.join()
