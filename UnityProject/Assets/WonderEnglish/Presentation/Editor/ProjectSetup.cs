using UnityEditor;
using UnityEditor.Build;
using UnityEngine;

namespace WonderEnglish.Presentation.EditorTools
{
    /// <summary>
    /// 阶段 0 的一次性工程初始化：配置包名、公司名、Android 构建设置与 URP。
    /// 通过 `Unity.exe -batchmode -executeMethod` 调用，可重复执行（幂等）。
    /// </summary>
    public static class ProjectSetup
    {
        private const string CompanyName = "WonderEnglish";
        private const string ProductName = "WonderEnglish";
        private const string BundleIdentifier = "com.wonderenglish.app";

        /// <summary>配置全部工程设置并保存。</summary>
        [MenuItem("Wonder English/阶段 0 - 应用工程配置")]
        public static void Apply()
        {
            PlayerSettings.companyName = CompanyName;
            PlayerSettings.productName = ProductName;

            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.Android, BundleIdentifier);
            PlayerSettings.Android.bundleVersionCode = 1;
            PlayerSettings.Android.minSdkVersion = AndroidSdkVersions.AndroidApiLevel24;
            PlayerSettings.Android.targetSdkVersion = (AndroidSdkVersions)35;

            // 儿童 App：固定横屏还是竖屏由课程交互决定，阶段 0 先锁定横屏，
            // 避免后续场景与 UI 布局反复返工。
            PlayerSettings.defaultInterfaceOrientation = UIOrientation.LandscapeLeft;

            // IL2CPP + ARM64 是目标设备的主流组合；保留 ARMv7 兼容老设备。
            PlayerSettings.SetScriptingBackend(NamedBuildTarget.Android, ScriptingImplementation.IL2CPP);
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARMv7 | AndroidArchitecture.ARM64;

            // 全离线：禁用需要网络的构建开关。
            PlayerSettings.Android.forceInternetPermission = false;

            AssetDatabase.SaveAssets();
            Debug.Log($"[ProjectSetup] 完成: bundle={BundleIdentifier} " +
                      $"minSdk={PlayerSettings.Android.minSdkVersion} " +
                      $"targetSdk={PlayerSettings.Android.targetSdkVersion} " +
                      $"backend={PlayerSettings.GetScriptingBackend(NamedBuildTarget.Android)} " +
                      $"abi={PlayerSettings.Android.targetArchitectures}");
        }
    }
}
