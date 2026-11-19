namespace WonderEnglish.Core
{
    /// <summary>
    /// 表示一次可能失败的操作结果，避免用异常表达正常业务流程分支。
    /// </summary>
    public readonly struct Result
    {
        private Result(bool isSuccess, string errorCode, string errorMessage)
        {
            IsSuccess = isSuccess;
            ErrorCode = errorCode;
            ErrorMessage = errorMessage;
        }

        /// <summary>操作是否成功。</summary>
        public bool IsSuccess { get; }

        /// <summary>失败时的稳定错误码，用于上层分支判断与日志聚合。</summary>
        public string ErrorCode { get; }

        /// <summary>失败时的可读说明，面向开发者日志，不直接展示给儿童。</summary>
        public string ErrorMessage { get; }

        /// <summary>创建成功结果。</summary>
        public static Result Ok() => new Result(true, null, null);

        /// <summary>创建失败结果。</summary>
        public static Result Fail(string errorCode, string errorMessage) =>
            new Result(false, errorCode, errorMessage);

        /// <inheritdoc />
        public override string ToString() =>
            IsSuccess ? "Ok" : $"{ErrorCode}: {ErrorMessage}";
    }

    /// <summary>
    /// 携带成功值或失败信息的操作结果。
    /// </summary>
    /// <typeparam name="T">成功时的值类型。</typeparam>
    public readonly struct Result<T>
    {
        private Result(bool isSuccess, T value, string errorCode, string errorMessage)
        {
            IsSuccess = isSuccess;
            Value = value;
            ErrorCode = errorCode;
            ErrorMessage = errorMessage;
        }

        /// <summary>操作是否成功。</summary>
        public bool IsSuccess { get; }

        /// <summary>成功时的值；失败时为 <c>default</c>。</summary>
        public T Value { get; }

        /// <summary>失败时的稳定错误码。</summary>
        public string ErrorCode { get; }

        /// <summary>失败时的可读说明。</summary>
        public string ErrorMessage { get; }

        /// <summary>创建成功结果。</summary>
        public static Result<T> Ok(T value) => new Result<T>(true, value, null, null);

        /// <summary>创建失败结果。</summary>
        public static Result<T> Fail(string errorCode, string errorMessage) =>
            new Result<T>(false, default, errorCode, errorMessage);

        /// <summary>尝试取值；失败时返回 <c>false</c> 且 <paramref name="value"/> 为 <c>default</c>。</summary>
        public bool TryGetValue(out T value)
        {
            value = Value;
            return IsSuccess;
        }

        /// <inheritdoc />
        public override string ToString() =>
            IsSuccess ? $"Ok({Value})" : $"{ErrorCode}: {ErrorMessage}";
    }
}
