#-*- coding:utf-8 -*-
import os
import time
import sys


namestr =  namestr = sys.argv[1] if len(sys.argv) > 1 else 'new-post'
rootpath = os.getcwd()
datestr = time.strftime('%Y-%m-%d %H-%M-%S', time.localtime(time.time()))
namestrp = namestr.replace(" ", "-")
filename = datestr+'-'+namestrp + '.markdown'
filepath = os.path.join(rootpath, "_posts", filename);
fileindex = 1;
while(os.path.exists(filepath)):
    filepath = os.path.join(rootpath, "_posts", datestr+'-'+ str(fileindex)+'-'+namestrp+'.markdown')
    fileindex+=1
    print '%s exists' % filepath

file = open(filepath, 'w')
filecontent = '---\nlayout:  post\ntitle:  %s \ndate:  %s \nauthor:  Gero\nheader-img:  "img/post-bg-miui6.jpg"\ntags: \n---' %(namestr, datestr)
file.write(filecontent)
file.close()

