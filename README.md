# NonePrompt

Prompt toolkit for console interaction.

**Typing** is fully supported. **Async** is also supported!

## Installation

```bash
pip install noneprompt
```

## Prompt Usage

### Input

```python
from noneprompt import InputPrompt

InputPrompt("What is your name?", validator=lambda string: True).prompt()
await InputPrompt("What is your name?", validator=lambda string: True).prompt_async()
```

### Confirm

```python
from noneprompt import ConfirmPrompt

ConfirmPrompt("Are you sure?", default_choice=False).prompt()
await ConfirmPrompt("Are you sure?", default_choice=False).prompt_async()
```

### List

```python
from noneprompt import ListPrompt, Choice

ListPrompt("What is your favorite color?", choices=[Choice("Red"), Choice("Blue")]).prompt()
await ListPrompt("What is your favorite color?", choices=[Choice("Red"), Choice("Blue")]).prompt_async()
```

### Checkbox

```python
from noneprompt import CheckboxPrompt, Choice

CheckboxPrompt("Choose your favorite colors", choices=[Choice("Red"), Choice("Blue")]).prompt()
await CheckboxPrompt("Choose your favorite colors", choices=[Choice("Red"), Choice("Blue")]).prompt_async()
```

## Defaults and Cancellation

```python
from noneprompt import InputPrompt

result = InputPrompt("Press Ctrl-C to cancel.").prompt(default="Cancelled")
assert result == "Cancelled"
```

```python
from noneprompt import InputPrompt, CancelledError

try:
    InputPrompt("Press Ctrl-C to cancel.").prompt()
except CancelledError:
    # Do something
    pass
```

## Style Guide

See the docstring of prompt classes for more information.

```python
from noneprompt import InputPrompt
from prompt_toolkit.styles import Style

InputPrompt("What is your name?").prompt(style=Style([("input": "#ffffff"), ("answer": "bold")]))
```

Disable ansi colors:

```python
from noneprompt import InputPrompt

InputPrompt("What is your name?").prompt(no_ansi=True)
```

## Try from command line

```bash
noneprompt -h
```
