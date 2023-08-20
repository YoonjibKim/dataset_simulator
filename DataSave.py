
import json
import pandas as pd
import AttackConfig

from datetime import datetime


class DataSave:
    __ev_installation_list = []
    __cs_installation_list = []
    __authentication_result_dict = {}
    __acn_data = []
    __acn_data_field_name_list = []
    __cs_id_pid_list = []
    __mean = 0
    __std = 0

    @classmethod
    def save_attack_configuration(cls, attack_scenario, attack_ev_min_count, attack_ev_max_count):
        temp_list = [attack_scenario, attack_ev_min_count, attack_ev_max_count]
        df = pd.DataFrame(temp_list)
        df.to_csv('./output/attack_config.csv', index=False)

    @classmethod
    def save_date(cls, begin_year, begin_month, begin_day, end_year, end_month, end_day):
        temp_list = [begin_year, begin_month, begin_day, end_year, end_month, end_day]
        df = pd.DataFrame(temp_list)
        df.to_csv('./output/date.csv', index=False)

    @classmethod
    def save_ev_authentication_result(cls, result_dict, return_pid_dict_items):
        cls.__authentication_result_dict = result_dict
        cls.__cs_id_pid_list = return_pid_dict_items

    @classmethod
    def save_cs_installation_result(cls, cs_id):
        cls.__cs_installation_list.append(cs_id)

    @classmethod
    def save_ev_installation_result(cls, data_list):
        cls.__ev_installation_list.append(data_list)

    @classmethod
    def save_all_data(cls, scenario, charging_schedule_list, ev_count_dict, guassian_attack_count_dict,
                      random_attack_on_off, guassian_heuristic_on_off):
        attack_mode_str = 'random_attack_on_off: ' + str(random_attack_on_off) + ', '
        attack_mode_str += 'guassian_heuristic_on_off: ' + str(guassian_heuristic_on_off)
        f = open('./output/attack_mode.txt', 'w')
        f.write(attack_mode_str)
        f.close()

        df = pd.DataFrame(cls.__acn_data)
        df.columns = cls.__acn_data_field_name_list
        df.to_csv('./output/acn_data.csv', index=False)

        df = pd.DataFrame(cls.__cs_installation_list)
        df.columns = ['CS ID']
        df.to_csv('./output/cs_installation.csv', index=False)

        df = pd.DataFrame(cls.__ev_installation_list)
        df.columns = ['Process Order', 'Session ID', 'CS Id', 'HEX EV ID', 'HEX Key', 'Installation']
        df.to_csv('./output/ev_installation.csv', index=False)

        df = pd.DataFrame(cls.__cs_id_pid_list, columns=['CS ID', 'CS PID'])
        df.to_csv('./output/cs_id_pid.csv', index=False)

        temp_list = []
        for key, values in cls.__authentication_result_dict.items():
            for value in values:
                temp_list.append(value)

        df = pd.DataFrame(temp_list)
        column_list = []
        for col in range(0, df.shape[1]):
            column_list.append('EV No. ' + str(col + 1))
        df.columns = column_list
        df.to_csv('./output/ev_authentication.csv', index=False)

        dual_record_list = []
        for outer_record in temp_list:
            for inner_record in outer_record:
                record_list = inner_record.split('|')
                dual_record_list.append(record_list)

        df = pd.DataFrame(dual_record_list)
        df.columns = ['Session ID', 'CS ID', 'Timestamp', 'Authentication', 'Installation', 'Type', 'Date_Time']
        df.to_csv('./output/authentication_results.csv', index=False)

        if scenario == AttackConfig.AttackConfig.attack_scenario_list(0):
            sec_delta_dict = cls.__calculate_normal_auth_time_delta(charging_schedule_list)
            f = open('./output/normal_time_diff.txt', 'w')
            json.dump(sec_delta_dict, f, indent=4)
        else:
            sec_delta_dict = cls.__calculate_attack_auth_time_delta(temp_list)
            f = open('./output/attack_time_diff.txt', 'w')
            json.dump(sec_delta_dict, f, indent=4)

        f.close()

        f = open('./output/ev_count.txt', 'w')
        json.dump(ev_count_dict, f, indent=4)
        f.close()

        f = open('./output/gaussian_attack_count.txt', 'w')
        json.dump(guassian_attack_count_dict, f, indent=4)
        f.close()

        f = open('./output/mean_std.txt', 'w')
        mean_std_str = 'mean: ' + str(cls.__mean) + ', std: ' + str(cls.__std)
        f.write(mean_std_str)
        f.close()

    @classmethod
    def save_mean_std(cls, mean, std):
        cls.__mean = mean
        cls.__std = std

    @classmethod
    def save_acn_data(cls, data_list, key_list):
        cls.__acn_data.append(data_list)
        cls.__acn_data_field_name_list = key_list

    @classmethod
    def __get_unique_cs_id_list(cls, data_dual_list):
        cs_id_list = []
        for outer_record in data_dual_list:
            for inner_record in outer_record:
                record_list = inner_record.split('|')
                cs_id_list.append(record_list[1])

        return list(set(cs_id_list))

    @classmethod
    def __get_ms(cls, date_time):
        temp = datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S.%f')
        return temp.utcnow().timestamp() * 1000

    @classmethod
    def __get_attack_time_diff(cls, data_dual_list):
        date_time_dict = {}
        for unique_cs_id in cls.__get_unique_cs_id_list(data_dual_list):
            temp_list = []
            for outer_record in data_dual_list:
                for inner_record in outer_record:
                    temp_record = inner_record.split('|')
                    cs_id = temp_record[1]
                    if unique_cs_id == cs_id:
                        date_time = temp_record[6]
                        temp_list.append(date_time)
            date_time_dict[unique_cs_id] = temp_list

        prev_time = 0
        time_diff_dict = {}
        for key, value_list in date_time_dict.items():
            temp_list = []
            for value in value_list:
                curr_ms = cls.__get_ms(value)
                ms_diff = curr_ms - prev_time
                prev_time = curr_ms
                temp_list.append(round(ms_diff, 4))
            temp_list.pop(0)
            time_diff_dict[key] = temp_list

        return time_diff_dict

    @classmethod
    def __get_normal_time_diff(cls, ev_cs_session_id_list):
        cs_id_list = []
        for record in ev_cs_session_id_list:
            cs_id = record[1]
            cs_id_list.append(cs_id)

        unique_cs_id_list = list(set(cs_id_list))
        cs_id_date_time_dict = {}
        for unique_cs_id in unique_cs_id_list:
            date_time_list = []
            prev_time = 0
            for record in ev_cs_session_id_list:
                cs_id = record[1]
                if unique_cs_id == cs_id:
                    temp_date_time = record[2]
                    temp_date_time = temp_date_time.split('_')[4]
                    curr_date_time = cls.__get_ms(temp_date_time)
                    time_diff = curr_date_time - prev_time
                    prev_time = curr_date_time
                    date_time_list.append(round(time_diff, 4))

            date_time_list.pop(0)
            cs_id_date_time_dict[unique_cs_id] = date_time_list

        return cs_id_date_time_dict

    @classmethod
    def save_sim_time(cls, sim_sec, scenario, start_sim_date, end_sim_date):
        if scenario != AttackConfig.AttackConfig.attack_scenario_list(0):
            fd = open('./input/sim_sec_attack.txt', 'w')
        else:
            fd = open('./input/sim_sec_normal.txt', 'w')

        fd.write(str(sim_sec) + ' ' + str(start_sim_date.year) + ' ' + str(start_sim_date.month) + ' '
                 + str(start_sim_date.day) + ' ' + str(end_sim_date.year) + ' ' + str(end_sim_date.month) + ' '
                 + str(end_sim_date.day))
        fd.close()

    @classmethod
    def __calculate_normal_auth_time_delta(cls, charging_schedule_list):
        date_time_dict = {}
        for outer_list in charging_schedule_list:
            cs_id = outer_list[0][1]
            temp_second_list = []
            for inner_list in outer_list:
                temp_seconds = inner_list[6]
                temp_second_list.append(temp_seconds)
            date_time_dict[cs_id] = temp_second_list

        return date_time_dict

    @classmethod
    def __calculate_attack_auth_time_delta(cls, data_dual_list):
        outer_sec_delta_list = {}
        for outer_list in data_dual_list:
            temp_list = outer_list[0].split('|')
            cs_id = temp_list[1]
            inner_sec_delta_list = []
            if len(outer_list) < 2:
                inner_sec_delta_list.append(0)
            else:
                for index in range(1, len(outer_list)):
                    prev_temp_list = outer_list[index-1].split('|')
                    next_temp_list = outer_list[index].split('|')
                    temp_prev_date_time = prev_temp_list[6]
                    temp_next_date_time = next_temp_list[6]
                    prev_date_time = datetime.strptime(temp_prev_date_time, '%Y-%m-%d %H:%M:%S.%f')
                    next_date_time = datetime.strptime(temp_next_date_time, '%Y-%m-%d %H:%M:%S.%f')
                    date_time_delta = next_date_time - prev_date_time
                    second_delta = date_time_delta.total_seconds()
                    inner_sec_delta_list.append(second_delta)

            outer_sec_delta_list[cs_id] = inner_sec_delta_list

        return outer_sec_delta_list