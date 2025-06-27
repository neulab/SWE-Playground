"""Tests for the PromptRetriever class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from jinja2 import TemplateNotFound

from swe_play.utils.prompt_retriever import PromptRetriever, get_prompt


class TestPromptRetriever:
    """Test cases for PromptRetriever class."""

    def test_init_with_default_prompts_dir(self) -> None:
        """Test initialization with default prompts directory."""
        retriever = PromptRetriever()

        # Instead of checking exact path (which differs between local and CI environments),
        # check that the prompts directory exists and contains expected templates
        assert retriever.prompts_dir.exists()
        assert retriever.prompts_dir.is_dir()

        # Verify that the default prompts directory contains expected templates
        template_names = retriever.get_template_names()
        assert "propose-next-project-system" in template_names
        assert "propose-next-project-user" in template_names

    def test_init_with_custom_prompts_dir(self, tmp_path: Path) -> None:
        """Test initialization with custom prompts directory."""
        custom_dir = tmp_path / "custom_prompts"
        custom_dir.mkdir()

        retriever = PromptRetriever(custom_dir)
        assert retriever.prompts_dir == custom_dir

    def test_init_with_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test initialization with nonexistent directory raises error."""
        nonexistent_dir = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError) as exc_info:
            PromptRetriever(nonexistent_dir)

        assert str(nonexistent_dir) in str(exc_info.value)

    def test_get_template_names(self) -> None:
        """Test getting list of available template names."""
        retriever = PromptRetriever()
        template_names = retriever.get_template_names()

        # Should include the actual templates in the prompts directory
        assert "propose-next-project-system" in template_names
        assert "propose-next-project-user" in template_names
        assert all(name.endswith(".jinja") is False for name in template_names)

    def test_template_exists(self) -> None:
        """Test checking if template exists."""
        retriever = PromptRetriever()

        assert retriever.template_exists("propose-next-project-system") is True
        assert retriever.template_exists("propose-next-project-user") is True
        assert retriever.template_exists("nonexistent-template") is False

    def test_get_template(self) -> None:
        """Test getting a template by name."""
        retriever = PromptRetriever()

        template = retriever.get_template("propose-next-project-system")
        assert template is not None
        assert hasattr(template, "render")

    def test_get_template_caching(self) -> None:
        """Test that templates are cached after first retrieval."""
        retriever = PromptRetriever()

        # First call should load template
        template1 = retriever.get_template("propose-next-project-system")

        # Second call should use cached template
        template2 = retriever.get_template("propose-next-project-system")

        assert template1 is template2
        assert "propose-next-project-system" in retriever._template_cache

    def test_get_nonexistent_template(self) -> None:
        """Test getting nonexistent template raises error."""
        retriever = PromptRetriever()

        with pytest.raises(TemplateNotFound) as exc_info:
            retriever.get_template("nonexistent-template")

        assert "nonexistent-template" in str(exc_info.value)

    def test_render_template(self) -> None:
        """Test rendering a template with variables."""
        retriever = PromptRetriever()

        # Create a simple test template
        test_template_content = "Hello {{ name }}, you are {{ age }} years old!"
        test_template_path = retriever.prompts_dir / "test_template.jinja"

        with open(test_template_path, "w") as f:
            f.write(test_template_content)

        try:
            result = retriever.render_template("test_template", name="Alice", age=25)
            assert result == "Hello Alice, you are 25 years old!"
        finally:
            # Clean up test template
            test_template_path.unlink(missing_ok=True)

    def test_get_prompt(self) -> None:
        """Test getting a prompt string by name."""
        retriever = PromptRetriever()

        # Test with existing template
        prompt = retriever.get_prompt("propose-next-project-system")
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_raw_template_content(self) -> None:
        """Test getting raw template content."""
        retriever = PromptRetriever()

        content = retriever.get_raw_template_content("propose-next-project-system")
        assert isinstance(content, str)

        # Load the actual template content to compare against
        template_path = retriever.prompts_dir / "propose-next-project-system.jinja"
        with open(template_path, "r") as f:
            expected_content = f.read()

        assert content == expected_content

    def test_get_raw_template_content_nonexistent(self) -> None:
        """Test getting raw content of nonexistent template raises error."""
        retriever = PromptRetriever()

        with pytest.raises(FileNotFoundError) as exc_info:
            retriever.get_raw_template_content("nonexistent-template")

        assert "nonexistent-template" in str(exc_info.value)

    def test_list_prompts(self) -> None:
        """Test listing all prompts with their content."""
        retriever = PromptRetriever()

        prompts = retriever.list_prompts()

        assert isinstance(prompts, dict)
        assert "propose-next-project-system" in prompts
        assert "propose-next-project-user" in prompts

        # Check that values are strings (raw content)
        for content in prompts.values():
            assert isinstance(content, str)
            assert len(content) > 0

    def test_init_with_string_path(self) -> None:
        """Test initialization with string path."""
        # Create a temporary directory for this test
        with pytest.MonkeyPatch().context():
            temp_dir = Path(__file__).parent / "temp_prompts"
            temp_dir.mkdir(exist_ok=True)

            try:
                retriever = PromptRetriever(str(temp_dir))
                assert retriever.prompts_dir == temp_dir
            finally:
                # Clean up
                temp_dir.rmdir()


