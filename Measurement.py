import multiprocessing
import os
import random
import signal
import subprocess
import time
from multiprocessing import Process

process_list = []
end_thread_flag = True


def multi_process_work_perf_top(param_pid, _dir, event):
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
    __process_perf_stat_dict = {}
    __process_perf_record_dict = {}
    __process_perf_top_dict = {}

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

    @classmethod
    def __choose_pid(cls, ps_list):
        index = random.randint(0, len(ps_list))
        return str(ps_list[index].pid)

    def start_perf_record(self, target_pid, _dir):
        process_perf_record_all = Process(target=multi_process_work_perf_record, args=(target_pid, _dir))
        process_perf_record_all.start()
        self.__process_perf_record_dict[target_pid] = process_perf_record_all.pid

    def start_perf_top(self, target_pid, _dir, event):
        process_perf_top = Process(target=multi_process_work_perf_top, args=(target_pid, _dir, event))
        process_perf_top.start()
        self.__process_perf_top_dict[target_pid] = process_perf_top.pid

    def start_perf_stat(self, target_pid, _dir):
        process_perf_stat = Process(target=multi_process_work_perf_stat, args=(target_pid, _dir))
        process_perf_stat.start()
        self.__process_perf_stat_dict[target_pid] = process_perf_stat.pid

    def end_perf_measurement(self, target_pid):
        if target_pid in self.__process_perf_top_dict:
            perf_pid = self.__process_perf_top_dict[target_pid]
            self.end_process(perf_pid)
            print('Top profiling on ' + str(target_pid) + ' has been terminated.')
        if target_pid in self.__process_perf_stat_dict:
            perf_pid = self.__process_perf_stat_dict[target_pid]
            self.end_process(perf_pid)
            print('Stat profiling on ' + str(target_pid) + ' has been terminated.')
        if target_pid in self.__process_perf_record_dict:
            perf_pid = self.__process_perf_record_dict[target_pid]
            self.end_process(perf_pid)
            print('Record profiling on ' + str(target_pid) + ' has been terminated.')

    @classmethod
    def end_process(cls, pid, kill=True):
        while True:
            try:
                if kill:
                    os.kill(pid, signal.SIGKILL)
                else:
                    os.kill(pid, signal.SIGTERM)
                break
            except OSError:
                print(str(pid) + ' is still alive!')
                time.sleep(0.1)

    @classmethod
    def kill_perf_and_python(cls):
        subprocess.call('sudo pkill -x perf', shell=True)
        subprocess.call('sudo pkill -x python3.10', shell=True)
