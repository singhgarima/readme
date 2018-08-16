import unittest
from unittest import mock
from unittest.mock import call

from click.testing import CliRunner

from readme.commands import Fetcher
from readme.readme import cli
from tests.fixtures import create_news


class TestSource(unittest.TestCase):
    def setUp(self):
        self._runner = CliRunner()
        self._cli = cli

    def test_help(self):
        result = self._runner.invoke(self._cli, ["source", "--help"])

        self.assertEqual(0, result.exit_code)
        self.assertIn("get latest news from different sources", result.output)
        self.assertIn("--format [list|html]  Displays news in a format", result.output)
        self.assertIn("--output TEXT         Write to FILE instead of stdout", result.output)

    @mock.patch('readme.commands.Fetcher.fetch_and_format')
    @mock.patch('readme.commands.Fetcher.valid')
    def test_source_when_typical_then_should_display_help_text(self, mock_valid, _):
        mock_valid.return_value = True

        source_name = "hacker-news"
        result = self._runner.invoke(self._cli, ["source", source_name])

        self.assertEqual(0, result.exit_code)
        self.assertIn("Fetching news from source: %s" % source_name, result.output)

    @mock.patch('readme.commands.Fetcher.valid')
    @mock.patch('readme.commands.Fetcher.fetch_and_format')
    def test_source_when_typical_then_fetch_and_format_using_fetcher(self, mock_fetch_and_format, mock_valid):
        mock_valid.return_value = True

        source_name = "hacker-news"
        self._runner.invoke(self._cli, ["source", source_name])

        mock_fetch_and_format.assert_called_once_with()

    @mock.patch('readme.commands.Fetcher')
    def test_source_when_keywords_provided_then_fetch_and_format_using_fetcher(self, mock_fetcher):
        mock_object = mock.Mock()
        mock_fetcher.return_value = mock_object
        mock_object.fetch_and_format.return_value = True
        mock_object.mock_valid.return_value = True

        source_name = "hacker-news"
        self._runner.invoke(self._cli, ["source", source_name, "--keywords", "python,chaos"])

        mock_fetcher.assert_called_once_with(source_name, format_type='list', keywords=["python", "chaos"])
        mock_object.fetch_and_format.assert_called_once_with()

    @mock.patch('readme.commands.Fetcher.fetch_and_format')
    @mock.patch('readme.news_output.NewsOutput')
    def test_source_when_typical_then_should_display_stories(self, mock_output, mock_fetch_and_format):
        news_list = [(create_news()), (create_news())]
        mock_fetch_and_format.return_value = news_list

        source_name = "hacker-news"
        self._runner.invoke(self._cli, ["source", source_name])

        mock_output.assert_has_calls([call(news_list), call().write_to(file_name=None)])

    def test_when_missing_source(self):
        result = self._runner.invoke(self._cli, ["source"])

        self.assertNotEqual(0, result.exit_code)
        self.assertIn("Error: Missing argument \"source_name\".", result.output)

    @mock.patch('readme.commands.Fetcher.valid')
    def test_when_invalid_source(self, mock_valid):
        mock_valid.return_value = False

        result = self._runner.invoke(self._cli, ["source", "invalid"])

        self.assertIn("Invalid source supplied. See --help", result.output)


class TestSourceList(unittest.TestCase):
    def setUp(self):
        self._runner = CliRunner()
        self._cli = cli

    def test_typical(self):
        result = self._runner.invoke(self._cli, ["source", "list"])
        self.assertIn("Currently the plugin supports the following sources", result.output)
        self.assertIn("hacker-new", result.output)


class TestFetcher(unittest.TestCase):
    def setUp(self):
        self._keywords = ['a', 'b']
        self._fetcher = Fetcher('hacker-news', 'list', self._keywords)

    def test_initialize_when_typical(self):
        self.assertEqual('hacker-news', self._fetcher._source_name)
        self.assertEqual('list', self._fetcher._format_type)
        self.assertEqual(['a', 'b'], self._fetcher._keywords)

    def test_initialize_when_no_optional_parameter_is_provided(self):
        self._fetcher = Fetcher('hacker-news')

        self.assertEqual('hacker-news', self._fetcher._source_name)
        self.assertEqual('list', self._fetcher._format_type)
        self.assertEqual(None, self._fetcher._keywords)

    def test_valid(self):
        self.assertTrue(self._fetcher.valid())

    def test_valid_when_invalid_source_then_is_false(self):
        invalid_fetcher = Fetcher('invalid', 'list')
        self.assertFalse(invalid_fetcher.valid())

    @mock.patch('readme.news_formatters.ListNewsFormatter')
    @mock.patch('readme.sources.hacker_news.HackerNews.fetch')
    def test_fetch_and_format_when_typical_then_should_fetch_from_hacker_news_source(self, mock_fetch, _):
        news_list = ['news1', 'news2']
        mock_fetch.return_value = news_list

        self._fetcher.fetch_and_format()

        self.assertEqual(news_list, self._fetcher._news_list)
        mock_fetch.assert_called_once_with(keywords=self._keywords)

    @mock.patch('readme.news_formatters.ListNewsFormatter')
    @mock.patch('readme.sources.hacker_news.HackerNews.fetch')
    def test_fetch_and_format_when_typical_then_should_use_list_formatter_to_format_news(self, mock_fetch,
                                                                                         mock_formatter):
        news_list = ['news1', 'news2']
        mock_fetch.return_value = news_list

        self._fetcher.fetch_and_format()

        mock_formatter.assert_has_calls([call(news_list), call().format()])

    @mock.patch('readme.news_formatters.HtmlNewsFormatter')
    @mock.patch('readme.sources.hacker_news.HackerNews.fetch')
    def test_fetch_and_format_when_format_is_html_then_should_use_html_formatter_to_format_news(self, mock_fetch,
                                                                                                mock_formatter):
        news_list = ['news1', 'news2']
        mock_fetch.return_value = news_list

        self._fetcher._format_type = "html"
        self._fetcher.fetch_and_format()

        mock_formatter.assert_has_calls([call(news_list), call().format()])

    @mock.patch('readme.news_formatters.ListNewsFormatter')
    @mock.patch('readme.sources.hacker_news.HackerNews.fetch')
    def test_fetch_and_format_when_no_keywords_are_passed_then_should_pass_keywords_to_source(self, mock_fetch,
                                                                                           mock_formatter):
        news_list = ['news1', 'news2']
        mock_fetch.return_value = news_list

        self._fetcher = Fetcher('hacker-news')
        self._fetcher.fetch_and_format()

        mock_formatter.assert_has_calls([call(news_list), call().format()])
