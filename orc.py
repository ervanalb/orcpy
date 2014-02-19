import struct
import time

class OrcBoard:
	HEADER=0x0ced0002

	def __init__(self,addr='192.168.237.7'):
		self.addr=addr
		self.transaction_id=0

	def get_version(self):
		self.do_command(0x0002)
		return '?'

	def get_transaction_id(self):
		tid=self.transaction_id
		self.transaction_id+=1
		return tid

	def get_time_ms(self):
		return int(time.time()*1000) & 0xFFFFFFFF

	def make_command(self,command_id,payload=''):
		tid=self.get_transaction_id()
		t=self.get_time_ms()
		cmd=struct.pack('IIII',self.HEADER,tid,t,command_id)
		cmd+=payload
		return cmd

	def do_command(self,command_id,payload=''):
		self.send(self.make_command(command_id,payload))

	def send(self,b):
		print b

o=OrcBoard()
o.get_version()
