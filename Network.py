import socket
import threading

from Security import Installation, Authentication

global_gs_side_cs_database = {}
global_gs_side_id_key_database = {}

# installation
global_gs_side_installation_ev_cs_database = {' ': [' ', ' ', ' ']}
global_server_finish_flag = False


class V2G_Network:
    __host_ip = 'localhost'
    __puf_value = 1

    @classmethod
    def get_open_port(cls):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("", 0))
        server.listen(1)
        port = server.getsockname()[1]
        server.close()
        return port

    @classmethod
    def __handle_client(cls, conn):
        global global_gs_side_installation_ev_cs_database
        global global_server_finish_flag

        cs_id = None
        challenge = None

        while True:
            recv_data = conn.recv(1024)
            if len(recv_data) > 0:
                recv_data = recv_data.decode('utf-8')
                recv_data_list = recv_data.split()
                send_data = ' '
                if recv_data_list[0] == 'cs_inst_1':
                    cs_id = recv_data_list[1]
                    challenge = Installation.gs_generate_challenge()
                    send_data = challenge + ' ' + cs_id
                elif recv_data_list[0] == 'cs_inst_2':
                    response = recv_data_list[1]
                    if int(challenge) + cls.__puf_value == int(response):
                        cs_loc = recv_data_list[2]
                        global_gs_side_cs_database[cs_id] = [challenge, response, cs_loc]
                        send_data = 'cs_inst_success'
                    else:
                        send_data = 'cs_inst_fail'
                elif recv_data_list[0] == 'ev_inst_1':
                    ev_id = recv_data_list[1]
                    cs_id = recv_data_list[2]

                    if ev_id in global_gs_side_installation_ev_cs_database:
                        send_data = 'ev_inst_fail'
                    else:
                        hex_key, hex_ev_id = Installation.gs_generate_ev_id_and_key(ev_id)
                        global_gs_side_id_key_database[hex_ev_id] = hex_key
                        global_gs_side_installation_ev_cs_database[ev_id] = [cs_id, hex_key, hex_ev_id]
                        send_data = 'ev_inst_success ' + str(hex_ev_id) + ' ' + str(hex_key) + ' ' + ev_id + ' ' + cs_id
                elif recv_data_list[0] == 'ev_auth_1':
                    send_data = \
                        Authentication.checking_evidtsid(recv_data_list, global_gs_side_cs_database, global_gs_side_id_key_database)
                elif recv_data_list[0] == 'client_terminate':
                    conn.close()
                    break
                elif recv_data_list[0] == 'server_terminate':
                    conn.close()
                    global_server_finish_flag = True
                    break

                conn.sendall(bytes(send_data, 'utf-8'))

    @classmethod
    def grid_server(cls, port):
        global global_server_finish_flag

        print('------------------------------------- GS Installation -------------------------------------')
        print('Server IP: ' + str(cls.__host_ip))
        print('Server Port: ' + str(port))
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((cls.__host_ip, port))
        server.listen(1000)

        while True:
            server.settimeout(0.01)
            try:
                conn, addr = server.accept()
            except socket.timeout:
                if global_server_finish_flag:
                    server.close()
                    break
            else:
                thread = threading.Thread(target=cls.__handle_client, args=(conn,))
                thread.daemon = True
                thread.start()

    @classmethod
    def end_cs_gs_connection(cls, conn):
        send_data = 'client_terminate'
        conn.sendall(bytes(send_data, 'utf-8'))

    @classmethod
    def end_gs_server(cls, port):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((cls.__host_ip, port))
        send_data = 'server_terminate'
        conn.sendall(bytes(send_data, 'utf-8'))

    @classmethod
    def installing_cs(cls, port, cs_id):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((cls.__host_ip, port))
        send_data = 'cs_inst_1 ' + cs_id
        conn.sendall(bytes(send_data, 'utf-8'))
        recv_data = conn.recv(1024).decode('utf-8')
        recv_data_list = recv_data.split()
        challenge = recv_data_list[0]
        temp_cs_id = recv_data_list[1]
        response = Installation.cs_generate_response(challenge, cls.__puf_value)
        cs_loc = 'CANADA_NB_FR_UNB'
        send_data = 'cs_inst_2 ' + response + ' ' + cs_loc + ' ' + temp_cs_id
        conn.sendall(bytes(send_data, 'utf-8'))
        recv_data = conn.recv(1024).decode('utf-8')
        is_cs_installed_ok = False
        if recv_data == 'cs_inst_success':
            is_cs_installed_ok = True

        return conn, cs_id, is_cs_installed_ok

    @classmethod
    def installing_ev(cls, conn, ev_id, cs_id):
        send_data = 'ev_inst_1 ' + ev_id + ' ' + cs_id
        conn.sendall(bytes(send_data, 'utf-8'))
        recv_data = conn.recv(1024).decode('utf-8')
        recv_data_list = recv_data.split()

        is_auth_ok = False
        hex_ev_id = None
        hex_key = None
        ev_id = None
        cs_id = None
        if recv_data_list[0] == 'ev_inst_success':
            hex_ev_id = recv_data_list[1]
            hex_key = recv_data_list[2]
            ev_id = recv_data_list[3]
            cs_id = recv_data_list[4]
            is_auth_ok = True

        return is_auth_ok, hex_ev_id, hex_key, ev_id, cs_id

    @classmethod
    def authenticating_ev(cls, conn, encryption, verification, bin_ev_id, ev_ts, cs_id):
        # cs sends evidtsid from to gs
        send_data = 'ev_auth_1 '
        send_data += encryption + ' ' + verification + ' ' + bin_ev_id + ' ' + ev_ts + ' ' + cs_id + ' '
        conn.sendall(bytes(send_data, 'utf-8'))
        ev_auth_flag = False
        recv_data = conn.recv(1024)
        if len(recv_data) > 1:
            recv_data = recv_data.decode('utf-8')
            recv_data_list = recv_data.split()
            bin_gs_ts = recv_data_list[2]
            gs_ts = int(bin_gs_ts, 2)
            bin_cs_ts = Authentication.get_time_stamp_bin()
            cs_ts = int(bin_cs_ts, 2)
            time_diff = cs_ts - gs_ts
            if time_diff < Authentication.get_time_fresh_limit():
                ev_auth_flag = True

        return ev_auth_flag
