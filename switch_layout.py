
import re
import click
import pyperclip
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

EN_LOWER = "`qwertyuiop[]asdfghjkl;'zxcvbnm,./"
RU_LOWER = "ёйцукенгшщзхъфывапролджэячсмитьбю."
EN_TO_RU = str.maketrans(EN_LOWER + EN_LOWER.upper(), RU_LOWER + RU_LOWER.upper())
RU_TO_EN = str.maketrans(RU_LOWER + RU_LOWER.upper(), EN_LOWER + EN_LOWER.upper())

CYRILLIC_RE = re.compile(r"[а-яА-ЯёЁ]")
LATIN_RE = re.compile(r"[a-zA-Z]")

DATABASE_URL = "sqlite:///stats.db"
engine = create_engine(DATABASE_URL)


class Base(DeclarativeBase):
    pass


class Translation(Base):
    __tablename__ = "translations"

    id: Mapped[int] = mapped_column(primary_key=True)
    direction: Mapped[str] = mapped_column()
    length: Mapped[int] = mapped_column()


def init_db():
    Base.metadata.create_all(engine)


def save_translation(session: Session, direction: str, length: int) -> None:
    session.add(Translation(direction=direction, length=length))
    session.commit()


def get_stats(session: Session):
    en_ru = session.scalar(
        select(func.count()).select_from(Translation).where(Translation.direction == "en-ru")
    ) or 0
    ru_en = session.scalar(
        select(func.count()).select_from(Translation).where(Translation.direction == "ru-en")
    ) or 0
    longest = session.scalar(select(func.max(Translation.length)))
    return en_ru, ru_en, longest or 0


def format_stat(count: int, total: int, view: str | None) -> str:
    percent = count / total * 100 if total else 0
    if view == "abs":
        return str(count)
    if view == "rel":
        return f"{percent:.1f}%"
    return f"{count} ({percent:.1f}%)"


def detect_direction(text: str) -> str:
    """Определить направление конвертации по буквам исходного текста."""
    if not text or not text.strip():
        raise ValueError("Буфер обмена пуст")

    cyrillic_count = len(CYRILLIC_RE.findall(text))
    latin_count = len(LATIN_RE.findall(text))

    if cyrillic_count == 0 and latin_count == 0:
        raise ValueError("В тексте нет букв для определения раскладки")

    if cyrillic_count == latin_count:
        raise ValueError("Не удалось однозначно определить раскладку")

    if latin_count > cyrillic_count:
        return "en-ru"

    return "ru-en"


def convert_layout(text: str) -> str:
    """Преобразовать текст в противоположную раскладку."""
    direction = detect_direction(text)
    table = EN_TO_RU if direction == "en-ru" else RU_TO_EN
    return text.translate(table)


@click.group()
def cli():
    """Конвертация текста между русской и английской раскладками."""


@cli.command()
def convert():
    """Преобразовать текст из буфера обмена."""
    try:
        original = pyperclip.paste()
        direction = detect_direction(original)
        converted = convert_layout(original)
        pyperclip.copy(converted)
    except (ValueError, pyperclip.PyperclipException) as error:
        raise click.ClickException(str(error)) from error

    init_db()
    with Session(engine) as session:
        save_translation(session, direction, len(original))

    click.echo(converted)


@click.command()
@click.option(
    "--view",
    type=click.Choice(["abs", "rel"]),
    default=None,
    help="abs — количество, rel — проценты; по умолчанию показываются оба значения.",
)
def stats(view):
    """Показать статистику конвертаций."""
    init_db()
    with Session(engine) as session:
        en_ru, ru_en, longest = get_stats(session)

    total = en_ru + ru_en
    click.echo(f"en-ru: {format_stat(en_ru, total, view)}")
    click.echo(f"ru-en: {format_stat(ru_en, total, view)}")
    click.echo(f"Самый длинный текст: {longest} символов")


@click.group()
def cli():
    """Команды утилиты switch_layout."""


cli.add_command(convert)
cli.add_command(stats)


if __name__ == "__main__":
    cli()
