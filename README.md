# NonePrompt

Prompt toolkit for console interaction.

Typing is supported.

## Installation

```bash
pip install noneprompt
```

## Usage

### Input

```python
from noneprompt import InputPrompt

InputPrompt("What is your name?", validator=lambda string: True).prompt()
```

### Confirm

```python
from noneprompt import ConfirmPrompt

ConfirmPrompt("Are you sure?", default_choice=False).prompt()
```

### List

```python
from noneprompt import ListPrompt, Choice

ListPrompt("What is your favorite color?", choices=[Choice("Red"), Choice("Blue")]).prompt()
```

### Checkbox

```python
from noneprompt import CheckboxPrompt, Choice

CheckboxPrompt("Choose your favorite colors", choices=[Choice("Red"), Choice("Blue")]).prompt()
```

## Try from command line

```bash
noneprompt -h
```
