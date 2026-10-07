"""Gamma-lift the six Habitat frames in figs/fig_storyboard.png (scanned scenes are dark).
Frame geometry from the original compose script: LEFT=24, FW=320, FH=240, GAP=12, BLOCKGAP=44, TOP=74, CAP=92, ROWGAP=30."""
import numpy as np
from PIL import Image
p = 'figs/fig_storyboard.png'
im = np.array(Image.open(p).convert('RGB')).astype(np.float32)
x0 = 24 + 3 * 320 + 2 * 12 + 44
for row in (74, 74 + 240 + 92 + 30):
    for ci in range(3):
        x = x0 + ci * (320 + 12)
        blk = im[row:row + 240, x:x + 320]
        im[row:row + 240, x:x + 320] = 255.0 * (blk / 255.0) ** 0.55
Image.fromarray(im.clip(0, 255).astype('uint8')).save(p, dpi=(200, 200))
print('brightened', p)
