#!/usr/bin/env python3.6
# -*- coding:utf-8 -*-

"""
Collect switch connection information.
Copyright (C) 2017-2018 Talen Hao. All Rights Reserved.
"""

import logging
import datetime
import sys
import getopt
import os
import re

import pymysql
import xlsxwriter


import collect_log

__author__ = "Talen Hao(天飞)<talenhao@gmail.com>"
__status__ = "develop"
__create_date__ = "2017/04/21"
__last_date__ = "2017/04/21"
excel_file = '/tmp/%r.xlsx' % sys.argv[0]
LogPath = '/tmp/%s.log.%s' % (sys.argv[0], datetime.datetime.now().strftime('%Y-%m-%d,%H.%M'))
c_logger = collect_log.GetLogger(LogPath, __name__, logging.DEBUG).get_l()
all_args = sys.argv[1:]
usage = '''
用法：
%s [--命令选项] [参数]

命令选项：
    --help, -h              Print this help.
    --version, -V           Show version.
    --logdir, -l <file>     Log file dir.
''' % sys.argv[0]


def help_check(func):
    def _wrapper(*args, **kwargs):
        # run_data_time = time.time()
        # c_logger.info("Current datetime is : %s", datetime.datetime.fromtimestamp(run_data_time))
        if sys.version_info < (2, 7):
            # raise RuntimeError('At least Python 3.4 is required')
            c_logger.warning('友情提示：当前系统版本低于3.6，建议升级python版本。')
        c_logger.info("当前脚本版本信息：%s", __last_date__)
        return func(*args, **kwargs)
    return _wrapper


def spend_time(func):
    def warpper(*args, **kwargs):
        start_time = datetime.datetime.now()
        c_logger.debug("Time start %s", start_time)
        func(*args, **kwargs)
        end_time = datetime.datetime.now()
        c_logger.debug("Time over %s,spend %s", end_time, end_time - start_time)
    return warpper


def get_options():
    if all_args:
        c_logger.debug("命令行参数是 %s", str(all_args))
    else:
        c_logger.error(usage)
        sys.exit()
    log_dir = ''
    try:
        opts, args = getopt.getopt(all_args, "hl:V", ["help", "logdir=", "version"])
    except getopt.GetoptError:
        c_logger.error(usage)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', "--help"):
            c_logger.info(usage)
            sys.exit()
        elif opt in ("-V", "--version"):
            print('Current version is %0.2f' % float(__last_date__))
            c_logger.debug('Version %s', __last_date__)
            sys.exit()
        elif opt in ("-l", "--logdir"):
            c_logger.info("Log file dir is %s", arg)
            log_dir = arg
    c_logger.debug("日志文件目录是%s", log_dir)
    return log_dir


def logs():
    log_list = []
    log_dir = get_options()
    c_logger.debug("log_dir: %r", log_dir)
    for logs in os.walk(log_dir):
        c_logger.debug("logs: %r", logs)
        for log in logs[2]:
            c_logger.debug("log: %r", log)
            log_list.append(log_dir + log)
    c_logger.info("log_list: %r", log_list)
    return log_list


def process_log(log_list):
    switch_neighbor = {}
    for log_file in log_list:
        c_logger.debug(log_file)
        with open(log_file) as logfile:
            c_logger.debug(logfile)
            switch_name = ''
            for line in logfile.readlines():
                c_logger.debug("line: %r", line)
                # 判断是否是已经有switch_name。
                if switch_name == '':
                    # 如果没有switch_name，则先进行switch_name匹配
                    switch_match = re.match(r'<(?P<SN>H3C.+)>', line)
                    c_logger.debug("switch_match: %r", switch_match)
                    if not switch_match:
                        # 没有匹配，不进行收集neighbor操作。
                        continue
                    else:
                        # 出现swithc_name,则收集。
                        switch_name = switch_match.group('SN')
                        c_logger.info("switch_name : %r", switch_name)
                        switch_neighbor[switch_name]=[]
                        c_logger.debug("%r >> switch_neighbor: %r", switch_name, switch_neighbor)
                else:
                    # switch_name已经存在的话，直接进行邻居匹配。
                    neighbor_line = re.match('(^H3C-[\w-]+.*)', line)
                    c_logger.info("%r >> neighbor_line: %r", switch_name, neighbor_line)
                    if neighbor_line:
                        c_logger.info("%r >> neighbor_line_string: %r", switch_name, neighbor_line.group(0).split())
                        system_name, local_interface, chassis_id, port_id = neighbor_line.group(0).split()
                        c_logger.info("%r >> system_name: %r, local_interface: %r, chassis_id: %r, port_id: %r",
                                      switch_name, system_name, local_interface, chassis_id, port_id)
                        switch_neighbor[switch_name].append(
                            {
                                "system_name": system_name,
                                "local_interface": local_interface,
                                "chassis_id": chassis_id,
                                "port_id": port_id}
                        )
    c_logger.debug("%r >> switch_neighbor: %r", switch_name, switch_neighbor)
    return switch_neighbor


