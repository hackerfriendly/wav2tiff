#!/usr/bin/python

import numpy as np
from scipy.ndimage.interpolation import zoom
from scikits.audiolab import wavread
from tifffile import imsave
import argparse

opts = {
	'wav':			{ 'value': None,		'help': 'wav file to process' },
	'tiff':			{ 'value': 'wav.tiff',	'help': 'tiff file to save' },
	'aspect_ratio':	{ 'value': 7. / 5.,		'help': 'final image aspect ratio' },
}

def find_edges(data, sample_rate, trim=None):
	''' Find the falling edges. If trim = True, discard edges whose interval fall outside 1%% of the trim value '''
	edges = []
	intervals = [0]
	last_sample = 0
	prev_interval = 0
	window = sample_rate * 0.002

	# smooth the sample data
	smoothed = np.convolve(data, np.ones((window,)) / window)[(window-1):]

	for i, sample in enumerate(smoothed):
		if(sample < 0) and (last_sample > 0):
			# print "found an edge at %d (%f -> %f)" % (i, last_sample, sample)
			edges.append(i + window)
			if trim:
				intervals.append(i - prev_interval)
				prev_interval = i
		last_sample = sample

	if not trim:
		return edges

	retval = []
	trim = float(trim)
	for i, sample in enumerate(intervals[1:]):
		if(abs(sample - trim) / trim < 0.01):
			retval.append(edges[i])
	return retval

def is_sync(data):
	''' Return True if it looks like sync data '''
	return np.std(np.diff(data[1:])) < 1

if __name__ == '__main__':

	# Build out a dynamic argument list based on opts
	PARSER = argparse.ArgumentParser(description=__doc__)
	for opt in sorted(opts):
		if opts[opt]['value'] == True:
			action = 'store_false'
		elif opts[opt]['value'] == False:
			action = 'store_true'
		else:
			action = 'store'

		PARSER.add_argument('--%s' % opt, default=opts[opt]['value'], action=action, help='%s (default: %s)' % (opts[opt]['help'], str(opts[opt]['value'])))

	ARGS = PARSER.parse_args()

	for arg in vars(ARGS):
		newarg = getattr(ARGS, arg)
		opts[arg]['value'] = newarg

	if not opts['wav']['value']:
		raise Exception("--wav must be specified.")

	# Load it up
	wav_data, sample_rate, encoding = wavread(opts['wav']['value'])
	try:
		assert(len(wav_data[0]) == 2)
	except TypeError, IndexError:
		raise Exception("WAV doesn't appear to have two channels.")

	samples = len(wav_data[:,0])

	if samples < sample_rate * 2:
		raise Exception("WAV too small to process.")

	# grab two seconds of samples from the middle
	mid = int((len(wav_data) / 2) - sample_rate)

	print "        length: %d seconds" % (samples / sample_rate)
	print "      encoding: %s" % encoding
	print "       samples: %d" % samples
	print "   sample rate: %d" % sample_rate

	left = find_edges(wav_data[:,0][mid:(mid + (sample_rate * 2))], sample_rate=sample_rate)
	right = find_edges(wav_data[:,1][mid:(mid + (sample_rate * 2))], sample_rate=sample_rate)

	# ^ in boolean context is xor
	if not (is_sync(left) ^ is_sync(right)):
		raise Exception('Could not find sync channel.')

	if is_sync(left):
		print "     H sync on: left channel"
		sync_data = wav_data[:,0]
		img_data = wav_data[:,1]
		mean_interval = int(np.mean(np.diff(left)))
	else:
		print "     H sync on: right channel"
		sync_data = wav_data[:,1]
		img_data = wav_data[:,0]
		mean_interval = int(np.mean(np.diff(right)))

	print "mean line size: %d" % mean_interval

	print "\nProcessing sync data..."
	# Find all of the sync edges
	sync = find_edges(sync_data, trim=mean_interval, sample_rate=sample_rate)

	height = len(sync)
	print "  image height: %d" % height

	# scale to aspect ratio
	width = (height * float(opts['aspect_ratio']['value'])) / mean_interval
	print "   image width: %d" % int(width * mean_interval)

	print "\nProcessing video data..."

	# Normalize the brightness data: signed 16-bit to unsigned
	img_data = img_data + 1
	img_data = img_data / 2

	# Extract all of the image data. There must be a way to do this faster
	# with numpy indexing, but I'm not seeing it.
	img = []
	for line in sync:
		line_data = img_data[line:line+mean_interval].tolist()
		if len(line_data) < mean_interval:
			continue
		img.append(line_data)

	# import pdb; pdb.set_trace()

	print "  Saving %s" % opts['tiff']['value']

	imsave(opts['tiff']['value'], zoom(input=np.asarray(img, dtype=np.float32), zoom=[1.0,width]))
