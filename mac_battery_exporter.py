import json
import subprocess
import time
from distutils import util

from prometheus_client import start_http_server
from prometheus_client.core import REGISTRY, GaugeMetricFamily


class Battery():
    """Class for retrieving and returning SPPowerDataType data
    from system_profiler in a Prometheus-friendly format"""

    def getData(self):
        """Fetch data from system_profiler"""
        powerdata = subprocess.run(["system_profiler", "SPPowerDataType", "-json"], stdout=subprocess.PIPE)
        return json.loads(powerdata.stdout)["SPPowerDataType"]

    def returnData(self):
        """Return a list of key-value pairs to iterate over"""
        data_list = []
        spbattery_information = self.getData()[0]

        for key, val in spbattery_information["sppower_battery_health_info"].items():
            # Really hackish way of skipping past sppower_battery_health, because I have no idea
            # how many states there are and how to convert them
            if key == "sppower_battery_health":
                continue

            # Maximum capacity has a % suffix that Prometheus doesn't like
            if key == "sppower_battery_health_maximum_capacity":
                if val.endswith("%"):
                    val = val[:-1]
            data_list.append({key: val})

        for key, val in spbattery_information["sppower_battery_charge_info"].items():
            # We need to convert string bool to a numeric value for the two keys below
            if key in ["sppower_battery_is_charging", "sppower_battery_fully_charged", "sppower_battery_at_warn_level"]:
                val = util.strtobool(val)
            data_list.append({key: val})

        if "sppower_current_amperage" in spbattery_information:
            data_list.append({"sppower_current_amperage": spbattery_information["sppower_current_amperage"]})
        if "sppower_current_voltage" in spbattery_information:
            data_list.append({"sppower_current_voltage": spbattery_information["sppower_current_voltage"]})

        return data_list


class CustomCollector(object):
    def __init__(self):
        pass

    def collect(self):
        battery = Battery()
        sppower = battery.returnData()

        for item in sppower:
            for metric_name, metric_value in item.items():
                g = GaugeMetricFamily(metric_name, "")
                g.add_metric([], metric_value)
                yield g


if __name__ == "__main__":
    start_http_server(8333)
    REGISTRY.register(CustomCollector())
    while True:
        time.sleep(1)
