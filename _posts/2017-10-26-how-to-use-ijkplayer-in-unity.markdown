---
layout:     post
title:      在unity中使用ijkplayer解析4k/hls/rtsp/rtmp
date:       2017-10-26 12:00:00
author:     Gero
header-img: "img/post-bg-miui6.jpg"
tags:
    - unity
    - 播放器
    - 视频解析
---

**需求**：在unity中解析4K视频/mpeg4/mp4/rtsp/rtmp/hls视频

**场景**：需要在unity中实现较为复杂的ui和空间交互的同时，解析播放各种复杂的视频流

**问题分析及思路**：unity 的MovieTexture和比较常见的插件支持的视频解析功能太弱，个人觉得比较好用的就是 bilibili的 [ijkplayer][1]，基于[ffmpeg][2]，功能强大性能稳定且开源，是我辈最爱。 如果讲ijkplayer解析出的纹理装载到unity中，即可完美解决问题，解析直播流或是4k视频毫无压力，可以贴到球体/弧面上面轻松实现VR全景播放器等复杂功能和交互。

**参考资料**：[EasyMovieTexture][3] [ijkplayer][1]

**方案**：这个思路中关键点在于把ijkplayer解析出来的纹理传递给unity，所以我们需要一个 TextureId 来传递纹理（这也可以用 `Texture.LoadRawTextureData(byte[]`传递图像数据），但是这样效率太低），仔细阅读EasyMovieTexture.java这部分工作事实上已经做好了，那么最简单粗暴的方法则是直接找到其中的android.media.MediaPlayer 替换为 tv.danmaku.ijk.media.player.IjkMediaPlayer 即可。
贴上代码：

{% highlight java %}
public class EasyMovieTexture implements IMediaPlayer.OnPreparedListener, IMediaPlayer.OnBufferingUpdateListener, IMediaPlayer.OnCompletionListener, IMediaPlayer.OnErrorListener, OnFrameAvailableListener {
	private Activity 		m_UnityActivity = null;
	private IjkMediaPlayer m_MediaPlayer = null;
	
	private int				m_iUnityTextureID = -1;
	private int				m_iSurfaceTextureID = -1;
	private SurfaceTexture	m_SurfaceTexture = null;
	private Surface			m_Surface = null;
	private int 			m_iCurrentSeekPercent = 0;
	private int				m_iCurrentSeekPosition = 0;
	public int 				m_iNativeMgrID;
	private String 			m_strFileName;
	private int 			m_iErrorCode;
	private int				m_iErrorCodeExtra;
	private boolean			m_bRockchip = true;
	private boolean 		m_bSplitOBB = false;
	private String 			m_strOBBName;
	public boolean 			m_bUpdate= false;
	
	public static ArrayList<EasyMovieTexture> m_objCtrl = new ArrayList<EasyMovieTexture>();
	
	public static EasyMovieTexture GetObject(int iID)
	{
		for(int i = 0; i < m_objCtrl.size(); i++)
		{
			if(m_objCtrl.get(i).m_iNativeMgrID == iID)
			{
				return m_objCtrl.get(i);
			}
		}
		
		return null;
		
	}
	

	private static final int GL_TEXTURE_EXTERNAL_OES = 0x8D65;
	
	
	public native int InitNDK(Object obj);
	
	public native void SetAssetManager(AssetManager assetManager);
	public native int InitApplication();
	public native void QuitApplication();
	public native void SetWindowSize(int iWidth,int iHeight,int iUnityTextureID,boolean bRockchip);
	public native void RenderScene(float [] fValue, int iTextureID,int iUnityTextureID);
	public native void SetManagerID(int iID);
	public native int GetManagerID();
	public native int InitExtTexture();
	
	public native void SetUnityTextureID(int iTextureID);
	
	
	static
	{
		 System.loadLibrary("BlueDoveMediaRender");
	}
	
	MEDIAPLAYER_STATE m_iCurrentState = MEDIAPLAYER_STATE.NOT_READY;
	
	public void Destroy()
	{
		if(m_iSurfaceTextureID != -1)
		{
			int [] textures = new int[1];
			textures[0] = m_iSurfaceTextureID;
			GLES20.glDeleteTextures(1, textures, 0);
			m_iSurfaceTextureID = -1;
		}
		
		SetManagerID(m_iNativeMgrID);
		QuitApplication();
		
		m_objCtrl.remove(this);
	
		
		
	}
	
