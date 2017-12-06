---
layout: post
title:  how to user face++ in unity 
date: 2017-12-06 
categories: unity face++ 人脸检测 ar
---


**需求**： 在Unity中使用face++人脸检测结果实现比较复杂的例如2d变脸/3d表情追踪等复杂效果

**场景**: 复杂AR应用

**问题**：face++本身的demo都是android的和ios的，需要在unity中做复杂场景时直接使用face++中的 `com.facepp.library.OpenglActivity` 来做检测的话，需要多做一步工作，就是需要把 android.hardware.Camera 获取的图像装载到 unity 的 texture2d 中，这一步工作比较麻烦(但是理论上这样使用  `Texture2D.UpdateExternalTexture(textureid)`这样效率更高一些)，并且我的应用场景中需要对摄像机有比较复杂的操作。所以需要在 unity 中直接使用face++sdk的 c++接口。

**方案**：
1. 直接使用 unity webcamtexture 获取摄像机视频流画面
2. 直接封装 face++sdk .so 中的 c++接口，在 unity 中调用。

**参考资料**: [face++sdk][1]

在实践过程中发现，主要影响效率的是 mg_facepp.Detect 这个接口，所以*首先*主要封装此接口：
{% highlight c++ %}
float landmarks_buffer[1890]; // 106 * 15
unsigned char imagebuffer[1024 * 1024 * 5];
void* nativeDetect(void* data, int handle,
    int width, int height, int rotation,
    int imageMode, int landmarksize, int* facecount)
{
    // LOGE("native detect begin %p %d %d %d %d %d ", data, handle,  width, height, imageMode, landmarksize);
   
    ApiHandle *h = reinterpret_cast<ApiHandle *>((long)handle);
    h->orientation = rotation;
    MG_FPP_APICONFIG config;
    mg_facepp.GetDetectConfig(h->api, &config);
    if( config.rotation != rotation)
    {
        config.rotation = rotation;
        mg_facepp.SetDetectConfig(h->api, &config);
    }

    if (h->imghandle != nullptr && (h->w != width || h->h != height)) {
        mg_facepp.ReleaseImageHandle(h->imghandle);
        h->imghandle = nullptr;
    }
    //  LOGE("native detect 0");
    if (h->imghandle == nullptr) {
        mg_facepp.CreateImageHandle(width, height, &h->imghandle);
        h->w = width;
        h->h = height;
    }
    // LOGE("native detect 1");
    MG_FPP_IMAGEHANDLE imageHandle = h->imghandle;
    auto datal = width * height;
    if(imageMode == 4)
        datal *= 3;
    else if(imageMode == 3)
    {
        datal *= 4;
    }
       
    // auto img = new unsigned char[datal];
    // memcpy(img, data, datal);
    memcpy(imagebuffer, data, datal);
    // mg_facepp.SetImageData(imageHandle, img, (MG_IMAGEMODE) imageMode);
    mg_facepp.SetImageData(imageHandle, imagebuffer, (MG_IMAGEMODE) imageMode);
    int faceCount = 0;
    mg_facepp.Detect(h->api, imageHandle, &faceCount);
    //  LOGE("nativeDetect facecout: %d, facecout: %d,", handle, faceCount);
    (*facecount) = faceCount;

    // load face info and get landmarks
    MG_POINT buff[LANDMARK_ST_NR];
    for(int i = 0; i< faceCount; i++)
    {
        mg_facepp.GetLandmark(h->api, i, true, landmarksize, buff);
        for (int j = 0; j < landmarksize; ++j) {
            float point[2];
            point[0] = buff[j].x;
            point[1] = buff[j].y;
    
            rotate_point_2d(h->w, h->h, point[0], point[1], h->orientation);
            *(landmarks_buffer + landmarksize * i + j * 2) = point[0];
            *(landmarks_buffer + landmarksize * i + j * 2 + 1) = point[1];
        }
    }
    // delete img;
    return (void*)landmarks_buffer;
}
{% endhighlight %}

对应的c#端

