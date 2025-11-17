from aiogram import types
from datetime import datetime

class ScheduleToday:
    def __init__(self, dp, states, api_client):
        self.dp = dp
        self.states = states
        self.api_client = api_client

    def _format_student_message(self, schedule_date, group_name, group_schedules):
        message = f"📅 <b>Расписание на сегодня</b>\n\n"
        message += f"👥 <b>Группа:</b> {group_name}\n"
        message += f"🗓️ <b>Дата:</b> {schedule_date}\n\n"

        for i, schedule in enumerate(group_schedules):
            message += f"{i + 1}. {schedule.get('time', '')} - {schedule.get('discipline', '')}\n"
            if schedule.get('teacher'):
                message += f"   👨‍🏫 {schedule['teacher']}\n"
            if schedule.get('classroom'):
                message += f"   🏫 {schedule['classroom']}\n"
            message += "\n"

        return message

    def _format_teacher_message(self, schedule_date, teacher_name, teacher_schedules):
        message = f"📅 <b>Расписание на сегодня</b>\n\n"
        message += f"👨‍🏫 <b>Преподаватель:</b> {teacher_name}\n"
        message += f"🗓️ <b>Дата:</b> {schedule_date}\n\n"

        for i, schedule in enumerate(teacher_schedules):
            message += f"{i + 1}. {schedule.get('time', '')} - {schedule.get('discipline', '')}\n"
            if schedule.get('groups'):
                message += f"   👥 Группы: {', '.join(schedule['groups'])}\n"
            if schedule.get('classroom'):
                message += f"   🏫 {schedule['classroom']}\n"
            message += "\n"

        return message

    def register_handlers(self):
        @self.dp.message(lambda msg: msg.text == "👨‍🏫 Расписание на сегодня")
        async def schedule_today(message: types.Message):

            user_info = await self.api_client.get_user_info(message.from_user.id)

            student_group = user_info.get("group_number")
            teacher_fio = user_info.get("teacher_fio")

            if student_group:
                schedule = await self.api_client.get_schedule_today(student_group=student_group)
            elif teacher_fio:
                schedule = await self.api_client.get_schedule_today(teacher_fio=teacher_fio)
            else:
                await message.answer("❗ Вы не зарегистрированы. Пожалуйста выберите группу.")
                return

            if not schedule:
                await message.answer("❌ Сегодня расписания нет.")
                return

            today_date = datetime.now().strftime("%d.%m.%Y")

            if student_group:
                formatted = self._format_student_message(
                    schedule_date=today_date,
                    group_name=student_group,
                    group_schedules=schedule
                )
                await message.answer(formatted, parse_mode="HTML")
                return

            if teacher_fio:
                formatted = self._format_teacher_message(
                    schedule_date=today_date,
                    teacher_name=teacher_fio,
                    teacher_schedules=schedule
                )
                await message.answer(formatted, parse_mode="HTML")
                return
