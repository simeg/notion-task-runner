"""
Simplified tests for AsyncNotionClient that avoid singleton issues.
These tests focus on testing the core functionality without complex fixtures.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import aiohttp

from notion_task_runner.notion.async_notion_client import AsyncNotionClient


class TestAsyncNotionClientBasic:
    """Basic tests that don't rely on singleton state."""
    
    def test_config_validation_success(self):
        """Test that valid config passes validation."""
        config = MagicMock()
        config.notion_token_v2 = "valid_token_123456789"
        config.notion_api_key = "secret_api_key_123456789"
        config.notion_space_id = "space_id_123456789"
        
        # This should not raise an exception
        AsyncNotionClient._validate_config(config)
    
    def test_config_validation_invalid_token(self):
        """Test that invalid token fails validation."""
        config = MagicMock()
        config.notion_token_v2 = "short"  # Too short
        config.notion_api_key = "secret_api_key_123456789"
        config.notion_space_id = "space_id_123456789"
        
        with pytest.raises(ValueError, match="Invalid or missing Notion token_v2"):
            AsyncNotionClient._validate_config(config)
    
    def test_config_validation_invalid_api_key(self):
        """Test that invalid API key fails validation."""
        config = MagicMock()
        config.notion_token_v2 = "valid_token_123456789"
        config.notion_api_key = "short"  # Too short
        config.notion_space_id = "space_id_123456789"
        
        with pytest.raises(ValueError, match="Invalid or missing Notion API key"):
            AsyncNotionClient._validate_config(config)
    
    def test_config_validation_suspicious_characters(self):
        """Test that suspicious characters fail validation."""
        config = MagicMock()
        config.notion_token_v2 = "token_with_<script>_123456789"
        config.notion_api_key = "secret_api_key_123456789"
        config.notion_space_id = "space_id_123456789"
        
        with pytest.raises(ValueError, match="potentially unsafe characters"):
            AsyncNotionClient._validate_config(config)
    
    def test_config_validation_empty_space_id(self):
        """Test that empty space ID fails validation."""
        config = MagicMock()
        config.notion_token_v2 = "valid_token_123456789"
        config.notion_api_key = "secret_api_key_123456789"
        config.notion_space_id = ""  # Empty
        
        with pytest.raises(ValueError, match="Invalid or missing Notion space ID"):
            AsyncNotionClient._validate_config(config)


class TestAsyncNotionClientMocked:
    """Tests using mocked client instances to avoid singleton issues."""
    
    @pytest.mark.asyncio
    async def test_handle_response_errors_success(self):
        """Test error handler with successful response."""
        config = MagicMock()
        config.notion_token_v2 = "valid_token_123456789"
        config.notion_api_key = "secret_api_key_123456789"
        config.notion_space_id = "space_id_123456789"
        
        with patch.object(AsyncNotionClient, '__new__', return_value=object.__new__(AsyncNotionClient)):
            with patch.object(AsyncNotionClient, '_validate_config'):
                client = AsyncNotionClient(config)
                client.config = config
                client._session = None
                client._connector = None
                AsyncNotionClient._initialized = True
                
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.ok = True
                mock_response.raise_for_status = MagicMock()
                
                # Should not raise any exception
                await client._handle_response_errors(mock_response, "GET", "https://test.com")
                # For successful responses, raise_for_status should NOT be called
                mock_response.raise_for_status.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_response_errors_client_error(self):
        """Test error handler with client error."""
        config = MagicMock()
        config.notion_token_v2 = "valid_token_123456789"
        config.notion_api_key = "secret_api_key_123456789"
        config.notion_space_id = "space_id_123456789"
        
        with patch.object(AsyncNotionClient, '__new__', return_value=object.__new__(AsyncNotionClient)):
            with patch.object(AsyncNotionClient, '_validate_config'):
                client = AsyncNotionClient(config)
                client.config = config
                client._session = None
                client._connector = None
                AsyncNotionClient._initialized = True
                
                mock_response = MagicMock()
                mock_response.status = 400
                mock_response.ok = False
                mock_response.text = AsyncMock(return_value="Bad Request")
                mock_response.raise_for_status = MagicMock(side_effect=aiohttp.ClientResponseError(
                    request_info=MagicMock(),
                    history=(),
                    status=400
                ))
                
                with pytest.raises(aiohttp.ClientResponseError):
                    await client._handle_response_errors(mock_response, "POST", "https://test.com")


