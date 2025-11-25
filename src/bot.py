import asyncio
import base64
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import BufferedInputFile
from aiogram import F

# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
# ВСТАВЬ СЮДА СВОЙ НОВЫЙ ТОКЕН ОТ @grok_camera_bot
API_TOKEN = "8205771927:AAG14vgGguDnDpWw_0VvTwvsaDam8wc5jpc"
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
KIE_API_KEY = "ef16727943715a5fe31680e1a6630e26"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Я Grok Imagine Video Bot 🎥\n\n"
        "Кидай фото + в подписи напиши движение камеры\n\n"
        "Примеры:\n"
        "• пролёт слева направо\n"
        "• камера приближается\n"
        "• облёт по кругу сверху\n"
        "• медленно отъезжает назад\n\n"
        "Видео 5–8 сек с аудио через 15–60 сек"
    )

@dp.message(F.photo & F.caption)
async def handle(message: types.Message):
    await message.reply("Скачиваю фото...")
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    photo_bytes = await bot.download_file(file.file_path)
image_b64 = base64.b64encode(photo_bytes.read()).decode()  # ← убрали await
    prompt = message.caption.strip()
    await message.reply(f"Генерирую видео...\nДвижение: {prompt}")

    payload = {
        "model": "grok-imagine-0.1",
        "prompt": prompt,
        "image": image_b64,
        "duration": 5,
        "quality": "720p",
        "aspectRatio": "16:9",
        "audio": True
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.kie.ai/v1/grok-imagine/video",
            json=payload,
            headers={"Authorization": f"Bearer {KIE_API_KEY}"}
        ) as resp:
            if resp.status != 200:
                await message.reply("Ошибка генерации")
                return
            data = await resp.json()
            task_id = data.get("task_id")

    video_url = None
    for i in range(30):
        await asyncio.sleep(6)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.kie.ai/v1/tasks/status",
                json={"task_id": task_id},
                headers={"Authorization": f"Bearer {KIE_API_KEY}"}
            ) as resp:
                result = await resp.json()
                if result.get("status") == "completed":
                    video_url = result.get("video_url")
                    break
        await message.reply(f"Генерация… {i*6 + 6} сек")

    if video_url:
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as r:
                if r.status == 200:
                    video_file = BufferedInputFile(await r.read(), "video.mp4")
                    await message.answer_video(video_file, caption=f"🎥 {prompt}")
    else:
        await message.reply("Таймаут")

async def main():
    print("Бот запущен!")                # ←←← ЭТА СТРОКА ОБЯЗАТЕЛЬНО ДОЛЖНА БЫТЬ
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
