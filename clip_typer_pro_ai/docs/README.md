# ClipTyper Pro + AI Assistant

Advanced clipboard automation and AI assistant application with comprehensive features.

## Features

- **Advanced Clipboard Management**: History tracking, monitoring, and quick access
- **AI Processing**: Support for multiple AI providers (DeepSeek, OpenAI, Claude)
- **File Context Attachment**: Attach PDF/TXT/DOC files for AI context with auto-cleanup
- **Global Hotkeys**: Customizable hotkey system with conflict detection
- **Telegram Integration**: Bi-directional communication with Telegram bot
- **Secure Storage**: Encrypted API keys and password protection
- **Typing Automation**: Human-like typing with interruption support
- **Snippet Management**: Text templates with variable expansion
- **Cross-platform**: Works on Windows, macOS, and Linux

## Architecture

The application follows a modular design with the following core components:

- **Core**: Business logic modules (typing engine, AI processor, clipboard manager, etc.)
- **UI**: User interface components (system tray, configuration dialogs, etc.)
- **Config**: Configuration management with versioned settings
- **Utils**: Utility functions and helpers
- **API**: AI provider integrations
- **Models**: Data models for the application

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r install/requirements.txt`
3. Run the application: `python main.py`

## Configuration

The application stores configuration in `config/app_settings.json` and supports:

- Hotkey customization
- AI provider settings
- Security configuration
- Performance tuning
- Display preferences

## Usage

### Default Hotkeys

- `Ctrl+Alt+Insert`: Type clipboard content
- `Ctrl+Alt+A`: Process clipboard with AI
- `Ctrl+Alt+V`: Paste clipboard content
- `Ctrl+Alt+M`: Toggle clipboard monitoring
- `Ctrl+Alt+C`: Clear history
- `Ctrl+Alt+H`: Show history

### System Tray Menu

Access the application through the system tray icon for quick actions and status information.

## Security

- API keys are stored encrypted
- Password protection for sensitive features
- Content filtering with configurable security levels
- Secure credential management

## Development

The project follows Python best practices with:

- Type hints for all public methods
- Comprehensive documentation
- Error handling and logging
- Unit and integration tests
- Code formatting with Black

## Contributing

See `docs/DEVELOPER_GUIDE.md` for detailed contribution guidelines.

## License

MIT License - see `LICENSE` file for details.