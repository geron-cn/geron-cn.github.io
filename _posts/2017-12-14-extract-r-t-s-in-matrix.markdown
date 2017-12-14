---
layout:  post
title:   matrix 中提取旋转、位移、缩放分量
date:    2017-12-06 10:19:56
author:  Gero
header-img: "img/post-bg-miui6.jpg"
tags:
    - OpengGL
    - 矩阵
---

仅仅针对主列矩阵，需要充分的理解矩阵的构建，可参考 Unity 和 cocos 源码

{% highlight c++ %} 
Vector3 translate;
translate.x = matrix[12];
translate.y = matrix[13];
translate.z = matrix[14];

Vector3 forward;
forward.x = matrix[8];
forward.y = matrix[9];
forward.z = matrix[10];

Vector3 upwards;
upwards.x = matrix[4];
upwards.y = matrix[5];
upwards.z = matrix[6];

return Quaternion.LookRotation(forward, upwards);

 Vector3 scale;
scale.x = new Vector4(matrix[0], matrix[1], matrix[2], matrix[3]).magnitude;
scale.y = new Vector4(matrix[4], matrix[5], matrix[6], matrix[7]).magnitude;
scale.z = new Vector4(matrix[8], matrix[9], matrix[10], matrix[11]).magnitude;
{% endhighlight %}
