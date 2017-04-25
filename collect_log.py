#!/usr/bin/env python
# -*- coding:UTF-8 -*-

import logging

__author__ = "Talen Hao(天飞)<talenhao@gmail.com>"
__status__ = "product"
__version__ = "2017.04.17"
__create_date__ = "2017/02/20"
__last_date__ = "2017/04/17"


class GetLogger:
    def __init__(self, log_path, logger_name, logging_level):
        self.log_path = log_path
        self.logger_name = logger_name
        self.logging_level = logging_level
        self.agent_logger = logging.getLogger(self.logger_name)
        self.agent_logger.setLevel(self.logging_level)

        # agent_logger.error('Failed to open file', exc_info=True)
    def get_l(self):
        # logging.config.fileConfig('logging.conf')

        # create root logger
        # logging.basicConfig(level=logging.NOTSET)

        # 创建file handler,写入日志文件
        logfile_handler = logging.FileHandler(self.log_path)
        logfile_handler.setLevel(logging.DEBUG)
        # 创建console handler 同时输出到stdout
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 创建formatter
        logfile_fmt_str = '%(asctime)-15s %(levelname)-5s ScriptFile: %(filename)s Funcation: %(funcName)s ' \
                          '+%(lineno)d [%(threadName)s] %(message)s'
        logfile_formatter = logging.Formatter(logfile_fmt_str)
        console_fmt_str = "%(asctime)-15s %(levelname)-5s %(threadName)s %(message)s"
        console_formatter = logging.Formatter(console_fmt_str)

        # handler set formatter
        logfile_handler.setFormatter(logfile_formatter)
        console_handler.setFormatter(console_formatter)

        # add handler and formatter to logger
        self.agent_logger.addHandler(logfile_handler)
        self.agent_logger.addHandler(console_handler)
        return self.agent_logger
