import customtkinter as ctk
import json
import os
from datetime import datetime
from tkinter import messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

DATA_FILE = "smoke_data.json"

# ─── АЧИВКИ (часы без курения, иконка, название, описание) ───────────────────
ACHIEVEMENTS = [
    (1,    "⚡", "Первый час",        "1 час без никотина — уровень CO в крови упал вдвое!"),
    (8,    "🌙", "Первая ночь",       "8 часов! Никотин почти выведен из крови."),
    (24,   "🌅", "Первые сутки",      "24 часа! Риск сердечного приступа уже снизился."),
    (48,   "👃", "Нюхач",             "48 часов — обоняние и вкус начали возвращаться!"),
    (72,   "💨", "Чистые лёгкие",     "3 дня! Никотина в теле больше нет. Ты справился!"),
    (168,  "🗓️", "Неделя",           "1 неделя! Кровообращение значительно улучшилось."),
    (336,  "💪", "Две недели",        "2 недели! Ходьба и бег стали легче."),
    (720,  "🏆", "Месяц",             "1 месяц без курения! Ты — боец."),
    (2160, "🌿", "Три месяца",        "3 месяца! Функция лёгких выросла на 30%."),
    (4380, "🦅", "Полгода",           "6 месяцев! Кашель и одышка почти исчезли."),
    (8760, "👑", "ГОД БЕЗ СИГАРЕТ",  "1 год! Риск болезней сердца снизился вдвое. ЛЕГЕНДА!"),
]

# ─── МОТИВАЦИОННЫЕ СООБЩЕНИЯ по временным зонам ──────────────────────────────
MOTIVATIONS = [
    (0,   "Каждая минута без сигареты — победа. Держись!"),
    (1,   "Первый час позади. Твоё тело уже благодарит тебя."),
    (6,   "Полдня! Углекислый газ покидает кровь прямо сейчас."),
    (24,  "День прошёл. Ты сильнее, чем думал."),
    (48,  "Два дня! Нервные окончания вкуса восстанавливаются."),
    (72,  "Трое суток! Никотина в организме больше нет. Серьёзно."),
    (168, "Неделя! Скажи кому-нибудь — ты заслужил похвалу."),
    (336, "Две недели. Лёгкие чище. Дыхание свободнее."),
    (720, "Месяц! Ты уже не зависимый — ты просто человек, который не курит."),
]

# ─── ФРАЗЫ ПРИ ЖЕЛАНИИ ПОКУРИТЬ ──────────────────────────────────────────────
CRAVING_TIPS = [
    "Выпей стакан холодной воды. Медленно. Тяга пройдёт через 3 минуты.",
    "Сделай 10 глубоких вдохов. Живот вперёд на вдохе.",
    "Пожуй жвачку или съешь что-нибудь хрустящее.",
    "Встань и пройдись. Тяга спадает при движении.",
    "Напомни себе: одна сигарета перечёркивает весь прогресс.",
    "Засеки 5 минут. Просто переживи их — тяга пройдёт сама.",
    "Позвони кому-нибудь или напиши другу. Отвлекись.",
    "Посмотри на свой таймер — ты слишком много вложил, чтобы сдаться.",
]
_craving_idx = 0


