---
layout:  post
title: 选择一个合适的 AR SDK
date: 2017-12-28
author: Gero
header-img:  "img/post-bg-miui6.jpg"
tags:
   - AR
---

基本需求：

1. 相机标定
2. Marker 追踪，根据在拍摄画面中检测目标图片（或3D物体）并实时追踪，构建三维空间
3. Markerless 检测，在拍摄画面中实时检测一个平面，构建三维空间

部分参考资料： [best-ar-sdk-review](https://thinkmobiles.com/blog/best-ar-sdk-review/)，包括功能和授权分析：

###  SDK Feature Comparison 
| |Vuforia| EasyAR| Wikitude| ARToolKit| Kudan| MaxST| Xzimg| NyARToolKit|
|---|----|---|----|---|----|---|----|----|
|Maximum distance capturing / holding marker (m)|1.2 / 3.7| 0.9 / 2.7| 0.8 / 3 |3 /3| 0.8/3|0.5/0.9| 0.7 / 5 |0.7 / 1|
|Recognition stability of immovable marker |10 |7 |6| 8 |10| 7 |8 |5|
|Recognition stability of movable marker |6| 3 |4| 6 |6| 2 |7| 3| 
|Minimum angle recognition |30| 35| 40| 10| 30 |50| 35| 45| 
|Minimum visibility for recognition overlapped marker| 20% |10%| 30%| 100%| 25% | 50% |10% | 75%| 
|2D Recognition| ✓ |✓| ✓| ✓(bordered)| ✓ |✓| ✓| ✓| 
|3D Recognition| ✓| – |✓(beta) |–| ✓| ✓ |–| –|
|Geo-Location| –| –|✓|– |– |– |–| –| 
|Cloud Recognition| ✓ |– |✓| –| –|–| –| –| 
|SLAM| – |–| ✓| –| ✓| ✓ |–| –| 
|Total (rating)|7.1| 4.4 |7.5| 2.8| 6.9| 5.2| 4.7| 3.1| 查阅资料后发现基本所有sdk都是基于OpenCV的基础上

以以上评分作为参考，考虑以 Unity 作为可视化开发工具，筛选了以下三个平台作为对比，找了些些资料作为对比：

|  | 支持平台| 文档 | 示例 | |
|:--:|:--|:--|:--|:--|
| Wikitude | [sdk download][1] |[documentation][3] |[samples][1]|*完全开源，可定制性相当强，支持全平台，资料比较散且乱*，自己编译和适配各平台还是比较折腾的，如果是有足够的时间和精力的话，作为学习和捣腾的首选。
| Kudan| [sdk download][2]| [documentation][4]|[samples][7]|*商业授权，development免费，支持全平台*，而且它支持 Unity PlayMode预览，理论上支持PlayMode就可以直接使用 Unity 打包 Desktop 的包了，但我折腾了很久都不行。给官方支持邮箱发了邮件得到回复是会支持的。另外 Kudan 的官网上例如 sdk下载，api document 的链接都没有，都是另外查的，只剩 SLAM 相关资料。
| ARToolkit |[sdk download][6]|[documentation][5]|[samples][8]|*商业授权，development免费，支持全平台，API优秀*，同时提供 JavaScript 接口，Native SDK 中的 OpenCV 代码可见，意味着在扩展方面可以完全无缝对接，提供都是插件形式功能扩展，十分让人喜爱。

另外还有一个 [AR.js](https://github.com/jeromeetienne/AR.js)，基于 ARToolKit 扩展的，支持光照等，全跨平台，性能也相当高,如果不考虑可视化编辑影响开发效率的话是非常好的选择。

[1]:https://www.wikitude.com/download/

[2]:https://www.kudan.eu/download-kudan-ar-sdk/

[3]:https://www.wikitude.com/external/doc/documentation/

[4]:https://kudan.readme.io/docs/getting-started

[5]:https://archive.artoolkit.org/documentation/

[6]:https://archive.artoolkit.org/download-artoolkit-sdk

[7]:https://github.com/kudan-eu

[8]:https://github.com/artoolkit/artoolkit5