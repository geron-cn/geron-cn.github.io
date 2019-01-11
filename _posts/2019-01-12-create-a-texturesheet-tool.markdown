---
layout:  post
title: 编写一个合图工具
date: 2019-01-12
author:  Gero
header-img:  "img/post-bg-miui6.jpg"
tags:
   - opencv
   - texturepacker
---

背景：最近写一个小动画，需要合图，但是texturepacker之类的合图工具基本上都要收费，装了cocos的机器又不在手边，
于是身为一个兼职的脚本工程师，就自己写了一个合图工具，还是很好用的。

其中各项参数根据自己的情况替换：
```python
import cv2
import numpy as np


img0 =  cv2.imread('bixin_000.png')
h = img0.shape[0]
w = img0.shape[1]

emptyimg = np.zeros((h*5, w*5, 4), np.uint8)
for  i in range(7,32):
    name='bixin_00%d.png'%(i)
    if i >= 10:
        name = 'bixin_0%d.png'%(i)
    i = i - 7
    print name
    imgsrc = cv2.imread(name, cv2.IMREAD_UNCHANGED)
    emptyimg[i/5*h:i/5*h+h, i%5 * w:i%5 * w+w] = imgsrc
cv2.imwrite('merge.png',emptyimg)

```

