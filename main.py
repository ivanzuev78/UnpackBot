import asyncio
import os
import tempfile
import zipfile
import tarfile
import logging
import subprocess
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

# --- Настройка логгера ---
logging.basicConfig(
    level=logging.INFO,  # можно DEBUG для более подробных логов
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    logger.critical("Не найден BOT_TOKEN в переменных окружения")
    raise RuntimeError("Не найден BOT_TOKEN в переменных окружения")

bot = Bot(token=TOKEN)
dp = Dispatcher()


def extract_rar_with_unrar(file_path: str, extract_to: str):
    logger.info(f"Распаковка RAR архива: {file_path}")
    try:
        subprocess.run(
            ["unrar", "x", "-kb", "-o+", file_path, extract_to],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logger.info("RAR архив успешно распакован")
    except subprocess.CalledProcessError:
        logger.error("Ошибка при распаковке RAR")
        raise Exception("Ошибка при распаковке RAR")


def is_archive(file_path: str) -> bool:
    logger.debug(f"Проверка файла на архив: {file_path}")
    return (
        zipfile.is_zipfile(file_path)
        or tarfile.is_tarfile(file_path)
        or file_path.lower().endswith(".rar")
    )


def extract_archive(file_path: str, extract_to: str):
    logger.info(f"Начинаем распаковку архива: {file_path}")
    if zipfile.is_zipfile(file_path):
        with zipfile.ZipFile(file_path, "r") as z:
            z.extractall(extract_to)
        logger.info("ZIP архив успешно распакован")
    elif tarfile.is_tarfile(file_path):
        with tarfile.open(file_path, "r:*") as t:
            t.extractall(extract_to)
        logger.info("TAR архив успешно распакован")
    elif file_path.lower().endswith(".rar"):
        extract_rar_with_unrar(file_path, extract_to)
    else:
        logger.warning("Формат архива не поддерживается")


@dp.message(Command("start"))
async def cmd_start(message: Message):
    logger.info(f"Получена команда /start от {message.from_user.id}")
    await message.answer("Привет! Отправь мне архив, и я распакую его.")


@dp.message(F.document)
async def handle_file(message: Message):
    doc = message.document
    file_name = doc.file_name
    user_id = message.from_user.id
    logger.info(f"Пользователь {user_id} отправил файл: {file_name}")

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, file_name)
        await bot.download(doc, file_path)
        logger.info(f"Файл сохранён во временную папку: {file_path}")

        if not is_archive(file_path):
            logger.info(f"Файл {file_name} не является архивом")
            await message.answer("Это не архив.")
            return

        try:
            extract_archive(file_path, tmpdir)
        except Exception as e:
            logger.error(f"Ошибка распаковки: {e}")
            await message.answer(f"Не удалось распаковать архив: {e}")
            return

        count = 0
        for root, dirs, files in os.walk(tmpdir):
            for file in files:
                if file == file_name:
                    continue
                file_path_send = os.path.join(root, file)
                logger.info(f"Отправка файла {file_path_send} пользователю {user_id}")
                await message.answer_document(FSInputFile(file_path_send))
                count += 1

        if count == 0:
            logger.info(f"В архиве не найдено файлов для отправки")
            await message.answer("В архиве нет файлов для отправки.")
        else:
            logger.info(f"Отправлено {count} файлов пользователю {user_id}")
            await message.answer("Готово ✅✅✅✅✅✅")


async def main():
    logger.info("Запуск бота")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
