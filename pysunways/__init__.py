"""PySunways interacts as a library to communicate with Sunways inverters"""

import asyncio
import httpx
import concurrent
from datetime import date
import logging
import requests_async as requests
from httpx import DigestAuth
from requests.auth import HTTPDigestAuth

# from pip._vendor import requests

_LOGGER = logging.getLogger(__name__)

INVERTER_MODEL = {
    "0": "AT2700",
    "1": "AT3600",
    "2": "AT4500",
    "3": "AT5000",
    "7": "AT3000",
}

MESSAGES_STATES = {
    "0": "Error",
    "1": "Warnings",
}

OUTPUTMODE_STATES = {
    "0": "MPP",
    "1": "DC current limitation",
    "2": "AC current limitation",
    "3": "AC output limitation",
    "4": "Temperature limitation",
}

OPERATINGMODE_STATES = {
    "0": "Start",
    "1": "Feed",
    "2": "Night",
    "3": "Test active",
}

URL_PATH = "/data/inverter.txt"


class Sensor(object):
    """Sensor definition"""

    def __init__(self, key, csv_1_key, csv_2_key, factor, name, unit='',
                 per_day_basis=False, per_total_basis=False):
        self.key = key
        self.csv_1_key = csv_1_key
        self.csv_2_key = csv_2_key
        self.factor = factor
        self.name = name
        self.unit = unit
        self.value = None
        self.per_day_basis = per_day_basis
        self.per_total_basis = per_total_basis
        self.date = date.today()


class Sensors(object):
    """Sunways sensors"""

    def __init__(self):
        self.__s = []
        self.add(
            (
                Sensor("p-ac", 11, 23, "", "current_power", "W")
                , Sensor("c-grid", 11, 23, "", "grid_current", "A")
                , Sensor("c-generator", 11, 23, "", "generator_current", "A")
                , Sensor("v-grid", 11, 23, "", "grid_voltage", "V")
                , Sensor("v-generator", 11, 23, "", "generator_voltage", "V")
                , Sensor("temp", 20, 32, "/10", "temperature", "°C")

                # ,Sensor("e-today", 3, 3, "/100", "today_yield", "kWh", True)
                # ,Sensor("e-Month", 3, 3, "/100", "month_yield", "kWh", True)
                # ,Sensor("e-year", 3, 3, "/100", "year_yield", "kWh", True)
                # ,Sensor("e-total", 1, 1, "/100", "total_yield", "kWh", False,True)
                # ,Sensor("s-Message", 22, 34, "", "state_Message")
                # ,Sensor("s-OutMode", 22, 34, "", "state_OutputMode")
                # ,Sensor("s-OpMode", 22, 34, "", "state_OperatingMode")
            )
        )

    def __len__(self):
        """Length."""
        return len(self.__s)

    def __contains__(self, key):
        """Get a sensor using either the name or key."""
        try:
            if self[key]:
                return True
        except KeyError:
            return False

    def __getitem__(self, key):
        """Get a sensor using either the name or key."""
        for sen in self.__s:
            if sen.name == key or sen.key == key:
                return sen
        raise KeyError(key)

    def __iter__(self):
        """Iterator."""
        return self.__s.__iter__()

    def add(self, sensor):
        """Add a sensor, warning if it exists."""
        if isinstance(sensor, (list, tuple)):
            for sss in sensor:
                self.add(sss)
            return

        if not isinstance(sensor, Sensor):
            raise TypeError("pysunways.Sensor expected")

        if sensor.name in self:
            old = self[sensor.name]
            self.__s.remove(old)
            _LOGGER.warning("Replacing sensor %s with %s", old, sensor)

        if sensor.key in self:
            _LOGGER.warning("Duplicate Sunways sensor key %s", sensor.key)

        self.__s.append(sensor)


