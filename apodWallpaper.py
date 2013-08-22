#!/usr/bin/python

import os
import re
import sys
import subprocess
import urlparse

try:  import requests
except ImportError:
    sys.exit("'requests' library not found! Make sure it is installed.")
try: import html2text
except ImportError:
    sys.exit("'html2text' library not found! Make sure it is installed.") 

#  config vars
apodURL = "http://apod.nasa.gov/apod/"
downloadDIR = "~/Downloads/wallpapers/"


#  replace ~ in downloadDIR 
downloadDIR = os.path.expanduser(downloadDIR)

#  screen dimensions
dimsOut, _ = subprocess.Popen("xdpyinfo | grep dimensions", stdout=subprocess.PIPE, shell=True).communicate()
dims = re.search("\s+([0-9]+)x([0-9]+)\s+pixels", dimsOut)
if dims == None:
    sys.exit("Cannot display resolution! Make sure xdpyinfo is installed.")
width, height = map(int, dims.groups())

#  get image src
htmlSRC = requests.get(apodURL).text
img = re.search('<a\s+href=\"([a-z]+\/[[0-9]{4}\/)([a-zA-Z0-9_]+.jpg)\">\s+<img\s+src=', htmlSRC, re.IGNORECASE)
try:
    imgPATH, imgNAME = img.groups()
except AttributeError:
    sys.exit("Cannot find image on %s! Probably other media (video) available." % apodURL)
imgLOC = os.path.join(downloadDIR, imgNAME)

print("Location of image: %s\n" % imgLOC)

#  create download dir
if not os.path.exists(downloadDIR):
    os.mkdir(downloadDIR)

#  check if image already downloaded
if os.path.exists(imgLOC):
    sys.exit("Most recent image already downloaded!")

#  download image
r = requests.get(urlparse.urljoin(apodURL, imgPATH) + imgNAME, stream=True)
if r.status_code == 200:
    print("Downloading image\n")
    with open(imgLOC, 'wb') as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)

#  check if imagemagick installed
out, _ = subprocess.Popen("which convert", shell=True, stdout=subprocess.PIPE).communicate()
if not out:
    sys.exit("Cannot find 'convert'! Make sure imagemagick is installed.")

# width and height of expDESC
expW = int(width*.8)
expH = int(height*.1)

#  resize image
new_height = height - expH
print("Resizing image to %sx%s\n" % (new_height, width))
_ = subprocess.Popen( "convert {0} -resize x{1} -size {2}x{1} xc:black +swap -gravity center -composite {0}".format(imgLOC, new_height, width), shell=True).communicate()

#  add image description
h = html2text.HTML2Text()
h.ignore_links = True
h.ignore_emphasis = True
htmlTEXT = h.handle(htmlSRC).replace('\n', ' ')
r = re.search("Explanation:\s*(.*)\s*Tomorrow's picture:", htmlTEXT, re.IGNORECASE | re.DOTALL)
expDESC = r.groups()[0]

print("Appending description to image:\n %s\n" % expDESC)
_ = subprocess.Popen("convert -background '#0008' -fill white -gravity center -pointsize 12 -size {0}x{1} caption:{2} {3} +swap -gravity south -append {3}".format(expW, expH, repr(expDESC), imgLOC), shell=True).communicate()

#  set image as desktop wallpaper
print("Set image as wallpaper")
subprocess.Popen("gconftool -t string -s /desktop/gnome/background/picture_filename %s" % imgLOC, shell=True)
subprocess.Popen("xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitor0/image-path -s %s" % imgLOC, shell=True)
