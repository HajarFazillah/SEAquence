package com.talkativ

import android.app.Application
import android.util.Log
import com.facebook.react.PackageList
import com.facebook.react.ReactApplication
import com.facebook.react.ReactHost
import com.facebook.react.ReactNativeApplicationEntryPoint.loadReactNative
import com.facebook.react.defaults.DefaultReactHost.getDefaultReactHost
import com.kakao.sdk.common.KakaoSdk
import com.kakao.sdk.common.util.Utility

class MainApplication : Application(), ReactApplication {

  override val reactHost: ReactHost by lazy {
    getDefaultReactHost(
      context = applicationContext,
      packageList =
        PackageList(this).packages.apply {
        },
    )
  }

  override fun onCreate() {
    super.onCreate()
    loadReactNative(this)
    KakaoSdk.init(this, getString(R.string.kakao_app_key))
    val keyHash = Utility.getKeyHash(this)
    Log.d("KeyHash", "KeyHash: $keyHash")
  }
}