class TestGetPromptFunction:
    """Test cases for the convenience get_prompt function."""

    def test_get_prompt_function(self) -> None:
        """Test the convenience get_prompt function."""
        prompt = get_prompt("propose-next-project-system")
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestPromptRetrieverWithMockTemplates:
    """Test cases using mocked templates for isolated testing."""

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.glob")
    def test_get_template_names_with_mock(
        self, mock_glob: MagicMock, mock_exists: MagicMock
    ) -> None:
        """Test get_template_names with mocked file system."""
        mock_exists.return_value = True
        mock_glob.return_value = [
            Path("template1.jinja"),
            Path("template2.jinja"),
            Path("template3.jinja"),
        ]

        with patch("swe_play.utils.prompt_retriever.Environment"):
            retriever = PromptRetriever()
            template_names = retriever.get_template_names()

            assert template_names == ["template1", "template2", "template3"]

    @patch("pathlib.Path.exists")
    def test_template_exists_with_mock(self, mock_exists: MagicMock) -> None:
        """Test template_exists with mocked file system."""
        mock_exists.return_value = True

        with patch("swe_play.utils.prompt_retriever.Environment"):
            retriever = PromptRetriever()
            assert retriever.template_exists("test-template") is True

            mock_exists.return_value = False
            assert retriever.template_exists("test-template") is False


class TestPromptRetrieverErrorHandling:
    """Test error handling scenarios."""

    def test_init_with_invalid_path_type(self) -> None:
        """Test initialization with invalid path type."""
        with pytest.raises(TypeError) as exc_info:
            PromptRetriever(123)  # type: ignore[arg-type]  # Invalid type for testing

        assert "int" in str(exc_info.value)

    @patch("pathlib.Path.exists")
    def test_get_template_with_template_not_found(self, mock_exists: MagicMock) -> None:
        """Test get_template when Jinja raises TemplateNotFound."""
        mock_exists.return_value = True

        with patch("swe_play.utils.prompt_retriever.Environment") as mock_env:
            mock_env_instance = mock_env.return_value
            mock_env_instance.get_template.side_effect = TemplateNotFound("test.jinja")

            retriever = PromptRetriever()

            with pytest.raises(TemplateNotFound) as exc_info:
                retriever.get_template("test")

            assert "test" in str(exc_info.value)

    def test_render_template_with_invalid_variables(self) -> None:
        """Test render_template with variables that cause Jinja errors."""
        retriever = PromptRetriever()

        # Create a template that requires a variable
        test_content = "Hello {{ name }}!"
        test_path = retriever.prompts_dir / "test_error.jinja"

        with open(test_path, "w") as f:
            f.write(test_content)

        try:
            # Should raise an error when 'name' variable is not provided
            with pytest.raises(Exception) as exc_info:
                retriever.render_template("test_error")

            # Check that it's a Jinja-related error
            assert "name" in str(exc_info.value)
        finally:
            test_path.unlink(missing_ok=True)
