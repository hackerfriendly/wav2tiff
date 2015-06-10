__wav2tiff.py__: Convert slow-scan WAV files to TIFF images

http://hackerfriendly.com/megapixel-images-from-an-analog-sem/

This method was designed to be used with a JEOL JSM-6320F microscope, but any
slow-scan TV signal with a dot clock lower than your best audio sampling rate
should work.

You'll need to figure out how to connect up your video source to a sound card,
and create a WAV file of the scan. Then _wav2tiff.py_ will turn it into a 32bit
TIFF file.


Hardware
========

NOTE: If you don't know what you're doing, get help. You can destroy your scan
generator, microscope, audio card, and/or computer if you're not careful! Use
an oscilloscope to find the proper lines, and be sure the input voltage
doesn't exceed a couple of volts.

  * Connect the video signal from the photo scanner to one channel of your
    audio card. On the JSM-6320F, that's the BNC labelled NA8 inside the back of
    the computer console.

  * Connect the horizontal sync line to the other channel of the audio card. I
    installed mine directly on the scan generator board U10, through a 10k ohm
    resistor.

The horizontal sync line is a sawtooth wave that falls at the end of each
video line:

           /|         /|         /|         /|         /|         /|
         /  |       /  |       /  |       /  |       /  |       /  |
       /    |     /    |     /    |     /    |     /    |     /    |
    _/      |___/      |___/      |___/      |___/      |___/      |___

You may need to add a potentiometer to ground to dial back the signal if it's
too high.

  * Choose a slow-scan mode within the capabilities of your sound card.
    Generally speaking, the slower you go, the better the photo. But also consider
    the sample: uncoated organics can hold quite a lot more charge at slow speeds.

Faster speeds contribute less charge to the sample over time, but you can
quickly overrun your audio card's sample speed.

The 6320F supports scans as slow as 1940 lines in 320 seconds, for an ultimate
dot clock of ~15.6 kHz:

    1940 lines * 4/3 = 2587 pixels wide
    1940 * 2587 * 1/320 fps = 15,684 pixels/second

Contrast that with NTSC, which most audio cards can't possibly keep up with:

    525 lines * 4/3 = 700 pixels wide
    525 * 700 * 30 fps = 11,025,000 pixels/second

Experimentally, I've found no real quality difference between 48 kHz sampling
(~3x oversampling) vs. 192000 kHz (12.8x). The software should work with just
about any sync rate, but there's no need to go nuts. YMMV.


Software
========

You can make the recording with just about any software. I recommend Audacity:

http://web.audacityteam.org/

Some recording tips:

  * Be sure to turn the gain down until you're no longer clipping.

  * Trim off any junk from the beginning and end of the file. You don't have to
    be precise; _wav2tiff.py_ will pull out the most likely sync signal from
    whichever side the sync is connected to.

  * Save the result as a signed 16 bit PCM WAV file. It should have two channels:
    the video on one, and the horizontal sync on the other.

  * You will want to adjust the white balance and crop the resulting photo in
    the image manipulation suite of your choice (Gimp, Photoshop, etc.)


wav2tiff
========

You'll need python (obviously), and a couple of packages:

  * numpy, https://pypi.python.org/pypi/numpy
  * scipy, https://pypi.python.org/pypi/scipy
  * scikits.audiolab, https://pypi.python.org/pypi/scikits.audiolab/
  * tifffile, https://pypi.python.org/pypi/tifffile

The script is pretty simple. Just run __wav2tiff.py --wav your_data_file.wav__ and
it will save the results as wav.tiff:

    $ wav2tiff.py --wav boron.wav
            length: 258 seconds
          encoding: pcm16
           samples: 12404159
       sample rate: 48000
         H sync on: right channel
    mean line size: 7201

    Processing sync data...
      image height: 1718
       image width: 2405

    Processing video data...
      Saving wav.tiff


You will be oversampling in the horizontal axis, with a fixed number of rows
equal to whatever your scan generator makes. _wav2tiff.py_ will automatically
scale the resulting image to the given aspect ratio. The default is 7:5 (1.4),
which seems to work well for the JSM-6320F. You can set it to whatever you
like (eg. 4:3, or 1.333) with the __--aspect_ratio__ switch:

    $ wav2tiff.py --wav pollen.wav --aspect_ratio 1.333

To skip scaling altogether, set the aspect ratio to 1.

For all available options, run it with -h:

    usage: wav2tiff.py [-h] [--aspect_ratio ASPECT_RATIO] [--tiff TIFF]
                       [--wav WAV]

    optional arguments:
      -h, --help            show this help message and exit
      --aspect_ratio ASPECT_RATIO
                            final image aspect ratio (default: 1.4)
      --tiff TIFF           tiff file to save (default: wav.tiff)
      --wav WAV             wav file to process (default: None)


FAQ
===

* __The picture looks washed out!__

  Convert the tiff to 16-bit and/or adjust the white balance.

* __The picture is squashed!__

  Adjust the aspect ratio to match your scope. A calibration target (such as
  text or a logo on a microchip) is helpful here.

* __There is a vertical band of junk on the left of the photo!__

  That is junk data that ordinarily wouldn't be visible during the horizontal
  blanking interval. I haven't found a reliable way to automatically trim it,
  so crop it yourself.

  This is why the default aspect ratio is 1.4 instead of 1.333. ;)

* __What about the AC coupling capacitors on the input of my sound card? Won't they distort the image?__

  Good question. I seem to get good results without any further modification
  as long as the gain isn't too high. I'll try bypassing them and post an
  update with the results.

* __wav2tiff.py complains that it can't find the sync channel!__

  The algorithm for finding the sync line is pretty basic. Open up the WAV
  file in Audacity and zoom into the sync line. Does it look like a repetitive
  rising sawtooth? Is your sample rate around 48 kHz?

  Patches are very welcome.
