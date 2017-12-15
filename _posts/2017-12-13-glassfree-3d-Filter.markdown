---
layout:  post
title:   使用 unity shader 实现裸眼3D
date:    2017-12-06 10:19:56
author: Gero
header-img: "img/post-bg-miui6.jpg"
tags:
    - 裸眼3D
    - Unity
    - shader
---

可支持大部分UI的裸眼3D化，3d模型部分则使用左右摄像机来达到这种效果。

**问题**：比较郁闷的是注释部分的代码在 `HLSL` 中都是好使的，翻译到 CG中就不行了，大概猜测是 cg shader 中`ComputeScreenPos`计算出来的屏幕坐标对应的`UV`坐标范围串了，然后鼓捣了一天，偶然的机会才试出来现在的方案，如果哪位大神知道其中原由，望告知不胜感激。

{% highlight shader %}
Shader "Hidden/NewImageEffectShader"
{
	Properties
	{
		_MainTex ("Texture", 2D) = "white" {}
	}
	SubShader
	{
		// No culling or depth
		//Cull Off ZWrite Off ZTest Always

		Pass
		{
			CGPROGRAM
			#pragma vertex vert
			#pragma fragment frag
			#pragma target 3.0
			#include "UnityCG.cginc"

			struct appdata
			{
				float4 vertex : POSITION;
				float2 uv : TEXCOORD0;
			};

			struct v2f
			{
				float2 uv : TEXCOORD0;
				float4 vertex : SV_POSITION;
			};

			v2f vert (appdata v)
			{
				v2f o;
				o.vertex = UnityObjectToClipPos(v.vertex);
				o.uv = v.uv;
				return o;
			}


			sampler2D _MainTex;



			fixed4 color1(float2 uv)
			{
			   return tex2D(_MainTex, float2(uv.x *0.5, uv.y));
			}

			fixed4 color2(float2 uv)
			{
			   return tex2D(_MainTex, float2(uv.x *0.5+0.5, uv.y));
			}

			fixed4 frag (v2f i) : SV_Target
			{
				float4 pos = ComputeScreenPos(i.vertex);
				float2 wpos = pos.xy / pos.w;
//				float2 uv = i.uv;
//				uv.x = uv.x * 0.5;
//                uv.x = uv.x + 0.5 * step(1.0, fmod(wpos.x, 2.0));
//				fixed4 col = tex2D(_MainTex, uv);
//				return col;

				float xset = step(1.0, fmod(wpos.x, 2.0));
				return color1(i.uv)*(1.0-xset) + color2(i.uv)*xset; 
			}
			ENDCG
		}
	}
}

{% endhighlight %}