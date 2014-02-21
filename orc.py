import struct
import time
import socket

class OrcBoard:
	HEADER=0x0ced0002
	SIGNATURE=0x0ced0001

	def __init__(self,addr='192.168.237.7',base_port=2378):
		self.addr=addr
		self.base_port=base_port
		self.transaction_id=0
		self.tx_socket=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		self.rx_socket=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		self.rx_socket.bind(('',self.base_port))

	def get_version(self):
		resp=self.do_command(0x0002)
		if len(resp)<1:
			raise Exception('Improperly sized response')
		if resp[-1]!='\0':
			raise Exception('Version did not return a null-terminated string')
		return resp[0:-1]

	def set_motor(self,motor,speed):
		if speed<-255 or speed>255:
			raise Exception('Speed not between -255 and 255')
		data=struct.pack('>BBh',motor,1,speed)
		resp=self.do_command(0x1000,data)
		# todo parse response

	def set_motor_coast(self,motor):
		data=struct.pack('>BBh',motor,0,0)
		resp=self.do_command(0x1000,data)
		# todo parse response

	def get_status(self):
		resp=self.do_command(0x0001)
		if len(resp) != 252:
			raise Exception('Improperly sized response')
		
		result=struct.unpack(
			'IH'+ # Status flags, debug chars waiting 
			'HHH'*13+ # Raw Analog (value, filtered value, filter alpha)
			'II'+ # Digital (value, direction)
			'BhhH'*4+ # Motors (enable, actual pwm, goal pwm, slew rate)
			'ii'*2+ # Encoders (position, velocity)

			'BI'*8+ # Fast Digital IO (mode, config)
			'lI'*3, # Gyro (integral, count)
			resp)
		out={
			'status_flags':result[0],
			'debug_chars_waiting':result[1],
			'raw_analog':[{'value':result[i],'filtered_value':result[i+1],'filter_alpha':result[i+2]} for i in range(2,41,3)],
			'digital_value':result[41],
			'digital_direction':result[42],
			'motors':[{'enable':result[i],'actual_pwm':result[i+1],'goal_pwm':result[i+2],'slew_rate':result[i+3]} for i in range(43,59,4)],
			'encoders':[{'position':result[i],'velocity':result[i+1]} for i in range(59,63,2)],
			'fast_digital_io':[{'mode':result[i],'config':result[i+1]} for i in range(63,79,2)],
			'gyro':[{'integral':result[i],'count':[i+1]} for i in range(79,85)],
		}
		return out

	def get_transaction_id(self):
		tid=self.transaction_id
		self.transaction_id+=1
		return tid

	def get_time_ms(self):
		return int(time.time()*1000)

	def do_command(self,command_id,payload='',rx_bufsize=1600):
		tid=self.get_transaction_id()
		t=self.get_time_ms()
		cmd=struct.pack('IILI',self.HEADER,tid,t,command_id)
		cmd+=payload
		port=self.base_port+((command_id>>24)&0xFF) # wtf
  		self.tx_socket.sendto(cmd, (self.addr, port))

		data,addr=self.rx_socket.recvfrom(rx_bufsize)
		if len(data)<20:
			raise Exception("Bad response from Orc: not enough data")
		header=data[0:20]
		result=data[20:]
		signature,rx_tid,rx_t,response_id=struct.unpack('IILI',header)
		if signature != self.SIGNATURE:
			raise Exception("Bad signature from Orc")
		#print rx_tid,rx_t,response_id
		return result

o=OrcBoard('localhost')
o.SIGNATURE=o.HEADER
o.get_status()
#print repr(o.get_version())

