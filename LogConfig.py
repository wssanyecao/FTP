#!/bin/env python3
# -*- coding=utf-8 -*-

import os
import datetime
import logging
import logging.handlers

class LogConfig:
	def __init__(self, log_level='INFO'):
		self._log_level = log_level

	def get_console_logger(self):
		def _gen_file_logger_handler():
			_handler = logging.StreamHandler()
			# formatter = logging.Formatter(
			# 	"[%(asctime)s %(msecs)03d][%(process)d][tid=%(thread)d][%(name)s][%(levelname)s] %(message)s [%(filename)s"
			# 	" %(funcName)s %(lineno)s] ", datefmt="%Y-%m-%d %H:%M:%S")
			# [2020-06-16 11:35:06 884][26508][tid=30280][20200616.log][INFO] print by info [LogConfig.py <module> 79]
			formatter = logging.Formatter(
				"[%(asctime)s][%(levelname)s] %(message)s [%(filename)s %(funcName)s %(lineno)s]"
				)
			# [2020-06-16 12:01:37,656 656][INFO] print by info [LogConfig.py <module> 85]
			# _handler.setLevel(getattr(logging, self._log_level.upper()))	# 在这里设置不起作用
			# _handler.setLevel(getattr(logging, _log_level.upper()) if hasattr(logging, set_level.upper()) else logging.INFO)  # 设置日志级别
			_handler.setFormatter(formatter)
			return _handler
		def _gen_console_logger():
			# 解决第一个问题--logging.basicConfig()会影响被调用库的日志--getLogger时给定一个名称而不是直接获取根logger
			_console_logger = logging.getLogger("console")
			_console_logger.addHandler(handler)
			return _console_logger

		handler = _gen_file_logger_handler()
		console_logger = _gen_console_logger()
		console_logger.setLevel(getattr(logging, self._log_level.upper()))
		return console_logger

	def get_file_logger(self,log_file_name=None):
		def _make_sure_log_dir_exist():
			if not os.path.isdir(log_file_dir):
				os.mkdir(log_file_dir)
		def _gen_file_logger_handler():
			# 操作系统本身不允许文件名包含:等特殊字符，所以这里也不要用，不然赋给filename时会报错
			# nowTime = datetime.datetime.now().strftime('%Y-%m-%d')
			file_path = f'{log_file_dir}/{log_file_name}'
			# formatter = logging.Formatter(
			# 	"[%(asctime)s %(msecs)03d][%(process)d][tid=%(thread)d][%(name)s][%(levelname)s] %(message)s [%(filename)s"
			# 	" %(funcName)s %(lineno)s] ", datefmt="%Y-%m-%d %H:%M:%S")
			# [2020-06-16 11:35:06 884][26508][tid=30280][20200616.log][INFO] print by info [LogConfig.py <module> 79] 
			formatter = logging.Formatter(
				"[%(asctime)s][%(levelname)s] %(message)s [%(filename)s %(funcName)s %(lineno)s]"
				)
			# 日志会不断增大需要手动去清理--使用TimedRotatingFileHandler等替换FileHandler
			# filename----日志文件
			# when----更换日志文件的时间单位
			# interval----更换日志文件的时间单位个数；这里是7天换一个文件
			# backupCount----保存的旧日志文件个数；这里即只保留上一个日志文件
			# encoding----日志文件编码
			_handler = logging.handlers.TimedRotatingFileHandler(filename=file_path,when='D',interval=7,backupCount=5,encoding='utf-8')
			# 实际发现有些时候这里setLevel并不起作用
			# _handler.setLevel(logging.INFO)
			_handler.setFormatter(formatter)
			return _handler
		def _gen_file_logger():
			# 解决第二个问题--不能定义多个日志文件--getLogger时给定一个名称而不是直接获取根logger
			_file_logger = logging.getLogger(log_file_name)
			_file_logger.addHandler(handler)
			return _file_logger

		log_file_dir = "log"
		if log_file_name == None:
			log_file_name = datetime.datetime.now().strftime('%Y%m%d') + ".log"
		_make_sure_log_dir_exist()
		handler = _gen_file_logger_handler()
		file_logger = _gen_file_logger()
		# 实际发现有些时候handler的setLevel并不起作用，要在这里setLevel
		file_logger.setLevel(getattr(logging, self._log_level.upper()))
		return file_logger

	def get_console_and_file_logger(self,log_file_name=None):
		log_file_dir = "log"
		if log_file_name == None:
			log_file_name = datetime.datetime.now().strftime('%Y%m%d') + ".log"
		if not os.path.isdir(log_file_dir):
			os.mkdir(log_file_dir)
		file_path = f'{log_file_dir}/{log_file_name}'
		formatter = logging.Formatter(
				"[%(asctime)s][%(levelname)s] %(message)s [%(filename)s %(funcName)s %(lineno)s]"
				)
		console_handler = logging.StreamHandler()
		console_handler.setFormatter(formatter)
		file_handler = logging.handlers.TimedRotatingFileHandler(filename=file_path,when='D',interval=7,backupCount=5,encoding='utf-8')
		file_handler.setFormatter(formatter)
		console_file_logger = logging.getLogger(log_file_name)
		console_file_logger.addHandler(console_handler)
		console_file_logger.addHandler(file_handler)
		console_file_logger.setLevel(getattr(logging,self._log_level.upper()))
		return console_file_logger

# if __name__ == "__main__":
# 	# log_type = "console"
# 	# logger = LogConfig().get_console_logger()
# 	# log_type = "file"
# 	# log_file_name不同，返回的是不同的logger，这样就可以方便地定义多个logger
# 	log_file_name = datetime.datetime.now().strftime('%Y%m%d') + ".log"
# 	# logger = LogConfig().get_file_logger(log_file_name)
# 	logger = LogConfig().get_console_logger()
# 	logger.debug('print by debug')
# 	logger.info('print by info')
# 	logger.warning('print by warning')
