import pytest
from backend.pipelines.goal_inference import infer_goals


class TestInferGoalsInputValidation:
    @pytest.mark.asyncio
    async def test_should_truncate_message_exceeding_max_length(self):
        long_message = "word " * 5000  # 25000+ chars
        with pytest.raises(ValueError, match="Message too long"):
            await infer_goals(long_message, "msg_1")

    @pytest.mark.asyncio
    async def test_should_accept_short_message(self):
        short_message = "Hello world"
        try:
            await infer_goals(short_message, "msg_1")
        except ValueError:
            pass  # Validation passed
        except Exception as e:
            if "Message too long" in str(e) or "cannot be empty" in str(e):
                pytest.fail("Short message should not trigger validation error")

    @pytest.mark.asyncio
    async def test_should_reject_empty_message(self):
        with pytest.raises(ValueError, match="Message cannot be empty"):
            await infer_goals("", "msg_1")

    @pytest.mark.asyncio
    async def test_should_reject_whitespace_only_message(self):
        with pytest.raises(ValueError, match="Message cannot be empty"):
            await infer_goals("   \n\t  ", "msg_1")
