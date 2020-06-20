#!/bin/env python3
# -*- coding=utf-8 -*-

from LogConfig import LogConfig
import os
import sys
import ftplib
import time
from ftplib import FTP_TLS
import ssl
import socket

log = LogConfig(log_level='INFO').get_console_and_file_logger()		# 输出到控制台与文件
# log = LogConfig(log_level='INFO').get_console_logger()			# 输出到控制台
# log = LogConfig(log_level='INFO').get_file_logger()				# 输出到日志文件

class FtpTLS(FTP_TLS):
	"""Ftp 使用 TLS"""
	def connect(self,host='',port=0,timeout=-999):
		if host != '':
			self.host = host
		if port > 0:
			self.port = port
		if timeout !=-999:
			self.timeout = timeout
		self.sock = socket.create_connection((self.host,self.port),self.timeout)
		self.af = self.sock.family
		try:
			# TSL 证书错误
			# [SSL: WRONG_VERSION_NUMBER] wrong version number (_ssl.c:1076)
			# self.sock = ssl.wrap_socket(self.sock, self.keyfile, self.certfile,ssl_version=ssl.PROTOCOL_SSLv23)
			self.sock = ssl.wrap_socket(self.sock, self.keyfile, self.certfile,ssl_version=ssl.PROTOCOL_TLSv1)
		except Exception as e:
			log.error("FtpTLS 连接失败 异常: %s" % e)
		self.file = self.sock.makefile('rb')
		self.welcome = self.getresp()
		return self.welcome


