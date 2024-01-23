token = "secret-token"
url = "rancher-urk"

import re

from pkg_resources import compatible_platforms

print("Testing...")

def compareResource(limit, value):
    def compareRAM(a,b):
        a = re.match(r'([\d]*)([\w]*)', a).groups()
        b = re.match(r'([\d]*)([\w]*)', b).groups()
        if a[1]==b[1]:
            print(f"{a=} == {b=}")
            if int(a[0])>int(b[0]):
                return False
        elif a[1]>b[1]:
            print(f"{a=} > {b=}")
            if int(a[0])>int(b[0])*1024:
                return False
        else:
            print(f"{a=} < {b=}")
            if int(a[0])*1024>int(b[0]):
                return False
        return True
    diffCPU=limit["cpu"]<=value["cpu"]
    diffRAM=compareRAM(limit["memory"],value["memory"])
    return diffCPU&diffRAM, {"cpu": diffCPU, "memory": diffRAM, "input": (limit,value)}

d1 = ({'cpu': '2', 'memory': '50000Mi'}, {'cpu': '4', 'memory': '65000Mi'})
d2 = ({'cpu': '2', 'memory': '50000Mi'}, {'cpu': '4', 'memory': '40Gi'})
d3 = ({'cpu': '2', 'memory': '50Gi'}, {'cpu': '4', 'memory': '55000Mi'})

print(compareResource(*d1))
print(compareResource(*d2))
print(compareResource(*d3))