class DbInitConnect(object):
    """
    数据库初始化及连接，游标
    """
    def __init__(self):
        self.host = '192.168.1.138'
        self.port = 3306
        self.password = 'yed'
        self.username = 'yed'
        self.db = 'switch_graph'

    # 连接数据库
    def db_connect(self):
        self.connect = pymysql.Connect(host=self.host,
                                       port=self.port,
                                       passwd=self.password,
                                       user=self.username,
                                       database=self.db)
        # 返回指针
        return self.connect

    # 游标
    def db_cursor(self):
        self.cursor = self.db_connect().cursor()
        return self.cursor

    def finally_close_all(self):
        """
        关闭游标，关闭连接。
        """
        self.connect.commit()
        self.cursor.close()
        self.connect.close()

    def show_databases(self):
        cursor = self.db_cursor()
        sql_cmd = 'show create database %s' % self.db
        try:
            cursor.execute(sql_cmd)
        except:
            c_logger.info('数据库连接有问题。')
            sys.exit()
        finally:
            for row in cursor.fetchall():
                c_logger.info(row)


def write_to_open_xlsx(switch_neighbor):
    wb = workbook()
    # 如果使用默认的sheet
    # ws = wb.active
    # 自己创建sheet
    ws = wb.create_sheet("switch_graph", 0)
    # 设置标签背景色
    ws.sheet_properties.tabColor = "1072BA"
    c_logger.debug(wb.sheetnames)


def write_to_excel(switch_neighbor):
    relation_title = ("Group", "Node", "source", "target")
    # Create a workbook and add a worksheet.
    workbook = xlsxwriter.Workbook(excel_file)
    c_logger.debug(workbook)
    worksheet = workbook.add_worksheet()
    c_logger.debug(worksheet)
    # Some data we want to write to the worksheet.
    # Start from the first cell. Rows and columns are zero indexed.
    row = 0
    col = 0
    st_row = 0
    st_col = 2
    for i in range(len(relation_title)):
        worksheet.write(row, col+i, relation_title[i])
    row += 1
    st_row += 1
    c_logger.debug("row: %r", row)
    interface_list = []
    for switch, neighbor in switch_neighbor.items():
        # neighbor是list
        worksheet.write(row, col+1, switch)
        row += 1
        for n in range(len(neighbor)):
            neighbor_sw = neighbor[n-1]["system_name"]
            sw_if = switch+":"+neighbor[n-1]["local_interface"]
            sw_con_if = neighbor_sw+":"+neighbor[n-1]["port_id"].replace('GigabitEthernet', 'GE')
            c_logger.debug(sw_if)
            c_logger.debug(sw_con_if)
            worksheet.write(st_row, st_col, sw_if)
            worksheet.write(st_row, st_col+1, sw_con_if)
            st_row += 1
            if sw_if not in interface_list:
                interface_list.append(sw_if)
                worksheet.write(row, col, switch)
                worksheet.write(row, col+1, sw_if)
                row += 1
            if sw_con_if not in interface_list:
                interface_list.append(sw_con_if)
                worksheet.write(row, col, neighbor_sw)
                worksheet.write(row, col+1, sw_con_if)
                row += 1
    workbook.close()


@spend_time
@help_check
def main():
    log_list = logs()
    switch_neighbor = process_log(log_list)
    c_logger.info("switch_neighbor >>>>> finally is :%r", switch_neighbor)
    write_to_excel(switch_neighbor)


if __name__ == "__main__":
    main()