class FtpClass:	
	def __init__(self, host, port,username,pwd):
		self.host = host
		self.port = port
		self.username = username
		self.pwd = pwd
		self.ftp = self.ftp_connect()
		log.info(self.ftp.welcome)
		

	def ftp_tls_connect(self,FtpTLSClass=FtpTLS):
		ftp = FtpTLSClass()
		try:
			ftp.connect(self.host,self.port,120)
			log.info("ftp tls connect success")
		except Exception as e:
			log.error("ftp tls connect failed")
			sys.exit()
		try:
			ftp.login(self.username,self.pwd)
			ftp.prot_p()
			log.info("ftp login success")
		except Exception as e:
			log.error("ftp login failed -- %s" % e )
			sys.exit()
		return ftp


	def ftp_connect(self,init=True):
		# timeOut = -999
		# socket.setdefaulttimeout(timeOut)
		ftp = ftplib.FTP()
		ftp.encoding = "utf-8"	# GB18030 GBK
		# ftp.set_debuglevel(2) #打开调试级别2，显示详细信息
		# ftp.set_pasv(0)      #0主动模式 1 #被动模式
		if init:
			try:
				ftp.connect(self.host,self.port)
				# ftp.connect(self.host,self.port,30)
				log.info("ftp 连接成功 %s:%s" % (self.host,self.port))
			except Exception as e:
				log.error("ftp 连接失败 %s:%s 异常: %s" % (self.host,self.port,e))
				sys.exit()
			try:
				ftp.login(self.username,self.pwd)
				log.info("ftp 登陆成功 %s %s" % (self.username,self.pwd))
			except Exception as e:
				log.error("ftp 登陆失败 %s %s 异常: %s" % (self.username,self.pwd,e))
				# tls 尚未测试通过
				# ftp=self.ftp_tls_connect()
				sys.exit()
		else:
			try:
				ftp.connect(self.host,self.port)
			except Exception as e:
				log.error("ftp 连接失败 %s:%s 异常: %s" % (self.host,self.port,e))
				sys.exit()
			try:
				ftp.login(self.username,self.pwd)
			except Exception as e:
				log.error("ftp 登陆失败 %s %s 异常: %s" % (self.username,self.pwd,e))
				sys.exit()
		return ftp

	def ftp_is_dir(self,path):
		isDir = False
		try:
			self.ftp.cwd(path)
			isDir = True
		except Exception as e:
			pass
		else:
			self.ftp.cwd('..')
		return isDir

	def check_remote_local_file(self,remoteFile,localFile):
		rsize = 0
		lsize = 0
		if os.path.isfile(localFile):
			lsize = os.path.getsize(localFile)	# Bytes
		try:
			rsize = self.ftp.size(remoteFile)
		except Exception as e:
			rsize = 0
		if rsize == 'None':
			rsize = 0
		return rsize,lsize
		

	def ftp_down_file(self,remoteFile,localFile):		
		rsize,lsize = self.check_remote_local_file(remoteFile,localFile)
		atime = time.time()
		bufSize = 10240
		self.ftp.voidcmd('TYPE I')	# 将传输模式改为二进制
		if rsize > lsize and lsize != 0:
			# 续传
			log.info("开始续传文件 remoteFile=%s  localFile=%s " % (self.ftp.pwd() + "/" + remoteFile,localFile))
			try:
				dataSock = self.ftp.transfercmd('RETR '+remoteFile,lsize)
			except Exception as e:
				log.error("下载失败 remoteFile=%s  localFile=%s" % (self.ftp.pwd() + "/" + remoteFile,localFile))
				log.error("打开ftp.transfercmd  异常: %s" % e)
				return
			try:
				with open(localFile,'ab') as fw:
					while True:
						data = dataSock.recv(bufSize)
						if not data:
							break
						fw.write(data)
				dataSock.close()
				self.ftp.voidcmd('NOOP')
				self.ftp.voidresp()
			except Exception as e:
				log.error("下载 remoteFile=%s  localFile=%s 异常: %s" % (self.ftp.pwd() + "/" + remoteFile,localFile,e))
				return			
		elif rsize == 0 or rsize == lsize:
			# 跳过
			log.info("文件大小相同,跳过下载 remoteFile=%s  localFile=%s " % (self.ftp.pwd() + "/" + remoteFile,localFile))
			return
		elif rsize < lsize or lsize == 0:
			# 重新下载
			log.info("开始下载文件 remoteFile=%s  localFile=%s " % (self.ftp.pwd() + "/" + remoteFile,localFile))
			try:
				fw = open(localFile,'wb').write
				self.ftp.retrbinary('RETR %s' % remoteFile,fw,bufSize)
			except Exception as e:
				log.error("下载 remoteFile=%s  localFile=%s 异常: %s" % (self.ftp.pwd() + "/" + remoteFile,localFile,e))
				return			
		btime = time.time()
		rxSize = (rsize - lsize)/1024/1024		# mb
		takeTime = btime - atime
		mbs = rxSize / takeTime
		log.info("下载完成: %s 文件大小: %0.2f MB 耗时: %0.2f s 速率: %0.2f MB/s" % (localFile,lsize/1024/1024,takeTime,mbs))



	def download(self,remoteDir,localDir):
		log.info("开始下载 remoteDir=%s --> localDir=%s " % (self.ftp.pwd() + "/" + remoteDir,localDir))
		try:
			# 判断remoteDir 是否是一个目录
			self.ftp.cwd(remoteDir)
		except Exception as e:
			# remoteDir 如果是一个文件
			position = remoteDir.rfind(os.sep)
			checkRemotePath = remoteDir[:position+1]
			checkRemoteFile = remoteDir[position+1:]
			try:
				self.ftp.cwd(checkRemotePath)
			except Exception as e:
				log.error("远程目录不存在 remoteDir=%s 异常: %s" % (self.ftp.pwd() + "/" + remoteDir,e))
				return
			else:
				# remoteDir 上一级目录存在
				# 判断文件是否在nlst中
				remotePathList = self.ftp.nlst()
				if checkRemoteFile in remotePathList:
					if not os.path.isdir(localDir):
						log.info("创建本地目录 %s" % localDir)
						os.makedirs(localDir)
					localFile = os.path.join(localDir,checkRemoteFile)
					self.ftp_down_file(checkRemoteFile,localFile)

		else:
			# remoteDir 是一个目录
			if not os.path.isdir(localDir):
				log.info("创建本地目录 %s" % localDir)
				os.makedirs(localDir)
			remotePathList = self.ftp.nlst()
			# log.debug("remotePathList=%s" % remotePathList)
			for file in remotePathList:
				localFile = os.path.join(localDir,file)
				if self.ftp_is_dir(file):
					self.download(file,localFile)
				else:
					self.ftp_down_file(file,localFile)
			self.ftp.cwd('..')


	def ftp_up_file(self,localFile,remoteFile):
		rsize,lsize = self.check_remote_local_file(remoteFile,localFile)
		atime = time.time()
		bufSize = 10240
		self.ftp.voidcmd('TYPE I')	# 将传输模式改为二进制
		if rsize < lsize and rsize != 0:
			log.info("开始续传文件 localFile=%s remoteFile=%s" % (localFile,self.ftp.pwd() + "/" + remoteFile))
			try:
				fr = open(localFile,'rb')
				fr.seek(rsize)
				dataSock = self.ftp.transfercmd('STOR '+remoteFile,rsize)				
			except Exception as e:
				log.error("上传失败 localFile=%s remoteFile=%s 异常:%s" % (localFile, self.ftp.pwd() + "/" + remoteFile,e))
				log.error("打开 ntransfercmd 异常: %s" % e)
				return
			try:
				while True:
					bufData = fr.read(bufSize)
					if not len(bufData):
						break
					dataSock.sendall(bufData)
				dataSock.close()
				fr.close()
				self.ftp.voidcmd('NOOP')
				self.ftp.voidresp()
			except Exception as e:
				log.error("上传失败 localFile=%s remoteFile=%s 异常:%s" % (localFile, self.ftp.pwd() + "/" + remoteFile,e))
				return
		elif rsize == lsize:
			log.info("文件大小相同,跳过上传 localFile=%s remoteFile=%s" % (localFile,self.ftp.pwd() + "/" + remoteFile))
			return
		elif lsize == 0:
			log.info("本地文件大小为0,跳过上传 localFile=%s remoteFile=%s" % (localFile,self.ftp.pwd() + "/" + remoteFile))
			return
		else:
			log.info("开始上传文件 localFile=%s remoteFile=%s" % (localFile,self.ftp.pwd() + "/" + remoteFile))
			try:
				fr = open(localFile,'rb')
				self.ftp.storbinary('STOR %s' % remoteFile,fr,bufSize)
				fr.close()
			except Exception as err:
				log.error("上传失败 localFile=%s remoteFile=%s 异常:%s" % (localFile, self.ftp.pwd() + "/" + remoteFile,err))
				return
		btime = time.time()
		txSize = (lsize - rsize)/1024/1024					# mb
		takeTime = btime - atime
		mbs = txSize / takeTime
		log.info("上传完成: %s 文件大小: %0.2f MB 耗时: %0.2f s 速率: %0.2f MB/s" % (localFile,lsize/1024/1024,takeTime,mbs))
			


	def upload(self,localDir,remoteDir):
		log.info("开始上传 localDir=%s remoteDir=%s" % (localDir,self.ftp.pwd() + "/" + remoteDir))
		if os.path.isdir(localDir):
			localList = os.listdir(localDir)
			try:
				self.ftp.cwd(remoteDir)
			except Exception as e:
				try:
					log.info("创建远程目录 remoteDir=%s" % self.ftp.pwd() + "/" + remoteDir)
					self.ftp.mkd(remoteDir)
					self.ftp.cwd(remoteDir)
				except Exception as e:
					log.error("创建远程目录 remoteDir=%s 异常: %s" % (self.ftp.pwd() + "/" + remoteDir,e))
					return
			for file in localList:
				filePath = os.path.join(localDir,file)
				if os.path.isdir(filePath):
					self.upload(filePath,file)
				else:
					self.ftp_up_file(filePath,file)
			self.ftp.cwd('..')
		elif os.path.isfile(localDir):
			remoteFileName = os.path.split(localDir)[1]
			self.ftp.cwd(remoteDir)
			self.ftp_up_file(localDir,remoteFileName)
		else:
			log.error("本地文件 %s 不存在" % localDir)
		

