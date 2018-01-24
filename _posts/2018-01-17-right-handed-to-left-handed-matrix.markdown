---
layout:  post
title: 左右手坐标系的相互转换
date: 2018-01-17
author:  Gero
header-img:  "img/post-bg-miui6.jpg"
tags:
   - Unity
   - Matrix
---

Unity中是左手坐标系，而在 native 代码中使用OpenGL接口渲染是右手坐标系，所以经常用到以下操作：

左手坐标系与右手坐标系相互转换：
```c#
    public static readonly Matrix4x4 FLIP_Z = Matrix4x4.Scale(new Vector3(1, 1, -1));
    static public Matrix4x4 FlipHandedness(Matrix4x4 matrix) {
        return FLIP_Z * matrix * FLIP_Z;
    }
```

比较常见的操作还有maya/3dmax 导出需选择Y轴向上；右手坐标系 转到左手坐标系  x y z = x z y 四元数 x y z w => -x -z -y w；水平翻转 texture等。

