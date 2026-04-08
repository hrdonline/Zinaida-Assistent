import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import pytz

# — НАСТРОЙКИ —

BOT_TOKEN = "8631951692:AAHGFkXrNVkrDB5z_C_5SLH1Vg5NuNm1asQ"
YOUR_ID = 682778809
MOSCOW = pytz.timezone(“Europe/Moscow”)

logging.basicConfig(level=logging.INFO)

# — СТРУКТУРА ДАННЫХ —

# Всё хранится здесь. Легко добавлять/убирать проекты и клиентов.

state = {
# Активные проекты — добавляй/убирай сколько нужно
“projects”: {
“Проект 1”: “статус”,
“Проект 2”: “статус”,
“Проект 3”: “статус”,
},

```
# Воронка продаж — текущие клиенты и лиды
"pipeline": {
    "Клиент 1 (название работы)": "статус",
    "Лид 1 (название услуги)": "КП не отправлено",
    "Лид 2 (название услуги)": "КП не отправлено",
},

# Встречи на сегодня — очищаются командой /clear_meetings
"meetings": [],

# Контент-план — платформы
"content": {
    "Telegram-канал": "0 постов на этой неделе",
    "ВКонтакте": "0 постов на этой неделе",
    "LinkedIn": "0 постов на этой неделе",
    "VC.ru": "0 статей на этой неделе",
},

# Финансы — обновляй через /update_finance
"finance": {
    "Ожидается на этой неделе": "0 руб",
    "Пришло вчера": "0 руб",
    "Следующий шаг для дохода": "не указан",
},

# Системное — ожидание ответа от пользователя
"waiting_for": None,
"waiting_key": None,
```

}

WEEKLY_QUESTIONS = [
“Ты двигаешься к цели или просто занята?”,
“Что изменилось в рынке на этой неделе?”,
“Что ты узнала про своих клиентов?”,
“Что ты делаешь сама — и что можно отдать?”,
“Где ты теряешь энергию и можно ли это остановить?”,
“Какое решение ты откладываешь уже больше недели?”,
“Что одно действие дало бы максимальный результат прямо сейчас?”,
]

# — ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ —

def get_week_question():
week = datetime.now(MOSCOW).isocalendar()[1]
return WEEKLY_QUESTIONS[week % len(WEEKLY_QUESTIONS)]

def format_dict(d: dict, prefix=”  “) -> str:
return “\n”.join(f”{prefix}{k}: {v}” for k, v in d.items())

def format_meetings() -> str:
if not state[“meetings”]:
return “  Встречи не добавлены”
return “\n”.join(f”  - {m}” for m in state[“meetings”])

# — СООБЩЕНИЯ —

def morning_message() -> str:
now = datetime.now(MOSCOW)
months = [“января”,“февраля”,“марта”,“апреля”,“мая”,“июня”,
“июля”,“августа”,“сентября”,“октября”,“ноября”,“декабря”]
days = [“понедельник”,“вторник”,“среда”,“четверг”,“пятница”,“суббота”,“воскресенье”]
date_str = f”{now.day} {months[now.month-1]}, {days[now.weekday()]}”

```
return f"""{date_str}
```

Главный вопрос дня: что ты сделаешь сегодня, чтобы приблизить деньги?

Энергия: 10 минут только для себя до первой задачи. Выпей стакан воды прямо сейчас.

Деньги:
{format_dict(state[“finance”])}

Воронка продаж:
{format_dict(state[“pipeline”])}

Проекты:
{format_dict(state[“projects”])}

Встречи сегодня:
{format_meetings()}

Контент на этой неделе:
{format_dict(state[“content”])}

Решение: есть что-то, что ты откладываешь? Назови это себе прямо сейчас.

Напиши /add_meeting чтобы добавить встречу на сегодня.”””

def evening_message() -> str:
return “”“Вечерний разбор.

Три вопроса — ответь честно:

1. Что сделала из запланированного сегодня?
1. Что не сделала и почему?
1. Один вывод про этот день.

Тело: была прогулка? Выпила достаточно воды?

Деньги: что сдвинулось по воронке сегодня?

Обнови статусы если что-то изменилось:
/update_pipeline — воронка
/update_finance — финансы
/update_content — контент”””

def sunday_message() -> str:
return f””“Итоги недели.

Без оценок, только факты.

Проекты — что продвинулось, что застряло?
{format_dict(state[“projects”])}

Воронка — текущий статус:
{format_dict(state[“pipeline”])}

Контент за неделю:
{format_dict(state[“content”])}

Один честный вывод про себя за эту неделю.

Стратегический вопрос: {get_week_question()}

Обнови данные на следующую неделю:
/update_pipeline /update_projects /update_content /update_finance”””

# — ПЛАНИРОВЩИК —

async def scheduler(app):
sent = set()
while True:
now = datetime.now(MOSCOW)
key_morning = f”morning_{now.date()}”
key_evening = f”evening_{now.date()}”
key_sunday = f”sunday_{now.date()}”

```
    if now.hour == 8 and now.minute == 0 and key_morning not in sent:
        await app.bot.send_message(chat_id=YOUR_ID, text=morning_message())
        sent.add(key_morning)

    if now.hour == 20 and now.minute == 0 and key_evening not in sent:
        await app.bot.send_message(chat_id=YOUR_ID, text=evening_message())
        sent.add(key_evening)

    if now.hour == 19 and now.minute == 0 and now.weekday() == 6 and key_sunday not in sent:
        await app.bot.send_message(chat_id=YOUR_ID, text=sunday_message())
        sent.add(key_sunday)

    await asyncio.sleep(30)
```

