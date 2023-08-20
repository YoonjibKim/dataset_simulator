import time
from datetime import datetime

from DataSave import DataSave
from acnportal.acndata import DataClient


class Dataset(DataClient):
    __site = None

    def __init__(self, api_token, site):
        self.__site = site
        super().__init__(api_token)

    def count_sessions(self):
        return super().count_sessions(self.__site)

    def get_sessions_by_time(self, start, end):
        return super().get_sessions_by_time(self.__site, start, end)


class DatasetManager:
    __session_cs_id_list = []

    def __init__(self, begin_year, begin_month, begin_day, end_year, end_month, end_day):
        DataSave.save_date(begin_year, begin_month, begin_day, end_year, end_month, end_day)
        print('------------------------------------- Initializing Parameters -------------------------------------')
        print('site, api_token, start, end, period')
        site = 'caltech'
        api_token = 'jzClgaOJjIb1EZrDKfI-4Sw_rX_o_U1RZBzavoiX8Os'
        dataset = Dataset(api_token, site)
        self.__start_time = datetime(year=begin_year, month=begin_month, day=begin_day)
        self.__end_time = datetime(year=end_year, month=end_month, day=end_day)
        print(site + ', ' + api_token + ', ' + str(self.__start_time) + ', ' + str(self.__end_time))

        sessions = dataset.get_sessions_by_time(self.__start_time, self.__end_time)

        flag_key = True
        key_list = []
        value_list = []

        print('--------------------------------------- Loading ACN Dataset ---------------------------------------')
        for index, session in enumerate(sessions):
            temp_list = list(session.values())
            for key in session.keys():
                if flag_key:
                    key_list.append(key)
            # print(temp_list)
            value_list.append(temp_list)
            flag_key = False
            self.__session_cs_id_list.append([session['_id'], session['stationID'], session['sessionID']])
            DataSave.save_acn_data(temp_list, key_list)

        # print('Fields: ', end=' ')
        # print(key_list)
        # print('Total: ' + str(dataset.count_sessions()))
        print('---------------------------------------- Loading Done ----------------------------------------')

    def extract_session_cs_id(self):
        return self.__session_cs_id_list

    def get_unique_cs_id_list(self):
        temp_cs_id_list = []
        for record in self.__session_cs_id_list:
            temp_cs_id_list.append(record[1])

        unique_cs_id_list = list(set(temp_cs_id_list))
        return unique_cs_id_list

    def get_unique_normal_ev_id_list(self):
        temp_session_id_list = []
        for record in self.__session_cs_id_list:
            temp_session_id_list.append(record[0])

        return temp_session_id_list

    def __get_access_time_list(self):
        access_date_time_list = []
        for record in self.__session_cs_id_list:
            temp = record[2].split('_')
            temp_date_time = datetime.strptime(temp[4], '%Y-%m-%d %H:%M:%S.%f')
            seconds = time.mktime(temp_date_time.timetuple())
            access_date_time_list.append(seconds)

        return access_date_time_list

    @classmethod
    def __calculate_sec_tick(cls, attack_sim_sec, normal_sim_sec):
        time_tick = attack_sim_sec / normal_sim_sec
        return time_tick

    def get_normal_auth_time_delta(self, attack_sim_sec):
        sim_start_seconds = time.mktime(self.__start_time.timetuple())
        sim_end_seconds = time.mktime(self.__end_time.timetuple())
        normal_sim_sec = sim_end_seconds - sim_start_seconds
        sim_normal_ev_seconds_list = self.__get_access_time_list()
        time_tick = self.__calculate_sec_tick(attack_sim_sec, normal_sim_sec)

        sec_delta_list = []
        for ev_auth_seconds in sim_normal_ev_seconds_list:
            sec_delta = ev_auth_seconds - sim_start_seconds
            sec_delta_list.append(sec_delta * time_tick)

        last_delta = 0
        last_seconds = sim_normal_ev_seconds_list[len(sim_normal_ev_seconds_list) - 1]
        if sim_end_seconds > last_seconds:
            last_delta = sim_end_seconds - sim_normal_ev_seconds_list[len(sim_normal_ev_seconds_list) - 1]
            last_delta *= time_tick

        return sec_delta_list, last_delta
