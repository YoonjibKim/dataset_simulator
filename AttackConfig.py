import random

from DataSave import DataSave


class AttackConfig:
    __wrong_ev_ts_flag = False
    __wrong_cs_ts_flag = False
    __random_victim_cs = False
    __random_attack_ev_count = False
    __attack_scenario_list = ['no attack', 'correct ID', 'wrong ID', 'wrong ev timestamp', 'wrong cs timestamp']

    def __init__(self, attack_scenario, attack_ev_min_count, attack_ev_max_count, random_victim_cs=True,
                 random_attack_ev_count=True):
        self.__attack_scenario = attack_scenario
        self.__attack_ev_min_count = attack_ev_min_count
        self.__attack_ev_max_count = attack_ev_max_count
        self.__random_victim_cs = random_victim_cs
        self.__random_attack_ev_count = random_attack_ev_count
        DataSave.save_attack_configuration(attack_scenario, attack_ev_max_count)

    def get_scenario(self):
        return self.__attack_scenario

    def normal_or_attack(self):
        scenario = self.__attack_scenario
        if self.__random_victim_cs:
            choice_list = ['attack', 'normal']
            scenario = random.choice(choice_list)

        return scenario

    def random_attack_ev_count(self):
        count = random.randrange(self.__attack_ev_min_count, self.__attack_ev_max_count + 1)
        return count

    def get_attack_scenario(self, charging_schedule):
        if self.__attack_scenario == self.__attack_scenario_list[0]:
            configuration = charging_schedule
        elif self.__attack_scenario == self.__attack_scenario_list[1]:
            scenario = self.normal_or_attack()
            if scenario == 'attack':
                attack_ev_id = charging_schedule[0][0]
                victim_cs_id = charging_schedule[0][1]
                wrong_hex_ev_id = '0000000000000000000000000000000000000000000000000000000000000000'
                wrong_hex_key = '0000000000000000000000000000000000000000000000000000000000000000'
                installation_flag = False
                attack_ev_schedule = [attack_ev_id, victim_cs_id, wrong_hex_ev_id, wrong_hex_key, installation_flag,
                                      'attack', 0.0]
                configuration = charging_schedule
                for i in range(0, self.random_attack_ev_count()):
                    configuration.append(attack_ev_schedule)
            else:
                configuration = charging_schedule
        elif self.__attack_scenario == self.__attack_scenario_list[2]:
            scenario = self.normal_or_attack()
            if scenario == 'attack':
                attack_ev_id = 'ATTACK_EV'
                victim_cs_id = charging_schedule[0][1]
                wrong_hex_ev_id = '0000000000000000000000000000000000000000000000000000000000000000'
                wrong_hex_key = '0000000000000000000000000000000000000000000000000000000000000000'
                installation_flag = False
                attack_ev_schedule = [attack_ev_id, victim_cs_id, wrong_hex_ev_id, wrong_hex_key, installation_flag,
                                      'attack', 0.0]
                configuration = charging_schedule
                for i in range(0, self.random_attack_ev_count()):
                    configuration.append(attack_ev_schedule)
            else:
                configuration = charging_schedule
        elif self.__attack_scenario == self.__attack_scenario_list[3]:
            scenario = self.normal_or_attack()
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
                for i in range(0, self.random_attack_ev_count()):
                    configuration.append(attack_ev_schedule)
            else:
                configuration = charging_schedule
        elif self.__attack_scenario == self.__attack_scenario_list[4]:
            scenario = self.normal_or_attack()
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
                for i in range(0, self.random_attack_ev_count()):
                    configuration.append(attack_ev_schedule)
            else:
                configuration = charging_schedule
        else:
            print('Wrong attack scenario')
            configuration = charging_schedule

        return configuration

    def get_wrong_ev_ts(self):
        return self.__wrong_ev_ts_flag

    def get_wrong_cs_ts(self):
        return self.__wrong_cs_ts_flag

    @classmethod
    def attack_scenario_list(cls, index):
        return cls.__attack_scenario_list[index]