if __name__ == '__main__':
	# ftp = FtpClass('192.168.20.188',21,'spdbFTP','dtkd_123321')
	# # ftp = FtpClass('10.174.238.10',49161,'ynyd','YnYd_2019ftp')
	# # ftp.download("/tmpUpload/test",r"d:\\testFTP")
	# ftp.upload(r"d:\\testFTP","/tmpUpload/test")
	from optparse import OptionParser
	usage = "脚本用于上传或下载FTP数据\n"
	usage += "使用方法: \npython3 ftp_python.py -t [download/upload] -H 192.168.1.100 -P 21 -u username -p password -l localfile -r remotefile"
	parser = OptionParser(usage=usage)
	optlist=(
			("-t","--type","ftp_type",'download',"Type of FTP upload or download"),
			("-H","--host","ftp_host","127.0.0.1","Host of FTP"),
			("-P","--port","ftp_port",'21',"Port of FTP"),
			("-u","--username","ftp_user",'anonymous',"anonymous"),
			("-p","--password","ftp_password",None,"password"),
			("-l","--localfile","localfile",None,"localfile"),
			("-r","--remotefile","remotefile",None,"remotefile")
		)
	for opt in optlist:
		parser.add_option(opt[0],opt[1],dest=opt[2],default=opt[3],help=opt[4])
	(options,args) = parser.parse_args()
	if len(sys.argv) < 2:
		print("userage: python3 ftp_python.py -t [download/upload] -H 192.168.1.100 -P 21 -u username -p password -l localfile -r remotefile"
			"\ndetails: python3 ftp_python.py -h")
		sys.exit()
	else:
		ftp_type = options.ftp_type
		ftp_host = options.ftp_host
		ftp_port = int(options.ftp_port)
		ftp_user = options.ftp_user
		ftp_password = options.ftp_password
		localFile = options.localfile
		remoteFile = options.remotefile
		try:
			ftp = FtpClass(ftp_host,ftp_port,ftp_user,ftp_password)
			if ftp_type == "download":
				ftp.download(remoteFile,localFile)
			elif ftp_type == "upload":
				ftp.upload(localFile,remoteFile)
			else:
				print("ftp_type error %s [download/upload]" % ftp_type)
		except BaseException as e:
			log.error("BaseException: %s" % e)
			raise e
		