	public void UnLoad()
	{
		
	
		if(m_MediaPlayer!=null)
		{
			if(m_iCurrentState != MEDIAPLAYER_STATE.NOT_READY )
			{
				try {
					m_MediaPlayer.stop();
					m_MediaPlayer.release();
					
					
				} catch (SecurityException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				} catch (IllegalStateException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
				m_MediaPlayer = null;
				
			}
			else
			{
				try {
					m_MediaPlayer.release();
					
					
				} catch (SecurityException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				} catch (IllegalStateException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
				m_MediaPlayer = null;
			}
			
			if(m_Surface != null)
			{
				m_Surface.release();
				m_Surface = null;
			}
			
			if(m_SurfaceTexture != null)
			{
				m_SurfaceTexture.release();
				m_SurfaceTexture = null;
			}
			
			if(m_iSurfaceTextureID != -1)
			{
				int [] textures = new int[1];
				textures[0] = m_iSurfaceTextureID;
				GLES20.glDeleteTextures(1, textures, 0);
				m_iSurfaceTextureID = -1;
			}
		}
	}
	


	public boolean Load() throws SecurityException, IllegalStateException, IOException
	{
		UnLoad();
		
		
		m_iCurrentState = MEDIAPLAYER_STATE.NOT_READY;

		
		m_MediaPlayer = new IjkMediaPlayer();
		m_MediaPlayer.setOption(OPT_CATEGORY_PLAYER, "mediacodec", 1);
		m_MediaPlayer.setOption(OPT_CATEGORY_PLAYER, "opensles", 1);
		m_MediaPlayer.setOption(OPT_CATEGORY_PLAYER, "mediacodec-auto-rotate", 1);
		//int mediaHardDecoder = isDeviceSupportHardDecorder()? 1 : 0;
		m_MediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_CODEC, "mediacodec", 1);
		//player.setOption(IjkMediaPlayer.OPT_CATEGORY_CODEC, "mediacodec-avc", mediaHardDecoder);
		m_MediaPlayer.setOption(OPT_CATEGORY_PLAYER, "mediacodec-auto-rotate", 1);
		m_MediaPlayer.setOption(OPT_CATEGORY_PLAYER, "overlay-format", IjkMediaPlayer.SDL_FCC_RV32);
		m_MediaPlayer.setOption(OPT_CATEGORY_PLAYER, "framedrop", 1);
		//mediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "framedrop", 30);
		m_MediaPlayer.setOption(OPT_CATEGORY_PLAYER, "max-fps", 0);
		m_MediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_CODEC, "skip_loop_filter", 48);
		m_MediaPlayer.setAudioStreamType(AudioManager.STREAM_MUSIC);

		m_bUpdate = false;
		
		if(m_strFileName.contains("file://") == true)
		{
               File sourceFile = new File(m_strFileName.replace("file://", ""));
                   
               if ( sourceFile.exists() )
               {
            	   FileInputStream fs = new FileInputStream(sourceFile);
            	   //m_MediaPlayer.setDataSource(fs.getFD());
				   m_MediaPlayer.setDataSource(m_strFileName);
            	   fs.close();
               }
			
			
        }
		else if(m_strFileName.contains("://") == true)
		{
			try {
				Map<String, String> headers = new HashMap<String, String>();
				headers.put("rtsp_transport", "tcp") ;
				headers.put("max_analyze_duration", "1000") ;
				
				  
				//m_MediaPlayer.setDataSource(m_UnityActivity, Uri.parse(m_strFileName), headers);
				m_MediaPlayer.setDataSource(m_strFileName);
			} catch (IOException e) {
				// TODO Auto-generated catch block
				Log.e("Unity","Error m_MediaPlayer.setDataSource() : " + m_strFileName);
				e.printStackTrace();
				
				m_iCurrentState = MEDIAPLAYER_STATE.ERROR;
				
				return false;
			}
		}
		else
		{
			
			if(m_bSplitOBB)
			{
				try {
					
					
					
			        ZipResourceFile expansionFile = new ZipResourceFile(m_strOBBName);

			        Log.e("unity", m_strOBBName + " " + m_strFileName);
			        AssetFileDescriptor afd = expansionFile.getAssetFileDescriptor("assets/" + m_strFileName);
			        
			        ZipEntryRO[] data =expansionFile.getAllEntries();
			        
			        for(int i = 0; i <data.length; i++)
			        {
			        	Log.e("unity", data[i].mFileName);
			        }
			        
			        Log.e("unity", afd + " " );
			        //m_MediaPlayer.setDataSource(afd.getFileDescriptor(),afd.getStartOffset(),afd.getLength());
					//m_MediaPlayer.setDataSource(afd.getFileDescriptor());
					m_MediaPlayer.setDataSource(m_strFileName);

			    } catch (IOException e) {
			    	m_iCurrentState = MEDIAPLAYER_STATE.ERROR;
			        e.printStackTrace();
			        return false;
			    }
			}
			else
			{
				AssetFileDescriptor afd;
				try {
					afd = m_UnityActivity.getAssets().openFd(m_strFileName);
					//m_MediaPlayer.setDataSource(afd.getFileDescriptor(),afd.getStartOffset(),afd.getLength());
					//m_MediaPlayer.setDataSource(afd.getFileDescriptor());
					m_MediaPlayer.setDataSource(m_strFileName);
			        afd.close();
				} catch (IOException e) {
					// TODO Auto-generated catch block
					Log.e("Unity","Error m_MediaPlayer.setDataSource() : " + m_strFileName);
					e.printStackTrace();
					m_iCurrentState = MEDIAPLAYER_STATE.ERROR;
					return false;
				}
			}
		
			
		}
	
		
		if(m_iSurfaceTextureID == -1)
		{
			m_iSurfaceTextureID = InitExtTexture();	
		}
		
		
		m_SurfaceTexture = new SurfaceTexture(m_iSurfaceTextureID);
		m_SurfaceTexture.setOnFrameAvailableListener(this);
		m_Surface = new Surface( m_SurfaceTexture);
		
		m_MediaPlayer.setSurface(m_Surface);
		m_MediaPlayer.setOnPreparedListener(this);
		m_MediaPlayer.setOnCompletionListener(this);
		m_MediaPlayer.setOnErrorListener(this);

		
		m_MediaPlayer.prepareAsync();
		
		
		
		
		return true;
	}
	
	
	synchronized public void onFrameAvailable(SurfaceTexture surface) { 
	
		m_bUpdate = true; 
	} 

	
	public void UpdateVideoTexture()
	{
		
		if(m_bUpdate == false)
			return;
			
		if(m_MediaPlayer != null)	
		{
			if(m_iCurrentState == MEDIAPLAYER_STATE.PLAYING || m_iCurrentState == MEDIAPLAYER_STATE.PAUSED)
			{
			
				SetManagerID(m_iNativeMgrID);
				
			
				boolean [] abValue = new boolean[1];
				GLES20.glGetBooleanv(GLES20.GL_DEPTH_TEST, abValue,0);
				GLES20.glDisable(GLES20.GL_DEPTH_TEST);
				m_SurfaceTexture.updateTexImage();
				
				
				
				
		
				float [] mMat = new float[16];
	
				
				m_SurfaceTexture.getTransformMatrix(mMat);
				
				RenderScene(mMat,m_iSurfaceTextureID,m_iUnityTextureID);
				
				
				if(abValue[0])
				{
					GLES20.glEnable(GLES20.GL_DEPTH_TEST);
				}
				else
				{
					
				}
				
				abValue = null;
				
			}
		}
	}
	
	
	public void SetRockchip(boolean bValue)
	{
		m_bRockchip = bValue;
	}