class Sunways(object):
    """Provides access to Sunways inverter data"""

    def __init__(self, host, username='customer', password='********'):
        self.host = host
        self.username = username
        self.password = password
        self.serialnumber = "XXXXXXXXXXXXXXXXX"

        self.url = "http://{0}/".format(self.host)
        self.url += URL_PATH

    async def read(self, sensors):
        """Returns necessary sensors from Sunways inverter"""

        try:
            print("ciao")
            #async with requests.Session() as session:


            current_url = self.url
            data = await httpx.get(current_url,  auth = DigestAuth(username=self.username, password=self.password), timeout=2)
            #    async with session.get(current_url, auth=HTTPDigestAuth(self.username, self.password), timeout=5) as response:
                #async with session.get(current_url) as response:
            #        data = await response.text()

                    # data="0.04 kW#0.2#226.3#0.1#350.3#---#---#10.42#138.2#2010.7#16147.1#4#0#0#0#"
                    # if len(data.split(#)) > 15 :
            power, netCurrent, netVoltage, genCurrent, \
            genVoltage, Temperature, irradiation, dayEnergy, \
            monthEnergy, yearEnergy, totalEnergy, val1, val2, \
            val3, val4, val5 = data.split('#')

            for sen in sensors:
                if sen.name == "current_power":
                    sen.value = eval(
                        "{0}{1}".format(power[:-2], sen.factor)
                    )
                else:
                    if sen.name == "grid_current":
                        sen.value = eval(
                            "{0}{1}".format(netCurrent, sen.factor)
                        )
                    else:
                        if sen.name == "generator_current":
                            sen.value = eval(
                                "{0}{1}".format(genCurrent, sen.factor)
                            )
                        else:
                            if sen.name == "grid_voltage":
                                sen.value = eval(
                                    "{0}{1}".format(netVoltage, sen.factor)
                                )
                            else:
                                if sen.name == "generator_voltage":
                                    sen.value = eval(
                                        "{0}{1}".format(genVoltage, sen.factor)
                                    )
                                else:
                                    if sen.name == "temperature":
                                        sen.value = eval(
                                            "{0}{1}".format(Temperature, sen.factor)
                                        )
                                    else:
                                        if sen.name == "today_yield":
                                            sen.value = eval(
                                                "{0}{1}".format(dayEnergy, sen.factor)
                                            )
                                        else:
                                            if sen.name == "month_yield":
                                                sen.value = eval(
                                                    "{0}{1}".format(monthEnergy, sen.factor)
                                                )
                                            else:
                                                if sen.name == "year_yield":
                                                    sen.value = eval(
                                                        "{0}{1}".format(yearEnergy, sen.factor)
                                                    )
                                                else:
                                                    if sen.name == "total_yield":
                                                        sen.value = eval(
                                                            "{0}{1}".format(totalEnergy, sen.factor)
                                                        )
                                                # else:
                                                #     raise KeyError

                # if sen.name == "state":
                #     sen.value = MAPPER_STATES[v]

                sen.date = date.today()

            _LOGGER.debug("Got new value for sensor %s: %s",
                          sen.name, sen.value)
            print("ciao")
            return True
        except ():
            return False


#       except (requests.client_exceptions.ClientConnectorError,
#               concurrent.futures._base.TimeoutError):
# Connection to inverter not possible.
# This can be "normal" - so warning instead of error - as Sunways
# inverters auto switch off after the sun
# has set.
#           _LOGGER.warning("Connection to Sunways inverter is not possible. " +
#                           "The inverter may be offline due to darkness. " +
#                           "Otherwise check host/ip address.")
#           return False
#       except requests.client_exceptions.ClientResponseError as err:
# 401 Unauthorized: wrong username/password
#           if err.status == 401:
#               raise UnauthorizedException(err)
#           else:
#               raise UnexpectedResponseException(err)
#       except KeyError:
# requested sensor not supported
#           raise UnexpectedResponseException(
#               str.format("Sunways sensor key {0} not found, inverter not " +
#                          "compatible?", sen.key)
#           )


class UnauthorizedException(Exception):
    """Exception for Unauthorized 401 status code"""

    def __init__(self, message):
        Exception.__init__(self, message)


class UnexpectedResponseException(Exception):
    """Exception for unexpected status code"""

    def __init__(self, message):
        Exception.__init__(self, message)


def handle_exception(loop, context): #loop context):
    # context["message"] will always be there; but context["exception"] may not
    msg = context.get("exception", context["message"])


async def main():
    sen = Sensors()
    sw = Sunways("192.168.30.50")
    await sw.read(sen)
    #loop = asyncio.get_event_loop()
    #loop.set_exception_handler(handle_exception)
    #loop.run_until_complete(sw.read(sen))
    #loop.close()



if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)
    #asyncio.run(main())#, debug=True)
    loop.run_until_complete(main())

