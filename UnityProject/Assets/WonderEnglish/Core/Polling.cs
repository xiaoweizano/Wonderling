using System.Threading;
using System.Threading.Tasks;

namespace WonderEnglish.Core
{
    /// <summary>
    /// 以固定时间间隔轮询外部状态，用于等待条件达成（如录音就绪、模型加载完成）。
    /// </summary>
    public static class Polling
    {
        /// <summary>
        /// 每隔 <paramref name="intervalMs"/> 毫秒检查一次 <paramref name="probe"/>，
        /// 直到其返回 <c>true</c>、超过 <paramref name="timeoutMs"/> 或令牌取消。
        /// </summary>
        /// <returns>条件在超时前达成返回 <c>true</c>；超时或取消返回 <c>false</c>。</returns>
        public static async Task<bool> WaitUntilAsync(
            System.Func<bool> probe,
            int intervalMs,
            int timeoutMs,
            CancellationToken token)
        {
            var elapsed = 0;
            while (elapsed < timeoutMs)
            {
                token.ThrowIfCancellationRequested();
                if (probe())
                {
                    return true;
                }

                await Task.Delay(intervalMs, token).ConfigureAwait(false);
                elapsed += intervalMs;
            }

            return probe();
        }
    }
}
