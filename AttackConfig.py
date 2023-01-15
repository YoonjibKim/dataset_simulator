import random
import numpy as np
from DataSave import DataSave
import scipy as sp


class AttackConfig:
    __wrong_ev_ts_flag = False
    __wrong_cs_ts_flag = False
    __random_victim_cs = False
    __random_attack_ev_count = False
    __attack_scenario_list = ['no attack', 'correct ID', 'wrong ID', 'wrong ev timestamp', 'wrong cs timestamp']
    __ev_count_dict = {}

    def __init__(self, attack_scenario, attack_ev_min_count, attack_ev_max_count, random_victim_cs=True,
                 random_attack_ev_count=True):
        self.__attack_scenario = attack_scenario
        self.__attack_ev_min_count = attack_ev_min_count
        self.__attack_ev_max_count = attack_ev_max_count
        self.__random_victim_cs = random_victim_cs
        self.__random_attack_ev_count = random_attack_ev_count
        DataSave.save_attack_configuration(attack_scenario, attack_ev_min_count, attack_ev_max_count)

    def get_scenario(self):
        return self.__attack_scenario

    def __generate_random_normal_or_attack_sub_scenario(self, random_attack_on_off):
        scenario = self.__attack_scenario
        if random_attack_on_off:
            if self.__random_victim_cs:
                choice_list = ['attack', 'normal']
                scenario = random.choice(choice_list)
        else:
            scenario = 'attack'

        return scenario

    def __get_attack_count(self):
        count = random.randrange(self.__attack_ev_min_count, self.__attack_ev_max_count + 1)
        return count

    def get_attack_scenario(self, charging_schedule, random_attack_on_off,
                            guassian_heuristic_on_off, guassian_attack_count_dict):

        if self.__attack_scenario == self.__attack_scenario_list[0]:
            configuration = charging_schedule
        elif self.__attack_scenario == self.__attack_scenario_list[1]:
            scenario = self.__generate_random_normal_or_attack_sub_scenario(random_attack_on_off)
            if scenario == 'attack':
                attack_ev_id = charging_schedule[0][0]
                victim_cs_id = charging_schedule[0][1]
                wrong_hex_ev_id = '0000000000000000000000000000000000000000000000000000000000000000'
                wrong_hex_key = '0000000000000000000000000000000000000000000000000000000000000000'
                installation_flag = False
                attack_ev_schedule = [attack_ev_id, victim_cs_id, wrong_hex_ev_id, wrong_hex_key, installation_flag,
                                      'attack', 0.0]
                configuration = charging_schedule
                if guassian_heuristic_on_off:
                    normal_ev_count = len(charging_schedule)
                    for original_count, attack_count in guassian_attack_count_dict.items():
                        if normal_ev_count == original_count:
                            count = round(attack_count)
                            for i in range(0, count):
                                configuration.append(attack_ev_schedule)
                else:
                    for i in range(0, self.__get_attack_count()):
                        configuration.append(attack_ev_schedule)
            else:
                configuration = charging_schedule
        elif self.__attack_scenario == self.__attack_scenario_list[2]:
            scenario = self.__generate_random_normal_or_attack_sub_scenario(random_attack_on_off)
            if scenario == 'attack':
                attack_ev_id = 'ATTACK_EV'
                victim_cs_id = charging_schedule[0][1]
                wrong_hex_ev_id = '0000000000000000000000000000000000000000000000000000000000000000'
                wrong_hex_key = '0000000000000000000000000000000000000000000000000000000000000000'
                installation_flag = False
                attack_ev_schedule = [attack_ev_id, victim_cs_id, wrong_hex_ev_id, wrong_hex_key, installation_flag,
                                      'attack', 0.0]
                configuration = charging_schedule
                if guassian_heuristic_on_off:
                    normal_ev_count = len(charging_schedule)
                    for original_count, attack_count in guassian_attack_count_dict.items():
                        if normal_ev_count == original_count:
                            count = round(attack_count)
                            for i in range(0, count):
                                configuration.append(attack_ev_schedule)
                else:
                    for i in range(0, self.__get_attack_count()):
                        configuration.append(attack_ev_schedule)
            else:
                configuration = charging_schedule
        elif self.__attack_scenario == self.__attack_scenario_list[3]:
            scenario = self.__generate_random_normal_or_attack_sub_scenario(random_attack_on_off)
            if scenario == 'attack':
                attack_ev_id = charging_schedule[0][0]
                victim_cs_id = charging_schedule[0][1]
                attack_hex_ev_id = charging_schedule[0][2]
                attack_hex_key = charging_schedule[0][3]
                installation_flag = False
                attack_ev_schedule = [attack_ev_id, victim_cs_id, attack_hex_ev_id, attack_hex_key, installation_flag,
                                      'attack', 0.0]
                self.__wrong_ev_ts_flag = True
                configuration = charging_schedule
                if guassian_heuristic_on_off:
                    normal_ev_count = len(charging_schedule)
                    for original_count, attack_count in guassian_attack_count_dict.items():
                        if normal_ev_count == original_count:
                            count = round(attack_count)
                            for i in range(0, count):
                                configuration.append(attack_ev_schedule)
                else:
                    for i in range(0, self.__get_attack_count()):
                        configuration.append(attack_ev_schedule)
            else:
                configuration = charging_schedule
        elif self.__attack_scenario == self.__attack_scenario_list[4]:
            scenario = self.__generate_random_normal_or_attack_sub_scenario(random_attack_on_off)
            if scenario == 'attack':
                attack_ev_id = charging_schedule[0][0]
                victim_cs_id = charging_schedule[0][1]
                attack_hex_ev_id = charging_schedule[0][2]
                attack_hex_key = charging_schedule[0][3]
                installation_flag = False
                attack_ev_schedule = [attack_ev_id, victim_cs_id, attack_hex_ev_id, attack_hex_key, installation_flag,
                                      'attack', 0.0]
                self.__wrong_cs_ts_flag = True
                configuration = charging_schedule
                if guassian_heuristic_on_off:
                    normal_ev_count = len(charging_schedule)
                    for original_count, attack_count in guassian_attack_count_dict.items():
                        if normal_ev_count == original_count:
                            count = round(attack_count)
                            for i in range(0, count):
                                configuration.append(attack_ev_schedule)
                else:
                    for i in range(0, self.__get_attack_count()):
                        configuration.append(attack_ev_schedule)
            else:
                configuration = charging_schedule
        else:
            print('Wrong attack scenario')
            configuration = charging_schedule

        ev_count_dict = self.__extract_ev_count(charging_schedule)
        return configuration, ev_count_dict

    def __extract_ev_count(self, charging_schedule):
        normal_evs = 0
        attack_evs = 0
        cs_id = charging_schedule[0][1]
        for record in charging_schedule:
            _type = record[5]
            if _type == 'attack':
                attack_evs += 1
            else:
                normal_evs += 1

        self.__ev_count_dict[cs_id] = [normal_evs, attack_evs]
        return self.__ev_count_dict

    def get_wrong_ev_ts(self):
        return self.__wrong_ev_ts_flag

    def get_wrong_cs_ts(self):
        return self.__wrong_cs_ts_flag

    @classmethod
    def attack_scenario_list(cls, index):
        return cls.__attack_scenario_list[index]

    @classmethod
    def __calculate_gaussian(cls, data, mean, std):
        probability = (1.0 / (np.sqrt(2 * np.pi))) * np.exp(-1 * (((data - mean)/std) ** 2))
        return probability

    @classmethod
    def get_normal_distribution(cls, scheduled_charging_list, alpha=10):
        temp_cs_id_list = []
        for record in scheduled_charging_list:
            temp_cs_id_list.append(record[1])

        temp_unique_cs_id_list = list(set(temp_cs_id_list))
        temp_cs_id_normal_ev_count_dict = {}
        ev_count = 0
        data_list = []
        for unique_cs_id in temp_unique_cs_id_list:
            for scheduled_charging in scheduled_charging_list:
                if unique_cs_id == scheduled_charging[1]:
                    ev_count += 1
            temp_cs_id_normal_ev_count_dict[unique_cs_id] = ev_count
            data_list.append(ev_count)
            ev_count = 0

        mean = np.mean(data_list)
        std = np.std(data_list)

        rv = sp.stats.norm(loc=mean, scale=std)
        pdf = rv.pdf(data_list)

        unique_gaussian_attack_count_list = list(set(data_list))
        gaussian_attack_count_dict = {}
        for unique_attack_count in unique_gaussian_attack_count_list:
            for index, probability in enumerate(pdf):
                count = data_list[index]
                if unique_attack_count == count:
                    gaussian_attack_count_dict[unique_attack_count] = probability
                    break

        unique_total_pdf = 0
        for value in gaussian_attack_count_dict.values():
            unique_total_pdf += value

        ratio_gaussian_attack_count_dict = {}
        for unique_count, sub_pdf in gaussian_attack_count_dict.items():
            ratio = (alpha * sub_pdf) / unique_total_pdf
            ratio_count = unique_count * ratio
            ratio_gaussian_attack_count_dict[unique_count] = ratio_count

        # CS들의 각 접근 횟수에 대한 가우스 PDF 구한 후 전체 PDF에서 각 PDF이 Ratio를 구하고 (10배 상수배 먼저하고) 이 Ratio에 대한
        # 각 CS들의 가운터에 대한 비율을 구해서 공격횟수로 선정
        return ratio_gaussian_attack_count_dict, mean, std
