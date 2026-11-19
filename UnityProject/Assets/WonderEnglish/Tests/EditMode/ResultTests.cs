using NUnit.Framework;
using WonderEnglish.Core;

namespace WonderEnglish.Tests.EditMode
{
    /// <summary>
    /// <see cref="Result"/> 与 <see cref="Result{T}"/> 的行为约定测试。
    /// 这两个类型是全部服务层错误传递的基础，行为变化会影响所有调用方。
    /// </summary>
    public sealed class ResultTests
    {
        [Test]
        public void Ok_ShouldHaveNoError()
        {
            var result = Result.Ok();

            Assert.IsTrue(result.IsSuccess);
            Assert.IsNull(result.ErrorCode);
            Assert.IsNull(result.ErrorMessage);
        }

        [Test]
        public void Fail_ShouldCarryCodeAndMessage()
        {
            var result = Result.Fail("test.code", "测试说明");

            Assert.IsFalse(result.IsSuccess);
            Assert.AreEqual("test.code", result.ErrorCode);
            Assert.AreEqual("测试说明", result.ErrorMessage);
        }

        [Test]
        public void GenericOk_ShouldExposeValue()
        {
            var result = Result<int>.Ok(42);

            Assert.IsTrue(result.IsSuccess);
            Assert.AreEqual(42, result.Value);
            Assert.IsTrue(result.TryGetValue(out var value));
            Assert.AreEqual(42, value);
        }

        [Test]
        public void GenericFail_ShouldReturnDefaultOnTryGetValue()
        {
            var result = Result<int>.Fail(ErrorCodes.AssetNotFound, "缺失资源");

            Assert.IsFalse(result.IsSuccess);
            Assert.IsFalse(result.TryGetValue(out var value));
            Assert.AreEqual(0, value);
            Assert.AreEqual(ErrorCodes.AssetNotFound, result.ErrorCode);
        }

        [Test]
        public void ToString_ShouldBeReadableInLogs()
        {
            StringAssert.Contains("test.code", Result.Fail("test.code", "说明").ToString());
            StringAssert.Contains("Ok", Result.Ok().ToString());
        }
    }
}
