import datetime
import hashlib
import random


class Crypto:
    @classmethod
    def change_string_to_bit(cls, string):
        return ''.join(format(ord(i), '08b') for i in str(string))

    @classmethod
    def get_hex_to_bin(cls, hex, size):
        temp = int(str(hex), 16)
        temp = format(temp, 'b')
        temp = temp.zfill(size)
        return temp

    @classmethod
    def calculate_xor_two_strings(cls, str_1, str_2):
        temp = [ord(a) ^ ord(b) for a, b in zip(str_1, str_2)]
        temp = ''.join(str(s) for s in temp)
        return temp

    @classmethod
    def get_time_stamp_bin(cls):
        temp = round(datetime.datetime.now().timestamp())
        temp = cls.change_string_to_bit(temp)
        temp = temp.zfill(32)
        return temp

    @classmethod
    def calculate_hash(cls, string):
        temp = hashlib.sha256(string.encode())
        return temp.hexdigest()

    @classmethod
    def get_bin_to_hex(cls, bin_string, size=64):
        temp = int(bin_string, 2)
        temp = str(hex(temp))[2:]
        temp = temp.zfill(size)
        return temp


class Installation(Crypto):
    @classmethod
    def cs_generate_response(cls, challenge, puf_value):
        response = int(challenge) + puf_value
        return str(response)

    @classmethod
    def gs_generate_ev_id_and_key(cls, old_ev_id):
        rand = str(random.randrange(10000000, 99999999))
        temp_id_key = rand + old_ev_id
        secret_key = cls.calculate_hash(temp_id_key)
        temp_ev_id_key = secret_key + old_ev_id
        new_ev_id = cls.calculate_hash(temp_ev_id_key)

        return secret_key, new_ev_id

    @classmethod
    def gs_generate_challenge(cls):
        challenge = random.randrange(1000000000000000, 9999999999999999)
        return str(challenge)


class Authentication(Crypto):
    __time_fresh_limit = 5

    @classmethod
    def get_time_fresh_limit(cls):
        return cls.__time_fresh_limit

    @classmethod
    def get_evidts(cls, hex_ev_id, hex_key):
        ev_loc = 'CANADA_NB_FR_UNB'
        ev_data = random.randrange(1000000000000000, 9999999999999999)
        ev_loc_data = ev_loc + str(ev_data)
        bin_ev_loc_data = cls.change_string_to_bit(ev_loc_data)
        bin_secret_key = cls.get_hex_to_bin(hex_key, 256)
        bin_encryption = cls.calculate_xor_two_strings(bin_ev_loc_data, bin_secret_key)
        bin_ev_loc_data = cls.change_string_to_bit(ev_loc_data)
        bin_ev_id = cls.get_hex_to_bin(hex_ev_id, 256)
        bin_ts = cls.get_time_stamp_bin()
        temp_verification = bin_ev_loc_data + bin_secret_key + bin_ev_id + bin_ts
        temp_verification = cls.calculate_hash(temp_verification)
        bin_verification = cls.get_hex_to_bin(temp_verification, 256)

        return bin_encryption, bin_verification, bin_ev_id, bin_ts

    @classmethod
    def cs_check_fresh(cls, bin_time_stamp):
        ev_ts = int(bin_time_stamp, 2)
        cv_ts = cls.get_time_stamp_bin()
        cv_ts = int(cv_ts, 2)
        time_diff = cv_ts - ev_ts
        fresh = False
        if cls.__time_fresh_limit > time_diff:
            fresh = True

        return fresh

    @classmethod
    def checking_evidtsid(cls, recv_data_list, gs_side_cs_database, gs_side_ev_id_key_database):
        bin_encryption = recv_data_list[1]
        bin_verification = recv_data_list[2]
        bin_ev_id = recv_data_list[3]
        bin_ev_ts = recv_data_list[4]
        cs_id = recv_data_list[5]

        send_data = ' '
        if cs_id in gs_side_cs_database:
            ev_ts = int(bin_ev_ts, 2)
            gs_ts = int(cls.get_time_stamp_bin(), 2)
            time_diff = gs_ts - ev_ts
            if time_diff < cls.__time_fresh_limit:
                hex_ev_id = cls.get_bin_to_hex(bin_ev_id, 64)
                if hex_ev_id in gs_side_ev_id_key_database:
                    hex_key = gs_side_ev_id_key_database[hex_ev_id]
                    bin_key = cls.get_hex_to_bin(hex_key, 256)
                    bin_loc_data = cls.calculate_xor_two_strings(bin_encryption, bin_key)
                    loc_data_key_id_ts = bin_loc_data + bin_key + bin_ev_id + bin_ev_ts
                    hex_verification = cls.calculate_hash(loc_data_key_id_ts)
                    gs_bin_verification = cls.get_hex_to_bin(hex_verification, 256)
                    if gs_bin_verification == bin_verification:
                        crloc = gs_side_cs_database[cs_id]
                        challenge = crloc[0]
                        response = crloc[1]
                        crts = challenge + response + str(gs_ts)
                        gs_hex_verification = cls.calculate_hash(crts)
                        send_data = \
                            str(gs_hex_verification) + ' ' + str(challenge) + ' ' + str(cls.get_time_stamp_bin())

        return send_data