	public void SetLooping(boolean bLoop)
	{
//		if(m_MediaPlayer != null)
//		m_MediaPlayer.setOption();
//		int loopCount = bLoop ? 0 : 1;
//		m_MediaPlayer.setOption(OPT_CATEGORY_PLAYER, "loop", loopCount);
//		_setLoopCount(loopCount);
	}
//
//	private native void _setLoopCount(int loopCount);

	
	public void SetVolume(float fVolume)
	{

		if(m_MediaPlayer != null)
		{
			m_MediaPlayer.setVolume(fVolume, fVolume);
		}


	}
	
	
	public void SetSeekPosition(int iSeek)
	{
		if(m_MediaPlayer != null)
		{
			if(m_iCurrentState == MEDIAPLAYER_STATE.READY || m_iCurrentState == MEDIAPLAYER_STATE.PLAYING || m_iCurrentState == MEDIAPLAYER_STATE.PAUSED)
			{
				m_MediaPlayer.seekTo(iSeek);
			}
		}
	}
	
	public int GetSeekPosition()
	{
		if(m_MediaPlayer != null)
		{
			if(m_iCurrentState == MEDIAPLAYER_STATE.READY || m_iCurrentState == MEDIAPLAYER_STATE.PLAYING  || m_iCurrentState == MEDIAPLAYER_STATE.PAUSED)
			{
				try {
					m_iCurrentSeekPosition = (int) m_MediaPlayer.getCurrentPosition();
				} catch (SecurityException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				} catch (IllegalStateException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
			}
		}
		
		return m_iCurrentSeekPosition;
	}
	
	public int GetCurrentSeekPercent()
	{
		return m_iCurrentSeekPercent;
	}
	
	
	public void Play(int iSeek)
	{
		if(m_MediaPlayer != null)
		{
			if(m_iCurrentState == MEDIAPLAYER_STATE.READY || m_iCurrentState == MEDIAPLAYER_STATE.PAUSED || m_iCurrentState == MEDIAPLAYER_STATE.END )
			{
					
				//m_MediaPlayer.seekTo(iSeek);
				m_MediaPlayer.start();
				
				m_iCurrentState = MEDIAPLAYER_STATE.PLAYING;
				
			}
		}
	}
	
	public void Reset()
	{
		if(m_MediaPlayer != null)
		{
			if(m_iCurrentState == MEDIAPLAYER_STATE.PLAYING)
			{
				m_MediaPlayer.reset();
				
			}
			
		}
		m_iCurrentState = MEDIAPLAYER_STATE.NOT_READY;
	}
	
	public void Stop()
	{
		if(m_MediaPlayer != null)
		{
			if(m_iCurrentState == MEDIAPLAYER_STATE.PLAYING)
			{
				m_MediaPlayer.stop();
				
			}
			
		}
		m_iCurrentState = MEDIAPLAYER_STATE.NOT_READY;
	}
	
	public void RePlay()
	{
		if(m_MediaPlayer != null)
		{
			if(m_iCurrentState == MEDIAPLAYER_STATE.PAUSED)
			{
				m_MediaPlayer.start();
				m_iCurrentState = MEDIAPLAYER_STATE.PLAYING;
				
			}
		}
	}
	
	public void Pause()
	{
		if(m_MediaPlayer != null)
		{
			if(m_iCurrentState == MEDIAPLAYER_STATE.PLAYING)
			{
				m_MediaPlayer.pause();
				m_iCurrentState = MEDIAPLAYER_STATE.PAUSED;
			}
		}
	}
	
	public int GetVideoWidth()
	{
		if(m_MediaPlayer != null)
		{
			return m_MediaPlayer.getVideoWidth();
		}
		
		return 0;
	}
	
	public int GetVideoHeight()
	{
		if(m_MediaPlayer != null)
		{
			return m_MediaPlayer.getVideoHeight();
		}
		
		return 0;
	}
	
	public boolean IsUpdateFrame()
	{
		if(m_bUpdate == true)
		{
			return true;
		}
		else
		{
			return false;
		}
	}
	
	public void SetUnityTexture(int iTextureID)
	{
		
		m_iUnityTextureID = iTextureID;
		SetManagerID(m_iNativeMgrID);
		SetUnityTextureID(m_iUnityTextureID);
		
	}
	public void SetUnityTextureID(Object texturePtr)
	{
		
	}
	
	
	public void SetSplitOBB( boolean bValue,String strOBBName)
	{
		m_bSplitOBB = bValue;
		m_strOBBName = strOBBName;
	}
	
	public int GetDuration()
	{
		if(m_MediaPlayer != null)
		{
			return (int)m_MediaPlayer.getDuration();
		}
		
		return -1;
	}
	
	
	public int InitNative(EasyMovieTexture obj) 
	{

		
		m_iNativeMgrID = InitNDK(obj);
		m_objCtrl.add(this);
		
		return m_iNativeMgrID;
		
	}
	
	public void SetUnityActivity(Activity unityActivity)
    {
		
		SetManagerID(m_iNativeMgrID);
		m_UnityActivity = unityActivity;
		SetAssetManager(m_UnityActivity.getAssets());
    }
	
	
	public void NDK_SetFileName(String strFileName)
	{
		m_strFileName = strFileName;
	}
	
	
	public void InitJniManager()
	{
		SetManagerID(m_iNativeMgrID);
		InitApplication();
	}
	
	
	

	public int GetStatus()
	{
		return m_iCurrentState.GetValue();
	}
	
	public void SetNotReady()
	{
		m_iCurrentState = MEDIAPLAYER_STATE.NOT_READY;
	}
	
	public void SetWindowSize()
	{
		
		SetManagerID(m_iNativeMgrID);
		SetWindowSize(GetVideoWidth(),GetVideoHeight(),m_iUnityTextureID ,m_bRockchip);
		
		
	}
	
	public int GetError()
	{
		return m_iErrorCode;
	}
	
	public int GetErrorExtra()
	{
		return m_iErrorCodeExtra;
	}

	@Override
	public boolean onError(IMediaPlayer iMediaPlayer, int i, int i1) {
	//public boolean onError(MediaPlayer arg0, int arg1, int arg2) {
		// TODO Auto-generated method stub


		if (iMediaPlayer == m_MediaPlayer)
        {
            String strError;

            switch (i)
            {
                case IMediaPlayer.MEDIA_ERROR_NOT_VALID_FOR_PROGRESSIVE_PLAYBACK:
                	strError = "MEDIA_ERROR_NOT_VALID_FOR_PROGRESSIVE_PLAYBACK";
                    break;
                case MediaPlayer.MEDIA_ERROR_SERVER_DIED:
                	strError = "MEDIA_ERROR_SERVER_DIED";
                	break;
                case MediaPlayer.MEDIA_ERROR_UNKNOWN:
                	strError = "MEDIA_ERROR_UNKNOWN";
                    break;
                default:
                	strError = "Unknown error " + i;
            }
            
            m_iErrorCode = i;
            m_iErrorCodeExtra = i1;
            
            



            m_iCurrentState = MEDIAPLAYER_STATE.ERROR;

            return true;
        }

        return false;
        
	}


	
	@Override
	public void onCompletion(IMediaPlayer arg0) {
		// TODO Auto-generated method stub
		if (arg0 == m_MediaPlayer)
			m_iCurrentState = MEDIAPLAYER_STATE.END;
		
	}

	@Override
	public void onBufferingUpdate(IMediaPlayer arg0, int arg1) {
		// TODO Auto-generated method stub
		
		
	
		if (arg0 == m_MediaPlayer)
			m_iCurrentSeekPercent = arg1;
		
		
		
        
	}

	@Override
	public void onPrepared(IMediaPlayer arg0) {
		// TODO Auto-generated method stub
		if (arg0 == m_MediaPlayer)
		{
			m_iCurrentState = MEDIAPLAYER_STATE.READY;
			
			SetManagerID(m_iNativeMgrID);
			m_iCurrentSeekPercent = 0;
			m_MediaPlayer.setOnBufferingUpdateListener(this);
			
		}
		
	}
	
	
	public enum MEDIAPLAYER_STATE
    {
		NOT_READY       (0),
		READY           (1),
        END     		(2),
        PLAYING         (3),
        PAUSED          (4),
        STOPPED         (5),
        ERROR           (6);

        private int iValue;
        MEDIAPLAYER_STATE (int i)
        {
            iValue = i;
        }
        public int GetValue()
        {
            return iValue;
        }
    }

}
{% endhighlight %}

**补充**: 以上仅仅针对有基础的同学们，如果看到这还是云里雾里的同学可以邮箱留言我直接发demo吧。


[1]:https://github.com/Bilibili/ijkplayer
[2]:https://github.com/FFmpeg/FFmpeg
[3]:https://www.assetstore.unity3d.com/en/#!/content/10032