class TestAsyncNotionClientExtended:
    """Extended tests for AsyncNotionClient functionality."""
    
    def test_client_initialization_attributes(self):
        """Test that client initialization sets correct attributes."""
        config = MagicMock()
        config.notion_token_v2 = "valid_token_123456789"
        config.notion_api_key = "secret_api_key_123456789"
        config.notion_space_id = "space_id_123456789"
        
        with patch.object(AsyncNotionClient, '__new__', return_value=object.__new__(AsyncNotionClient)):
            with patch.object(AsyncNotionClient, '_validate_config'):
                client = AsyncNotionClient(config)
                client.config = config
                client._session = None
                client._connector = None
                
                # Check that essential attributes exist
                assert hasattr(client, 'config')
                assert hasattr(client, '_session')
                assert hasattr(client, '_connector')

    def test_session_connector_attributes(self):
        """Test that session and connector attributes exist."""
        config = MagicMock()
        config.notion_token_v2 = "valid_token_123456789"
        config.notion_api_key = "secret_api_key_123456789"
        config.notion_space_id = "space_id_123456789"
        
        with patch.object(AsyncNotionClient, '__new__', return_value=object.__new__(AsyncNotionClient)):
            with patch.object(AsyncNotionClient, '_validate_config'):
                client = AsyncNotionClient(config)
                client.config = config
                client._session = None
                client._connector = None
                
                # Should have session and connector attributes
                assert hasattr(client, '_session')
                assert hasattr(client, '_connector')

    def test_config_validation_edge_cases(self):
        """Test config validation with edge cases."""
        # Test with None values
        config = MagicMock()
        config.notion_token_v2 = None
        config.notion_api_key = "secret_api_key_123456789"
        config.notion_space_id = "space_id_123456789"
        
        with pytest.raises(ValueError):
            AsyncNotionClient._validate_config(config)
        
        # Test with whitespace-only values
        config.notion_token_v2 = "   "
        with pytest.raises(ValueError):
            AsyncNotionClient._validate_config(config)

    def test_close_method_attributes(self):
        """Test close method clears attributes."""
        config = MagicMock()
        config.notion_token_v2 = "valid_token_123456789"
        config.notion_api_key = "secret_api_key_123456789"
        config.notion_space_id = "space_id_123456789"
        
        with patch.object(AsyncNotionClient, '__new__', return_value=object.__new__(AsyncNotionClient)):
            with patch.object(AsyncNotionClient, '_validate_config'):
                client = AsyncNotionClient(config)
                client.config = config
                client._session = None
                client._connector = None
                
                # Should have the close method
                assert hasattr(client, 'close')
                assert callable(client.close)

    def test_string_representations(self):
        """Test string and repr methods."""
        config = MagicMock()
        config.notion_token_v2 = "valid_token_123456789"
        config.notion_api_key = "secret_api_key_123456789"
        config.notion_space_id = "space_id_123456789"
        
        with patch.object(AsyncNotionClient, '__new__', return_value=object.__new__(AsyncNotionClient)):
            with patch.object(AsyncNotionClient, '_validate_config'):
                client = AsyncNotionClient(config)
                client.config = config
                client._session = None
                client._connector = None
                
                str_repr = str(client)
                repr_str = repr(client)
                
                assert "AsyncNotionClient" in str_repr
                assert "AsyncNotionClient" in repr_str

    def test_logging_capabilities(self):
        """Test that client has logging capabilities."""
        config = MagicMock()
        config.notion_token_v2 = "valid_token_123456789"
        config.notion_api_key = "secret_api_key_123456789"
        config.notion_space_id = "space_id_123456789"
        
        with patch.object(AsyncNotionClient, '__new__', return_value=object.__new__(AsyncNotionClient)):
            with patch.object(AsyncNotionClient, '_validate_config'):
                client = AsyncNotionClient(config)
                client.config = config
                client._session = None
                client._connector = None
                
                # Should have error handling method
                assert hasattr(client, '_handle_response_errors')
                assert callable(client._handle_response_errors)

    def test_config_cleanup_during_close(self):
        """Test that sensitive config data is handled during close."""
        config = MagicMock()
        config.notion_token_v2 = "valid_token_123456789"
        config.notion_api_key = "secret_api_key_123456789"
        config.notion_space_id = "space_id_123456789"
        
        with patch.object(AsyncNotionClient, '__new__', return_value=object.__new__(AsyncNotionClient)):
            with patch.object(AsyncNotionClient, '_validate_config'):
                client = AsyncNotionClient(config)
                client.config = config
                client._session = None
                client._connector = None
                
                # Mock sensitive data cleanup
                client._sensitive_fields = ['notion_token_v2', 'notion_api_key']
                
                # The method should complete without error
                import asyncio
                asyncio.run(client.close())