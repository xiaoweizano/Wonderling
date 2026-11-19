using UnityEngine;

namespace WonderEnglish.Presentation.Boot
{
    /// <summary>
    /// 应用入口。阶段 0 只负责确认安装包能启动、能显示状态并干净退出；
    /// 课程加载与场景切换在阶段 1 之后接入。
    /// </summary>
    public sealed class BootEntry : MonoBehaviour
    {
        private const string VersionText = "Wonder English — 阶段 0";

        private void Awake()
        {
            // 儿童 App 不锁屏休眠会让设备在课程中途黑屏。
            Screen.sleepTimeout = SleepTimeout.NeverSleep;
            Application.targetFrameRate = 60;

            // 阶段 0 的启动自检：确认应用能拿到基本运行环境。
            // 不做假数据填充，只输出真实可用信息。
            Debug.Log($"[Boot] 启动 platform={Application.platform} " +
                      $"version={Application.version} " +
                      $"unity={Application.unityVersion} " +
                      $"offline-mode={Application.internetReachability}");
        }

        private void OnGUI()
        {
            var style = new GUIStyle(GUI.skin.label)
            {
                fontSize = Mathf.RoundToInt(Screen.height * 0.035f),
                alignment = TextAnchor.MiddleCenter,
            };

            GUI.Label(new Rect(0, Screen.height * 0.42f, Screen.width, Screen.height * 0.16f),
                VersionText, style);
        }
    }
}
