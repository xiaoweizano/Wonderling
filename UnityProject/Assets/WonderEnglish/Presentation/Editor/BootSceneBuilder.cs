using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace WonderEnglish.Presentation.EditorTools
{
    /// <summary>
    /// 创建并维护 Boot 场景与 Android 构建入口。
    /// 阶段 0 只需要一个能启动的最小场景，用来验证安装包能装、能起、能退。
    /// </summary>
    public static class BootSceneBuilder
    {
        private const string ScenesFolder = "Assets/Scenes";
        private const string BootScenePath = ScenesFolder + "/Boot.unity";

        /// <summary>创建 Boot 场景并加入构建列表。</summary>
        [MenuItem("Wonder English/阶段 0 - 创建 Boot 场景")]
        public static void CreateBootScene()
        {
            if (!Directory.Exists(ScenesFolder))
            {
                Directory.CreateDirectory(ScenesFolder);
                AssetDatabase.Refresh();
            }

            var scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);
            var root = new GameObject("[Boot]");
            root.AddComponent<Boot.BootEntry>();

            EditorSceneManager.SaveScene(scene, BootScenePath);

            EditorBuildSettings.scenes = new[]
            {
                new EditorBuildSettingsScene(BootScenePath, true),
            };

            AssetDatabase.SaveAssets();
            Debug.Log($"[BootSceneBuilder] Boot 场景已创建: {BootScenePath}");
        }

        /// <summary>构建 Android APK 到 Builds/ 目录。</summary>
        [MenuItem("Wonder English/阶段 0 - 构建 Android APK")]
        public static void BuildApk()
        {
            var output = Path.GetFullPath(Path.Combine(Application.dataPath, "../Builds/WonderEnglish.apk"));
            Directory.CreateDirectory(Path.GetDirectoryName(output));

            var options = new BuildPlayerOptions
            {
                scenes = new[] { BootScenePath },
                locationPathName = output,
                target = BuildTarget.Android,
                targetGroup = BuildTargetGroup.Android,
                options = BuildOptions.None,
            };

            var report = BuildPipeline.BuildPlayer(options);
            var summary = report.summary;

            Debug.Log($"[BootSceneBuilder] 构建结果: {summary.result} " +
                      $"大小 {summary.totalSize / 1048576.0:F1} MB " +
                      $"耗时 {summary.totalTime.TotalSeconds:F0}s " +
                      $"错误 {summary.totalErrors}");

            if (summary.result != UnityEditor.Build.Reporting.BuildResult.Succeeded)
            {
                throw new BuildFailedException($"Android 构建失败: {summary.result}, " +
                                               $"错误数 {summary.totalErrors}");
            }
        }
    }
}
