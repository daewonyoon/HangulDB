import sys
import os

import numpy as np
from PIL import Image


max_wh = [ 0, 0 ]


class HguImage:
	def __init__(self, code, w, h, t, r, d):
		self.code = code
		self.ch = code.decode('cp949')
		hangul_ord = ord(self.ch) - ord('가')
		self.ch3 = (hangul_ord//588, (hangul_ord%588)//28, hangul_ord%28)
		self.width = w
		self.height = h
		self.type = t
		self.reserved = r
		self.data = [ ]
		self.databytes = d
		
		for y in range(h):
			self.data.append([])
			for x in range(w):
				self.data[y].append(int(d[w*y+x]))

	def norm_size(self):
		'''
			change size to (100, 100)
			align center
		'''				
		w, h = self.width, self.height
		new_data = [ [ 0xFF for x in range(100)] for y in range(100) ]
		ox, oy = (100-w)//2, (100-h)//2
		for y in range(h):
			for x in range(w):
				if self.data[y][x] != 0xFF:
					new_data[oy+y][ox+x] = self.data[y][x]
		self.data = new_data					
		new_databytes = b''
		for y in range(100):
			line = bytes(self.data[y])
			new_databytes += line
		self.databytes = new_databytes
		self.width, self.height = 100, 100	
		return			


def dispaly_main():
	if len(sys.argv) < 2:
		print("Usage: %s <.hgu1 filename>"%(sys.argv[0],))
		return
	display_file(sys.argv[1])
	return		


def convert_main():
	if len(sys.argv) < 2:
		print("Usage: %s <foldername>"%(sys.argv[0]))
		return

	for r, _dirnames, filenames  in os.walk(sys.argv[1]):
		for i, filename in enumerate(filenames):
			#if i == 2:
			#	break
			if not filename.endswith('.hgu1'):
				continue
			filepath = os.path.join(r, filename)
			dirpath = filepath[:-5]
			convert_file(filepath, dirpath)
	return


def convert_file(filepath, dirpath):
	os.makedirs(dirpath, exist_ok=True)
	with open(filepath, 'rb') as f:
		file_header = f.read(8)
		assert(file_header[:4] == b'HGU1')
		print("file_header = %s"%(str(file_header)))


		for n, image in enumerate(read_hgu1(f)):
			#if n == 10:
			#	break
			if image == None:
				break
			img_filepath = os.path.join(dirpath, '%s_%03d.png'%(image.ch, n))

			save_to_png(img_filepath, image)

			if max_wh[0] < image.width:
				max_wh[0] = image.width
			if max_wh[1] < image.height:
				max_wh[1] = image.height

			# input("press enter to continue")
		print('max wh = %s'%(max_wh))
	return	
				
def save_to_png(img_filepath, image):
	img = Image.frombytes('L', (image.width, image.height), image.databytes)
	#img = Image.new('L', (image.width, image.height))
	#dat = []
	#for line in image.data:
	#	dat += line
	#img.putdata(dat)
	img.save(img_filepath)


def display_file(filepath):
	with open(filepath, 'rb') as f:
		file_header = f.read(8)
		assert(file_header[:4] == b'HGU1')
		print("file_header = %s"%(str(file_header)))

		max_wh = [ 0, 0 ]

		for n, image in enumerate(read_hgu1(f)):
			if image == None:
				break
			print("image %d"%(n, ))

			# write_hgu1(out_file, image)

			display_image(image)
			log_image(image, filepath+"_display.log")
			if max_wh[0] < image.width:
				max_wh[0] = image.width
			if max_wh[1] < image.height:
				max_wh[1] = image.height

			# input("press enter to continue")
		print('max wh = %s'%(max_wh))
	return


def display_image(image):
	print("code = [%x%x], ch = %s, w x h = %d, %d, type = %d, reserved = %d"%(
		image.code[0], image.code[1], image.ch, image.width, image.height, image.type, image.reserved
	))

	for y in range(image.height):
		for x in range(image.width):
			print("%02x"%(image.data[y][x]), end='')
		print("")
	
	return


def log_image(image, filename):
	with open(filename, 'a', encoding='utf-8') as f:
		print("code = [%x%x], ch = %s, w x h = %d, %d, type = %d, reserved = %d"%(
			image.code[0], image.code[1], image.ch, image.width, image.height, image.type, image.reserved
		), file=f)

		for y in range(image.height):
			for x in range(image.width):
				print("%02x"%(image.data[y][x]), end='', file=f)
			print("", file=f)
	return			


def read_hgu1(f):
	while True:
		img_hdr = f.read(6)
		if len(img_hdr) == 0:
			break
		code = img_hdr[:2]
		w, h = int(img_hdr[2]), int(img_hdr[3])
		t, r = int(img_hdr[4]), int(img_hdr[5])
		#print("w, h, t, r = %d, %d, %d, %d"%(w, h, t, r))
		data_bytes = f.read(w*h)
		image = HguImage(code, w, h, t, r, data_bytes)
		image.norm_size()
		yield image
	return


if __name__ == '__main__':
	convert_main()
