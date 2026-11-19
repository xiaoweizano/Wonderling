using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using WonderEnglish.Core;

namespace WonderEnglish.Domain
{
    /// <summary>
    /// 老师语义动作。表现层映射为具体 Animator 状态，
    /// 课程 JSON 只引用这些语义名，不接触 Animator 参数。
    /// </summary>
    public enum TeacherAction
    {
        /// <summary>自然待机。</summary>
        Idle,

        /// <summary>面向孩子打招呼。</summary>
        Greeting,

        /// <summary>正在讲解。</summary>
        Speaking,

        /// <summary>专注倾听。</summary>
        Listening,

        /// <summary>思考，不表现焦虑。</summary>
        Thinking,

        /// <summary>温和鼓励。</summary>
        Encourage,

        /// <summary>庆祝成功。</summary>
        Celebrate,

        /// <summary>指向或引导视线。</summary>
        Guide,
    }

    /// <summary>
    /// 老师表现层控制器。由课程引擎通过语义动作命令驱动。
    /// </summary>
    public interface ITeacherPresenter
    {
        /// <summary>播放指定语义动作；返回的动作在完成或被打断时结束。</summary>
        Task PerformAsync(TeacherAction action, CancellationToken token);
    }

    /// <summary>
    /// 音频播放服务。所有方法必须在 Unity 主线程调用。
    /// </summary>
    public interface IAudioService
    {
        /// <summary>播放指定音频资源。</summary>
        void Play(string audioId);

        /// <summary>停止当前播放。</summary>
        void Stop();

        /// <summary>暂停当前播放，保留播放位置。</summary>
        void Pause();

        /// <summary>从暂停位置继续播放。</summary>
        void Resume();

        /// <summary>当前是否有音频在播放。</summary>
        bool IsPlaying { get; }

        /// <summary>一次播放结束后触发，参数为音频资源 ID。</summary>
        event Action<string> PlaybackCompleted;
    }

    /// <summary>
    /// 单次语音识别结果。ASR 置信度不等于发音评分，两者不可混用。
    /// </summary>
    public sealed class SpeechResult
    {
        /// <summary>识别流程是否成功完成（不代表发音正确）。</summary>
        public bool Success { get; set; }

        /// <summary>识别到的文本；失败时为空字符串。</summary>
        public string RecognizedText { get; set; } = string.Empty;

        /// <summary>ASR 置信度，仅供调试与阈值判断，不得作为发音分数。</summary>
        public float? Confidence { get; set; }

        /// <summary>录音时长（毫秒）。</summary>
        public int DurationMs { get; set; }

        /// <summary>失败时的错误码，见 <see cref="ErrorCodes"/>。</summary>
        public string ErrorCode { get; set; } = string.Empty;

        /// <summary>失败时的可读说明。</summary>
        public string ErrorMessage { get; set; } = string.Empty;
    }

    /// <summary>
    /// 离线语音服务。实现必须保证录音只在本地处理，不产生任何网络传输。
    /// </summary>
    public interface ISpeechService
    {
        /// <summary>初始化录音与识别引擎；失败时返回错误，调用方应降级而非阻断课程。</summary>
        Task<Result> InitializeAsync(CancellationToken token);

        /// <summary>开始录音。权限被拒绝时返回 <see cref="ErrorCodes.SpeechPermissionDenied"/>。</summary>
        Task<Result> StartRecordingAsync(CancellationToken token);

        /// <summary>停止录音并返回识别结果。</summary>
        Task<SpeechResult> StopRecordingAsync(CancellationToken token);

        /// <summary>取消当前录音并清理临时文件。</summary>
        Task CancelRecordingAsync();

        /// <summary>释放引擎与音频资源。</summary>
        Task DisposeAsync();
    }

    /// <summary>
    /// 本地资源清单中的一条资源记录。
    /// </summary>
    public sealed class AssetDescriptor
    {
        /// <summary>资源逻辑 ID，课程 JSON 引用该值。</summary>
        public string AssetId { get; set; } = string.Empty;

        /// <summary>资源在本地资源系统中的地址。</summary>
        public string Location { get; set; } = string.Empty;

        /// <summary>资源类型，例如 <c>audio</c>、<c>sprite</c>、<c>prefab</c>。</summary>
        public string AssetType { get; set; } = string.Empty;
    }

    /// <summary>
    /// 本地资源提供者。所有必需资源随安装包交付，不得依赖远程下载。
    /// </summary>
    public interface IResourceProvider
    {
        /// <summary>该资源实例是否已加载。</summary>
        bool IsLoaded(string assetId);

        /// <summary>加载资源实例；失败时返回错误而不是抛异常。</summary>
        Task<Result<T>> LoadAsync<T>(string assetId, CancellationToken token) where T : class;

        /// <summary>释放单个资源实例。</summary>
        void Release(string assetId);

        /// <summary>释放全部已加载资源。</summary>
        void ReleaseAll();

        /// <summary>查询资源是否存在于清单。</summary>
        bool Contains(string assetId);

        /// <summary>清单中的全部资源，用于课程加载前的引用校验。</summary>
        IReadOnlyCollection<AssetDescriptor> AllAssets { get; }
    }
}
