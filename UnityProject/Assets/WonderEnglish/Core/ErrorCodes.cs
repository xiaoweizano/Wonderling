using System;

namespace WonderEnglish.Core
{
    /// <summary>
    /// 操作失败时使用的稳定错误码常量。
    /// 用常量而非散落的字符串字面量，避免拼写不一致导致上层分支失配。
    /// </summary>
    public static class ErrorCodes
    {
        /// <summary>课程 JSON 缺少必需字段。</summary>
        public const string CourseMissingField = "course.missing_field";

        /// <summary>课程 schemaVersion 不受当前引擎支持。</summary>
        public const string CourseUnsupportedSchema = "course.unsupported_schema";

        /// <summary>课程 JSON 结构或类型错误，无法反序列化。</summary>
        public const string CourseMalformed = "course.malformed";

        /// <summary>步骤引用了不存在的 stepId。</summary>
        public const string CourseBrokenJump = "course.broken_jump";

        /// <summary>步骤引用了本地资源清单中不存在的资源。</summary>
        public const string CourseMissingAsset = "course.missing_asset";

        /// <summary>课程文件中存在重复的 stepId。</summary>
        public const string CourseDuplicateStep = "course.duplicate_step";

        /// <summary>资源加载失败。</summary>
        public const string AssetLoadFailed = "asset.load_failed";

        /// <summary>请求的资源在清单中不存在。</summary>
        public const string AssetNotFound = "asset.not_found";

        /// <summary>麦克风权限被用户拒绝。</summary>
        public const string SpeechPermissionDenied = "speech.permission_denied";

        /// <summary>未检测到语音输入。</summary>
        public const string SpeechNoInput = "speech.no_input";

        /// <summary>语音识别过程发生错误。</summary>
        public const string SpeechRecognitionFailed = "speech.recognition_failed";

        /// <summary>离线语音模型加载失败或缺失。</summary>
        public const string SpeechModelUnavailable = "speech.model_unavailable";

        /// <summary>当前平台不支持该能力（例如 Editor 下调用真实录音）。</summary>
        public const string PlatformUnsupported = "platform.unsupported";

        /// <summary>操作被取消令牌中止。</summary>
        public const string OperationCancelled = "operation.cancelled";

        /// <summary>数据库读写失败。</summary>
        public const string DatabaseFailure = "database.failure";
    }

    /// <summary>
    /// 操作被取消时抛出的异常，用于区分正常取消与真实故障。
    /// </summary>
    public sealed class OperationCancelledException : OperationCanceledException
    {
        /// <summary>使用指定取消令牌创建异常。</summary>
        public OperationCancelledException(System.Threading.CancellationToken token)
            : base("操作已取消。", token)
        {
        }
    }
}
