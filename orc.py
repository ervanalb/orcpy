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
		self.sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

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
		if len(resp) != 205:
			raise Exception('Improperly sized response')
		
		result=struct.unpack('>'+
			'IH'+ # Status flags, debug chars waiting 
			'HHH'*13+ # Raw Analog (value, filtered value, filter alpha)
			'II'+ # Digital (value, direction)
			'BhhH'*3+ # Motors (enable, actual pwm, goal pwm, slew rate)
			'ii'*2+ # Encoders (position, velocity)

			'BI'*8+ # Fast Digital IO (mode, config)
			'qI'*3, # Gyro (integral, count)
			resp)
		out={
			'status_flags':result[0],
			'debug_chars_waiting':result[1],
			'raw_analog':[{'value':result[i],'filtered_value':result[i+1],'filter_alpha':result[i+2]} for i in range(2,41,3)],
			'digital_value':result[41],
			'digital_direction':result[42],
			'motors':[{'enable':result[i],'actual_pwm':result[i+1],'goal_pwm':result[i+2],'slew_rate':result[i+3]} for i in range(43,55,4)],
			'encoders':[{'position':result[i],'velocity':result[i+1]} for i in range(55,59,2)],
			'fast_digital_io':[{'mode':result[i],'config':result[i+1]} for i in range(59,75,2)],
			'gyro':[{'integral':result[i],'count':result[i+1]} for i in range(75,81,2)],
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
		cmd=struct.pack('>IIQI',self.HEADER,tid,t,command_id)
		cmd+=payload
		port=self.base_port+((command_id>>24)&0xFF) # wtf
  		self.sock.sendto(cmd, (self.addr, port))

		data,addr=self.sock.recvfrom(rx_bufsize)
		if len(data)<20:
			raise Exception("Bad response from Orc: not enough data")
		header=data[0:20]
		result=data[20:]
		signature,rx_tid,rx_t,response_id=struct.unpack('>IIQI',header)
		if signature != self.SIGNATURE:
			raise Exception("Bad signature from Orc")
		if rx_tid != tid:
			raise Exception("Received response out of order")
		return result

if __name__=='__main__':
	import time
	o=OrcBoard()
	print "VERSION ",o.get_version()
	while True:
		o.set_motor(0,100) # Left wheel forward
		o.set_motor(1,-100) # Right wheel forward
		status=o.get_status()
		print status['encoders'][0]
		print status['encoders'][1]
		time.sleep(0.01)

