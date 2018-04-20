from pyModbusTCP.client import ModbusClient
import pymysql.cursors
import time

SERVER_HOST = "192.168.2.253"
SERVER_PORT = 502

c = ModbusClient()
c.host(SERVER_HOST)
c.port(SERVER_PORT)



mppt_charge_state_str = ["STRAT",
                         "NIGHT_CHECK",
                         "DISCONNET",
                         "NIGHT",
                         "FAULT",
                         "MPPT",
                         "ABSORPTION",
                         "FLOAT",
                         "EQUALIZE",
                         "SLAVE"]
tmp = []


class Mppt(object):
    """docstring for Mppt"""

    def __init__(self):
        super(Mppt, self).__init__()
        # sca
        self.vpu = 0
        self.ipu = 0

        # batt
        self.battery_voltage = 0
        self.target_voltage = 0
        self.charge_current = 0
        self.charge_state = 0
        self.output_power = 0

        # array
        self.array_voltage = 0
        self.array_current = 0
        self.sweep_vmp = 0
        self.sweep_voc = 0
        self.sweep_pmax = 0

        # temp
        self.battery_temp = 0
        self.headsink_temp = 0

        # log
        self.amp_hours = 0
        self.kw_hours = 0

    def set_dummy(self):
        self.vpu = 0
        self.ipu = 0

        # batt
        self.battery_voltage = 1
        self.target_voltage = 2
        self.charge_current = 3
        self.charge_state = mppt_charge_state_str[3]
        self.output_power = 3

        # array
        self.array_voltage = 3
        self.array_current = 3
        self.sweep_vmp = 3.23
        self.sweep_voc = 3
        self.sweep_pmax = 3

        # temp
        self.battery_temp = 3
        self.headsink_temp = 4

        # log
        self.amp_hours = 4
        self.kw_hours = 4

    def show(self):
        print(self.battery_voltage)
        print(self.target_voltage)
        print(self.charge_current)
        print(self.charge_state)
        print(self.output_power)
        print("")

        # array
        print(self.array_voltage)
        print(self.array_current)
        print(self.sweep_vmp)
        print(self.sweep_voc)
        print(self.sweep_pmax)
        print("")

        # temp
        print(self.battery_temp)
        print(self.headsink_temp)
        print("")

        # log
        print(self.amp_hours)
        print(self.kw_hours)

        print("----------------------------------------")
        print("")


def mysql_insert(mqtt):

    conn = pymysql.connect(host='127.0.0.1',
                           user='root',
                           password='elsys1234',
                           db='mppt_log',
                           charset='utf8mb4')

    time.strftime('%Y-%m-%d %H:%M:%S')
    try:
        with conn.cursor() as cursor:
            sql = """INSERT INTO live_data(U_DT,
                                         BAT_VOLT,
                                         TARGET_VOLT,
                                         CHARGE_CRNT,
                                         CHARGE_STATE,
                                         OUT_PWR,
                                         ARR_VOLT,
                                         ARR_CRNT,
                                         SWEEP_VMP,
                                         SWEEP_VOC,
                                         SWEEP_PMAX,
                                         TEMP_BAT,
                                         TEMP_HEAT_SINK,
                                         RC_AH,
                                         RC_KWH
            ) VALUES ( % s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            cursor.execute(sql, (time.strftime('%Y-%m-%d %H:%M:%S'),
                                 mqtt.battery_voltage,
                                 mqtt.target_voltage,
                                 mqtt.charge_current,
                                 mqtt.charge_state,
                                 mqtt.output_power,

                                 mqtt.array_voltage,
                                 mqtt.array_current,
                                 mqtt.sweep_vmp,
                                 mqtt.sweep_voc,
                                 mqtt.sweep_pmax,

                                 mqtt.battery_temp,
                                 mqtt.headsink_temp,

                                 mqtt.amp_hours,
                                 mqtt.kw_hours,))
            conn.commit()
            print(cursor.lastrowid)
            # 1 (last insert id)
    finally:
        conn.close()


def mppt_parser(mppt):
    global tmp

    tmp = c.read_holding_registers(0, 4)
    mppt.vpu = tmp[0]
    mppt.ipu = tmp[2]

    mppt.battery_voltage = c.read_holding_registers(
        0x26, 1)[0] * mppt.vpu * (2**(-15))
    mppt.target_voltage = c.read_holding_registers(
        0x33, 1)[0] * mppt.vpu * (2**(-15))
    mppt.charge_current = c.read_holding_registers(
        0x27, 1)[0] * mppt.ipu * (2**(-15))
    mppt.charge_state = mppt_charge_state_str[
        c.read_holding_registers(0x32, 1)[0]]
    mppt.output_power = c.read_holding_registers(
        0x3a, 1)[0] * mppt.vpu * mppt.ipu * (2**(-17))

    # array
    mppt.array_voltage = c.read_holding_registers(
        0x1b, 1)[0] * mppt.vpu * (2**(-15))
    mppt.array_current = c.read_holding_registers(
        0x1d, 1)[0] * mppt.ipu * (2**(-15))
    mppt.sweep_vmp = c.read_holding_registers(
        0x3d, 1)[0] * mppt.vpu * (2**(-15))
    mppt.sweep_voc = c.read_holding_registers(
        0x3e, 1)[0] * mppt.vpu * (2**(-15))
    mppt.sweep_pmax = c.read_holding_registers(
        0x3c, 1)[0] * mppt.vpu * mppt.ipu * (2**(-17))

    # temp
    mppt.battery_temp = c.read_holding_registers(0x25, 1)[0]
    mppt.headsink_temp = c.read_holding_registers(0x23, 1)[0]

    # log
    mppt.amp_hours = (c.read_holding_registers(0xe082, 2)[
        1] * 65536 + c.read_holding_registers(0xe082, 2)[0]) * 0.1
    mppt.kw_hours = c.read_holding_registers(0xe086, 1)[0]


if __name__ == "__main__":

    mppt = Mppt()

    while True:
        if not c.is_open():
            if not c.open():
                print("unable to connect to " +
                      SERVER_HOST + ":" + str(SERVER_PORT))

        if c.is_open():
            mppt_parser(mppt)
            mppt.show()
            mysql_insert(mppt)

        # mppt.set_dummy()
        # mysql_insert(mppt)
        # mppt.show()
        
        time.sleep(1)