{% highlight c# %}
[DllImport("MegviiFacepp-jni-0.4.7")]
		private static extern System.IntPtr nativeDetect(System.IntPtr imgdata, int handle, int width, int height, int rotation,
			 int imagemode, int landmarksize,  ref int facecount);
{% endhighlight %}

其次授权部分的整合：

{% highlight java %}
 // init without camera
    public void initSDK()
    {
        isStartRecorder = false;//getIntent().getBooleanExtra("isStartRecorder", false);
        is3DPose = false;//getIntent().getBooleanExtra("is3DPose", false);
        isDebug = false;//getIntent().getBooleanExtra("isdebug", false);
        isROIDetect = false;//getIntent().getBooleanExtra("ROIDetect", false);
        is106Points = true;//getIntent().getBooleanExtra("is106Points", false);
        isBackCamera = false;//getIntent().getBooleanExtra("isBackCamera", false);
        isFaceProperty = false;//getIntent().getBooleanExtra("isFaceProperty", false);
        isOneFaceTrackig = true;//getIntent().getBooleanExtra("isOneFaceTrackig", false);

        min_face_size = 200;//getIntent().getIntExtra("faceSize", min_face_size);
        detection_interval = 100;//getIntent().getIntExtra("interval", detection_interval);
        resolutionMap = null;//(HashMap<String, Integer>) getIntent().getSerializableExtra("resolution");
        getCurrentActivity();//  set activity from unit(unityplayer) first


        final LicenseManager licenseManager = new LicenseManager(current);

        licenseManager.setExpirationMillis(Facepp.getApiExpirationMillis(current, ConUtil.getFileContent(current, R.raw
                .megviifacepp_0_4_7_model)));
        String uuid = ConUtil.getUUIDString(current);
        long apiName = Facepp.getApiName();
        licenseManager.setAuthTimeBufferMillis(0);
        licenseManager.takeLicenseFromNetwork(uuid, Util.API_KEY, Util.API_SECRET, apiName,
                LicenseManager.DURATION_30DAYS, "Landmark", "1", true, new LicenseManager.TakeLicenseCallback() {
                    @Override
                    public void onSuccess() {
                        facepp = new Facepp();
                        String errorCode = facepp.init(current, ConUtil.getFileContent(current, R.raw.megviifacepp_0_4_7_model));
                        Facepp.FaceppConfig faceppConfig = facepp.getFaceppConfig();
                        faceppConfig.interval = 100;
                        faceppConfig.minFaceSize = 50;
                        faceppConfig.roi_left = 0;
                        faceppConfig.roi_top = 0;
                        faceppConfig.roi_right = 0;
                        faceppConfig.roi_bottom = 0;
                        faceppConfig.one_face_tracking = 0;
                        faceppConfig.rotation = 270;
                        faceppConfig.detectionMode = Facepp.FaceppConfig.DETECTION_MODE_TRACKING_ROBUST;
                        facepp.setFaceppConfig(faceppConfig);
                        inited = true;
                    }

                    @Override
                    public void onFailed(int i, byte[] bytes) {
                        String str = new String(bytes);
                        authState = false; Log.e("facepp", "failed to auth!!!!!!!!!!!!!!!!");
                        Log.e("facepp", str);
                    }
                });


    }
{% endhighlight %}

*再次*一些其他接口的封装：

{% highlight java %}
// get facepp apihandle com.megvii.facepp.sdk.Facepp
   public long getFaceppHandle()
    {
        return FaceppHandle;
    }

{% endhighlight %}

{% highlight c++ %}
int nativeSetFaceppConfig(int handle, int minFaceSize, int rotation,
                              int interval,
                              int detection_mode,
                              int left, int top,
                              int right, int bottom,
                              int one_face_tracking){
    ApiHandle *h = reinterpret_cast<ApiHandle *>((long)handle);
    if(rotation != -1)
    h->orientation = rotation;
    MG_FPP_APICONFIG config;
    mg_facepp.GetDetectConfig(h->api, &config);
    if(minFaceSize != -1)
    config.min_face_size = minFaceSize;
    if(rotation != -1)
    config.rotation = rotation;
  if(interval != -1)
    config.interval = interval;
  if(detection_mode != -1)
    config.detection_mode = (MG_FPP_DETECTIONMODE) detection_mode;
  if(left != -1 && top != -1 &&right != -1 &&bottom != -1)
  {
    MG_RECTANGLE _roi;
    _roi.left = left;
    _roi.top = top;
    _roi.right = right;
    _roi.bottom = bottom;
    config.roi = _roi;
  }
  if(one_face_tracking != -1)
    config.one_face_tracking = one_face_tracking;
    int retcode = mg_facepp.SetDetectConfig(h->api, &config);
    return retcode;
}
{% endhighlight %}

webcamtexture 纹理转为byte[] 数组
{% highlight c# %}
[DllImport("MegviiFacepp-jni-0.4.7")]
		private static extern int nativeSetFaceppConfig (int handle, int minFaceSize, int rotation,
		                          int interval,
		                          int detection_mode,
		                          int left, int top,
		                          int right, int bottom,
		                          int one_face_tracking);

private float[] nativeDetect(byte[] imagedata, int w, int h, int rotation, FaceImageMode imagemode, ref int facecount)
		{
			Texture2D t;
			t.UpdateExternalTexture
			facecount = 0;
			GCHandle datah = GCHandle.Alloc (imagedata, GCHandleType.Pinned);

			System.IntPtr markp;
			lock (detectLock) {
				markp = nativeDetect (datah.AddrOfPinnedObject (), apihandle,
					w, h, rotation, (int)imagemode, facelandmarksize, ref facecount);
			}
			datah.Free();
//			System.IntPtr markp = nativeDetect ( System.Text.Encoding.UTF8.GetString(imagedata), apihandle,
//				w, h, (int)imagemode, facelandmarksize, ref facecount);
			if (facecount != 0) {
//				var p = Marshal.SizeOf (typeof(float));
				var  pointsl = facecount * facelandmarksize * 2 ;
				float[] landmarks = new float[pointsl];
				Marshal.Copy (markp, landmarks, 0, pointsl);
				return landmarks;
			}
			return new float[0];
		}

        public DetectData(Color32[] colors, int w, int h, int rotation, FaceImageMode imagemode)
			{
				this.width = w;
				this.height = h;
				this.rotation = rotation;
				var pixels = colors;
				this.imagemode = imagemode;
				var l = w * h;
				//@TODO MOVE TO THREAD
				if(imagemode == FaceImageMode.RGBA)
				{
					l *= 4;
					data = new byte[l];
					GCHandle handle = default(GCHandle);
					try
					{
						handle = GCHandle.Alloc(colors, GCHandleType.Pinned);
						IntPtr ptr = handle.AddrOfPinnedObject();
						Marshal.Copy(ptr, data, 0, l);
					}
					finally
					{
						if (handle != default(GCHandle))
							handle.Free();
					}
				}
				else if(imagemode == FaceImageMode.GRAY)
				{
					data = new byte[l];
					Color32 pixel;
					for(int i= 0; i < l; i++)
					{
						pixel = pixels[i];
	//					graydata[i] =  (byte)(pixels[i]. * 255);
	//				for (int j = 0; j < texture.height; ++j)
	//					for (int i = 0; i < texture.width; ++i) {
	//						var pixel = pixels[
						data[i] = (byte) ((299 * pixel.r  + 587
							* pixel.g  + 114 * pixel.b )/1000 );
					}
	//					}
				}
				else if(imagemode == FaceImageMode.RGB)
				{
					data = new byte[l * 3];
					Color32 pixel;
					for(int i = 0; i < l; i++)
					{
						pixel = pixels[i];
						data[i*3 ] = pixel.r;
						data[i*3 + 1] = pixel.g;
						data[i*3 + 2] = pixel.b;
					}
				}

			}
{% endhighlight %}


**补充**：以上仅针对有些基础的同学，如果看了这些还是云里雾里的话，直接邮箱留言我发demo吧。

[1]:https://www.faceplusplus.com.cn/face-landmark-sdk/


