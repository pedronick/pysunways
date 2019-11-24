"""PySunways interacts as a library to communicate with Sunways inverters"""
import aiohttp
import asyncio
import concurrent
import csv
from io import StringIO
from datetime import date
import logging
import xml.etree.ElementTree as ET

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
                Sensor("p-ac", 11, 23, "", "current_power", "W"),
                Sensor("c-grid", 11, 23, "", "grid_current", "A"),
                Sensor("c-generator", 11, 23, "", "generator_current", "A"),
                Sensor("v-grid", 11, 23, "", "grid_voltage", "V"),
                Sensor("v-generator", 11, 23, "", "generator_voltage", "V"),
                Sensor("temp", 20, 32, "/10", "temperature", "°C"),
                
                Sensor("e-today", 3, 3, "/100", "today_yield", "kWh", True),
                Sensor("e-Month", 3, 3, "/100", "month_yield", "kWh", True),
                Sensor("e-year", 3, 3, "/100", "year_yield", "kWh", True),         
                Sensor("e-total", 1, 1, "/100", "total_yield", "kWh", False,True),
                Sensor("s-Message", 22, 34, "", "state_Message")
                Sensor("s-OutMode", 22, 34, "", "state_OutputMode")
                Sensor("s-OpMode", 22, 34, "", "state_OperatingMode")
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
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout,
                                             raise_for_status=True) as session:
                auth = aiohttp.auth.DigestAuth(self.username,self.password,session)
                #https://github.com/aio-libs/aiohttp/pull/2213
                #https://https://github.com/aio-libs/aiohttp/pull/2213/files/26a6064e3e742b84e64a51cd9df3f03cca5466aa
                #riga 1481
                
                current_url = self.url
                async with auth.get(current_url) as response:
                    data = await response.text()

                    #data="0.04 kW#0.2#226.3#0.1#350.3#---#---#10.42#138.2#2010.7#16147.1#4#0#0#0#"
                    #if len(data.split(#)) > 15 :
                    power, netCurrent, netVoltage, genCurrent, genVoltage,Temperature,irradiation,dayEnergy,monthEnergy,yearEnergy,totalEnergy,val1,val2,val3,val4,val5= data.split('#')

                   # csv_data = StringIO(data)
                    #reader = csv.reader(csv_data)
                    #ncol = len(next(reader))
                    #csv_data.seek(0)

                    #values = []

                    #for row in reader:
                    #    for (i, v) in enumerate(row):
                    #        values.append(v)

                    for sen in sensors:
                        if sen.name == "current_power":
                            sen.value = eval(
                                "{0}{1}".format(power[:-2], sen.factor)
                            )
                        if sen.name == "grid_current":
                            sen.value = eval(
                                "{0}{1}".format(netCurrent, sen.factor)
                            )      
                        if sen.name == "generator_current":
                            sen.value = eval(
                                "{0}{1}".format(genCurrent, sen.factor)
                            )      
                        if sen.name == "grid_voltage":
                            sen.value = eval(
                                "{0}{1}".format(netVoltage, sen.factor)
                            )      
                        if sen.name == "generator_voltage":
                            sen.value = eval(
                                "{0}{1}".format(genVoltage, sen.factor)
                            )      
                        if sen.name == "temperature":
                            sen.value = eval(
                                "{0}{1}".format(Temperature, sen.factor)
                            )      
                        if sen.name == "today_yield":
                            sen.value = eval(
                                "{0}{1}".format(dayEnergy, sen.factor)
                            )      
                        if sen.name == "month_yield":
                            sen.value = eval(
                                "{0}{1}".format(monthEnergy, sen.factor)
                            )      
                        if sen.name == "year_yield":
                            sen.value = eval(
                                "{0}{1}".format(yearEnergy, sen.factor)
                            )      
                        if sen.name == "total_yield":
                            sen.value = eval(
                                "{0}{1}".format(totalEnergy, sen.factor)
                            )      
                            
                        if sen.name == "state":
                            sen.value = MAPPER_STATES[v]
               
                        sen.date = date.today()
                   

                    _LOGGER.debug("Got new value for sensor %s: %s",
                                  sen.name, sen.value)

                    return True
        except (aiohttp.client_exceptions.ClientConnectorError,
                concurrent.futures._base.TimeoutError):
            # Connection to inverter not possible.
            # This can be "normal" - so warning instead of error - as Sunways
            # inverters auto switch off after the sun
            # has set.
            _LOGGER.warning("Connection to Sunways inverter is not possible. " +
                            "The inverter may be offline due to darkness. " +
                            "Otherwise check host/ip address.")
            return False
        except aiohttp.client_exceptions.ClientResponseError as err:
            # 401 Unauthorized: wrong username/password
            if err.status == 401:
                raise UnauthorizedException(err)
            else:
                raise UnexpectedResponseException(err)
        except csv.Error:
            # CSV is not valid
            raise UnexpectedResponseException(
                str.format("No valid CSV received from {0} at {1}", self.host,
                           current_url)
            )
        except IndexError:
            # CSV received does not have all the required elements
            raise UnexpectedResponseException(
                str.format(
                    "Sunways sensor name {0} at CSV position {1} not found, " +
                    "inverter not compatible?",
                    sen.name,
                    sen.csv_1_key if ncol < 24 else sen.csv_2_key
                )
            )


class UnauthorizedException(Exception):
    """Exception for Unauthorized 401 status code"""
    def __init__(self, message):
        Exception.__init__(self, message)


class UnexpectedResponseException(Exception):
    """Exception for unexpected status code"""
    def __init__(self, message):
        Exception.__init__(self, message)
