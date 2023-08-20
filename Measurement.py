import multiprocessing
import os
import subprocess
from multiprocessing import Process

process_list = []
end_thread_flag = True


def multi_process_work_perf_top(param_pid, _dir, event):
    # sim_flag.wait()
    print('Perf Top PID: ' + str(param_pid))
    os.system('perf top -d 1 --show-total-period -U -e ' + event + ' -p ' + str(param_pid) +
              ' --stdio > ./output/' + _dir + '/perf_top_' + event + '_' + str(param_pid) + '.txt')


def multi_process_work_perf_record(param_pid, _dir):
    print('Perf Record PID: ' + str(param_pid))
    subprocess.call(['perf', 'record', '-e', 'cycles,instructions,branch', '-o', './output/' + _dir + '/perf_record_'
                     + str(param_pid), '-p', str(param_pid)])


def multi_process_work_perf_stat(param_pid, _dir):
    print('Perf Stat PID: ' + str(param_pid))
    os.system('perf stat -p ' + str(param_pid) + ' -I 100 -o ./output/' + _dir + '/perf_stat_' + str(param_pid) +
              '.txt')


global_ev_auth_list = []


class Measurement:
    __process_perf_record_dict = {}
    __gs_pid = None

    def __init__(self, return_pid_dict):
        self.__return_pid_dict = return_pid_dict
        manager = multiprocessing.Manager()
        self.__pid_list = manager.list()
        if not os.path.exists('./output/cs_stat'):
            os.mkdir('./output/cs_stat')
        if not os.path.exists('./output/cs_top'):
            os.mkdir('./output/cs_top')
        if not os.path.exists('./output/cs_record'):
            os.mkdir('./output/cs_record')
        if not os.path.exists('./output/gs_stat'):
            os.mkdir('./output/gs_stat')
        if not os.path.exists('./output/gs_top'):
            os.mkdir('./output/gs_top')
        if not os.path.exists('./output/gs_record'):
            os.mkdir('./output/gs_record')

    def start_perf_record(self, target_pid, _dir):
        if _dir == 'gs_record':
            self.__gs_pid = target_pid

        process_perf_record_all = Process(target=multi_process_work_perf_record, args=(target_pid, _dir))
        process_perf_record_all.start()
        self.__process_perf_record_dict[target_pid] = process_perf_record_all.pid

    @classmethod
    def start_perf_top(cls, target_pid, _dir, event):
        process_perf_top = Process(target=multi_process_work_perf_top, args=(target_pid, _dir, event))
        process_perf_top.start()

    @classmethod
    def start_perf_stat(cls, target_pid, _dir):
        process_perf_stat = Process(target=multi_process_work_perf_stat, args=(target_pid, _dir))
        process_perf_stat.start()

    def convert_perf_record_to_file(self):
        for target_pid in self.__process_perf_record_dict.keys():
            if target_pid == self.__gs_pid:
                os.system('perf report -i ./output/gs_record/perf_record_' + str(target_pid) +
                          ' > ./output/gs_record/perf_record_' + str(target_pid) + '.txt')
            else:
                os.system('perf report -i ./output/cs_record/perf_record_' + str(target_pid) +
                          ' > ./output/cs_record/perf_record_' + str(target_pid) + '.txt')

    @classmethod
    def kill_perf(cls):
        os.system('pkill -x perf')
