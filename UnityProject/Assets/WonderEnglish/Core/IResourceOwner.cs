namespace WonderEnglish.Core
{
    /// <summary>
    /// 可被显式释放的资源持有者。实现必须幂等：重复调用 <see cref="Dispose"/> 不得抛异常。
    /// </summary>
    public interface IResourceOwner
    {
        /// <summary>释放持有的资源并取消未完成的操作。</summary>
        void Dispose();
    }
}
