#!/bin/python

import re
import time

class QSLog():
    '''The QS Logging Mechanism

    Logs data and writes them to console. Returning API data for REST API Calls.
    
    '''
    
    def __init__(self) -> None:
        self.__fail_log = []
        self.__warn_log = []
        self.__success_log = []
        self.__info_log = []
        self.__lastRun = 0

    @property
    def fails(self):
        return self.__fail_log

    @property
    def warn(self):
        return self.__warn_log
    
    @property
    def success(self):
        return self.__success_log
    
    @property
    def info(self):
        return self.__info_log

    @property
    def lastRun(self):
        return self.__lastRun

    @property
    def total(self):
        return len(self.__fail_log) + len(self.__warn_log) + len(self.__success_log)
    
    def write(self, log:str):
        '''
        Write the result to Console and store the information in a list separating by type

        Params
        ------
        log : str
            the log to write. Color encoded...
        
        Raises
        ------
        NotImplementedError
            The Log Format does not exist. Must be in OK, Warn, Failed...
        '''
        print(log)
        log = log.split("\t")
        description = re.search(r'[^m]m(.*?)\x1b', log[0]).groups()[0].lower()
        event = log[-1]
        if description == "failed":
            self.__fail_log.append(event)
        elif description == "warn":
            self.__warn_log.append(event)
        elif description ==  "ok":
            self.__success_log.append(event)
        elif description == "info":
            self.__info_log.append(event)
        else:
            raise NotImplementedError("{} not a valid identifier".format(description))
    
    def summarize(self):
        '''
        Pretty Print the Faillog to Console
        '''

        self.__lastRun = time.time()
        print("\n{}".format("".join(["*" for i in range(28)])))
        print("\nSummary")
        print("\n{}".format("".join(["-" for i in range(28)])))
        print(f"tests failed\t\t|{len(self.__fail_log):3}")
        print(f"tests warned\t\t|{len(self.__warn_log):3}")
        print(f"tests succeeded\t\t|{len(self.__success_log):3}")
        print("{}".format("".join(["-" for i in range(28)])))
        print(f"total tests\t\t|{self.total:3}")
        print(f"\nTests ran {time.strftime('%a, %d.%m.%y %H:%M:%S')}")
        print("\n{}".format("".join(["*" for i in range(28)])))