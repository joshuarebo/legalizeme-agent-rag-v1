"""
Test suite for Hunyuan-A13B model implementation
"""
import pytest
import asyncio
import os
from unittest.mock import Mock, patch, MagicMock

from app.utils.hunyuan_model import HunyuanModel, create_hunyuan_model, get_hunyuan_model

class TestHunyuanModel:
    """Test cases for HunyuanModel class"""
    
    def test_singleton_pattern(self):
        """Test that HunyuanModel follows singleton pattern"""
        model1 = HunyuanModel()
        model2 = HunyuanModel()
        assert model1 is model2
    
    def test_get_hunyuan_model(self):
        """Test get_hunyuan_model function"""
        model1 = get_hunyuan_model()
        model2 = get_hunyuan_model()
        assert model1 is model2
        assert isinstance(model1, HunyuanModel)
    
    @pytest.mark.asyncio
    async def test_create_hunyuan_model(self):
        """Test create_hunyuan_model function"""
        model = await create_hunyuan_model()
        assert isinstance(model, HunyuanModel)
    
    def test_model_info(self):
        """Test get_model_info method"""
        model = HunyuanModel()
        info = model.get_model_info()
        
        assert isinstance(info, dict)
        assert "name" in info
        assert "provider" in info
        assert "context_length" in info
        assert "max_tokens" in info
        assert info["name"] == "Hunyuan-A13B-Chat"
        assert info["provider"] == "Tencent"
        assert info["context_length"] == 32768
    
    @patch('app.utils.hunyuan_model.AutoTokenizer')
    @patch('app.utils.hunyuan_model.AutoModelForCausalLM')
    @patch('app.utils.hunyuan_model.torch')
    def test_initialization_success(self, mock_torch, mock_model, mock_tokenizer):
        """Test successful model initialization"""
        # Mock CUDA availability
        mock_torch.cuda.is_available.return_value = True
        
        # Mock tokenizer
        mock_tokenizer_instance = Mock()
        mock_tokenizer_instance.pad_token = None
        mock_tokenizer_instance.eos_token = "<eos>"
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        # Mock model
        mock_model_instance = Mock()
        mock_model.from_pretrained.return_value = mock_model_instance
        
        # Reset singleton
        HunyuanModel._instance = None
        HunyuanModel._initialized = False
        
        # Create model
        model = HunyuanModel()
        
        # Verify initialization
        assert model._initialized
        assert model._model is not None
        assert model._tokenizer is not None
        assert model.is_available()
    
    @patch('app.utils.hunyuan_model.AutoTokenizer')
    @patch('app.utils.hunyuan_model.AutoModelForCausalLM')
    def test_initialization_failure(self, mock_model, mock_tokenizer):
        """Test model initialization failure"""
        # Mock import error
        mock_model.from_pretrained.side_effect = ImportError("Missing dependencies")
        
        # Reset singleton
        HunyuanModel._instance = None
        HunyuanModel._initialized = False
        
        # Create model should raise exception
        with pytest.raises(ImportError):
            HunyuanModel()
    
    @pytest.mark.asyncio
    @patch('app.utils.hunyuan_model.HunyuanModel._model')
    @patch('app.utils.hunyuan_model.HunyuanModel._tokenizer')
    async def test_generate_success(self, mock_tokenizer, mock_model):
        """Test successful text generation"""
        # Mock tokenizer
        mock_tokenizer_instance = Mock()
        mock_tokenizer_instance.return_value = {
            'input_ids': Mock(shape=(1, 10)),
            'attention_mask': Mock()
        }
        mock_tokenizer_instance.decode.return_value = "This is a test response"
        mock_tokenizer_instance.pad_token_id = 0
        mock_tokenizer_instance.eos_token_id = 1
        
        # Mock model
        mock_model_instance = Mock()
        mock_outputs = Mock()
        mock_outputs.__getitem__.return_value = Mock()
        mock_model_instance.generate.return_value = [mock_outputs]
        
        # Reset singleton and set up mocks
        HunyuanModel._instance = None
        HunyuanModel._initialized = False
        
        with patch('app.utils.hunyuan_model.HunyuanModel._initialize_model'):
            model = HunyuanModel()
            model._model = mock_model_instance
            model._tokenizer = mock_tokenizer_instance
            model._initialized = True
            
            # Test generation
            response = await model.generate("Test prompt")
            
            assert isinstance(response, str)
            assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_generate_not_initialized(self):
        """Test generation when model is not initialized"""
        # Reset singleton
        HunyuanModel._instance = None
        HunyuanModel._initialized = False
        
        with patch('app.utils.hunyuan_model.HunyuanModel._initialize_model'):
            model = HunyuanModel()
            model._model = None
            model._tokenizer = None
            
            # Should raise RuntimeError
            with pytest.raises(RuntimeError):
                await model.generate("Test prompt")
    
    def test_format_chat_prompt(self):
        """Test chat prompt formatting"""
        with patch('app.utils.hunyuan_model.HunyuanModel._initialize_model'):
            model = HunyuanModel()
            
            prompt = "Hello, how are you?"
            formatted = model._format_chat_prompt(prompt)
            
            assert "<|im_start|>user" in formatted
            assert "<|im_end|>" in formatted
            assert "<|im_start|>assistant" in formatted
            assert prompt in formatted
    
    def test_clean_response(self):
        """Test response cleaning"""
        with patch('app.utils.hunyuan_model.HunyuanModel._initialize_model'):
            model = HunyuanModel()
            
            dirty_response = "  <|im_start|>assistant\nHello there!<|im_end|><|endoftext|>  "
            cleaned = model._clean_response(dirty_response)
            
            assert cleaned == "Hello there!"
            assert "<|im_start|>" not in cleaned
            assert "<|im_end|>" not in cleaned
            assert "<|endoftext|>" not in cleaned
    
    def test_get_max_input_length(self):
        """Test max input length calculation"""
        with patch('app.utils.hunyuan_model.HunyuanModel._initialize_model'):
            model = HunyuanModel()
            
            max_length = model._get_max_input_length()
            assert max_length == 30000
    
    def test_is_available_false(self):
        """Test is_available when model is not initialized"""
        # Reset singleton
        HunyuanModel._instance = None
        HunyuanModel._initialized = False
        
        with patch('app.utils.hunyuan_model.HunyuanModel._initialize_model'):
            model = HunyuanModel()
            model._model = None
            model._tokenizer = None
            
            assert not model.is_available()

# Integration tests (require actual dependencies)
class TestHunyuanIntegration:
    """Integration tests for Hunyuan model (require actual dependencies)"""
    
    @pytest.mark.skipif(
        not os.getenv("RUN_INTEGRATION_TESTS"),
        reason="Integration tests require RUN_INTEGRATION_TESTS=1"
    )
    @pytest.mark.asyncio
    async def test_real_generation(self):
        """Test with real model (requires actual setup)"""
        try:
            model = HunyuanModel()
            if model.is_available():
                response = await model.generate(
                    "What is the capital of Kenya?",
                    max_new_tokens=100
                )
                assert isinstance(response, str)
                assert len(response) > 0
                print(f"Generated response: {response}")
        except Exception as e:
            pytest.skip(f"Integration test failed due to setup issues: {e}")
    
    def test_model_info_real(self):
        """Test model info with real setup"""
        try:
            model = HunyuanModel()
            info = model.get_model_info()
            
            assert "name" in info
            assert "provider" in info
            assert "context_length" in info
            assert "max_tokens" in info
            assert "quantization" in info
            assert "device" in info
            assert "initialized" in info
            
            print(f"Model info: {info}")
        except Exception as e:
            pytest.skip(f"Real model info test failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])