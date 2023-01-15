import multiprocessing
import os
import random
import signal
import subprocess
import time
from multiprocessing import Process

process_list = []
end_thread_flag = True


def multi_process_work_perf_top_branch(param_pid):
    print('Perf Top Branch GS PID: ' + str(param_pid))
    os.system('perf top -d 1 --show-total-period -U -e branch -p ' + str(param_pid) +
              ' --stdio > ./output/perf_top_branch.txt')


def multi_process_work_perf_top_instruction(param_pid):
    print('Perf Top Instruction GS PID: ' + str(param_pid))
    os.system('perf top -d 1 --show-total-period -U -e instructions -p ' + str(param_pid) +
              ' --stdio > ./output/perf_top_instruction.txt')


def multi_process_work_perf_top_cycle(param_pid):
    print('Perf Top Cycle GS PID: ' + str(param_pid))
    os.system('perf top -d 1 --show-total-period -U -e cycles -p ' + str(param_pid) +
              ' --stdio > ./output/perf_top_cycle.txt')


def multi_process_work_perf_record_all(param_pid):
    print('Perf Record GS PID: ' + str(param_pid))
    subprocess.call(['perf', 'record', '-e', 'cycles,instructions,branch', '-o', './output/perf_gs_record',
                     '-p', str(param_pid)])


def multi_process_work_perf_stat_cs(param_cs_pid):
    print('Perf Stat Instruction CS PID: ' + str(param_cs_pid))
    os.system('perf stat -p ' + str(param_cs_pid) + ' -I 100 -o ./output/cs/cs_' + str(param_cs_pid) + '.txt')


def multi_process_work_perf_stat_gs(param_gs_pid):
    print('Perf Stat Instruction GS PID: ' + str(param_gs_pid))
    os.system('perf stat -p ' + str(param_gs_pid) + ' -I 100 -o ./output/gs_' + str(param_gs_pid) + '.txt')


global_ev_auth_list = []


class Measurement:
    __process_perf_stat_cs_list = []
    __process_perf_stat_gs = None

    def __init__(self, return_pid_dict):
        self.__process_perf_record_all = None
        self.__process_perf_top_instruction = None
        self.__process_perf_top_cycle = None
        self.__process_perf_top_branch = None
        self.__return_pid_dict = return_pid_dict
        manager = multiprocessing.Manager()
        self.__pid_list = manager.list()
        if not os.path.exists('./output/cs'):
            os.mkdir('./output/cs')

    def get_process_perf_record_all(self):
        return self.__process_perf_record_all

    def get_process_perf_top_instruction(self):
        return self.__process_perf_top_instruction

    def get_process_perf_top_branch(self):
        return self.__process_perf_top_branch

    def get_process_perf_top_cycle(self):
        return self.__process_perf_top_cycle

    @classmethod
    def __choose_pid(cls, ps_list):
        index = random.randint(0, len(ps_list))
        return str(ps_list[index].pid)

    def start_perf_record_all(self, gs_pid):
        self.__process_perf_record_all = Process(target=multi_process_work_perf_record_all, args=(gs_pid,))
        self.__process_perf_record_all.start()

    def start_perf_top_cycle(self, gs_pid):
        self.__process_perf_top_cycle = Process(target=multi_process_work_perf_top_cycle, args=(gs_pid,))
        self.__process_perf_top_cycle.start()

    def start_perf_top_instruction(self, gs_pid):
        self.__process_perf_top_instruction = Process(target=multi_process_work_perf_top_instruction, args=(gs_pid,))
        self.__process_perf_top_instruction.start()

    def start_perf_top_branch(self, gs_pid):
        self.__process_perf_top_branch = Process(target=multi_process_work_perf_top_branch, args=(gs_pid,))
        self.__process_perf_top_branch.start()

    def start_perf_stat_cs(self, cs_pid):
        process_perf_stat = Process(target=multi_process_work_perf_stat_cs, args=(cs_pid,))
        process_perf_stat.start()
        self.__process_perf_stat_cs_list.append(process_perf_stat)

    def end_perf_stat_cs(self, cs_pid):
        for pid in self.__process_perf_stat_cs_list:
            if pid == cs_pid:
                pid.join()

    def start_perf_stat_gs(self, gs_pid):
        self.__process_perf_stat_gs = Process(target=multi_process_work_perf_stat_gs, args=(gs_pid,))
        self.__process_perf_stat_gs.start()

    def end_perf_stat_gs(self):
        self.__process_perf_stat_gs.join()

    @classmethod
    def terminate_process(cls, pid, kill=False):
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
    def terminate_perf(cls):
        subprocess.call('pkill -x perf', shell=True)
