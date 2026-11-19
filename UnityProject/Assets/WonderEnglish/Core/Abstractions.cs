using System.Threading;
using System.Threading.Tasks;

namespace WonderEnglish.Core
{
    /// <summary>
    /// 日志级别。数值越小越详细。
    /// </summary>
    public enum LogLevel
    {
        /// <summary>调试细节，正式包默认关闭。</summary>
        Debug = 0,

        /// <summary>常规运行信息。</summary>
        Info = 1,

        /// <summary>可恢复的异常情况。</summary>
        Warning = 2,

        /// <summary>需要关注的失败。</summary>
        Error = 3,
    }

    /// <summary>
    /// 应用日志抽象。领域层只依赖该接口，具体输出由基础设施层实现。
    /// </summary>
    public interface ILogger
    {
        /// <summary>写入一条日志。</summary>
        void Log(LogLevel level, string category, string message);
    }

    /// <summary>
    /// 时钟抽象，便于对超时、耗时统计做确定性测试。
    /// </summary>
    public interface IClock
    {
        /// <summary>自某个固定起点经过的毫秒数，单调递增。</summary>
        long ElapsedMilliseconds { get; }
    }

    /// <summary>
    /// 课程步骤执行器的异步执行入口。
    /// 任务实现只报告结果，不自行决定课程下一步。
    /// </summary>
    /// <typeparam name="TContext">执行所需上下文。</typeparam>
    /// <typeparam name="TResult">执行结果。</typeparam>
    public interface IStepExecutor<in TContext, TResult>
    {
        /// <summary>执行步骤；<paramref name="token"/> 取消时必须尽快返回。</summary>
        Task<Result<TResult>> ExecuteAsync(TContext context, CancellationToken token);
    }
}