# — КОМАНДЫ —

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(
“Бизнес-ассистент активен.\n\n”
“Просмотр:\n”
“/morning — утренняя сводка\n”
“/evening — вечерний разбор\n”
“/week — итоги недели\n”
“/pipeline — воронка продаж\n”
“/projects — проекты\n”
“/finance — финансы\n”
“/content — контент\n”
“/meetings — встречи сегодня\n\n”
“Обновление:\n”
“/update_pipeline — обновить воронку\n”
“/update_projects — обновить проекты\n”
“/update_finance — обновить финансы\n”
“/update_content — обновить контент\n”
“/add_meeting — добавить встречу\n”
“/clear_meetings — очистить встречи”
)

async def cmd_morning(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(morning_message())

async def cmd_evening(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(evening_message())

async def cmd_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(sunday_message())

async def cmd_pipeline(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(“Воронка продаж:\n\n” + format_dict(state[“pipeline”]))

async def cmd_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(“Проекты:\n\n” + format_dict(state[“projects”]))

async def cmd_finance(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(“Финансы:\n\n” + format_dict(state[“finance”]))

async def cmd_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(“Контент:\n\n” + format_dict(state[“content”]))

async def cmd_meetings(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(“Встречи сегодня:\n\n” + format_meetings())

async def cmd_add_meeting(update: Update, context: ContextTypes.DEFAULT_TYPE):
state[“waiting_for”] = “add_meeting”
await update.message.reply_text(“Напиши встречу.\nПример: 14:00 — созвон с клиентом”)

async def cmd_clear_meetings(update: Update, context: ContextTypes.DEFAULT_TYPE):
state[“meetings”] = []
await update.message.reply_text(“Встречи очищены.”)

# — УНИВЕРСАЛЬНОЕ ОБНОВЛЕНИЕ СЛОВАРЕЙ —

def build_update_prompt(section_name: str, d: dict) -> str:
lines = [f”Что обновить в разделе ‘{section_name}’?”, “Напиши: номер: новый статус\n”]
for i, (k, v) in enumerate(d.items(), 1):
lines.append(f”{i}. {k}: {v}”)
lines.append(”\nПример: 2: Договор подписан”)
return “\n”.join(lines)

async def start_update(update: Update, section: str):
d = state[section]
state[“waiting_for”] = f”update_{section}”
await update.message.reply_text(build_update_prompt(section, d))

async def cmd_update_pipeline(update: Update, context: ContextTypes.DEFAULT_TYPE):
await start_update(update, “pipeline”)

async def cmd_update_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
await start_update(update, “projects”)

async def cmd_update_finance(update: Update, context: ContextTypes.DEFAULT_TYPE):
await start_update(update, “finance”)

async def cmd_update_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
await start_update(update, “content”)

# — ОБРАБОТКА ТЕКСТА —

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
text = update.message.text
wf = state[“waiting_for”]

```
if wf == "add_meeting":
    state["meetings"].append(text)
    state["waiting_for"] = None
    await update.message.reply_text(f"Встреча добавлена: {text}")

elif wf and wf.startswith("update_"):
    section = wf.replace("update_", "")
    try:
        parts = text.split(":", 1)
        idx = int(parts[0].strip()) - 1
        new_val = parts[1].strip()
        keys = list(state[section].keys())
        key = keys[idx]
        state[section][key] = new_val
        state["waiting_for"] = None
        await update.message.reply_text(f"Обновлено:\n{key}: {new_val}")
    except Exception:
        await update.message.reply_text(
            "Не понял формат. Попробуй ещё раз.\nПример: 1: Новый статус"
        )
else:
    await update.message.reply_text(
        "Принято. Напиши /start чтобы увидеть все команды."
    )
```

# — ЗАПУСК —

async def main():
app = Application.builder().token(BOT_TOKEN).build()

```
app.add_handler(CommandHandler("start", cmd_start))
app.add_handler(CommandHandler("morning", cmd_morning))
app.add_handler(CommandHandler("evening", cmd_evening))
app.add_handler(CommandHandler("week", cmd_week))
app.add_handler(CommandHandler("pipeline", cmd_pipeline))
app.add_handler(CommandHandler("projects", cmd_projects))
app.add_handler(CommandHandler("finance", cmd_finance))
app.add_handler(CommandHandler("content", cmd_content))
app.add_handler(CommandHandler("meetings", cmd_meetings))
app.add_handler(CommandHandler("add_meeting", cmd_add_meeting))
app.add_handler(CommandHandler("clear_meetings", cmd_clear_meetings))
app.add_handler(CommandHandler("update_pipeline", cmd_update_pipeline))
app.add_handler(CommandHandler("update_projects", cmd_update_projects))
app.add_handler(CommandHandler("update_finance", cmd_update_finance))
app.add_handler(CommandHandler("update_content", cmd_update_content))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

await app.initialize()
await app.start()
await app.updater.start_polling()

asyncio.create_task(scheduler(app))

print("Бот запущен. Timezone: Moscow. Ctrl+C для остановки.")
await asyncio.Event().wait()
```

if **name** == “**main**”:
asyncio.run(main())
