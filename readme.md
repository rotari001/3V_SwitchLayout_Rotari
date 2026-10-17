Evgheni Rotari TI 232 Rus

# switch_layout

консольная утилита для переключения текста между русской и английской раскладками клавиатуры. Текст берётся из буфера обмена, преобразуется, записывается обратно и выводится в консоль.

## установка

```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

установка зависимостей:
```bash
pip install -r requirements.txt
```

## использование

скопируйте текст, набранный в неправильной раскладке, затем выполните команду:

```bash
python switch_layout.py convert
```

как пример: `ghbdtn` преобразуется в `привет`.

стата:
```bash
python switch_layout.py stats
python switch_layout.py stats --view abs
python switch_layout.py stats --view rel
```

история же хранится в SQLite-файле `stats.db`, который создаётся автоматически!

## тесты

```bash
pytest -v
```
