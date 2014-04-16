from orc import OrcBoard
import math

class Robot(OrcBoard):
	TICKS_PER_REV=2000

	def __init__(self):
		OrcBoard.__init__(self)

	def drive(self,(left,right)):
		result=self.communicate(left*255,-right*255)
		return (float(result['encoders'][0]['value'])/self.TICKS_PER_REV*2*math.pi,-float(result['encoders'][1]['value'])/self.TICKS_PER_REV*2*math.pi)