class QuitSmokingApp:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("🚭 Бросаю курить")
        self.window.geometry("440x700")
        self.window.resizable(False, False)

        self.data = self.load_data()
        self.running = True
        self._last_notified_achievement = set(self.data.get("notified_achievements", []))

        self.build_ui()
        self.update_timer()
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.window.mainloop()

    # ── Данные ────────────────────────────────────────────────────────────────
    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "quit_date": datetime.now().isoformat(),
            "price_per_pack": 200,
            "cigs_per_day": 15,
            "cigs_per_pack": 20,
            "relapses": [],
            "notified_achievements": [],
        }

    def save_data(self):
        self.data["notified_achievements"] = list(self._last_notified_achievement)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    # ── Интерфейс ─────────────────────────────────────────────────────────────
    def build_ui(self):
        ctk.CTkLabel(
            self.window, text="🚭 Дыши свободно",
            font=ctk.CTkFont(size=26, weight="bold")
        ).pack(pady=(16, 4))

        # Таймер
        self.timer_label = ctk.CTkLabel(
            self.window, text="00 дн. 00:00:00",
            font=ctk.CTkFont(size=34, weight="bold")
        )
        self.timer_label.pack(pady=6)

        # Мотивационное сообщение
        self.motiv_label = ctk.CTkLabel(
            self.window, text="",
            font=ctk.CTkFont(size=12),
            text_color="#aaffaa",
            wraplength=390,
        )
        self.motiv_label.pack(pady=(0, 8))

        # Карточки статистики (2 в ряд)
        row = ctk.CTkFrame(self.window, fg_color="transparent")
        row.pack(padx=20, fill="x")

        self.cig_label  = self._stat_card(row, "🚬 Не выкурено", "0 сигарет",  side="left")
        self.money_label = self._stat_card(row, "💰 Сэкономлено", "0 ₽",       side="right")

        # Прогресс здоровья
        ctk.CTkLabel(
            self.window, text="Восстановление организма",
            font=ctk.CTkFont(size=12)
        ).pack(pady=(14, 4))

        self.health_bar = ctk.CTkProgressBar(self.window, width=380, height=18)
        self.health_bar.pack()
        self.health_bar.set(0)

        self.health_text = ctk.CTkLabel(
            self.window, text="", font=ctk.CTkFont(size=11), text_color="#88ccff"
        )
        self.health_text.pack(pady=4)

        # ── Ачивки ────────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self.window, text="🏅 Достижения",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(pady=(12, 4))

        ach_outer = ctk.CTkFrame(self.window, fg_color="#1a1a2e", corner_radius=12)
        ach_outer.pack(padx=20, fill="x")

        self.ach_scroll = ctk.CTkScrollableFrame(
            ach_outer, height=100, fg_color="transparent"
        )
        self.ach_scroll.pack(fill="x", padx=4, pady=4)

        self.ach_labels = {}
        row_frame = None
        for i, (hours, icon, name, desc) in enumerate(ACHIEVEMENTS):
            if i % 3 == 0:
                row_frame = ctk.CTkFrame(self.ach_scroll, fg_color="transparent")
                row_frame.pack(fill="x", pady=1)
            lbl = ctk.CTkLabel(
                row_frame,
                text=f"{icon}\n{name}",
                font=ctk.CTkFont(size=10),
                width=110, height=50,
                corner_radius=8,
                fg_color="#2a2a3e",
                text_color="#555566",
            )
            lbl.pack(side="left", padx=3)
            self.ach_labels[hours] = lbl

        # ── Кнопки ────────────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        btn_frame.pack(pady=14)

        ctk.CTkButton(
            btn_frame, text="⚙️ Настройки", width=130,
            command=self.open_settings
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame, text="💬 Хочу курить", width=140,
            fg_color="#555500", hover_color="#777700",
            command=self.craving_help
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame, text="❌ СРЫВ", width=100,
            fg_color="#8B0000", hover_color="#A00000",
            command=self.relapse
        ).pack(side="left", padx=8)

        # Статистика срывов
        self.stats_label = ctk.CTkLabel(
            self.window, text="", font=ctk.CTkFont(size=11), text_color="gray"
        )
        self.stats_label.pack(pady=4)

    def _stat_card(self, parent, title, default, side):
        frame = ctk.CTkFrame(parent, fg_color="#2B2B2B", corner_radius=12)
        frame.pack(side=side, expand=True, fill="x", padx=5, pady=4)
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=12)).pack(pady=(8,0))
        lbl = ctk.CTkLabel(frame, text=default, font=ctk.CTkFont(size=22, weight="bold"))
        lbl.pack(pady=(2, 8))
        return lbl

    # ── Таймер и логика ───────────────────────────────────────────────────────
    def update_timer(self):
        if not self.running:
            return

        quit_date = datetime.fromisoformat(self.data["quit_date"])
        now = datetime.now()
        if now < quit_date:
            self.timer_label.configure(text="Ещё не начали")
            self.window.after(1000, self.update_timer)
            return

        delta = now - quit_date
        days = delta.days
        hours_total = delta.total_seconds() / 3600
        hours, rem = divmod(delta.seconds, 3600)
        mins, secs = divmod(rem, 60)

        self.timer_label.configure(text=f"{days} дн. {hours:02d}:{mins:02d}:{secs:02d}")

        # Сигареты и деньги
        cigs = (delta.total_seconds() / 86400) * self.data["cigs_per_day"]
        money = (cigs / self.data["cigs_per_pack"]) * self.data["price_per_pack"]
        self.cig_label.configure(text=f"{int(cigs)} сигарет")
        self.money_label.configure(text=f"{int(money)} ₽")

        # Прогресс здоровья
        if hours_total < 72:
            progress = (hours_total / 72) * 0.3
            stage = "Угарный газ выводится из крови"
        elif hours_total < 336:
            progress = 0.3 + ((hours_total - 72) / 264) * 0.3
            stage = "Улучшается кровообращение"
        elif hours_total < 720:
            progress = 0.6 + ((hours_total - 336) / 384) * 0.2
            stage = "Восстанавливаются лёгкие"
        else:
            progress = min(0.8 + ((hours_total - 720) / 8040) * 0.2, 1.0)
            stage = "Риск инфаркта снижается"
        self.health_bar.set(progress)
        self.health_text.configure(text=f"{stage}  •  {int(progress*100)}%")

        # Мотивационное сообщение
        msg = MOTIVATIONS[0][1]
        for h, text in MOTIVATIONS:
            if hours_total >= h:
                msg = text
        self.motiv_label.configure(text=f'"{msg}"')

        # Ачивки
        self._update_achievements(hours_total)

        # Срывы
        n = len(self.data.get("relapses", []))
        self.stats_label.configure(
            text=f"Срывов: {n}" if n > 0 else "Срывов не было! 💪"
        )

        self.window.after(1000, self.update_timer)

    def _update_achievements(self, hours_total):
        for hours, icon, name, desc in ACHIEVEMENTS:
            lbl = self.ach_labels[hours]
            if hours_total >= hours:
                lbl.configure(fg_color="#1a3a1a", text_color="#aaffaa")
                # Уведомление при первом получении
                if hours not in self._last_notified_achievement:
                    self._last_notified_achievement.add(hours)
                    self.save_data()
                    self._show_achievement_popup(icon, name, desc)
            else:
                lbl.configure(fg_color="#2a2a3e", text_color="#555566")

    def _show_achievement_popup(self, icon, name, desc):
        popup = ctk.CTkToplevel(self.window)
        popup.title("Новое достижение!")
        popup.geometry("340x200")
        popup.grab_set()
        popup.resizable(False, False)

        ctk.CTkLabel(popup, text="🏅 НОВОЕ ДОСТИЖЕНИЕ!", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#ffdd00").pack(pady=(18, 4))
        ctk.CTkLabel(popup, text=f"{icon} {name}", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="#aaffaa").pack(pady=4)
        ctk.CTkLabel(popup, text=desc, font=ctk.CTkFont(size=12),
                     wraplength=300, text_color="white").pack(pady=6)
        ctk.CTkButton(popup, text="Круто! 💪", width=120, command=popup.destroy).pack(pady=10)

    # ── Помощь при тяге ───────────────────────────────────────────────────────
    def craving_help(self):
        global _craving_idx
        tip = CRAVING_TIPS[_craving_idx % len(CRAVING_TIPS)]
        _craving_idx += 1

        popup = ctk.CTkToplevel(self.window)
        popup.title("Держись!")
        popup.geometry("360x200")
        popup.grab_set()
        popup.resizable(False, False)

        ctk.CTkLabel(popup, text="💬 Тяга — это временно!",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color="#ffaa00").pack(pady=(18, 10))
        ctk.CTkLabel(popup, text=tip, font=ctk.CTkFont(size=13),
                     wraplength=320, text_color="white").pack(pady=4)
        ctk.CTkButton(popup, text="Понял, держусь! 💪", width=180,
                      command=popup.destroy).pack(pady=16)

    # ── Срыв ──────────────────────────────────────────────────────────────────
    def relapse(self):
        if messagebox.askyesno("Подтверждение", "Вы действительно сорвались?\nСчётчик будет сброшен."):
            quit_date = datetime.fromisoformat(self.data["quit_date"])
            days_clean = (datetime.now() - quit_date).days
            self.data["relapses"].append({
                "date": datetime.now().isoformat(),
                "days_clean": days_clean
            })
            self.data["quit_date"] = datetime.now().isoformat()
            self._last_notified_achievement.clear()
            self.save_data()
            self.timer_label.configure(text_color="red")
            self.window.after(2000, lambda: self.timer_label.configure(text_color="white"))

    # ── Настройки ─────────────────────────────────────────────────────────────
    def open_settings(self):
        dialog = ctk.CTkToplevel(self.window)
        dialog.title("Настройки")
        dialog.geometry("350x380")
        dialog.grab_set()
        dialog.resizable(False, False)

        fields = [
            ("Дата бросания (ГГГГ-ММ-ДД ЧЧ:ММ):", "quit_date",
             self.data["quit_date"][:16]),
            ("Цена пачки (₽):", "price_per_pack", str(self.data["price_per_pack"])),
            ("Сигарет в день:", "cigs_per_day",   str(self.data["cigs_per_day"])),
            ("Сигарет в пачке:", "cigs_per_pack", str(self.data["cigs_per_pack"])),
        ]
        entries = {}
        for label, key, default in fields:
            ctk.CTkLabel(dialog, text=label).pack(pady=(10, 2))
            e = ctk.CTkEntry(dialog, width=280)
            e.insert(0, default)
            e.pack()
            entries[key] = e

        def save():
            try:
                raw = entries["quit_date"].get().strip()
                # Принимаем формат ГГГГ-ММ-ДД или с временем
                if len(raw) == 16:
                    raw += ":00"
                datetime.fromisoformat(raw)  # проверка
                self.data["quit_date"]      = raw
                self.data["price_per_pack"] = float(entries["price_per_pack"].get())
                self.data["cigs_per_day"]   = int(entries["cigs_per_day"].get())
                self.data["cigs_per_pack"]  = int(entries["cigs_per_pack"].get())
                self.save_data()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Ошибка", "Проверь формат даты и числа")

        ctk.CTkButton(dialog, text="Сохранить", command=save).pack(pady=16)

    def on_close(self):
        self.running = False
        self.window.destroy()


if __name__ == "__main__":
    QuitSmokingApp()